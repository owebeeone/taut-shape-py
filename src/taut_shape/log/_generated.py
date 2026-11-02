# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_log.taut.py
# Schema sha256: 3e1224747430e12188beab3ece4d8ebe44decbcae3fe4b86c2731136617863a9
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.log', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.log: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class LogMsgType(_taut_Enum):
    push = 0
    seal = 1
    close = 2
    read = 3
    end_stream = 4
    timer_expired = 5
    evict = 6
    read_response = 7
    set_timer = 8
    cancel_timer = 9
    producer_stop = 10
    diagnostic = 11

class LogState(_taut_Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    expired = 5

class LogErrorCode(_taut_Enum):
    unknown_log = 0
    producer_error = 1
    internal = 2

class LogStopReason(_taut_Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class LogSeverity(_taut_Enum):
    warn = 0
    error = 1

class LogDiagCode(_taut_Enum):
    push_after_terminal = 0

@_taut_dataclass(slots=True)
class LogCursor:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int

@_taut_dataclass(slots=True)
class LogRecord:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int
    payload: bytes

@_taut_dataclass(slots=True)
class LogError:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    code: LogErrorCode
    message: str | None

@_taut_dataclass(slots=True)
class LogPush:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    payload: bytes

@_taut_dataclass(slots=True)
class LogSeal:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]

@_taut_dataclass(slots=True)
class LogClose:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    error: LogError | None

@_taut_dataclass(slots=True)
class LogReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    log_id: str
    stream_id: str
    cursor: LogCursor | None
    max_records: int | None
    max_bytes: int | None
    timeout_ms: int | None

@_taut_dataclass(slots=True)
class LogEndStream:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    log_id: str
    stream_id: str

@_taut_dataclass(slots=True)
class LogTimerExpired:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class LogEvict:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    up_to_seq: int

@_taut_dataclass(slots=True)
class LogReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    log_id: str
    stream_id: str
    records: list[LogRecord]
    next_cursor: LogCursor
    state: LogState
    error: LogError | None

@_taut_dataclass(slots=True)
class LogSetTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int
    ms: int

@_taut_dataclass(slots=True)
class LogCancelTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class LogProducerStop:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    reason: LogStopReason

@_taut_dataclass(slots=True)
class LogDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: LogSeverity
    code: LogDiagCode

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'LogMsgType': _taut_facts.EnumDef(name='LogMsgType', members={'push': 0, 'seal': 1, 'close': 2, 'read': 3, 'end_stream': 4, 'timer_expired': 5, 'evict': 6, 'read_response': 7, 'set_timer': 8, 'cancel_timer': 9, 'producer_stop': 10, 'diagnostic': 11}, options={}), 'LogState': _taut_facts.EnumDef(name='LogState', members={'data': 0, 'would_block': 1, 'eof': 2, 'closed': 3, 'failed': 4, 'expired': 5}, options={}), 'LogErrorCode': _taut_facts.EnumDef(name='LogErrorCode', members={'unknown_log': 0, 'producer_error': 1, 'internal': 2}, options={}), 'LogStopReason': _taut_facts.EnumDef(name='LogStopReason', members={'last_reader_gone': 0, 'closed': 1, 'failed': 2}, options={}), 'LogSeverity': _taut_facts.EnumDef(name='LogSeverity', members={'warn': 0, 'error': 1}, options={}), 'LogDiagCode': _taut_facts.EnumDef(name='LogDiagCode', members={'push_after_terminal': 0}, options={})}, messages={'LogCursor': _taut_facts.MessageDef(name='LogCursor', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogRecord': _taut_facts.MessageDef(name='LogRecord', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogError': _taut_facts.MessageDef(name='LogError', fields=(_taut_facts.FieldDef(name='code', tag=1, type=_taut_facts.EnumRef(name='LogErrorCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='message', tag=2, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogPush': _taut_facts.MessageDef(name='LogPush', fields=(_taut_facts.FieldDef(name='payload', tag=1, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogSeal': _taut_facts.MessageDef(name='LogSeal', fields=(), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogClose': _taut_facts.MessageDef(name='LogClose', fields=(_taut_facts.FieldDef(name='error', tag=1, type=_taut_facts.MsgRef(name='LogError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogReadRequest': _taut_facts.MessageDef(name='LogReadRequest', fields=(_taut_facts.FieldDef(name='log_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='cursor', tag=3, type=_taut_facts.MsgRef(name='LogCursor'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='max_records', tag=4, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='max_bytes', tag=5, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='timeout_ms', tag=6, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogEndStream': _taut_facts.MessageDef(name='LogEndStream', fields=(_taut_facts.FieldDef(name='log_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogTimerExpired': _taut_facts.MessageDef(name='LogTimerExpired', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogEvict': _taut_facts.MessageDef(name='LogEvict', fields=(_taut_facts.FieldDef(name='up_to_seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogReadResponse': _taut_facts.MessageDef(name='LogReadResponse', fields=(_taut_facts.FieldDef(name='log_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='records', tag=3, type=_taut_facts.ListOf(elem=_taut_facts.MsgRef(name='LogRecord')), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='next_cursor', tag=4, type=_taut_facts.MsgRef(name='LogCursor'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=5, type=_taut_facts.EnumRef(name='LogState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='error', tag=6, type=_taut_facts.MsgRef(name='LogError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogSetTimer': _taut_facts.MessageDef(name='LogSetTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='ms', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogCancelTimer': _taut_facts.MessageDef(name='LogCancelTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogProducerStop': _taut_facts.MessageDef(name='LogProducerStop', fields=(_taut_facts.FieldDef(name='reason', tag=1, type=_taut_facts.EnumRef(name='LogStopReason'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'LogDiagnostic': _taut_facts.MessageDef(name='LogDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='LogSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='LogDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'LogCursor': LogCursor, 'LogRecord': LogRecord, 'LogError': LogError, 'LogPush': LogPush, 'LogSeal': LogSeal, 'LogClose': LogClose, 'LogReadRequest': LogReadRequest, 'LogEndStream': LogEndStream, 'LogTimerExpired': LogTimerExpired, 'LogEvict': LogEvict, 'LogReadResponse': LogReadResponse, 'LogSetTimer': LogSetTimer, 'LogCancelTimer': LogCancelTimer, 'LogProducerStop': LogProducerStop, 'LogDiagnostic': LogDiagnostic},
    {'LogMsgType': LogMsgType, 'LogState': LogState, 'LogErrorCode': LogErrorCode, 'LogStopReason': LogStopReason, 'LogSeverity': LogSeverity, 'LogDiagCode': LogDiagCode},
    identity='taut_shape.log', ir_version=2, external=(),
    attributes={'LogCursor': {'seq': 'seq'}, 'LogRecord': {'seq': 'seq', 'payload': 'payload'}, 'LogError': {'code': 'code', 'message': 'message'}, 'LogPush': {'payload': 'payload'}, 'LogSeal': {}, 'LogClose': {'error': 'error'}, 'LogReadRequest': {'log_id': 'log_id', 'stream_id': 'stream_id', 'cursor': 'cursor', 'max_records': 'max_records', 'max_bytes': 'max_bytes', 'timeout_ms': 'timeout_ms'}, 'LogEndStream': {'log_id': 'log_id', 'stream_id': 'stream_id'}, 'LogTimerExpired': {'token': 'token'}, 'LogEvict': {'up_to_seq': 'up_to_seq'}, 'LogReadResponse': {'log_id': 'log_id', 'stream_id': 'stream_id', 'records': 'records', 'next_cursor': 'next_cursor', 'state': 'state', 'error': 'error'}, 'LogSetTimer': {'token': 'token', 'ms': 'ms'}, 'LogCancelTimer': {'token': 'token'}, 'LogProducerStop': {'reason': 'reason'}, 'LogDiagnostic': {'severity': 'severity', 'code': 'code'}})

__all__ = ['LogMsgType', 'LogState', 'LogErrorCode', 'LogStopReason', 'LogSeverity', 'LogDiagCode', 'LogCursor', 'LogRecord', 'LogError', 'LogPush', 'LogSeal', 'LogClose', 'LogReadRequest', 'LogEndStream', 'LogTimerExpired', 'LogEvict', 'LogReadResponse', 'LogSetTimer', 'LogCancelTimer', 'LogProducerStop', 'LogDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
