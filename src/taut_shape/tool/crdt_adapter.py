"""`crdt.oracle/v1` implementation of the generic engine adapter."""

from __future__ import annotations

from ..crdt.engine import CrdtInput, CrdtNode, CrdtOutput
from ..crdt import wire
from . import framing
from .runtime import EngineEffect, require_engine_shape


class CrdtAdapter:
    shape = "crdt"

    def __init__(self, *, max_pending: int = 1024) -> None:
        require_engine_shape(self.shape)
        self._node = CrdtNode(max_pending=max_pending)

    def decode_input(self, frame: framing.Frame) -> CrdtInput:
        return wire.decode_input(frame)

    def dispatch(self, input_: CrdtInput) -> list[CrdtOutput]:
        return self._node.handle(input_)

    def encode_output(self, output: CrdtOutput) -> EngineEffect[CrdtOutput]:
        wire.encode_message(output)
        return EngineEffect(frame=output)

    def finish(self) -> list[CrdtOutput]:
        return []
