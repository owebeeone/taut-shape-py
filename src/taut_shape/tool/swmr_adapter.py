"""``swmr.oracle/v1`` implementation of the generic engine adapter."""

from __future__ import annotations

from ..log.engine import StopWhen
from ..swmr import _generated as g
from ..swmr import wire
from ..swmr.engine import SwmrInput, SwmrNode, SwmrOutput, SwmrRecoveryPolicy
from . import framing
from .runtime import EngineEffect, TeardownAction, TimerAction, require_engine_shape


class SwmrAdapter:
    shape = "swmr"

    def __init__(
        self,
        *,
        stop_when: StopWhen = StopWhen.LAST_READER,
        max_deltas: int | None = None,
        expire_profile: bool = False,
    ) -> None:
        self.shape = "snapshot_delta" if expire_profile else "swmr"
        require_engine_shape(self.shape)
        self._node = SwmrNode(
            stop_when=stop_when,
            max_deltas=64 if expire_profile and max_deltas is None else max_deltas,
            recovery_policy=SwmrRecoveryPolicy.EXPIRE
            if expire_profile
            else SwmrRecoveryPolicy.REPAIR,
        )

    def decode_input(self, frame: framing.Frame) -> SwmrInput:
        return wire.decode_input(frame)

    def dispatch(self, input_: SwmrInput) -> list[SwmrOutput]:
        return self._node.handle(input_)

    def encode_output(self, output: SwmrOutput) -> EngineEffect[SwmrOutput]:
        timer: TimerAction | None = None
        teardown: TeardownAction | None = None
        if isinstance(output, g.SwmrSetTimer):
            timer = TimerAction("set", output.token, output.ms)
        elif isinstance(output, g.SwmrCancelTimer):
            timer = TimerAction("cancel", output.token)
        elif isinstance(output, g.SwmrProducerStop):
            teardown = TeardownAction(output.reason.name)
        wire.encode_output(output)
        return EngineEffect(frame=output, timer=timer, teardown=teardown)

    def finish(self) -> list[SwmrOutput]:
        return []
