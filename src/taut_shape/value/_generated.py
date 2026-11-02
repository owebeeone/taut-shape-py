# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_value.taut.py
# Schema sha256: ad7dd65908271473ba23dc1f9907ad9913e57962c7644d07c729a4216aa29b5d
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.value', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.value: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class ValueMsgType(_taut_Enum):
    set = 0
    read = 1
    read_response = 2
    diagnostic = 3

class ValueState(_taut_Enum):
    data = 0
    empty = 1

class ValueSeverity(_taut_Enum):
    warn = 0
    error = 1

class ValueDiagCode(_taut_Enum):
    equivocation = 0

@_taut_dataclass(slots=True)
class ValueStamp:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    origin: str
    seq: int
    lamport: int

@_taut_dataclass(slots=True)
class ValueSet:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    origin: str
    seq: int
    lamport: int
    prev: bytes | None
    payload: bytes

@_taut_dataclass(slots=True)
class ValueReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    value_id: str
    stream_id: str

@_taut_dataclass(slots=True)
class ValueReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    value_id: str
    stream_id: str
    value: bytes | None
    winner: ValueStamp | None
    state: ValueState

@_taut_dataclass(slots=True)
class ValueDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: ValueSeverity
    code: ValueDiagCode

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'ValueMsgType': _taut_facts.EnumDef(name='ValueMsgType', members={'set': 0, 'read': 1, 'read_response': 2, 'diagnostic': 3}, options={}), 'ValueState': _taut_facts.EnumDef(name='ValueState', members={'data': 0, 'empty': 1}, options={}), 'ValueSeverity': _taut_facts.EnumDef(name='ValueSeverity', members={'warn': 0, 'error': 1}, options={}), 'ValueDiagCode': _taut_facts.EnumDef(name='ValueDiagCode', members={'equivocation': 0}, options={})}, messages={'ValueStamp': _taut_facts.MessageDef(name='ValueStamp', fields=(_taut_facts.FieldDef(name='origin', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='lamport', tag=3, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'ValueSet': _taut_facts.MessageDef(name='ValueSet', fields=(_taut_facts.FieldDef(name='origin', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='lamport', tag=3, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='prev', tag=4, type=_taut_facts.Scalar(kind='bytes'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=5, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'ValueReadRequest': _taut_facts.MessageDef(name='ValueReadRequest', fields=(_taut_facts.FieldDef(name='value_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'ValueReadResponse': _taut_facts.MessageDef(name='ValueReadResponse', fields=(_taut_facts.FieldDef(name='value_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='value', tag=3, type=_taut_facts.Scalar(kind='bytes'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='winner', tag=4, type=_taut_facts.MsgRef(name='ValueStamp'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=5, type=_taut_facts.EnumRef(name='ValueState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'ValueDiagnostic': _taut_facts.MessageDef(name='ValueDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='ValueSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='ValueDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'ValueStamp': ValueStamp, 'ValueSet': ValueSet, 'ValueReadRequest': ValueReadRequest, 'ValueReadResponse': ValueReadResponse, 'ValueDiagnostic': ValueDiagnostic},
    {'ValueMsgType': ValueMsgType, 'ValueState': ValueState, 'ValueSeverity': ValueSeverity, 'ValueDiagCode': ValueDiagCode},
    identity='taut_shape.value', ir_version=2, external=(),
    attributes={'ValueStamp': {'origin': 'origin', 'seq': 'seq', 'lamport': 'lamport'}, 'ValueSet': {'origin': 'origin', 'seq': 'seq', 'lamport': 'lamport', 'prev': 'prev', 'payload': 'payload'}, 'ValueReadRequest': {'value_id': 'value_id', 'stream_id': 'stream_id'}, 'ValueReadResponse': {'value_id': 'value_id', 'stream_id': 'stream_id', 'value': 'value', 'winner': 'winner', 'state': 'state'}, 'ValueDiagnostic': {'severity': 'severity', 'code': 'code'}})

__all__ = ['ValueMsgType', 'ValueState', 'ValueSeverity', 'ValueDiagCode', 'ValueStamp', 'ValueSet', 'ValueReadRequest', 'ValueReadResponse', 'ValueDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
