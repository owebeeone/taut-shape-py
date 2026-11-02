# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_stream.taut.py
# Schema sha256: 278d6fd4d64374ab6c2874ab82a0b61724d7987486e6467611fededddf325528
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.stream', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.stream: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class StreamMsgType(_taut_Enum):
    push = 0
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

class StreamState(_taut_Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    dropped = 5

class StreamErrorCode(_taut_Enum):
    unknown_stream = 0
    producer_error = 1
    internal = 2
    slow_consumer = 3

class StreamStopReason(_taut_Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class StreamSeverity(_taut_Enum):
    warn = 0
    error = 1

class StreamDiagCode(_taut_Enum):
    push_after_terminal = 0

@_taut_dataclass(slots=True)
class StreamPosition:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int

@_taut_dataclass(slots=True)
class StreamRecord:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int
    payload: bytes

@_taut_dataclass(slots=True)
class StreamError:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    code: StreamErrorCode
    message: str | None

@_taut_dataclass(slots=True)
class StreamPush:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    payload: bytes

@_taut_dataclass(slots=True)
class StreamSeal:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]

@_taut_dataclass(slots=True)
class StreamClose:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    error: StreamError | None

@_taut_dataclass(slots=True)
class StreamReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    stream_id: str
    max_records: int | None
    max_bytes: int | None
    timeout_ms: int | None

@_taut_dataclass(slots=True)
class StreamEndStream:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    stream_id: str

@_taut_dataclass(slots=True)
class StreamTimerExpired:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class StreamReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    stream_id: str
    records: list[StreamRecord]
    next_position: StreamPosition
    state: StreamState
    error: StreamError | None

@_taut_dataclass(slots=True)
class StreamSetTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int
    ms: int

@_taut_dataclass(slots=True)
class StreamCancelTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class StreamProducerStop:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    reason: StreamStopReason

@_taut_dataclass(slots=True)
class StreamDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: StreamSeverity
    code: StreamDiagCode

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'StreamMsgType': _taut_facts.EnumDef(name='StreamMsgType', members={'push': 0, 'seal': 1, 'close': 2, 'read': 3, 'end_stream': 4, 'timer_expired': 5, 'read_response': 6, 'set_timer': 7, 'cancel_timer': 8, 'producer_stop': 9, 'diagnostic': 10}, options={}), 'StreamState': _taut_facts.EnumDef(name='StreamState', members={'data': 0, 'would_block': 1, 'eof': 2, 'closed': 3, 'failed': 4, 'dropped': 5}, options={}), 'StreamErrorCode': _taut_facts.EnumDef(name='StreamErrorCode', members={'unknown_stream': 0, 'producer_error': 1, 'internal': 2, 'slow_consumer': 3}, options={}), 'StreamStopReason': _taut_facts.EnumDef(name='StreamStopReason', members={'last_reader_gone': 0, 'closed': 1, 'failed': 2}, options={}), 'StreamSeverity': _taut_facts.EnumDef(name='StreamSeverity', members={'warn': 0, 'error': 1}, options={}), 'StreamDiagCode': _taut_facts.EnumDef(name='StreamDiagCode', members={'push_after_terminal': 0}, options={})}, messages={'StreamPosition': _taut_facts.MessageDef(name='StreamPosition', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamRecord': _taut_facts.MessageDef(name='StreamRecord', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamError': _taut_facts.MessageDef(name='StreamError', fields=(_taut_facts.FieldDef(name='code', tag=1, type=_taut_facts.EnumRef(name='StreamErrorCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='message', tag=2, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamPush': _taut_facts.MessageDef(name='StreamPush', fields=(_taut_facts.FieldDef(name='payload', tag=1, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamSeal': _taut_facts.MessageDef(name='StreamSeal', fields=(), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamClose': _taut_facts.MessageDef(name='StreamClose', fields=(_taut_facts.FieldDef(name='error', tag=1, type=_taut_facts.MsgRef(name='StreamError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamReadRequest': _taut_facts.MessageDef(name='StreamReadRequest', fields=(_taut_facts.FieldDef(name='stream_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='max_records', tag=2, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='max_bytes', tag=3, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='timeout_ms', tag=4, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamEndStream': _taut_facts.MessageDef(name='StreamEndStream', fields=(_taut_facts.FieldDef(name='stream_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamTimerExpired': _taut_facts.MessageDef(name='StreamTimerExpired', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamReadResponse': _taut_facts.MessageDef(name='StreamReadResponse', fields=(_taut_facts.FieldDef(name='stream_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='records', tag=2, type=_taut_facts.ListOf(elem=_taut_facts.MsgRef(name='StreamRecord')), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='next_position', tag=3, type=_taut_facts.MsgRef(name='StreamPosition'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=4, type=_taut_facts.EnumRef(name='StreamState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='error', tag=5, type=_taut_facts.MsgRef(name='StreamError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamSetTimer': _taut_facts.MessageDef(name='StreamSetTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='ms', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamCancelTimer': _taut_facts.MessageDef(name='StreamCancelTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamProducerStop': _taut_facts.MessageDef(name='StreamProducerStop', fields=(_taut_facts.FieldDef(name='reason', tag=1, type=_taut_facts.EnumRef(name='StreamStopReason'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'StreamDiagnostic': _taut_facts.MessageDef(name='StreamDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='StreamSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='StreamDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'StreamPosition': StreamPosition, 'StreamRecord': StreamRecord, 'StreamError': StreamError, 'StreamPush': StreamPush, 'StreamSeal': StreamSeal, 'StreamClose': StreamClose, 'StreamReadRequest': StreamReadRequest, 'StreamEndStream': StreamEndStream, 'StreamTimerExpired': StreamTimerExpired, 'StreamReadResponse': StreamReadResponse, 'StreamSetTimer': StreamSetTimer, 'StreamCancelTimer': StreamCancelTimer, 'StreamProducerStop': StreamProducerStop, 'StreamDiagnostic': StreamDiagnostic},
    {'StreamMsgType': StreamMsgType, 'StreamState': StreamState, 'StreamErrorCode': StreamErrorCode, 'StreamStopReason': StreamStopReason, 'StreamSeverity': StreamSeverity, 'StreamDiagCode': StreamDiagCode},
    identity='taut_shape.stream', ir_version=2, external=(),
    attributes={'StreamPosition': {'seq': 'seq'}, 'StreamRecord': {'seq': 'seq', 'payload': 'payload'}, 'StreamError': {'code': 'code', 'message': 'message'}, 'StreamPush': {'payload': 'payload'}, 'StreamSeal': {}, 'StreamClose': {'error': 'error'}, 'StreamReadRequest': {'stream_id': 'stream_id', 'max_records': 'max_records', 'max_bytes': 'max_bytes', 'timeout_ms': 'timeout_ms'}, 'StreamEndStream': {'stream_id': 'stream_id'}, 'StreamTimerExpired': {'token': 'token'}, 'StreamReadResponse': {'stream_id': 'stream_id', 'records': 'records', 'next_position': 'next_position', 'state': 'state', 'error': 'error'}, 'StreamSetTimer': {'token': 'token', 'ms': 'ms'}, 'StreamCancelTimer': {'token': 'token'}, 'StreamProducerStop': {'reason': 'reason'}, 'StreamDiagnostic': {'severity': 'severity', 'code': 'code'}})

__all__ = ['StreamMsgType', 'StreamState', 'StreamErrorCode', 'StreamStopReason', 'StreamSeverity', 'StreamDiagCode', 'StreamPosition', 'StreamRecord', 'StreamError', 'StreamPush', 'StreamSeal', 'StreamClose', 'StreamReadRequest', 'StreamEndStream', 'StreamTimerExpired', 'StreamReadResponse', 'StreamSetTimer', 'StreamCancelTimer', 'StreamProducerStop', 'StreamDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
