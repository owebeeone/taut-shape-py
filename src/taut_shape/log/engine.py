"""``LogNode`` — the pure mailbox engine, one per log (D1).

No I/O, no clock, no executor, no locks (the shell owns serialization, D15).
Held long-polls are engine state: a tail ``Read`` that cannot be answered is
parked in its session and answered when a later input releases it. Outputs are
a deterministic function of the input history (D16).

``handle(msg) -> list[OutMsg]`` is the whole contract surface. Read resolution
(shared §3.4), lifecycle (D12), timers (D14/D16), and the ``ProducerStop``
policy (refined D6) are all behind it, pinned by the oracle.
"""

from __future__ import annotations

from enum import Enum
from typing import NoReturn

from ._generated import (
    LogCancelTimer,
    LogClose,
    LogCursor,
    LogDiagCode,
    LogDiagnostic,
    LogEndStream,
    LogError,
    LogEvict,
    LogProducerStop,
    LogPush,
    LogReadRequest,
    LogReadResponse,
    LogRecord,
    LogSeal,
    LogSetTimer,
    LogSeverity,
    LogState,
    LogStopReason,
    LogTimerExpired,
)
from ._sessions import _Session, _SessionTable
from ._window import Lifecycle, _Window
from .messages import InMsg, OutMsg


def _assert_never(value: NoReturn) -> NoReturn:
    """``typing.assert_never`` backport (added in 3.11); the plan targets 3.10.
    A closed ``match`` over the ``InMsg`` union should never reach this."""
    raise AssertionError(f"unhandled message: {value!r}")


class StopWhen(Enum):
    """Construction knob (D6). String values are the corpus ``node.stop_when``
    tokens, so a corpus loader maps them directly."""

    LAST_READER = "last_reader"
    EXPLICIT_ONLY = "explicit"


