# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_crdt.taut.py
# Schema sha256: 089a22f8c886208d9304afe394b146343420d6a3214461ee1e9288ee3b6c3ad6
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.crdt', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.crdt: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class CrdtMsgType(_taut_Enum):
    apply = 0
    install_bootstrap = 1
    seal = 2
    close = 3
    read = 4
    read_response = 5
    diagnostic = 6

class CrdtState(_taut_Enum):
    data = 0
    empty = 1
    eof = 2
    closed = 3
    failed = 4
    bootstrap_required = 5
    invalid_cursor = 6

class CrdtErrorCode(_taut_Enum):
    unknown_crdt = 0
    producer_error = 1
    internal = 2

class CrdtSeverity(_taut_Enum):
    warn = 0
    error = 1

class CrdtDiagCode(_taut_Enum):
    apply_after_terminal = 0
    invalid_operation = 1
    equivocation = 2
    bootstrap_conflict = 3
    pending_bound_exceeded = 4

@_taut_dataclass(slots=True)
class CrdtClockEntry:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    origin: str
    seq: int

@_taut_dataclass(slots=True)
class CrdtClock:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    entries: list[CrdtClockEntry]

@_taut_dataclass(slots=True)
class CrdtOp:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    origin: str
    seq: int
    deps: CrdtClock
    payload: bytes

@_taut_dataclass(slots=True)
class CrdtBootstrap:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    clock: CrdtClock
    state: bytes

@_taut_dataclass(slots=True)
class CrdtError:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    code: CrdtErrorCode
    message: str | None

@_taut_dataclass(slots=True)
class CrdtApply:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    op: CrdtOp

@_taut_dataclass(slots=True)
class CrdtInstallBootstrap:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    bootstrap: CrdtBootstrap

@_taut_dataclass(slots=True)
class CrdtSeal:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]

@_taut_dataclass(slots=True)
class CrdtClose:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    error: CrdtError | None

@_taut_dataclass(slots=True)
class CrdtReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    crdt_id: str
    stream_id: str
    cursor: CrdtClock | None

@_taut_dataclass(slots=True)
class CrdtReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    crdt_id: str
    stream_id: str
    bootstrap: CrdtBootstrap | None
    ops: list[CrdtOp]
    next_cursor: CrdtClock
    state: CrdtState
    error: CrdtError | None

