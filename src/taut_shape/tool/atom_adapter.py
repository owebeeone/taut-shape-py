"""`atom.oracle/v1` implementation of the generic engine adapter."""

from __future__ import annotations

from ..atom import wire
from ..atom.engine import AtomInput, AtomNode, AtomOutput
from ..log.engine import StopWhen
from . import framing
from .runtime import EngineEffect, TeardownAction, TimerAction, require_engine_shape


class AtomAdapter:
    shape = "atom"

    def __init__(self, *, stop_when: StopWhen = StopWhen.LAST_READER) -> None:
        require_engine_shape(self.shape)
        self._node = AtomNode(stop_when=stop_when)

    def decode_input(self, frame: framing.Frame) -> AtomInput:
        return wire.decode_input(frame)

    def dispatch(self, input_: AtomInput) -> list[AtomOutput]:
        return self._node.handle(input_)

    def encode_output(self, output: AtomOutput) -> EngineEffect[AtomOutput]:
        timer: TimerAction | None = None
        teardown: TeardownAction | None = None
        from ..atom import _generated as g

        if isinstance(output, g.AtomSetTimer):
            timer = TimerAction("set", output.token, output.ms)
        elif isinstance(output, g.AtomCancelTimer):
            timer = TimerAction("cancel", output.token)
        elif isinstance(output, g.AtomProducerStop):
            teardown = TeardownAction(output.reason.name)
        wire.encode_output(output)
        return EngineEffect(frame=output, timer=timer, teardown=teardown)

    def finish(self) -> list[AtomOutput]:
        return []
