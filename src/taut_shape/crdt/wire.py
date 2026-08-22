"""CBOR/jsoncodec bridge for the canonical CRDT schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taut.ir.load import load_schema
from taut.wire import codec, jsoncodec

from . import _generated as g
from .engine import CrdtInput, CrdtOutput
from ..tool import framing

_SCHEMA = load_schema(Path(__file__).parents[4] / "taut-shape" / "ir" / "shape_crdt.taut.py")
_NAMES = {
    "apply": "CrdtApply", "install_bootstrap": "CrdtInstallBootstrap", "seal": "CrdtSeal",
    "close": "CrdtClose", "read": "CrdtReadRequest", "read_response": "CrdtReadResponse",
    "diagnostic": "CrdtDiagnostic",
}


def _to_clock(value: dict[str, Any]) -> g.CrdtClock:
    return g.CrdtClock([g.CrdtClockEntry(**entry) for entry in value["entries"]])


def _to_op(value: dict[str, Any]) -> g.CrdtOp:
    return g.CrdtOp(value["origin"], value["seq"], _to_clock(value["deps"]), value["payload"])


def _to_bootstrap(value: dict[str, Any]) -> g.CrdtBootstrap:
    return g.CrdtBootstrap(_to_clock(value["clock"]), value["state"])


def _from_native(kind: str, value: dict[str, Any]) -> CrdtInput | CrdtOutput:
    if kind == "apply": return g.CrdtApply(_to_op(value["op"]))
    if kind == "install_bootstrap": return g.CrdtInstallBootstrap(_to_bootstrap(value["bootstrap"]))
    if kind == "seal": return g.CrdtSeal()
    if kind == "close":
        err = value["error"]
        return g.CrdtClose(None if err is None else g.CrdtError(g.CrdtErrorCode[err["code"]], err["message"]))
    if kind == "read":
        cursor = value["cursor"]
        return g.CrdtReadRequest(value["crdt_id"], value["stream_id"], None if cursor is None else _to_clock(cursor))
    if kind == "read_response":
        bootstrap = value["bootstrap"]
        err = value["error"]
        return g.CrdtReadResponse(value["crdt_id"], value["stream_id"], None if bootstrap is None else _to_bootstrap(bootstrap), [_to_op(op) for op in value["ops"]], _to_clock(value["next_cursor"]), g.CrdtState[value["state"]], None if err is None else g.CrdtError(g.CrdtErrorCode[err["code"]], err["message"]))
    return g.CrdtDiagnostic(g.CrdtSeverity[value["severity"]], g.CrdtDiagCode[value["code"]], value["origin"], value["seq"])


def json_to_input(message: dict[str, Any]) -> CrdtInput:
    kind = str(message["type"])
    if kind not in {"apply", "install_bootstrap", "seal", "close", "read"}:
        raise ValueError(f"unknown CRDT input {kind!r}")
    native = jsoncodec.from_json_value(_SCHEMA, _NAMES[kind], {k: v for k, v in message.items() if k != "type"})
    result = _from_native(kind, native)
    assert not isinstance(result, (g.CrdtReadResponse, g.CrdtDiagnostic))
    return result


def message_to_json(message: CrdtInput | CrdtOutput) -> dict[str, Any]:
    kind = {
        g.CrdtApply: "apply", g.CrdtInstallBootstrap: "install_bootstrap", g.CrdtSeal: "seal",
        g.CrdtClose: "close", g.CrdtReadRequest: "read", g.CrdtReadResponse: "read_response",
        g.CrdtDiagnostic: "diagnostic",
    }[type(message)]
    # The generated dataclasses are structurally identical to codec native
    # values after recursively replacing enums with their names.
    def native(value: Any) -> Any:
        if isinstance(value, list): return [native(item) for item in value]
        if hasattr(value, "name") and isinstance(value, (g.CrdtState, g.CrdtErrorCode, g.CrdtSeverity, g.CrdtDiagCode)):
            return value.name
        if hasattr(value, "__dataclass_fields__"):
            return {name: native(getattr(value, name)) for name in value.__dataclass_fields__}
        return value
    return {"type": kind, **jsoncodec.to_json_value(_SCHEMA, _NAMES[kind], native(message))}


def decode_input(frame: framing.Frame) -> CrdtInput:
    try:
        kind = g.CrdtMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if kind not in {"apply", "install_bootstrap", "seal", "close", "read"}:
        raise framing.FrameError(f"output-only tag {kind} on the CRDT input channel")
    try:
        return _from_native(kind, codec.decode(_SCHEMA, _NAMES[kind], frame.body))  # type: ignore[return-value]
    except Exception as error:
        raise framing.FrameError(f"malformed CRDT frame body: {error}") from error


def encode_message(message: CrdtInput | CrdtOutput) -> tuple[int, bytes]:
    encoded = message_to_json(message)
    kind = encoded.pop("type")
    native = jsoncodec.from_json_value(_SCHEMA, _NAMES[kind], encoded)
    return g.CrdtMsgType[kind].value, codec.encode(_SCHEMA, _NAMES[kind], native)


def decode_output(frame: framing.Frame) -> CrdtOutput:
    try:
        kind = g.CrdtMsgType(frame.tag).name
    except ValueError as error:
        raise framing.UnknownMessageTagError(frame.tag) from error
    if kind not in {"read_response", "diagnostic"}:
        raise framing.FrameError(f"input-only tag {kind} on the CRDT output channel")
    return _from_native(kind, codec.decode(_SCHEMA, _NAMES[kind], frame.body))  # type: ignore[return-value]
