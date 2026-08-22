"""The session table — one entry per stream instance. INTERNAL.

No byte/retention concepts here (D3): just the per-stream read loop state — the
held ``Read`` (≤1 outstanding, D5), its timer token, the delivery watermark
(D7), and the creation tick that fixes multi-release emission order (D16).

Reader-count tracking for ``ProducerStop`` (D6) is derived from this table: a
session counts as a live reader from creation until ``EndStream``.
"""

from __future__ import annotations

import bisect
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
    is preserved via an insertion-ordered dict + a monotonic tick.

    56-F6: ``_held_ranks``/``_rank_to_id`` and ``_timer_index`` are auxiliary
    indices kept in lockstep with ``session.held``/``session.timer_token`` by
    ``set_held``/``clear_held`` (the only two ways those fields may change).
    They hold *only* the currently held sessions, so a wake
    (``held_in_creation_order``) touches ``H`` (held reads) instead of ``S``
    (all live streams) — the insertion-ordered ``_sessions`` dict already
    makes the ``sorted(...)`` this replaces redundant, but sorting/filtering
    all of ``_sessions`` on every wake is still ``O(S)``/``O(S + H log H)`` —
    and a timer expiry (``find_by_timer``) is an O(1) dict lookup instead of
    an O(S) scan.
    """

    __slots__ = ("_sessions", "_tick", "_held_ranks", "_rank_to_id", "_timer_index")

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._tick: int = 0
        # Sorted ascending creation ticks of sessions that currently hold a
        # read (D16); kept via bisect insert/remove so a wake touches only H
        # (held count) work, not S (live stream count).
        self._held_ranks: list[int] = []
        self._rank_to_id: dict[int, str] = {}
        # timer_token -> stream_id (D14): O(1) expiry lookup instead of an
        # O(S) scan for a matching token.
        self._timer_index: dict[int, str] = {}

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
        """Remove a stream instance (D4 EndStream). Clears any auxiliary
        held/timer index entries for it (56-F6)."""
        sess = self._sessions.pop(stream_id, None)
        if sess is not None and sess.held is not None:
            self._remove_held_rank(sess.created)
            if sess.timer_token is not None:
                self._timer_index.pop(sess.timer_token, None)
        return sess

    @property
    def reader_count(self) -> int:
        return len(self._sessions)

    def set_held(
        self, sess: _Session, held: LogReadRequest, timer_token: int | None
    ) -> None:
        """Park (or replace) ``sess``'s held read, updating the creation-order
        and timer indices in lockstep (D16/D14). The caller must have already
        released any prior held read via ``clear_held``."""
        sess.held = held
        sess.timer_token = timer_token
        self._insert_held_rank(sess.created)
        self._rank_to_id[sess.created] = sess.stream_id
        if timer_token is not None:
            self._timer_index[timer_token] = sess.stream_id

    def clear_held(self, sess: _Session) -> int | None:
        """Release ``sess``'s held read, if any, clearing both auxiliary
        indices. Returns the cancelled timer token, if any (a no-op,
        returning ``None``, when the session was not held)."""
        if sess.held is None:
            return None
        self._remove_held_rank(sess.created)
        self._rank_to_id.pop(sess.created, None)
        token = sess.timer_token
        if token is not None:
            self._timer_index.pop(token, None)
        sess.held = None
        sess.timer_token = None
        return token

    def clear_held_many(self, sessions: list[_Session]) -> list[int | None]:
        """Release a wake batch in one pass over the held-rank index.

        Returned timer tokens align with ``sessions``. Filtering the rank list
        once makes clearing H reads O(H), rather than H repeated list pops
        (O(H²)).
        """
        if not sessions:
            return []
        ranks = {sess.created for sess in sessions if sess.held is not None}
        tokens: list[int | None] = []
        for sess in sessions:
            if sess.held is None:
                tokens.append(None)
                continue
            self._rank_to_id.pop(sess.created, None)
            token = sess.timer_token
            tokens.append(token)
            if token is not None:
                self._timer_index.pop(token, None)
            sess.held = None
            sess.timer_token = None
        if ranks:
            self._held_ranks = [rank for rank in self._held_ranks if rank not in ranks]
        return tokens

    def held_in_creation_order(self) -> list[_Session]:
        """All sessions with a held read, ordered by creation tick (D16).
        O(H): ``_held_ranks`` contains only held sessions' ticks."""
        return [self._sessions[self._rank_to_id[r]] for r in self._held_ranks]

    def find_by_timer(self, token: int) -> _Session | None:
        """The session whose held read is waiting on ``token``, if any (D14).
        O(1) via the timer index, instead of scanning held sessions."""
        stream_id = self._timer_index.get(token)
        return self._sessions.get(stream_id) if stream_id is not None else None

    def min_watermark(self) -> int | None:
        if not self._sessions:
            return None
        return min(s.watermark for s in self._sessions.values())

    def _insert_held_rank(self, rank: int) -> None:
        bisect.insort(self._held_ranks, rank)

    def _remove_held_rank(self, rank: int) -> None:
        i = bisect.bisect_left(self._held_ranks, rank)
        if i < len(self._held_ranks) and self._held_ranks[i] == rank:
            self._held_ranks.pop(i)
