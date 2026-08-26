"""Atom message codec and jsoncodec bridge over the canonical Taut schema."""

from __future__ import annotations

from typing import Any, BinaryIO, cast

from taut.wire import codec, jsoncodec

from .._schema import load_packaged_schema
from ..tool import framing
from . import _generated as g
from .engine import AtomInput, AtomOutput

_SCHEMA = load_packaged_schema("atom")
_TYPE_TO_MESSAGE = {
    "replace": "AtomReplace",
    "seal": "AtomSeal",
    "close": "AtomClose",
    "read": "AtomReadRequest",
    "end_stream": "AtomEndStream",
    "timer_expired": "AtomTimerExpired",
    "read_response": "AtomReadResponse",
    "set_timer": "AtomSetTimer",
    "cancel_timer": "AtomCancelTimer",
    "producer_stop": "AtomProducerStop",
    "diagnostic": "AtomDiagnostic",
}
_INPUT_NAMES = frozenset(
    {"replace", "seal", "close", "read", "end_stream", "timer_expired"}
)


def _error(native: dict[str, Any] | None) -> g.AtomError | None:
    if native is None:
        return None
    return g.AtomError(
        code=g.AtomErrorCode[native["code"]],
        message=native["message"],
    )


def _input(message_type: str, native: dict[str, Any]) -> AtomInput:
    if message_type == "replace":
        return g.AtomReplace(payload=native["payload"])
    if message_type == "seal":
        return g.AtomSeal()
    if message_type == "close":
        return g.AtomClose(error=_error(native["error"]))
    if message_type == "read":
        version = native["version"]
        return g.AtomReadRequest(
            atom_id=native["atom_id"],
            stream_id=native["stream_id"],
            version=None if version is None else g.AtomVersion(**version),
            timeout_ms=native["timeout_ms"],
        )
    if message_type == "end_stream":
        return g.AtomEndStream(
            atom_id=native["atom_id"],
            stream_id=native["stream_id"],
        )
    if message_type == "timer_expired":
        return g.AtomTimerExpired(token=native["token"])
    raise ValueError(f"output-only atom message {message_type!r}")


def _output(message_type: str, native: dict[str, Any]) -> AtomOutput:
    if message_type == "read_response":
        value = native["value"]
        return g.AtomReadResponse(
            atom_id=native["atom_id"],
            stream_id=native["stream_id"],
            value=None if value is None else g.AtomValue(**value),
            next_version=g.AtomVersion(**native["next_version"]),
            state=g.AtomState[native["state"]],
            error=_error(native["error"]),
        )
    if message_type == "set_timer":
        return g.AtomSetTimer(token=native["token"], ms=native["ms"])
    if message_type == "cancel_timer":
        return g.AtomCancelTimer(token=native["token"])
    if message_type == "producer_stop":
        return g.AtomProducerStop(reason=g.AtomStopReason[native["reason"]])
    if message_type == "diagnostic":
        return g.AtomDiagnostic(
            severity=g.AtomSeverity[native["severity"]],
            code=g.AtomDiagCode[native["code"]],
        )
    raise ValueError(f"input-only atom message {message_type!r}")


def _output_native(message: AtomOutput) -> tuple[str, dict[str, Any]]:
    if isinstance(message, g.AtomReadResponse):
        return "read_response", {
            "atom_id": message.atom_id,
            "stream_id": message.stream_id,
            "value": None
            if message.value is None
            else {"version": message.value.version, "payload": message.value.payload},
            "next_version": {"version": message.next_version.version},
            "state": message.state.name,
            "error": None
            if message.error is None
            else {"code": message.error.code.name, "message": message.error.message},
        }
    if isinstance(message, g.AtomSetTimer):
        return "set_timer", {"token": message.token, "ms": message.ms}
    if isinstance(message, g.AtomCancelTimer):
        return "cancel_timer", {"token": message.token}
    if isinstance(message, g.AtomProducerStop):
        return "producer_stop", {"reason": message.reason.name}
    return "diagnostic", {
        "severity": message.severity.name,
        "code": message.code.name,
    }


def decode_input(frame: framing.Frame) -> AtomInput:
    try:
        message_type = g.AtomMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type not in _INPUT_NAMES:
        raise framing.FrameError(
            f"output-only tag {message_type} on the atom input channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _input(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed atom frame body: {error}") from error


def encode_output(message: AtomOutput) -> tuple[int, bytes]:
    message_type, native = _output_native(message)
    return (
        g.AtomMsgType[message_type].value,
        codec.encode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], native),
    )


def decode_output(frame: framing.Frame) -> AtomOutput:
    try:
        message_type = g.AtomMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type in _INPUT_NAMES:
        raise framing.FrameError(
            f"input-only tag {message_type} on the atom response channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _output(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed atom frame body: {error}") from error


def write_output(stream: BinaryIO, message: AtomOutput) -> None:
    tag, body = encode_output(message)
    framing.write_frame(stream, tag, body)


def write_read(stream: BinaryIO, message: g.AtomReadRequest) -> None:
    native = {
        "atom_id": message.atom_id,
        "stream_id": message.stream_id,
        "version": None
        if message.version is None
        else {"version": message.version.version},
        "timeout_ms": message.timeout_ms,
    }
    body = codec.encode(_SCHEMA, "AtomReadRequest", native)
    framing.write_frame(stream, g.AtomMsgType.read.value, body)


def json_to_input(message: dict[str, Any]) -> AtomInput:
    message_type = str(message["type"])
    if message_type not in _INPUT_NAMES:
        raise ValueError(f"unknown atom input {message_type!r}")
    schema_name = _TYPE_TO_MESSAGE[message_type]
    native = jsoncodec.from_json_value(
        _SCHEMA,
        schema_name,
        {key: value for key, value in message.items() if key != "type"},
    )
    return _input(message_type, cast(dict[str, Any], native))


def output_to_json(message: AtomOutput) -> dict[str, Any]:
    message_type, native = _output_native(message)
    return {
        "type": message_type,
        **jsoncodec.to_json_value(
            _SCHEMA,
            _TYPE_TO_MESSAGE[message_type],
            native,
        ),
    }
