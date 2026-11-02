# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_atom.taut.py
# Schema sha256: 2fff65c82bad67de654037cd10a2792f80586c70996edb8ca91f3abe7e986dcb
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.atom', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.atom: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class AtomMsgType(_taut_Enum):
    replace = 0
    seal = 1
    close = 2
    read = 3
    end_stream = 4
    timer_expired = 5
    read_response = 6
    set_timer = 7
    cancel_timer = 8
    producer_stop = 9
    diagnostic = 10

class AtomState(_taut_Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4

class AtomErrorCode(_taut_Enum):
    unknown_atom = 0
    producer_error = 1
    internal = 2

class AtomStopReason(_taut_Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class AtomSeverity(_taut_Enum):
    warn = 0
    error = 1

class AtomDiagCode(_taut_Enum):
    replace_after_terminal = 0

@_taut_dataclass(slots=True)
class AtomVersion:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    version: int

@_taut_dataclass(slots=True)
class AtomValue:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    version: int
    payload: bytes

@_taut_dataclass(slots=True)
class AtomError:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    code: AtomErrorCode
    message: str | None

@_taut_dataclass(slots=True)
class AtomReplace:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    payload: bytes

@_taut_dataclass(slots=True)
class AtomSeal:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]

@_taut_dataclass(slots=True)
class AtomClose:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    error: AtomError | None

@_taut_dataclass(slots=True)
class AtomReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    atom_id: str
    stream_id: str
    version: AtomVersion | None
    timeout_ms: int | None

@_taut_dataclass(slots=True)
class AtomEndStream:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    atom_id: str
    stream_id: str

@_taut_dataclass(slots=True)
class AtomTimerExpired:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class AtomReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    atom_id: str
    stream_id: str
    value: AtomValue | None
    next_version: AtomVersion
    state: AtomState
    error: AtomError | None

@_taut_dataclass(slots=True)
class AtomSetTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int
    ms: int

@_taut_dataclass(slots=True)
class AtomCancelTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class AtomProducerStop:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    reason: AtomStopReason

@_taut_dataclass(slots=True)
class AtomDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: AtomSeverity
    code: AtomDiagCode

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'AtomMsgType': _taut_facts.EnumDef(name='AtomMsgType', members={'replace': 0, 'seal': 1, 'close': 2, 'read': 3, 'end_stream': 4, 'timer_expired': 5, 'read_response': 6, 'set_timer': 7, 'cancel_timer': 8, 'producer_stop': 9, 'diagnostic': 10}, options={}), 'AtomState': _taut_facts.EnumDef(name='AtomState', members={'data': 0, 'would_block': 1, 'eof': 2, 'closed': 3, 'failed': 4}, options={}), 'AtomErrorCode': _taut_facts.EnumDef(name='AtomErrorCode', members={'unknown_atom': 0, 'producer_error': 1, 'internal': 2}, options={}), 'AtomStopReason': _taut_facts.EnumDef(name='AtomStopReason', members={'last_reader_gone': 0, 'closed': 1, 'failed': 2}, options={}), 'AtomSeverity': _taut_facts.EnumDef(name='AtomSeverity', members={'warn': 0, 'error': 1}, options={}), 'AtomDiagCode': _taut_facts.EnumDef(name='AtomDiagCode', members={'replace_after_terminal': 0}, options={})}, messages={'AtomVersion': _taut_facts.MessageDef(name='AtomVersion', fields=(_taut_facts.FieldDef(name='version', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomValue': _taut_facts.MessageDef(name='AtomValue', fields=(_taut_facts.FieldDef(name='version', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomError': _taut_facts.MessageDef(name='AtomError', fields=(_taut_facts.FieldDef(name='code', tag=1, type=_taut_facts.EnumRef(name='AtomErrorCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='message', tag=2, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomReplace': _taut_facts.MessageDef(name='AtomReplace', fields=(_taut_facts.FieldDef(name='payload', tag=1, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomSeal': _taut_facts.MessageDef(name='AtomSeal', fields=(), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomClose': _taut_facts.MessageDef(name='AtomClose', fields=(_taut_facts.FieldDef(name='error', tag=1, type=_taut_facts.MsgRef(name='AtomError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomReadRequest': _taut_facts.MessageDef(name='AtomReadRequest', fields=(_taut_facts.FieldDef(name='atom_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='version', tag=3, type=_taut_facts.MsgRef(name='AtomVersion'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='timeout_ms', tag=4, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomEndStream': _taut_facts.MessageDef(name='AtomEndStream', fields=(_taut_facts.FieldDef(name='atom_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomTimerExpired': _taut_facts.MessageDef(name='AtomTimerExpired', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomReadResponse': _taut_facts.MessageDef(name='AtomReadResponse', fields=(_taut_facts.FieldDef(name='atom_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='value', tag=3, type=_taut_facts.MsgRef(name='AtomValue'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='next_version', tag=4, type=_taut_facts.MsgRef(name='AtomVersion'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=5, type=_taut_facts.EnumRef(name='AtomState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='error', tag=6, type=_taut_facts.MsgRef(name='AtomError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomSetTimer': _taut_facts.MessageDef(name='AtomSetTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='ms', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomCancelTimer': _taut_facts.MessageDef(name='AtomCancelTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomProducerStop': _taut_facts.MessageDef(name='AtomProducerStop', fields=(_taut_facts.FieldDef(name='reason', tag=1, type=_taut_facts.EnumRef(name='AtomStopReason'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'AtomDiagnostic': _taut_facts.MessageDef(name='AtomDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='AtomSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='AtomDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'AtomVersion': AtomVersion, 'AtomValue': AtomValue, 'AtomError': AtomError, 'AtomReplace': AtomReplace, 'AtomSeal': AtomSeal, 'AtomClose': AtomClose, 'AtomReadRequest': AtomReadRequest, 'AtomEndStream': AtomEndStream, 'AtomTimerExpired': AtomTimerExpired, 'AtomReadResponse': AtomReadResponse, 'AtomSetTimer': AtomSetTimer, 'AtomCancelTimer': AtomCancelTimer, 'AtomProducerStop': AtomProducerStop, 'AtomDiagnostic': AtomDiagnostic},
    {'AtomMsgType': AtomMsgType, 'AtomState': AtomState, 'AtomErrorCode': AtomErrorCode, 'AtomStopReason': AtomStopReason, 'AtomSeverity': AtomSeverity, 'AtomDiagCode': AtomDiagCode},
    identity='taut_shape.atom', ir_version=2, external=(),
    attributes={'AtomVersion': {'version': 'version'}, 'AtomValue': {'version': 'version', 'payload': 'payload'}, 'AtomError': {'code': 'code', 'message': 'message'}, 'AtomReplace': {'payload': 'payload'}, 'AtomSeal': {}, 'AtomClose': {'error': 'error'}, 'AtomReadRequest': {'atom_id': 'atom_id', 'stream_id': 'stream_id', 'version': 'version', 'timeout_ms': 'timeout_ms'}, 'AtomEndStream': {'atom_id': 'atom_id', 'stream_id': 'stream_id'}, 'AtomTimerExpired': {'token': 'token'}, 'AtomReadResponse': {'atom_id': 'atom_id', 'stream_id': 'stream_id', 'value': 'value', 'next_version': 'next_version', 'state': 'state', 'error': 'error'}, 'AtomSetTimer': {'token': 'token', 'ms': 'ms'}, 'AtomCancelTimer': {'token': 'token'}, 'AtomProducerStop': {'reason': 'reason'}, 'AtomDiagnostic': {'severity': 'severity', 'code': 'code'}})

__all__ = ['AtomMsgType', 'AtomState', 'AtomErrorCode', 'AtomStopReason', 'AtomSeverity', 'AtomDiagCode', 'AtomVersion', 'AtomValue', 'AtomError', 'AtomReplace', 'AtomSeal', 'AtomClose', 'AtomReadRequest', 'AtomEndStream', 'AtomTimerExpired', 'AtomReadResponse', 'AtomSetTimer', 'AtomCancelTimer', 'AtomProducerStop', 'AtomDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