@_taut_dataclass(slots=True)
class CrdtDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: CrdtSeverity
    code: CrdtDiagCode
    origin: str | None
    seq: int | None

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'CrdtMsgType': _taut_facts.EnumDef(name='CrdtMsgType', members={'apply': 0, 'install_bootstrap': 1, 'seal': 2, 'close': 3, 'read': 4, 'read_response': 5, 'diagnostic': 6}, options={}), 'CrdtState': _taut_facts.EnumDef(name='CrdtState', members={'data': 0, 'empty': 1, 'eof': 2, 'closed': 3, 'failed': 4, 'bootstrap_required': 5, 'invalid_cursor': 6}, options={}), 'CrdtErrorCode': _taut_facts.EnumDef(name='CrdtErrorCode', members={'unknown_crdt': 0, 'producer_error': 1, 'internal': 2}, options={}), 'CrdtSeverity': _taut_facts.EnumDef(name='CrdtSeverity', members={'warn': 0, 'error': 1}, options={}), 'CrdtDiagCode': _taut_facts.EnumDef(name='CrdtDiagCode', members={'apply_after_terminal': 0, 'invalid_operation': 1, 'equivocation': 2, 'bootstrap_conflict': 3, 'pending_bound_exceeded': 4}, options={})}, messages={'CrdtClockEntry': _taut_facts.MessageDef(name='CrdtClockEntry', fields=(_taut_facts.FieldDef(name='origin', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtClock': _taut_facts.MessageDef(name='CrdtClock', fields=(_taut_facts.FieldDef(name='entries', tag=1, type=_taut_facts.ListOf(elem=_taut_facts.MsgRef(name='CrdtClockEntry')), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtOp': _taut_facts.MessageDef(name='CrdtOp', fields=(_taut_facts.FieldDef(name='origin', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='deps', tag=3, type=_taut_facts.MsgRef(name='CrdtClock'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=4, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtBootstrap': _taut_facts.MessageDef(name='CrdtBootstrap', fields=(_taut_facts.FieldDef(name='clock', tag=1, type=_taut_facts.MsgRef(name='CrdtClock'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtError': _taut_facts.MessageDef(name='CrdtError', fields=(_taut_facts.FieldDef(name='code', tag=1, type=_taut_facts.EnumRef(name='CrdtErrorCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='message', tag=2, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtApply': _taut_facts.MessageDef(name='CrdtApply', fields=(_taut_facts.FieldDef(name='op', tag=1, type=_taut_facts.MsgRef(name='CrdtOp'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtInstallBootstrap': _taut_facts.MessageDef(name='CrdtInstallBootstrap', fields=(_taut_facts.FieldDef(name='bootstrap', tag=1, type=_taut_facts.MsgRef(name='CrdtBootstrap'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtSeal': _taut_facts.MessageDef(name='CrdtSeal', fields=(), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtClose': _taut_facts.MessageDef(name='CrdtClose', fields=(_taut_facts.FieldDef(name='error', tag=1, type=_taut_facts.MsgRef(name='CrdtError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtReadRequest': _taut_facts.MessageDef(name='CrdtReadRequest', fields=(_taut_facts.FieldDef(name='crdt_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='cursor', tag=3, type=_taut_facts.MsgRef(name='CrdtClock'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtReadResponse': _taut_facts.MessageDef(name='CrdtReadResponse', fields=(_taut_facts.FieldDef(name='crdt_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='bootstrap', tag=3, type=_taut_facts.MsgRef(name='CrdtBootstrap'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='ops', tag=4, type=_taut_facts.ListOf(elem=_taut_facts.MsgRef(name='CrdtOp')), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='next_cursor', tag=5, type=_taut_facts.MsgRef(name='CrdtClock'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=6, type=_taut_facts.EnumRef(name='CrdtState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='error', tag=7, type=_taut_facts.MsgRef(name='CrdtError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'CrdtDiagnostic': _taut_facts.MessageDef(name='CrdtDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='CrdtSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='CrdtDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='origin', tag=3, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=4, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'CrdtClockEntry': CrdtClockEntry, 'CrdtClock': CrdtClock, 'CrdtOp': CrdtOp, 'CrdtBootstrap': CrdtBootstrap, 'CrdtError': CrdtError, 'CrdtApply': CrdtApply, 'CrdtInstallBootstrap': CrdtInstallBootstrap, 'CrdtSeal': CrdtSeal, 'CrdtClose': CrdtClose, 'CrdtReadRequest': CrdtReadRequest, 'CrdtReadResponse': CrdtReadResponse, 'CrdtDiagnostic': CrdtDiagnostic},
    {'CrdtMsgType': CrdtMsgType, 'CrdtState': CrdtState, 'CrdtErrorCode': CrdtErrorCode, 'CrdtSeverity': CrdtSeverity, 'CrdtDiagCode': CrdtDiagCode},
    identity='taut_shape.crdt', ir_version=2, external=(),
    attributes={'CrdtClockEntry': {'origin': 'origin', 'seq': 'seq'}, 'CrdtClock': {'entries': 'entries'}, 'CrdtOp': {'origin': 'origin', 'seq': 'seq', 'deps': 'deps', 'payload': 'payload'}, 'CrdtBootstrap': {'clock': 'clock', 'state': 'state'}, 'CrdtError': {'code': 'code', 'message': 'message'}, 'CrdtApply': {'op': 'op'}, 'CrdtInstallBootstrap': {'bootstrap': 'bootstrap'}, 'CrdtSeal': {}, 'CrdtClose': {'error': 'error'}, 'CrdtReadRequest': {'crdt_id': 'crdt_id', 'stream_id': 'stream_id', 'cursor': 'cursor'}, 'CrdtReadResponse': {'crdt_id': 'crdt_id', 'stream_id': 'stream_id', 'bootstrap': 'bootstrap', 'ops': 'ops', 'next_cursor': 'next_cursor', 'state': 'state', 'error': 'error'}, 'CrdtDiagnostic': {'severity': 'severity', 'code': 'code', 'origin': 'origin', 'seq': 'seq'}})

__all__ = ['CrdtMsgType', 'CrdtState', 'CrdtErrorCode', 'CrdtSeverity', 'CrdtDiagCode', 'CrdtClockEntry', 'CrdtClock', 'CrdtOp', 'CrdtBootstrap', 'CrdtError', 'CrdtApply', 'CrdtInstallBootstrap', 'CrdtSeal', 'CrdtClose', 'CrdtReadRequest', 'CrdtReadResponse', 'CrdtDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
