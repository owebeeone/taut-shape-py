"""``stream.oracle/v1`` implementation of the generic engine adapter."""

from __future__ import annotations

from ..log.engine import StopWhen
from ..stream import _generated as g
from ..stream import wire
from ..stream.engine import StreamInput, StreamNode, StreamOutput
from . import framing
from .runtime import EngineEffect, TeardownAction, TimerAction, require_engine_shape


class StreamAdapter:
    shape = "stream"

    def __init__(
        self,
        *,
        capacity_records: int = 64,
        stop_when: StopWhen = StopWhen.LAST_READER,
    ) -> None:
        require_engine_shape(self.shape)
        self._node = StreamNode(
            capacity_records=capacity_records,
            stop_when=stop_when,
        )

    def decode_input(self, frame: framing.Frame) -> StreamInput:
        return wire.decode_input(frame)

    def dispatch(self, input_: StreamInput) -> list[StreamOutput]:
        return self._node.handle(input_)

    def encode_output(self, output: StreamOutput) -> EngineEffect[StreamOutput]:
        timer: TimerAction | None = None
        teardown: TeardownAction | None = None
        if isinstance(output, g.StreamSetTimer):
            timer = TimerAction("set", output.token, output.ms)
        elif isinstance(output, g.StreamCancelTimer):
            timer = TimerAction("cancel", output.token)
        elif isinstance(output, g.StreamProducerStop):
            teardown = TeardownAction(output.reason.name)
        wire.encode_output(output)
        return EngineEffect(frame=output, timer=timer, teardown=teardown)

    def finish(self) -> list[StreamOutput]:
        return []
