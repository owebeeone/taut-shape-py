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

    __slots__ = ("_records", "_head", "_floor", "lifecycle", "error")

    def __init__(self) -> None:
        # _records is dense; index 0 holds seq=_floor. We keep it simple: a list
        # of LogRecord in seq order, with _floor tracking the earliest retained.
        self._records: list[LogRecord] = []
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
        evict-past-head, D7/D9)."""
        if up_to_seq < self._floor - 1:
            return
        evicted_through = min(up_to_seq, self._head)
        new_floor = evicted_through + 1
        # drop from the front while seq <= up_to_seq
        drop = 0
        for rec in self._records:
            if rec.seq <= up_to_seq:
                drop += 1
            else:
                break
        if drop:
            del self._records[:drop]
        if new_floor > self._floor:
            self._floor = new_floor

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
        ``max_bytes``."""
        out: list[LogRecord] = []
        used_bytes = 0
        for rec in self._records:
            if rec.seq <= from_seq:
                continue
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
