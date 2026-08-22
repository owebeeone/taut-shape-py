"""Stream codec/jsoncodec bridge over the canonical Taut schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, cast

from taut.ir.load import load_schema
from taut.wire import codec, jsoncodec

from ..tool import framing
from . import _generated as g
from .engine import StreamInput, StreamOutput

_SCHEMA_PATH = Path(__file__).parents[4] / "taut-shape" / "ir" / "shape_stream.taut.py"
_SCHEMA = load_schema(_SCHEMA_PATH)
_TYPE_TO_MESSAGE = {
    "push": "StreamPush",
    "seal": "StreamSeal",
    "close": "StreamClose",
    "read": "StreamReadRequest",
    "end_stream": "StreamEndStream",
    "timer_expired": "StreamTimerExpired",
    "read_response": "StreamReadResponse",
    "set_timer": "StreamSetTimer",
    "cancel_timer": "StreamCancelTimer",
    "producer_stop": "StreamProducerStop",
    "diagnostic": "StreamDiagnostic",
}
_INPUT_NAMES = frozenset(
    {"push", "seal", "close", "read", "end_stream", "timer_expired"}
)


def _error(native: dict[str, Any] | None) -> g.StreamError | None:
    if native is None:
        return None
    return g.StreamError(g.StreamErrorCode[native["code"]], native["message"])


def _input(message_type: str, native: dict[str, Any]) -> StreamInput:
    if message_type == "push":
        return g.StreamPush(payload=native["payload"])
    if message_type == "seal":
        return g.StreamSeal()
    if message_type == "close":
        return g.StreamClose(error=_error(native["error"]))
    if message_type == "read":
        return g.StreamReadRequest(
            stream_id=native["stream_id"],
            max_records=native["max_records"],
            max_bytes=native["max_bytes"],
            timeout_ms=native["timeout_ms"],
        )
    if message_type == "end_stream":
        return g.StreamEndStream(stream_id=native["stream_id"])
    if message_type == "timer_expired":
        return g.StreamTimerExpired(token=native["token"])
    raise ValueError(f"output-only stream message {message_type!r}")


def _output(message_type: str, native: dict[str, Any]) -> StreamOutput:
    if message_type == "read_response":
        return g.StreamReadResponse(
            stream_id=native["stream_id"],
            records=[g.StreamRecord(**record) for record in native["records"]],
            next_position=g.StreamPosition(**native["next_position"]),
            state=g.StreamState[native["state"]],
            error=_error(native["error"]),
        )
    if message_type == "set_timer":
        return g.StreamSetTimer(token=native["token"], ms=native["ms"])
    if message_type == "cancel_timer":
        return g.StreamCancelTimer(token=native["token"])
    if message_type == "producer_stop":
        return g.StreamProducerStop(reason=g.StreamStopReason[native["reason"]])
    if message_type == "diagnostic":
        return g.StreamDiagnostic(
            severity=g.StreamSeverity[native["severity"]],
            code=g.StreamDiagCode[native["code"]],
        )
    raise ValueError(f"input-only stream message {message_type!r}")


def _output_native(message: StreamOutput) -> tuple[str, dict[str, Any]]:
    if isinstance(message, g.StreamReadResponse):
        return "read_response", {
            "stream_id": message.stream_id,
            "records": [
                {"seq": record.seq, "payload": record.payload}
                for record in message.records
            ],
            "next_position": {"seq": message.next_position.seq},
            "state": message.state.name,
            "error": None
            if message.error is None
            else {
                "code": message.error.code.name,
                "message": message.error.message,
            },
        }
    if isinstance(message, g.StreamSetTimer):
        return "set_timer", {"token": message.token, "ms": message.ms}
    if isinstance(message, g.StreamCancelTimer):
        return "cancel_timer", {"token": message.token}
    if isinstance(message, g.StreamProducerStop):
        return "producer_stop", {"reason": message.reason.name}
    return "diagnostic", {
        "severity": message.severity.name,
        "code": message.code.name,
    }


def decode_input(frame: framing.Frame) -> StreamInput:
    try:
        message_type = g.StreamMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type not in _INPUT_NAMES:
        raise framing.FrameError(
            f"output-only tag {message_type} on the stream input channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _input(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed stream frame body: {error}") from error


def encode_output(message: StreamOutput) -> tuple[int, bytes]:
    message_type, native = _output_native(message)
    return (
        g.StreamMsgType[message_type].value,
        codec.encode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], native),
    )


def decode_output(frame: framing.Frame) -> StreamOutput:
    try:
        message_type = g.StreamMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type in _INPUT_NAMES:
        raise framing.FrameError(
            f"input-only tag {message_type} on the stream response channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _output(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed stream frame body: {error}") from error


def write_output(stream: BinaryIO, message: StreamOutput) -> None:
    tag, body = encode_output(message)
    framing.write_frame(stream, tag, body)


def write_read(stream: BinaryIO, message: g.StreamReadRequest) -> None:
    body = codec.encode(
        _SCHEMA,
        "StreamReadRequest",
        {
            "stream_id": message.stream_id,
            "max_records": message.max_records,
            "max_bytes": message.max_bytes,
            "timeout_ms": message.timeout_ms,
        },
    )
    framing.write_frame(stream, g.StreamMsgType.read.value, body)


def json_to_input(message: dict[str, Any]) -> StreamInput:
    message_type = str(message["type"])
    if message_type not in _INPUT_NAMES:
        raise ValueError(f"unknown stream input {message_type!r}")
    native = jsoncodec.from_json_value(
        _SCHEMA,
        _TYPE_TO_MESSAGE[message_type],
        {key: value for key, value in message.items() if key != "type"},
    )
    return _input(message_type, cast(dict[str, Any], native))


def output_to_json(message: StreamOutput) -> dict[str, Any]:
    message_type, native = _output_native(message)
    return {
        "type": message_type,
        **jsoncodec.to_json_value(
            _SCHEMA, _TYPE_TO_MESSAGE[message_type], native
        ),
    }
