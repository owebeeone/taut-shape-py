"""Pure attributed LWW register implementing ``value.oracle/v0``."""

from __future__ import annotations

from . import _generated as g

ValueInput = g.ValueSet | g.ValueReadRequest
ValueOutput = g.ValueReadResponse | g.ValueDiagnostic


class ValueNode:
    def __init__(self) -> None:
        self._ops: dict[tuple[str, int], g.ValueSet] = {}

    @property
    def size(self) -> int:
        return len(self._ops)

    def handle(self, message: ValueInput) -> list[ValueOutput]:
        if isinstance(message, g.ValueSet):
            return self._set(message)
        if isinstance(message, g.ValueReadRequest):
            return [self._read(message)]
        raise TypeError(f"unsupported value input {type(message).__name__}")

    def _set(self, op: g.ValueSet) -> list[ValueOutput]:
        key = (op.origin, op.seq)
        prior = self._ops.get(key)
        if prior is not None:
            if prior.payload != op.payload or prior.prev != op.prev:
                return [
                    g.ValueDiagnostic(
                        severity=g.ValueSeverity.error,
                        code=g.ValueDiagCode.equivocation,
                    )
                ]
            return []
        self._ops[key] = g.ValueSet(
            origin=op.origin,
            seq=op.seq,
            lamport=op.lamport,
            prev=op.prev,
            payload=op.payload,
        )
        return []

    def _read(self, request: g.ValueReadRequest) -> g.ValueReadResponse:
        if not self._ops:
            return g.ValueReadResponse(
                value_id=request.value_id,
                stream_id=request.stream_id,
                value=None,
                winner=None,
                state=g.ValueState.empty,
            )
        winner = max(self._ops.values(), key=lambda op: (op.lamport, op.origin, op.seq))
        return g.ValueReadResponse(
            value_id=request.value_id,
            stream_id=request.stream_id,
            value=winner.payload,
            winner=g.ValueStamp(
                origin=winner.origin,
                seq=winner.seq,
                lamport=winner.lamport,
            ),
            state=g.ValueState.data,
        )
