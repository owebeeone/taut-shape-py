"""Step 2.1 engine-adapter contract tests."""

from __future__ import annotations

import io
from io import StringIO
import importlib

import pytest

from taut_shape.log import _generated as g
from taut_shape.tool import framing
from taut_shape.tool.log_adapter import LogAdapter
from taut_shape.tool.runtime import (
    EngineEffect,
    EngineRuntime,
    SUPPORTED_ENGINE_SHAPES,
    UnsupportedShapeError,
    require_engine_shape,
)

tool_main = importlib.import_module("taut_shape.tool.main")


class TextAdapter:
    """Non-log proof that the shared shell imposes no cursor/lifecycle types."""

    shape = "text-test"

    def decode_input(self, frame: str) -> int:
        return len(frame)

    def dispatch(self, input_: int) -> list[bool]:
        return [input_ % 2 == 0]

    def encode_output(self, output: bool) -> EngineEffect[str]:
        return EngineEffect(frame="even" if output else "odd")

    def finish(self) -> list[bool]:
        return []


def test_cli_help_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    assert tool_main.main(["--help"]) == 0
    captured = capsys.readouterr()
    assert "USAGE:" in captured.out
    assert captured.err == ""


def test_runtime_contract_is_shape_neutral() -> None:
    emissions = EngineRuntime(TextAdapter()).process("abcd")
    assert [(e.output, e.effect.frame) for e in emissions] == [(True, "even")]


def test_unknown_shape_is_typed() -> None:
    with pytest.raises(UnsupportedShapeError) as caught:
        require_engine_shape("window")
    assert caught.value.code == "TAUT_SHAPE_UNSUPPORTED_SHAPE"
    assert caught.value.shape == "window"


def test_registry_names_exactly_the_implemented_engines() -> None:
    assert SUPPORTED_ENGINE_SHAPES == (
        "atom",
        "crdt",
        "log",
        "snapshot_delta",
        "stream",
        "swmr",
        "text_crdt",
        "value",
    )


def test_unknown_message_tag_is_typed() -> None:
    frame = framing.read_frame(io.BytesIO(bytes([2, 0, 0, 0, 99, 0xA0])))
    assert frame is not None
    with pytest.raises(framing.UnknownMessageTagError) as caught:
        LogAdapter().decode_input(frame)
    assert caught.value.code == "TAUT_SHAPE_UNKNOWN_TAG"
    assert caught.value.tag == 99


def test_log_timer_and_teardown_are_shape_neutral_effects() -> None:
    runtime = EngineRuntime(LogAdapter())
    held = runtime.dispatch(
        g.LogReadRequest(
            log_id="log-A",
            stream_id="s1",
            cursor=g.LogCursor(seq=0),
            max_records=None,
            max_bytes=None,
            timeout_ms=25,
        )
    )
    assert held[0].effect.timer is not None
    assert (held[0].effect.timer.kind, held[0].effect.timer.delay_ms) == ("set", 25)

    closed = runtime.dispatch(g.LogClose(error=None))
    assert any(e.effect.teardown is not None for e in closed)


def test_unsupported_shape_exits_before_node_or_client_startup() -> None:
    invalid_frame = bytes([1, 0, 0, 0, 99])
    for mode, args in (("node", []), ("client", [])):  # type: str, list[str]
        stdin = io.BytesIO(invalid_frame)
        stdout = io.BytesIO()
        stderr = StringIO()
        runner = tool_main.run_node if mode == "node" else tool_main.run_client
        code = runner(["--shape", "window", *args], stdin, stdout, stderr)
        assert code == 2
        assert stdin.tell() == 0
        assert stdout.getvalue() == b""
        assert "TAUT_SHAPE_UNSUPPORTED_SHAPE" in stderr.getvalue()
