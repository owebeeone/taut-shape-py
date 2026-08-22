"""`value.oracle/v0` implementation of the generic engine adapter."""

from __future__ import annotations

from ..value.engine import ValueInput, ValueNode, ValueOutput
from ..value import wire
from . import framing
from .runtime import EngineEffect, require_engine_shape


class ValueAdapter:
    shape = "value"

    def __init__(self) -> None:
        require_engine_shape(self.shape)
        self._node = ValueNode()

    def decode_input(self, frame: framing.Frame) -> ValueInput:
        return wire.decode_input(frame)

    def dispatch(self, input_: ValueInput) -> list[ValueOutput]:
        return self._node.handle(input_)

    def encode_output(self, output: ValueOutput) -> EngineEffect[ValueOutput]:
        wire.encode_output(output)
        return EngineEffect(frame=output)

    def finish(self) -> list[ValueOutput]:
        return []
