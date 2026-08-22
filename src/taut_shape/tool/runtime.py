"""Shape-neutral engine dispatch shell used by the conformance CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar


FrameIn = TypeVar("FrameIn")
Input = TypeVar("Input")
Output = TypeVar("Output")
FrameOut = TypeVar("FrameOut")
FrameInContra = TypeVar("FrameInContra", contravariant=True)
FrameOutCo = TypeVar("FrameOutCo", covariant=True)


class AdapterDiagnostic(Exception):
    """Typed, stable failure at the shell/shape boundary."""

    def __init__(self, code: str, message: str, *, shape: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.shape = shape


class UnsupportedShapeError(AdapterDiagnostic):
    def __init__(self, shape: str, supported: tuple[str, ...]) -> None:
        super().__init__(
            "TAUT_SHAPE_UNSUPPORTED_SHAPE",
            f"unsupported engine shape {shape!r}; supported: {', '.join(supported)}",
            shape=shape,
        )
        self.supported = supported


@dataclass(frozen=True, slots=True)
class TimerAction:
    kind: str
    token: int
    delay_ms: int | None = None


@dataclass(frozen=True, slots=True)
class TeardownAction:
    reason: str


@dataclass(frozen=True, slots=True)
class EngineEffect(Generic[FrameOutCo]):
    frame: FrameOutCo
    timer: TimerAction | None = None
    teardown: TeardownAction | None = None


@dataclass(frozen=True, slots=True)
class EngineEmission(Generic[Output, FrameOut]):
    output: Output
    effect: EngineEffect[FrameOut]


class EngineAdapter(Protocol[FrameInContra, Input, Output, FrameOutCo]):
    """Shape-owned codec and state-machine boundary; no log types belong here."""

    shape: str

    def decode_input(self, frame: FrameInContra) -> Input: ...

    def dispatch(self, input_: Input) -> list[Output]: ...

    def encode_output(self, output: Output) -> EngineEffect[FrameOutCo]: ...

    def finish(self) -> list[Output]: ...


class EngineRuntime(Generic[FrameIn, Input, Output, FrameOut]):
    """Ordered shell that delegates every shape decision to one adapter."""

    def __init__(self, adapter: EngineAdapter[FrameIn, Input, Output, FrameOut]) -> None:
        self.adapter = adapter

    def process(self, frame: FrameIn) -> list[EngineEmission[Output, FrameOut]]:
        return self.dispatch(self.adapter.decode_input(frame))

    def dispatch(self, input_: Input) -> list[EngineEmission[Output, FrameOut]]:
        return [
            EngineEmission(output=output, effect=self.adapter.encode_output(output))
            for output in self.adapter.dispatch(input_)
        ]

    def finish(self) -> list[EngineEmission[Output, FrameOut]]:
        return [
            EngineEmission(output=output, effect=self.adapter.encode_output(output))
            for output in self.adapter.finish()
        ]


SUPPORTED_ENGINE_SHAPES = (
    "atom",
    "crdt",
    "log",
    "snapshot_delta",
    "stream",
    "swmr",
    "text_crdt",
    "value",
)


def require_engine_shape(shape: str) -> str:
    if shape not in SUPPORTED_ENGINE_SHAPES:
        raise UnsupportedShapeError(shape, SUPPORTED_ENGINE_SHAPES)
    return shape
