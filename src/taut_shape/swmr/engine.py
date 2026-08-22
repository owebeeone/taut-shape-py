"""Single-writer snapshot plus retained deltas (`swmr.oracle/v1`)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..log.engine import StopWhen
from . import _generated as g

SwmrInput: TypeAlias = (
    g.SwmrSnapshotPush
    | g.SwmrDeltaPush
    | g.SwmrReset
    | g.SwmrSeal
    | g.SwmrClose
    | g.SwmrReadRequest
    | g.SwmrEndStream
    | g.SwmrTimerExpired
)
SwmrOutput: TypeAlias = (
    g.SwmrReadResponse
    | g.SwmrSetTimer
    | g.SwmrCancelTimer
    | g.SwmrProducerStop
    | g.SwmrDiagnostic
)


class SwmrRecoveryPolicy(str, Enum):
    """Closed public profile selector; storage/resolution stays shared."""

    REPAIR = "repair"
    EXPIRE = "expire"


@dataclass(slots=True)
class _Held:
    swmr_id: str
    cursor: g.SwmrCursor | None
    timeout_ms: int | None
    timer_token: int | None


class SwmrNode:
    """Snapshot/delta store with durable reset epochs and disposable readers."""

    def __init__(
        self,
        *,
        stop_when: StopWhen = StopWhen.LAST_READER,
        max_deltas: int | None = None,
        recovery_policy: SwmrRecoveryPolicy = SwmrRecoveryPolicy.REPAIR,
    ) -> None:
        if max_deltas is not None and max_deltas < 0:
            raise ValueError("max_deltas must be non-negative or None")
        self.stop_when = stop_when
        self.max_deltas = max_deltas
        self.recovery_policy = recovery_policy
        self.snapshot: g.SwmrSnapshot | None = None
        self.deltas: list[g.SwmrDelta] = []
        self.sealed = False
        self.closed = False
        self.close_error: g.SwmrError | None = None
        self.writer_id: str | None = None
        self.epoch = 0
        self.reset_reason: g.SwmrResetReason | None = None
        self.reset_detail: bytes | None = None
        self._streams: dict[str, _Held | None] = {}
        self._order: list[str] = []
        self._next_token = 1

    @property
    def head(self) -> int:
        return 0 if self.snapshot is None else self.snapshot.seq + len(self.deltas)

    def handle(self, message: SwmrInput) -> list[SwmrOutput]:
        if isinstance(message, g.SwmrSnapshotPush):
            return self._snapshot_push(message)
        if isinstance(message, g.SwmrDeltaPush):
            return self._delta_push(message)
        if isinstance(message, g.SwmrReset):
            return self._reset(message)
        if isinstance(message, g.SwmrSeal):
            return self._seal()
        if isinstance(message, g.SwmrClose):
            return self._close(message)
        if isinstance(message, g.SwmrReadRequest):
            return self._read(message)
        if isinstance(message, g.SwmrEndStream):
            return self._end_stream(message)
        if isinstance(message, g.SwmrTimerExpired):
            return self._timer_expired(message)
        raise TypeError(f"unsupported swmr input {type(message).__name__}")

    @property
    def _terminal(self) -> bool:
        return self.sealed or self.closed

    def _check_writer(self, writer_id: str) -> bool:
        if self.writer_id is None:
            self.writer_id = writer_id
            return True
        return writer_id == self.writer_id

    @staticmethod
    def _diagnostic(code: g.SwmrDiagCode) -> list[SwmrOutput]:
        severity = (
            g.SwmrSeverity.warn
            if code is g.SwmrDiagCode.push_after_terminal
            else g.SwmrSeverity.error
        )
        return [g.SwmrDiagnostic(severity, code)]

    def _snapshot_push(self, message: g.SwmrSnapshotPush) -> list[SwmrOutput]:
        if self._terminal:
            return self._diagnostic(g.SwmrDiagCode.push_after_terminal)
        if not self._check_writer(message.writer_id):
            return self._diagnostic(g.SwmrDiagCode.writer_conflict)
        self.snapshot = g.SwmrSnapshot(self.head, bytes(message.payload))
        self.deltas = []
        return self._answer_all_held()

    def _delta_push(self, message: g.SwmrDeltaPush) -> list[SwmrOutput]:
        if self._terminal:
            return self._diagnostic(g.SwmrDiagCode.push_after_terminal)
        if not self._check_writer(message.writer_id):
            return self._diagnostic(g.SwmrDiagCode.writer_conflict)
        if self.snapshot is None:
            return self._diagnostic(g.SwmrDiagCode.delta_before_snapshot)
        if self.max_deltas is not None and len(self.deltas) >= self.max_deltas:
            return self._diagnostic(g.SwmrDiagCode.retention_bound_exceeded)
        seq = self.head + 1
        self.deltas.append(g.SwmrDelta(seq - 1, seq, bytes(message.payload)))
        return self._answer_all_held()

    def _reset(self, message: g.SwmrReset) -> list[SwmrOutput]:
        if self._terminal:
            return self._diagnostic(g.SwmrDiagCode.push_after_terminal)
        if not self._check_writer(message.writer_id):
            return self._diagnostic(g.SwmrDiagCode.writer_conflict)
        reason = message.reason
        if reason is not g.SwmrResetReason.producer_requested:
            reason = g.SwmrResetReason.producer_requested
        self.epoch += 1
        self.snapshot = None
        self.deltas = []
        self.reset_reason = reason
        self.reset_detail = None if message.detail is None else bytes(message.detail)
        outputs: list[SwmrOutput] = []
        for stream_id in self._order:
            held = self._streams.get(stream_id)
            if held is None:
                continue
            if held.cursor is None:
                response = self._resolve(
                    held.swmr_id,
                    stream_id,
                    None,
                    held.timeout_ms,
                )
                if response is not None:
                    if held.timer_token is not None:
                        outputs.append(g.SwmrCancelTimer(held.timer_token))
                    outputs.append(response)
                    self._streams[stream_id] = None
                continue
            if held.timer_token is not None:
                outputs.append(g.SwmrCancelTimer(held.timer_token))
            outputs.append(
                self._response(
                    held.swmr_id,
                    stream_id,
                    state=g.SwmrState.reset,
                    reset_reason=reason,
                    reset_detail=self.reset_detail,
                )
            )
            self._streams[stream_id] = None
        return outputs

    def _seal(self) -> list[SwmrOutput]:
        if self.sealed:
            return []
        self.sealed = True
        return self._answer_all_held()

    def _close(self, message: g.SwmrClose) -> list[SwmrOutput]:
        if self.closed:
            return []
        self.closed = True
        self.close_error = message.error
        outputs = self._answer_all_held()
        outputs.append(
            g.SwmrProducerStop(
                g.SwmrStopReason.failed
                if self.close_error is not None
                else g.SwmrStopReason.closed
            )
        )
        return outputs

    def _ensure_stream(self, stream_id: str) -> None:
        if stream_id not in self._streams:
            self._streams[stream_id] = None
            self._order.append(stream_id)

    def _read(self, message: g.SwmrReadRequest) -> list[SwmrOutput]:
        self._ensure_stream(message.stream_id)
        outputs: list[SwmrOutput] = []
        prior = self._streams[message.stream_id]
        if prior is not None and prior.timer_token is not None:
            outputs.append(g.SwmrCancelTimer(prior.timer_token))
        self._streams[message.stream_id] = None
        response = self._resolve(
            message.swmr_id,
            message.stream_id,
            message.cursor,
            message.timeout_ms,
        )
        if response is not None:
            outputs.append(response)
            return outputs
        timer_token = None
        if message.timeout_ms is not None and message.timeout_ms > 0:
            timer_token = self._next_token
            self._next_token += 1
            outputs.append(g.SwmrSetTimer(timer_token, message.timeout_ms))
        self._streams[message.stream_id] = _Held(
            message.swmr_id,
            message.cursor,
            message.timeout_ms,
            timer_token,
        )
        return outputs

    def _resolve(
        self,
        swmr_id: str,
        stream_id: str,
        cursor: g.SwmrCursor | None,
        timeout_ms: int | None,
    ) -> g.SwmrReadResponse | None:
        if cursor is not None and cursor.epoch < self.epoch:
            return self._response(
                swmr_id,
                stream_id,
                snapshot=self.snapshot,
                deltas=self.deltas if self.snapshot is not None else [],
                next_cursor=self._current_cursor(),
                state=g.SwmrState.reset,
                reset_reason=self.reset_reason or g.SwmrResetReason.producer_requested,
                reset_detail=self.reset_detail,
            )
        if cursor is not None and cursor.epoch > self.epoch:
            return self._response(
                swmr_id,
                stream_id,
                snapshot=self.snapshot,
                deltas=self.deltas if self.snapshot is not None else [],
                next_cursor=self._current_cursor(),
                state=g.SwmrState.reset,
                reset_reason=g.SwmrResetReason.invalid_resume_seq,
            )
        if self.snapshot is None:
            return self._caught_up(swmr_id, stream_id, None, timeout_ms)
        if cursor is None:
            return self._response(
                swmr_id,
                stream_id,
                snapshot=self.snapshot,
                deltas=self.deltas,
                next_cursor=self._current_cursor(),
                state=g.SwmrState.data,
            )
        if cursor.seq < self.snapshot.seq:
            return self._response(
                swmr_id,
                stream_id,
                snapshot=self.snapshot,
                deltas=self.deltas,
                next_cursor=self._current_cursor(),
                state=g.SwmrState.reset,
                reset_reason=g.SwmrResetReason.retention_exceeded,
            )
        if cursor.seq == self.head:
            return self._caught_up(
                swmr_id,
                stream_id,
                g.SwmrCursor(self.head, self.epoch),
                timeout_ms,
            )
        if cursor.seq > self.head:
            return self._response(
                swmr_id,
                stream_id,
                snapshot=self.snapshot,
                deltas=self.deltas,
                next_cursor=self._current_cursor(),
                state=g.SwmrState.reset,
                reset_reason=g.SwmrResetReason.invalid_resume_seq,
            )
        tail = self.deltas[cursor.seq - self.snapshot.seq :]
        return self._response(
            swmr_id,
            stream_id,
            deltas=tail,
            next_cursor=self._current_cursor(),
            state=g.SwmrState.data,
        )

    def _current_cursor(self) -> g.SwmrCursor | None:
        return None if self.snapshot is None else g.SwmrCursor(self.head, self.epoch)

    def _caught_up(
        self,
        swmr_id: str,
        stream_id: str,
        next_cursor: g.SwmrCursor | None,
        timeout_ms: int | None,
    ) -> g.SwmrReadResponse | None:
        if self.closed:
            return self._response(
                swmr_id,
                stream_id,
                next_cursor=next_cursor,
                state=(
                    g.SwmrState.failed
                    if self.close_error is not None
                    else g.SwmrState.closed
                ),
                error=self.close_error,
            )
        if self.sealed:
            return self._response(
                swmr_id,
                stream_id,
                next_cursor=next_cursor,
                state=g.SwmrState.eof,
            )
        if timeout_ms == 0:
            return self._response(
                swmr_id,
                stream_id,
                next_cursor=next_cursor,
                state=g.SwmrState.would_block,
            )
        return None

    @staticmethod
    def _response(
        swmr_id: str,
        stream_id: str,
        *,
        snapshot: g.SwmrSnapshot | None = None,
        deltas: list[g.SwmrDelta] | None = None,
        next_cursor: g.SwmrCursor | None = None,
        state: g.SwmrState,
        reset_reason: g.SwmrResetReason | None = None,
        error: g.SwmrError | None = None,
        reset_detail: bytes | None = None,
    ) -> g.SwmrReadResponse:
        return g.SwmrReadResponse(
            swmr_id,
            stream_id,
            None if snapshot is None else g.SwmrSnapshot(snapshot.seq, bytes(snapshot.payload)),
            []
            if deltas is None
            else [g.SwmrDelta(delta.base_seq, delta.seq, bytes(delta.payload)) for delta in deltas],
            next_cursor,
            state,
            reset_reason,
            error,
            None if reset_detail is None else bytes(reset_detail),
        )

    def _answer_all_held(self) -> list[SwmrOutput]:
        outputs: list[SwmrOutput] = []
        for stream_id in self._order:
            held = self._streams.get(stream_id)
            if held is None:
                continue
            response = self._resolve(
                held.swmr_id,
                stream_id,
                held.cursor,
                held.timeout_ms,
            )
            if response is None:
                continue
            if held.timer_token is not None:
                outputs.append(g.SwmrCancelTimer(held.timer_token))
            outputs.append(response)
            self._streams[stream_id] = None
        return outputs

    def _end_stream(self, message: g.SwmrEndStream) -> list[SwmrOutput]:
        if message.stream_id not in self._streams:
            return []
        held = self._streams.pop(message.stream_id)
        self._order.remove(message.stream_id)
        outputs: list[SwmrOutput] = []
        if held is not None and held.timer_token is not None:
            outputs.append(g.SwmrCancelTimer(held.timer_token))
        if not self._streams and self.stop_when is StopWhen.LAST_READER:
            outputs.append(g.SwmrProducerStop(g.SwmrStopReason.last_reader_gone))
        return outputs

    def _timer_expired(self, message: g.SwmrTimerExpired) -> list[SwmrOutput]:
        for stream_id in self._order:
            held = self._streams[stream_id]
            if held is None or held.timer_token != message.token:
                continue
            self._streams[stream_id] = None
            response = self._resolve(held.swmr_id, stream_id, held.cursor, 0)
            assert response is not None
            return [response]
        return []
