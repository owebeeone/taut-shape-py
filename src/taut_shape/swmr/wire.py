"""SWMR codec/jsoncodec bridge over the canonical Taut schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, cast

from taut.ir.load import load_schema
from taut.wire import codec, jsoncodec

from ..tool import framing
from . import _generated as g
from .engine import SwmrInput, SwmrOutput

_SCHEMA_PATH = Path(__file__).parents[4] / "taut-shape" / "ir" / "shape_swmr.taut.py"
_SCHEMA = load_schema(_SCHEMA_PATH)
_TYPE_TO_MESSAGE = {
    "snapshot_push": "SwmrSnapshotPush",
    "delta_push": "SwmrDeltaPush",
    "reset": "SwmrReset",
    "seal": "SwmrSeal",
    "close": "SwmrClose",
    "read": "SwmrReadRequest",
    "end_stream": "SwmrEndStream",
    "timer_expired": "SwmrTimerExpired",
    "read_response": "SwmrReadResponse",
    "set_timer": "SwmrSetTimer",
    "cancel_timer": "SwmrCancelTimer",
    "producer_stop": "SwmrProducerStop",
    "diagnostic": "SwmrDiagnostic",
}
_INPUT_NAMES = frozenset(
    {
        "snapshot_push",
        "delta_push",
        "reset",
        "seal",
        "close",
        "read",
        "end_stream",
        "timer_expired",
    }
)


def _error(native: dict[str, Any] | None) -> g.SwmrError | None:
    if native is None:
        return None
    return g.SwmrError(g.SwmrErrorCode[native["code"]], native["message"])


def _cursor(native: dict[str, Any] | None) -> g.SwmrCursor | None:
    return None if native is None else g.SwmrCursor(**native)


def _input(message_type: str, native: dict[str, Any]) -> SwmrInput:
    if message_type == "snapshot_push":
        return g.SwmrSnapshotPush(native["writer_id"], native["payload"])
    if message_type == "delta_push":
        return g.SwmrDeltaPush(native["writer_id"], native["payload"])
    if message_type == "reset":
        return g.SwmrReset(
            native["writer_id"],
            g.SwmrResetReason[native["reason"]],
            native["detail"],
        )
    if message_type == "seal":
        return g.SwmrSeal()
    if message_type == "close":
        return g.SwmrClose(_error(native["error"]))
    if message_type == "read":
        return g.SwmrReadRequest(
            native["swmr_id"],
            native["stream_id"],
            _cursor(native["cursor"]),
            native["timeout_ms"],
        )
    if message_type == "end_stream":
        return g.SwmrEndStream(native["swmr_id"], native["stream_id"])
    if message_type == "timer_expired":
        return g.SwmrTimerExpired(native["token"])
    raise ValueError(f"output-only swmr message {message_type!r}")


def _output(message_type: str, native: dict[str, Any]) -> SwmrOutput:
    if message_type == "read_response":
        snapshot = native["snapshot"]
        return g.SwmrReadResponse(
            native["swmr_id"],
            native["stream_id"],
            None if snapshot is None else g.SwmrSnapshot(**snapshot),
            [g.SwmrDelta(**delta) for delta in native["deltas"]],
            _cursor(native["next_cursor"]),
            g.SwmrState[native["state"]],
            None
            if native["reset_reason"] is None
            else g.SwmrResetReason[native["reset_reason"]],
            _error(native["error"]),
            native["reset_detail"],
        )
    if message_type == "set_timer":
        return g.SwmrSetTimer(native["token"], native["ms"])
    if message_type == "cancel_timer":
        return g.SwmrCancelTimer(native["token"])
    if message_type == "producer_stop":
        return g.SwmrProducerStop(g.SwmrStopReason[native["reason"]])
    if message_type == "diagnostic":
        return g.SwmrDiagnostic(
            g.SwmrSeverity[native["severity"]],
            g.SwmrDiagCode[native["code"]],
        )
    raise ValueError(f"input-only swmr message {message_type!r}")


def _error_native(error: g.SwmrError | None) -> dict[str, Any] | None:
    return None if error is None else {"code": error.code.name, "message": error.message}


def _cursor_native(cursor: g.SwmrCursor | None) -> dict[str, Any] | None:
    return None if cursor is None else {"seq": cursor.seq, "epoch": cursor.epoch}


def _output_native(message: SwmrOutput) -> tuple[str, dict[str, Any]]:
    if isinstance(message, g.SwmrReadResponse):
        return "read_response", {
            "swmr_id": message.swmr_id,
            "stream_id": message.stream_id,
            "snapshot": None
            if message.snapshot is None
            else {"seq": message.snapshot.seq, "payload": message.snapshot.payload},
            "deltas": [
                {
                    "base_seq": delta.base_seq,
                    "seq": delta.seq,
                    "payload": delta.payload,
                }
                for delta in message.deltas
            ],
            "next_cursor": _cursor_native(message.next_cursor),
            "state": message.state.name,
            "reset_reason": None
            if message.reset_reason is None
            else message.reset_reason.name,
            "error": _error_native(message.error),
            "reset_detail": message.reset_detail,
        }
    if isinstance(message, g.SwmrSetTimer):
        return "set_timer", {"token": message.token, "ms": message.ms}
    if isinstance(message, g.SwmrCancelTimer):
        return "cancel_timer", {"token": message.token}
    if isinstance(message, g.SwmrProducerStop):
        return "producer_stop", {"reason": message.reason.name}
    return "diagnostic", {
        "severity": message.severity.name,
        "code": message.code.name,
    }


def decode_input(frame: framing.Frame) -> SwmrInput:
    try:
        message_type = g.SwmrMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type not in _INPUT_NAMES:
        raise framing.FrameError(
            f"output-only tag {message_type} on the swmr input channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _input(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed swmr frame body: {error}") from error


def encode_output(message: SwmrOutput) -> tuple[int, bytes]:
    message_type, native = _output_native(message)
    return (
        g.SwmrMsgType[message_type].value,
        codec.encode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], native),
    )


def decode_output(frame: framing.Frame) -> SwmrOutput:
    try:
        message_type = g.SwmrMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if message_type in _INPUT_NAMES:
        raise framing.FrameError(
            f"input-only tag {message_type} on the swmr response channel"
        )
    try:
        native = codec.decode(_SCHEMA, _TYPE_TO_MESSAGE[message_type], frame.body)
        return _output(message_type, native)
    except framing.FrameError:
        raise
    except Exception as error:
        raise framing.FrameError(f"malformed swmr frame body: {error}") from error


def write_output(stream: BinaryIO, message: SwmrOutput) -> None:
    tag, body = encode_output(message)
    framing.write_frame(stream, tag, body)


def write_read(stream: BinaryIO, message: g.SwmrReadRequest) -> None:
    body = codec.encode(
        _SCHEMA,
        "SwmrReadRequest",
        {
            "swmr_id": message.swmr_id,
            "stream_id": message.stream_id,
            "cursor": _cursor_native(message.cursor),
            "timeout_ms": message.timeout_ms,
        },
    )
    framing.write_frame(stream, g.SwmrMsgType.read.value, body)


def json_to_input(message: dict[str, Any]) -> SwmrInput:
    message_type = str(message["type"])
    if message_type not in _INPUT_NAMES:
        raise ValueError(f"unknown swmr input {message_type!r}")
    native = jsoncodec.from_json_value(
        _SCHEMA,
        _TYPE_TO_MESSAGE[message_type],
        {key: value for key, value in message.items() if key != "type"},
    )
    return _input(message_type, cast(dict[str, Any], native))


def output_to_json(message: SwmrOutput) -> dict[str, Any]:
    message_type, native = _output_native(message)
    return {
        "type": message_type,
        **jsoncodec.to_json_value(
            _SCHEMA,
            _TYPE_TO_MESSAGE[message_type],
            native,
        ),
    }
