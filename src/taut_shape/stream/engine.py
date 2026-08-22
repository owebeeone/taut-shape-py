"""Bounded disposable ordered delivery (`stream.oracle/v1`)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TypeAlias

from ..log.engine import StopWhen
from . import _generated as g

StreamInput: TypeAlias = (
    g.StreamPush
    | g.StreamSeal
    | g.StreamClose
    | g.StreamReadRequest
    | g.StreamEndStream
    | g.StreamTimerExpired
)
StreamOutput: TypeAlias = (
    g.StreamReadResponse
    | g.StreamSetTimer
    | g.StreamCancelTimer
    | g.StreamProducerStop
    | g.StreamDiagnostic
)


@dataclass(slots=True)
class _Held:
    max_records: int | None
    max_bytes: int | None
    timeout_ms: int | None
    timer_token: int | None


@dataclass(slots=True)
class _Reader:
    cursor: int
    held: _Held | None = None


class StreamNode:
    """A live-only bounded ring with node-owned reader positions."""

    def __init__(
        self,
        *,
        capacity_records: int = 64,
        stop_when: StopWhen = StopWhen.LAST_READER,
    ) -> None:
        if capacity_records <= 0:
            raise ValueError("capacity_records must be positive")
        self.capacity_records = capacity_records
        self.stop_when = stop_when
        self.head = 0
        self._sequence: deque[int] = deque()
        self._payloads: dict[int, bytes] = {}
        self.sealed = False
        self.closed = False
        self.close_error: g.StreamError | None = None
        self._readers: dict[str, _Reader] = {}
        self._order: list[str] = []
        self._next_token = 1

    @property
    def floor(self) -> int:
        return self._sequence[0] if self._sequence else self.head + 1

    def handle(self, message: StreamInput) -> list[StreamOutput]:
        if isinstance(message, g.StreamPush):
            return self._push(message)
        if isinstance(message, g.StreamSeal):
            return self._seal()
        if isinstance(message, g.StreamClose):
            return self._close(message)
        if isinstance(message, g.StreamReadRequest):
            return self._read(message)
        if isinstance(message, g.StreamEndStream):
            return self._end_stream(message)
        if isinstance(message, g.StreamTimerExpired):
            return self._timer_expired(message)
        raise TypeError(f"unsupported stream input {type(message).__name__}")

    def _push(self, message: g.StreamPush) -> list[StreamOutput]:
        if self.sealed or self.closed:
            return [
                g.StreamDiagnostic(
                    severity=g.StreamSeverity.warn,
                    code=g.StreamDiagCode.push_after_terminal,
                )
            ]
        self.head += 1
        self._sequence.append(self.head)
        self._payloads[self.head] = bytes(message.payload)
        if len(self._sequence) > self.capacity_records:
            del self._payloads[self._sequence.popleft()]
        return self._answer_all_held()

    def _seal(self) -> list[StreamOutput]:
        if self.sealed or self.closed:
            return []
        self.sealed = True
        return self._answer_all_held()

    def _close(self, message: g.StreamClose) -> list[StreamOutput]:
        if self.closed:
            return []
        self.closed = True
        self.close_error = message.error
        outputs = self._answer_all_held()
        outputs.append(
            g.StreamProducerStop(
                reason=(
                    g.StreamStopReason.failed
                    if self.close_error is not None
                    else g.StreamStopReason.closed
                )
            )
        )
        return outputs

    def _ensure_reader(self, stream_id: str) -> _Reader:
        reader = self._readers.get(stream_id)
        if reader is None:
            reader = _Reader(cursor=self.head)
            self._readers[stream_id] = reader
            self._order.append(stream_id)
        return reader

    def _read(self, message: g.StreamReadRequest) -> list[StreamOutput]:
        reader = self._ensure_reader(message.stream_id)
        outputs: list[StreamOutput] = []
        if reader.held is not None and reader.held.timer_token is not None:
            outputs.append(g.StreamCancelTimer(token=reader.held.timer_token))
        reader.held = None
        response = self._resolve(
            message.stream_id,
            reader,
            message.max_records,
            message.max_bytes,
            message.timeout_ms,
        )
        if response is not None:
            outputs.append(response)
            if response.state is g.StreamState.dropped:
                outputs.extend(self._remove_reader(message.stream_id))
            return outputs
        timer_token = None
        if message.timeout_ms is not None and message.timeout_ms > 0:
            timer_token = self._next_token
            self._next_token += 1
            outputs.append(
                g.StreamSetTimer(token=timer_token, ms=message.timeout_ms)
            )
        reader.held = _Held(
            message.max_records,
            message.max_bytes,
            message.timeout_ms,
            timer_token,
        )
        return outputs

    def _resolve(
        self,
        stream_id: str,
        reader: _Reader,
        max_records: int | None,
        max_bytes: int | None,
        timeout_ms: int | None,
    ) -> g.StreamReadResponse | None:
        if reader.cursor < self.floor - 1:
            return self._response(
                stream_id,
                [],
                self.head,
                g.StreamState.dropped,
                g.StreamError(g.StreamErrorCode.slow_consumer, None),
            )
        selected: list[g.StreamRecord] = []
        used = 0
        for seq in range(reader.cursor + 1, self.head + 1):
            payload = self._payloads.get(seq)
            if payload is None:
                continue
            if max_records is not None and max_records > 0 and len(selected) >= max_records:
                break
            if (
                max_bytes is not None
                and max_bytes >= 0
                and selected
                and used + len(payload) > max_bytes
            ):
                break
            selected.append(g.StreamRecord(seq=seq, payload=payload))
            used += len(payload)
        if selected:
            reader.cursor = selected[-1].seq
            return self._response(
                stream_id, selected, reader.cursor, g.StreamState.data, None
            )
        if self.closed:
            return self._response(
                stream_id,
                [],
                reader.cursor,
                (
                    g.StreamState.failed
                    if self.close_error is not None
                    else g.StreamState.closed
                ),
                self.close_error,
            )
        if self.sealed:
            return self._response(
                stream_id, [], reader.cursor, g.StreamState.eof, None
            )
        if timeout_ms == 0:
            return self._response(
                stream_id, [], reader.cursor, g.StreamState.would_block, None
            )
        return None

    @staticmethod
    def _response(
        stream_id: str,
        records: list[g.StreamRecord],
        position: int,
        state: g.StreamState,
        error: g.StreamError | None,
    ) -> g.StreamReadResponse:
        return g.StreamReadResponse(
            stream_id=stream_id,
            records=records,
            next_position=g.StreamPosition(seq=position),
            state=state,
            error=error,
        )

    def _answer_all_held(self) -> list[StreamOutput]:
        outputs: list[StreamOutput] = []
        for stream_id in list(self._order):
            reader = self._readers.get(stream_id)
            if reader is None or reader.held is None:
                continue
            held = reader.held
            response = self._resolve(
                stream_id,
                reader,
                held.max_records,
                held.max_bytes,
                held.timeout_ms,
            )
            if response is None:
                continue
            if held.timer_token is not None:
                outputs.append(g.StreamCancelTimer(token=held.timer_token))
            reader.held = None
            outputs.append(response)
            if response.state is g.StreamState.dropped:
                outputs.extend(self._remove_reader(stream_id))
        return outputs

    def _remove_reader(self, stream_id: str) -> list[StreamOutput]:
        if stream_id not in self._readers:
            return []
        del self._readers[stream_id]
        self._order.remove(stream_id)
        if not self._readers and self.stop_when is StopWhen.LAST_READER:
            return [
                g.StreamProducerStop(reason=g.StreamStopReason.last_reader_gone)
            ]
        return []

    def _end_stream(self, message: g.StreamEndStream) -> list[StreamOutput]:
        reader = self._readers.get(message.stream_id)
        if reader is None:
            return []
        outputs: list[StreamOutput] = []
        if reader.held is not None and reader.held.timer_token is not None:
            outputs.append(g.StreamCancelTimer(token=reader.held.timer_token))
        outputs.extend(self._remove_reader(message.stream_id))
        return outputs

    def _timer_expired(self, message: g.StreamTimerExpired) -> list[StreamOutput]:
        for stream_id in self._order:
            reader = self._readers[stream_id]
            if reader.held is None or reader.held.timer_token != message.token:
                continue
            held = reader.held
            reader.held = None
            response = self._resolve(
                stream_id, reader, held.max_records, held.max_bytes, 0
            )
            assert response is not None
            return [response]
        return []
