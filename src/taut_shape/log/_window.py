"""The store core — a bounded record window. INTERNAL (not a public seam).

No stream concepts live here (D2): just the append-only record window, its
``head``/``floor`` bounds, the ``Evict`` retention primitive, and the
sealed/closed/failed lifecycle flags. The session table (``_sessions``) and the
engine (``engine``) compose over this.

Positions (D8): the first record is ``seq = 1``; ``START = {seq: 0}``; an empty
log has ``head = 0``. ``floor`` is the earliest **retained** seq (``1`` before
any eviction); records with ``seq < floor`` have been evicted.
"""

from __future__ import annotations

from enum import Enum, auto

from ._generated import LogError, LogRecord


class Lifecycle(Enum):
    """The log's terminal-state machine (D12). ``Live`` and ``Sealed`` are
    non-terminal; ``Closed`` and ``Failed`` are terminal. ``Sealed -> Closed``
    is still a transition (a close after a seal), which the engine treats as a
    ProducerStop-emitting transition (refined D6)."""

    LIVE = auto()
    SEALED = auto()
    CLOSED = auto()
    FAILED = auto()


class _Window:
    """The append-only record window + lifecycle flags. Pure, no I/O."""

    __slots__ = ("_records", "_start", "_head", "_floor", "lifecycle", "error")

    def __init__(self) -> None:
        # _records is dense; _records[_start] holds seq=_floor (once non-empty).
        # 56-F5: `_start` is a logical index of the first retained record —
        # eviction advances it instead of `del self._records[:drop]` (O(N) per
        # call, making N incremental evictions O(N^2)); the dead prefix is
        # reclaimed by an occasional compaction (amortized O(1) per evicted
        # record) once it reaches half the backing list.
        self._records: list[LogRecord] = []
        self._start: int = 0           # logical index of the first retained record
        self._head: int = 0            # last assigned seq (0 = empty), D8
        self._floor: int = 1           # earliest retained seq (1 before eviction)
        self.lifecycle: Lifecycle = Lifecycle.LIVE
        self.error: LogError | None = None   # attached on Close{error} (D12)

    # --- lifecycle predicates -------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        return self.lifecycle in (Lifecycle.CLOSED, Lifecycle.FAILED)

    @property
    def is_sealed_or_terminal(self) -> bool:
        """A Push is dropped once the log is no longer Live (D19)."""
        return self.lifecycle is not Lifecycle.LIVE

    # --- bounds ---------------------------------------------------------------

    @property
    def head(self) -> int:
        return self._head

    @property
    def floor(self) -> int:
        return self._floor

    # --- mutations ------------------------------------------------------------

    def append(self, payload: bytes) -> int:
        """Assign ``seq := head + 1`` (first record seq=1, D8), append, return
        the new seq. Callers must guard against terminal state (D19); this
        method assumes it is allowed to append."""
        self._head += 1
        self._records.append(LogRecord(seq=self._head, payload=payload))
        return self._head

    def evict(self, up_to_seq: int) -> None:
        """Drop records with ``seq <= up_to_seq``, raising the floor (D7). The
        floor never regresses; eviction past the head is allowed (empties the
        window). The new floor is the lowest retained seq — ``up_to_seq + 1``,
        but clamped to ``head + 1`` so eviction never claims to drop beyond head
        (matches the reference: ``next_cursor = floor - 1`` stays ``<= head`` on
        evict-past-head, D7/D9).

        56-F5: advances the logical ``_start`` index instead of
        ``del self._records[:drop]`` on every call (O(N) per call, making N
        incremental evictions O(N^2)). The dead prefix ``[0, _start)`` is
        reclaimed by a single ``del`` only once it reaches half the backing
        list, so the amortized cost per evicted record stays O(1)."""
        if up_to_seq < self._floor - 1:
            return
        evicted_through = min(up_to_seq, self._head)
        new_floor = evicted_through + 1
        n = len(self._records)
        i = self._start
        while i < n and self._records[i].seq <= up_to_seq:
            i += 1
        self._start = i
        if new_floor > self._floor:
            self._floor = new_floor
        if self._start > 0 and self._start * 2 >= len(self._records):
            del self._records[: self._start]
            self._start = 0

    def seal(self) -> None:
        if self.lifecycle is Lifecycle.LIVE:
            self.lifecycle = Lifecycle.SEALED

    def close(self, error: LogError | None) -> bool:
        """Transition into a terminal state. Returns ``True`` iff this call
        performed the transition (i.e. the log was non-terminal). First-terminal
        wins: a Close after Seal still transitions; a Close on an already-closed
        or already-failed log is a no-op returning ``False`` (refined D6)."""
        if self.is_terminal:
            return False
        if error is not None:
            self.lifecycle = Lifecycle.FAILED
            self.error = error
        else:
            self.lifecycle = Lifecycle.CLOSED
        return True

    # --- reads ----------------------------------------------------------------

    def scan(
        self, from_seq: int, max_records: int | None, max_bytes: int | None
    ) -> tuple[LogRecord, ...]:
        """Records with ``seq > from_seq``, bounded by ``max_records`` and
        ``max_bytes`` (raw payload bytes only). Forward progress (D10): if any
        record is available, return at least one even if it alone exceeds
        ``max_bytes``.

        56-F5: ``_records[_start + i].seq == front.seq + i`` (dense-sequence
        invariant: ``append`` only assigns the next seq, ``evict`` only
        advances ``_start``), so the first candidate index is computed
        directly from the front record's seq instead of scanning from the
        front and skipping already-consumed records. A read is O(K) for K
        returned records rather than O(N) in the retained window size."""
        out: list[LogRecord] = []
        n = len(self._records)
        if self._start >= n:
            return tuple(out)
        front_seq = self._records[self._start].seq
        offset = from_seq - front_seq + 1 if from_seq >= front_seq else 0
        start = self._start + offset
        used_bytes = 0
        for i in range(start, n):
            rec = self._records[i]
            if max_records is not None and len(out) >= max_records:
                break
            rec_bytes = len(rec.payload)
            if (
                max_bytes is not None
                and out                         # forward progress: never on the first
                and used_bytes + rec_bytes > max_bytes
            ):
                break
            out.append(rec)
            used_bytes += rec_bytes
        return tuple(out)
