"""The session table — one entry per stream instance. INTERNAL.

No byte/retention concepts here (D3): just the per-stream read loop state — the
held ``Read`` (≤1 outstanding, D5), its timer token, the delivery watermark
(D7), and the creation tick that fixes multi-release emission order (D16).

Reader-count tracking for ``ProducerStop`` (D6) is derived from this table: a
session counts as a live reader from creation until ``EndStream``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._generated import LogReadRequest


@dataclass(slots=True)
class _Session:
    stream_id: str
    created: int                       # creation-order tick (D16 emission order)
    held: LogReadRequest | None = None  # ≤1 outstanding; a new Read supersedes (D5)
    timer_token: int | None = None      # canceled on supersede/EndStream/Close
    watermark: int = 0                  # last seq delivered to this stream (D7)


class _SessionTable:
    """The set of live stream instances, keyed by ``stream_id``. Creation order
    is preserved via an insertion-ordered dict + a monotonic tick."""

    __slots__ = ("_sessions", "_tick")

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._tick: int = 0

    def get(self, stream_id: str) -> _Session | None:
        return self._sessions.get(stream_id)

    def get_or_create(self, stream_id: str) -> _Session:
        """First use of a stream_id implicitly creates the session (D4)."""
        sess = self._sessions.get(stream_id)
        if sess is None:
            self._tick += 1
            sess = _Session(stream_id=stream_id, created=self._tick)
            self._sessions[stream_id] = sess
        return sess

    def remove(self, stream_id: str) -> _Session | None:
        return self._sessions.pop(stream_id, None)

    @property
    def reader_count(self) -> int:
        return len(self._sessions)

    def held_in_creation_order(self) -> list[_Session]:
        """All sessions with a held read, ordered by creation tick (D16)."""
        return sorted(
            (s for s in self._sessions.values() if s.held is not None),
            key=lambda s: s.created,
        )

    def find_by_timer(self, token: int) -> _Session | None:
        for s in self._sessions.values():
            if s.timer_token == token:
                return s
        return None

    def min_watermark(self) -> int | None:
        if not self._sessions:
            return None
        return min(s.watermark for s in self._sessions.values())
