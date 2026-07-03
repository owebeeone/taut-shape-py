"""Oracle-format bridge: corpus JSON (taut jsoncodec form) <-> engine messages.

The corpus (``TautShapeOracle.md`` §3) stores each message as the **taut
jsoncodec form** of a ``shape_log`` schema message (base64 bytes, i64-as-string,
enums as member names, absent optionals as ``null``) plus a ``type``
discriminator (the ``LogMsgType`` member name).

This module is the single place that maps between that wire-legible form and the
generated dataclasses the engine consumes/produces. It reuses taut verbatim:

* ``taut.ir.load.load_schema`` loads the pinned ``shape_log.taut.py`` schema.
* ``taut.wire.jsoncodec.to_json_value`` / ``from_json_value`` do the
  scalar/bytes/enum/optional normalization — no bespoke corpus serializer.

The only hand-written glue is (a) the ``type`` <-> schema-message-name table and
(b) the native-dict <-> dataclass reconstruction, both mechanical over the
generated types.
"""

from __future__ import annotations

import os
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from taut.ir.load import load_schema
from taut.wire import jsoncodec

from ..log import _generated as g

# type discriminator (LogMsgType member) -> (schema message name, dataclass)
_BY_TYPE: dict[str, tuple[str, type]] = {
    "push": ("LogPush", g.LogPush),
    "seal": ("LogSeal", g.LogSeal),
    "close": ("LogClose", g.LogClose),
    "read": ("LogReadRequest", g.LogReadRequest),
    "end_stream": ("LogEndStream", g.LogEndStream),
    "timer_expired": ("LogTimerExpired", g.LogTimerExpired),
    "evict": ("LogEvict", g.LogEvict),
    "read_response": ("LogReadResponse", g.LogReadResponse),
    "set_timer": ("LogSetTimer", g.LogSetTimer),
    "cancel_timer": ("LogCancelTimer", g.LogCancelTimer),
    "producer_stop": ("LogProducerStop", g.LogProducerStop),
    "diagnostic": ("LogDiagnostic", g.LogDiagnostic),
}
# dataclass -> (type discriminator, schema message name)
_BY_CLASS: dict[type, tuple[str, str]] = {
    cls: (tag, name) for tag, (name, cls) in _BY_TYPE.items()
}


def _default_schema_path() -> Path:
    override = os.environ.get("TAUT_SHAPE_SCHEMA")
    if override:
        return Path(override)
    # sibling taut-shape repo: taut-shape-py/.. -> taut-shape/ir/shape_log.taut.py
    here = Path(__file__).resolve()
    repo_root = here.parents[3]                      # .../taut-shape-py
    return repo_root.parent / "taut-shape" / "ir" / "shape_log.taut.py"


_SCHEMA = load_schema(_default_schema_path())


# ---- native-dict (jsoncodec form) <-> dataclass -----------------------------

def _to_native(value: Any) -> Any:
    """Dataclass instance -> jsoncodec native value (dict keyed by field name,
    enums as member-name strings, nested dataclasses recursed, bytes/None kept).
    """
    if isinstance(value, Enum):
        return value.name
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_native(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (list, tuple)):
        return [_to_native(v) for v in value]
    return value


def _from_native(cls: type, native: dict[str, Any]) -> Any:
    """jsoncodec native value (dict) -> dataclass instance of ``cls``."""
    kwargs: dict[str, Any] = {}
    hints = _field_types(cls)
    for f in fields(cls):
        kwargs[f.name] = _coerce(hints[f.name], native.get(f.name))
    return cls(**kwargs)


def _field_types(cls: type) -> dict[str, Any]:
    # dataclass field.type may be a string (PEP 563); resolve against the
    # generated module + typing so we can reconstruct enums/nested messages.
    import typing

    return typing.get_type_hints(cls, globalns=vars(g))


def _coerce(hint: Any, native: Any) -> Any:
    if native is None:
        return None
    origin = getattr(hint, "__args__", None)
    # optional/union: pick the non-None member
    if origin is not None:
        members = [a for a in hint.__args__ if a is not type(None)]  # noqa: E721
        if len(members) == 1:
            return _coerce(members[0], native)
        # list[X]
        list_origin = getattr(hint, "__origin__", None)
        if list_origin in (list, tuple) and members:
            return [_coerce(members[0], v) for v in native]
        return native
    list_origin = getattr(hint, "__origin__", None)
    if list_origin in (list, tuple):
        (elem,) = hint.__args__
        return [_coerce(elem, v) for v in native]
    if isinstance(hint, type) and issubclass(hint, Enum):
        return hint[native]                          # member name -> enum
    if isinstance(hint, type) and is_dataclass(hint):
        return _from_native(hint, native)
    return native


# ---- public: corpus JSON <-> engine messages --------------------------------

def json_to_msg(obj: dict[str, Any]) -> Any:
    """Corpus JSON object (with ``type``) -> engine message dataclass."""
    tag = obj["type"]
    name, cls = _BY_TYPE[tag]
    jv = {k: v for k, v in obj.items() if k != "type"}
    native = jsoncodec.from_json_value(_SCHEMA, name, jv)
    return _from_native(cls, native)


def msg_to_json(msg: Any) -> dict[str, Any]:
    """Engine message dataclass -> corpus JSON object (with ``type``)."""
    tag, name = _BY_CLASS[type(msg)]
    native = _to_native(msg)
    jv = jsoncodec.to_json_value(_SCHEMA, name, native)
    return {"type": tag, **jv}