class LogNode:
    """The engine. Construct one per log; drive it with ``handle``."""

    __slots__ = ("_log_id", "_stop_when", "_window", "_sessions", "_next_token")

    def __init__(
        self,
        *,
        log_id: str = "log-A",
        stop_when: StopWhen = StopWhen.EXPLICIT_ONLY,
    ) -> None:
        self._log_id = log_id
        self._stop_when = stop_when
        self._window = _Window()
        self._sessions = _SessionTable()
        self._next_token = 1            # monotonic timer tokens from 1 (D16)

    # ---- dispatch ------------------------------------------------------------

    def handle(self, msg: InMsg) -> list[OutMsg]:
        match msg:
            case LogPush():         return self._on_push(msg)
            case LogSeal():         return self._on_seal()
            case LogClose():        return self._on_close(msg)
            case LogReadRequest():  return self._on_read(msg)
            case LogEndStream():    return self._on_end_stream(msg)
            case LogTimerExpired(): return self._on_timer_expired(msg)
            case LogEvict():        return self._on_evict(msg)
            case _:                 _assert_never(msg)

    # ---- read-only accessors (never mutate; not part of the wire) ------------

    @property
    def head(self) -> int:
        return self._window.head

    @property
    def floor(self) -> int:
        return self._window.floor

    @property
    def min_watermark(self) -> int | None:
        return self._sessions.min_watermark()

    @property
    def stream_count(self) -> int:
        return self._sessions.reader_count

    # ---- token allocation ----------------------------------------------------

    def _alloc_token(self) -> int:
        token = self._next_token
        self._next_token += 1
        return token

    # ---- producer side -------------------------------------------------------

    def _on_push(self, msg: LogPush) -> list[OutMsg]:
        # Push after any terminal/sealed state is dropped and warned (D19).
        if self._window.is_sealed_or_terminal:
            return [
                LogDiagnostic(
                    severity=LogSeverity.warn, code=LogDiagCode.push_after_terminal
                )
            ]
        self._window.append(msg.payload)
        # A new record can release held reads (in creation order, D16).
        return self._release_held_reads()

    def _on_seal(self) -> list[OutMsg]:
        # Seal only transitions from Live; a repeated seal is a silent no-op.
        if self._window.lifecycle is not Lifecycle.LIVE:
            return []
        self._window.seal()
        # Held caught-up reads are answered `eof` by the seal itself.
        return self._release_held_reads()

    def _on_close(self, msg: LogClose) -> list[OutMsg]:
        # Refined D6: ProducerStop fires only on the TRANSITION into a terminal
        # state. A Close on an already-terminal log emits nothing (idempotent
        # outputs, symmetric with Seal).
        if self._window.is_terminal:
            return []
        transitioned = self._window.close(msg.error)
        assert transitioned  # not terminal above ⇒ this always transitions
        out: list[OutMsg] = self._release_held_reads()
        reason = (
            LogStopReason.failed
            if self._window.lifecycle is Lifecycle.FAILED
            else LogStopReason.closed
        )
        out.append(LogProducerStop(reason=reason))
        return out

    def _on_evict(self, msg: LogEvict) -> list[OutMsg]:
        self._window.evict(msg.up_to_seq)
        return []

    # ---- stream side ---------------------------------------------------------

    def _on_read(self, req: LogReadRequest) -> list[OutMsg]:
        sess = self._sessions.get_or_create(req.stream_id)
        out: list[OutMsg] = []
        # A new Read supersedes a held one (D5): drop it unanswered, cancel its
        # timer.
        prev_token = self._sessions.clear_held(sess)
        if prev_token is not None:
            out.append(LogCancelTimer(token=prev_token))

        resolved = self._resolve_read(sess, req)
        if resolved is not None:
            out.append(resolved)
            return out

        # Caught up and not terminal: hold or probe per timeout_ms (D14).
        timeout = req.timeout_ms
        if timeout == 0:
            # Immediate would_block probe; the session stays (reader counted).
            out.append(self._would_block(sess, req))
            return out
        # Hold the read (absent timeout ⇒ indefinite; >0 ⇒ hold + timer).
        token: int | None = None
        if timeout is not None and timeout > 0:
            token = self._alloc_token()
            out.append(LogSetTimer(token=token, ms=timeout))
        self._sessions.set_held(sess, req, token)
        return out

    def _on_end_stream(self, msg: LogEndStream) -> list[OutMsg]:
        sess = self._sessions.get(msg.stream_id)
        if sess is None:
            return []                    # unknown stream_id = no-op (D4)
        out: list[OutMsg] = []
        if sess.held is not None and sess.timer_token is not None:
            out.append(LogCancelTimer(token=sess.timer_token))
        had_readers = self._sessions.reader_count
        self._sessions.remove(msg.stream_id)
        out.extend(self._maybe_last_reader_stop(had_readers))
        return out

    def _on_timer_expired(self, msg: LogTimerExpired) -> list[OutMsg]:
        # 56-F6: find_by_timer is O(1) via the timer index, not an O(S) scan.
        sess = self._sessions.find_by_timer(msg.token)
        if sess is None or sess.held is None:
            return []                    # late/canceled tokens are no-ops (D14)
        held = sess.held
        self._sessions.clear_held(sess)
        return [self._would_block(sess, held)]

    # ---- read resolution helpers --------------------------------------------

    def _resolve_read(
        self, sess: _Session, req: LogReadRequest
    ) -> LogReadResponse | None:
        """Return a Response if the read resolves immediately (data / eof /
        closed / failed / expired), else ``None`` (caught up, non-terminal)."""
        cursor_seq = req.cursor.seq if req.cursor is not None else 0
        head = self._window.head
        floor = self._window.floor

        # Invalid cursor -> expired (D9). Below the retained floor, or beyond
        # head. next_cursor is the earliest resumable position.
        if cursor_seq + 1 < floor:
            return self._response(
                sess, records=(), next_seq=floor - 1, state=LogState.expired
            )
        if cursor_seq > head:
            return self._response(
                sess, records=(), next_seq=head, state=LogState.expired
            )

        # Data available (cursor strictly behind head, records retained).
        if cursor_seq < head:
            records = self._window.scan(cursor_seq, req.max_records, req.max_bytes)
            if records:
                next_seq = records[-1].seq
                return self._response(
                    sess, records=records, next_seq=next_seq, state=LogState.data
                )
            # No records despite cursor<head means the tail was evicted; the
            # earlier expired checks already covered the invalid-cursor case,
            # so falling through here means caught-up-at-floor — treat as
            # caught up below.

        # Caught up (cursor == head, or evicted-empty). Terminal states resolve
        # immediately and remain re-readable (rule 4).
        lifecycle = self._window.lifecycle
        if lifecycle is Lifecycle.SEALED:
            return self._response(
                sess, records=(), next_seq=cursor_seq, state=LogState.eof
            )
        if lifecycle is Lifecycle.CLOSED:
            return self._response(
                sess, records=(), next_seq=cursor_seq, state=LogState.closed
            )
        if lifecycle is Lifecycle.FAILED:
            return self._response(
                sess,
                records=(),
                next_seq=cursor_seq,
                state=LogState.failed,
                error=self._window.error,
            )
        return None  # Live + caught up ⇒ hold/probe (caller decides)

    def _would_block(self, sess: _Session, req: LogReadRequest) -> LogReadResponse:
        cursor_seq = req.cursor.seq if req.cursor is not None else 0
        return self._response(
            sess, records=(), next_seq=cursor_seq, state=LogState.would_block
        )

    def _response(
        self,
        sess: _Session,
        *,
        records: tuple[LogRecord, ...],
        next_seq: int,
        state: LogState,
        error: LogError | None = None,
    ) -> LogReadResponse:
        # Watermark tracks the last seq delivered to this stream (D7).
        if state is LogState.data and next_seq > sess.watermark:
            sess.watermark = next_seq
        return LogReadResponse(
            log_id=self._log_id,
            stream_id=sess.stream_id,
            records=list(records),
            next_cursor=LogCursor(seq=next_seq),
            state=state,
            error=error,
        )

    def _release_held_reads(self) -> list[OutMsg]:
        """Answer every held read that can now resolve, in stream-creation
        order (D16). A push/seal/close changed the window or lifecycle; re-run
        resolution for each held session. 56-F6: held_in_creation_order() is
        O(H), not O(S) / O(S + H log H)."""
        out: list[OutMsg] = []
        resolved_reads: list[tuple[_Session, LogReadResponse]] = []
        for sess in self._sessions.held_in_creation_order():
            assert sess.held is not None
            resolved = self._resolve_read(sess, sess.held)
            if resolved is not None:
                resolved_reads.append((sess, resolved))
        # Clear the answerable subset in one linear batch. Repeated removal
        # from the sorted rank list made a full H-reader wake O(H²).
        tokens = self._sessions.clear_held_many(
            [sess for sess, _ in resolved_reads]
        )
        for token, (_, resolved) in zip(tokens, resolved_reads, strict=True):
            if token is not None:
                out.append(LogCancelTimer(token=token))
            out.append(resolved)
        return out

    def _maybe_last_reader_stop(self, had_readers: int) -> list[OutMsg]:
        """Emit ProducerStop on the reader-count ≥1→0 transition, under
        ``stop_when=last_reader`` only (D6). Not on a never-read log."""
        if (
            self._stop_when is StopWhen.LAST_READER
            and had_readers >= 1
            and self._sessions.reader_count == 0
        ):
            return [LogProducerStop(reason=LogStopReason.last_reader_gone)]
        return []
