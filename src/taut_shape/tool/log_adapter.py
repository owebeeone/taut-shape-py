"""`log.v0` implementation of the shape-neutral engine adapter contract."""

from __future__ import annotations

from ..log import _generated as g
from ..log.engine import LogNode, StopWhen
from . import framing
from .runtime import (
    AdapterDiagnostic,
    EngineEffect,
    TeardownAction,
    TimerAction,
    require_engine_shape,
)


_INPUT_TYPES = (
    g.LogPush,
    g.LogSeal,
    g.LogClose,
    g.LogReadRequest,
    g.LogEndStream,
    g.LogTimerExpired,
    g.LogEvict,
)


class LogAdapter:
    shape = "log"

    def __init__(self, *, stop_when: StopWhen = StopWhen.LAST_READER) -> None:
        require_engine_shape(self.shape)
        self._node = LogNode(log_id="log-A", stop_when=stop_when)

    def decode_input(self, frame: framing.Frame) -> object:
        msg = framing.decode_message(frame)
        if not isinstance(msg, _INPUT_TYPES):
            raise AdapterDiagnostic(
                "TAUT_SHAPE_DIRECTION_VIOLATION",
                f"output-only tag {g.LogMsgType(frame.tag).name} on the input channel",
                shape=self.shape,
            )
        return msg

    def dispatch(self, input_: object) -> list[object]:
        if not isinstance(input_, _INPUT_TYPES):
            raise AdapterDiagnostic(
                "TAUT_SHAPE_DIRECTION_VIOLATION",
                f"unsupported log input {type(input_).__name__}",
                shape=self.shape,
            )
        return list(self._node.handle(input_))

    def encode_output(self, output: object) -> EngineEffect[object]:
        timer: TimerAction | None = None
        teardown: TeardownAction | None = None
        if isinstance(output, g.LogSetTimer):
            timer = TimerAction("set", output.token, output.ms)
        elif isinstance(output, g.LogCancelTimer):
            timer = TimerAction("cancel", output.token)
        elif isinstance(output, g.LogProducerStop):
            teardown = TeardownAction(output.reason.name)
        try:
            framing.encode_message(output)
        except KeyError as exc:
            raise AdapterDiagnostic(
                "TAUT_SHAPE_ADAPTER_FAILURE",
                f"unsupported log output {type(output).__name__}",
                shape=self.shape,
            ) from exc
        return EngineEffect(frame=output, timer=timer, teardown=teardown)

    def finish(self) -> list[object]:
        return []
