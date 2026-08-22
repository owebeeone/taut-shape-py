"""Value message codec and jsoncodec bridge over the canonical Taut schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

from taut.ir.load import load_schema
from taut.wire import codec, jsoncodec

from . import _generated as g
from .engine import ValueInput, ValueOutput
from ..tool import framing


_SCHEMA_PATH = Path(__file__).parents[4] / "taut-shape" / "ir" / "shape_value.taut.py"
_SCHEMA = load_schema(_SCHEMA_PATH)
_TYPE_TO_MESSAGE = {
    "set": "ValueSet",
    "read": "ValueReadRequest",
    "read_response": "ValueReadResponse",
    "diagnostic": "ValueDiagnostic",
}


def decode_input(frame: framing.Frame) -> ValueInput:
    try:
        message_type = g.ValueMsgType(frame.tag)
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    try:
        if message_type is g.ValueMsgType.set:
            native = codec.decode(_SCHEMA, "ValueSet", frame.body)
            return g.ValueSet(**native)
        if message_type is g.ValueMsgType.read:
            native = codec.decode(_SCHEMA, "ValueReadRequest", frame.body)
            return g.ValueReadRequest(**native)
    except Exception as error:
        raise framing.FrameError(f"malformed value frame body: {error}") from error
    raise framing.FrameError(f"output-only tag {message_type.name} on the value input channel")


def encode_output(message: ValueOutput) -> tuple[int, bytes]:
    if isinstance(message, g.ValueReadResponse):
        native = {
            "value_id": message.value_id,
            "stream_id": message.stream_id,
            "value": message.value,
            "winner": None
            if message.winner is None
            else {
                "origin": message.winner.origin,
                "seq": message.winner.seq,
                "lamport": message.winner.lamport,
            },
            "state": message.state.name,
        }
        return g.ValueMsgType.read_response.value, codec.encode(
            _SCHEMA, "ValueReadResponse", native
        )
    native = {"severity": message.severity.name, "code": message.code.name}
    return g.ValueMsgType.diagnostic.value, codec.encode(_SCHEMA, "ValueDiagnostic", native)


def encode_read(message: g.ValueReadRequest) -> tuple[int, bytes]:
    native = {"value_id": message.value_id, "stream_id": message.stream_id}
    return g.ValueMsgType.read.value, codec.encode(_SCHEMA, "ValueReadRequest", native)


def write_output(stream: BinaryIO, message: ValueOutput) -> None:
    tag, body = encode_output(message)
    framing.write_frame(stream, tag, body)


def write_read(stream: BinaryIO, message: g.ValueReadRequest) -> None:
    tag, body = encode_read(message)
    framing.write_frame(stream, tag, body)


def json_to_input(message: dict[str, Any]) -> ValueInput:
    message_type = str(message["type"])
    schema_name = _TYPE_TO_MESSAGE.get(message_type)
    if schema_name not in ("ValueSet", "ValueReadRequest"):
        raise ValueError(f"unknown value input {message_type!r}")
    native = jsoncodec.from_json_value(
        _SCHEMA,
        schema_name,
        {key: value for key, value in message.items() if key != "type"},
    )
    if schema_name == "ValueSet":
        return g.ValueSet(**native)
    return g.ValueReadRequest(**native)


def output_to_json(message: ValueOutput) -> dict[str, Any]:
    if isinstance(message, g.ValueDiagnostic):
        native: dict[str, Any] = {
            "severity": message.severity.name,
            "code": message.code.name,
        }
        message_type = "diagnostic"
        schema_name = "ValueDiagnostic"
    else:
        native = {
            "value_id": message.value_id,
            "stream_id": message.stream_id,
            "value": message.value,
            "winner": None
            if message.winner is None
            else {
                "origin": message.winner.origin,
                "seq": message.winner.seq,
                "lamport": message.winner.lamport,
            },
            "state": message.state.name,
        }
        message_type = "read_response"
        schema_name = "ValueReadResponse"
    return {
        "type": message_type,
        **jsoncodec.to_json_value(_SCHEMA, schema_name, native),
    }


def decode_output(frame: framing.Frame) -> ValueOutput:
    try:
        message_type = g.ValueMsgType(frame.tag)
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    try:
        if message_type is g.ValueMsgType.read_response:
            native = codec.decode(_SCHEMA, "ValueReadResponse", frame.body)
            winner = native["winner"]
            return g.ValueReadResponse(
                value_id=native["value_id"],
                stream_id=native["stream_id"],
                value=native["value"],
                winner=None if winner is None else g.ValueStamp(**winner),
                state=g.ValueState[native["state"]],
            )
        if message_type is g.ValueMsgType.diagnostic:
            native = codec.decode(_SCHEMA, "ValueDiagnostic", frame.body)
            return g.ValueDiagnostic(
                severity=g.ValueSeverity[native["severity"]],
                code=g.ValueDiagCode[native["code"]],
            )
    except Exception as error:
        raise framing.FrameError(f"malformed value frame body: {error}") from error
    raise framing.FrameError(f"input-only tag {message_type.name} on the value response channel")
