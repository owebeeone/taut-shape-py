"""Pure latest-state mailbox implementing ``atom.oracle/v1``."""

from __future__ import annotations

from dataclasses import dataclass

from ..log.engine import StopWhen
from . import _generated as g

AtomInput = (
    g.AtomReplace
    | g.AtomSeal
    | g.AtomClose
    | g.AtomReadRequest
    | g.AtomEndStream
    | g.AtomTimerExpired
)
AtomOutput = (
    g.AtomReadResponse
    | g.AtomSetTimer
    | g.AtomCancelTimer
    | g.AtomProducerStop
    | g.AtomDiagnostic
)


@dataclass(slots=True)
class _Held:
    atom_id: str
    version: int
    timeout_ms: int | None
    timer_token: int | None


class AtomNode:
    """One retained value with versioned reads, holds, timers, and lifecycle."""

    def __init__(self, *, stop_when: StopWhen = StopWhen.LAST_READER) -> None:
        self.stop_when = stop_when
        self.version = 0
        self.payload: bytes | None = None
        self.sealed = False
        self.closed = False
        self.close_error: g.AtomError | None = None
        self._streams: dict[str, _Held | None] = {}
        self._order: list[str] = []
        self._next_token = 1

    def handle(self, message: AtomInput) -> list[AtomOutput]:
        if isinstance(message, g.AtomReplace):
            return self._replace(message)
        if isinstance(message, g.AtomSeal):
            return self._seal()
        if isinstance(message, g.AtomClose):
            return self._close(message)
        if isinstance(message, g.AtomReadRequest):
            return self._read(message)
        if isinstance(message, g.AtomEndStream):
            return self._end_stream(message)
        if isinstance(message, g.AtomTimerExpired):
            return self._timer_expired(message)
        raise TypeError(f"unsupported atom input {type(message).__name__}")

    def _replace(self, message: g.AtomReplace) -> list[AtomOutput]:
        if self.sealed or self.closed:
            return [
                g.AtomDiagnostic(
                    severity=g.AtomSeverity.warn,
                    code=g.AtomDiagCode.replace_after_terminal,
                )
            ]
        self.version += 1
        self.payload = bytes(message.payload)
        return self._answer_all_held()

    def _seal(self) -> list[AtomOutput]:
        if self.sealed:
            return []
        self.sealed = True
        return self._answer_all_held()

    def _close(self, message: g.AtomClose) -> list[AtomOutput]:
        if self.closed:
            return []
        self.closed = True
        self.close_error = None if message.error is None else g.AtomError(
            code=message.error.code,
            message=message.error.message,
        )
        outputs = self._answer_all_held()
        reason = (
            g.AtomStopReason.failed
            if self.close_error is not None
            else g.AtomStopReason.closed
        )
        outputs.append(g.AtomProducerStop(reason=reason))
        return outputs

    def _ensure_stream(self, stream_id: str) -> None:
        if stream_id not in self._streams:
            self._streams[stream_id] = None
            self._order.append(stream_id)

    def _read(self, message: g.AtomReadRequest) -> list[AtomOutput]:
        self._ensure_stream(message.stream_id)
        outputs: list[AtomOutput] = []
        prior = self._streams[message.stream_id]
        if prior is not None and prior.timer_token is not None:
            outputs.append(g.AtomCancelTimer(token=prior.timer_token))
        self._streams[message.stream_id] = None

        version = 0 if message.version is None else message.version.version
        response = self._resolve(
            message.atom_id,
            message.stream_id,
            version,
            message.timeout_ms,
        )
        if response is not None:
            outputs.append(response)
            return outputs

        token: int | None = None
        if message.timeout_ms is not None and message.timeout_ms > 0:
            token = self._next_token
            self._next_token += 1
            outputs.append(g.AtomSetTimer(token=token, ms=message.timeout_ms))
        self._streams[message.stream_id] = _Held(
            atom_id=message.atom_id,
            version=version,
            timeout_ms=message.timeout_ms,
            timer_token=token,
        )
        return outputs

    def _resolve(
        self,
        atom_id: str,
        stream_id: str,
        version: int,
        timeout_ms: int | None,
    ) -> g.AtomReadResponse | None:
        if version < self.version:
            assert self.payload is not None
            return g.AtomReadResponse(
                atom_id=atom_id,
                stream_id=stream_id,
                value=g.AtomValue(version=self.version, payload=self.payload),
                next_version=g.AtomVersion(version=self.version),
                state=g.AtomState.data,
                error=None,
            )
        next_version = g.AtomVersion(version=self.version)
        if self.closed:
            return g.AtomReadResponse(
                atom_id=atom_id,
                stream_id=stream_id,
                value=None,
                next_version=next_version,
                state=(
                    g.AtomState.failed
                    if self.close_error is not None
                    else g.AtomState.closed
                ),
                error=self.close_error,
            )
        if self.sealed:
            return g.AtomReadResponse(
                atom_id=atom_id,
                stream_id=stream_id,
                value=None,
                next_version=next_version,
                state=g.AtomState.eof,
                error=None,
            )
        if timeout_ms == 0:
            return g.AtomReadResponse(
                atom_id=atom_id,
                stream_id=stream_id,
                value=None,
                next_version=next_version,
                state=g.AtomState.would_block,
                error=None,
            )
        return None

    def _answer_all_held(self) -> list[AtomOutput]:
        outputs: list[AtomOutput] = []
        for stream_id in self._order:
            held = self._streams.get(stream_id)
            if held is None:
                continue
            response = self._resolve(
                held.atom_id,
                stream_id,
                held.version,
                held.timeout_ms,
            )
            if response is None:
                continue
            if held.timer_token is not None:
                outputs.append(g.AtomCancelTimer(token=held.timer_token))
            outputs.append(response)
            self._streams[stream_id] = None
        return outputs

    def _end_stream(self, message: g.AtomEndStream) -> list[AtomOutput]:
        if message.stream_id not in self._streams:
            return []
        held = self._streams.pop(message.stream_id)
        self._order.remove(message.stream_id)
        outputs: list[AtomOutput] = []
        if held is not None and held.timer_token is not None:
            outputs.append(g.AtomCancelTimer(token=held.timer_token))
        if not self._streams and self.stop_when is StopWhen.LAST_READER:
            outputs.append(
                g.AtomProducerStop(reason=g.AtomStopReason.last_reader_gone)
            )
        return outputs

    def _timer_expired(self, message: g.AtomTimerExpired) -> list[AtomOutput]:
        for stream_id, held in self._streams.items():
            if held is None or held.timer_token != message.token:
                continue
            self._streams[stream_id] = None
            response = self._resolve(held.atom_id, stream_id, held.version, 0)
            assert response is not None
            return [response]
        return []
