# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_swmr.taut.py
# Schema sha256: e0609b19921545e3d027606152a725da1e5c2921c0e809bd2758b55a9f65d5cc
# Regenerate: python tools/regenerate_python_facts.py
"""GENERATED native Python types — do not edit."""
# Generator build: python-oneof-reference.1; descriptor=1; codec=1; owner=taut.python.foundation
from __future__ import annotations
from dataclasses import dataclass as _taut_dataclass, field as _taut_field
from enum import Enum as _taut_Enum
from typing import ClassVar as _taut_ClassVar
try:
    from taut.contracts import require_contract as _taut_require_contract
    _taut_require_contract(artifact='taut_shape.swmr', descriptor=1, codec=1, capabilities=('descriptors.v1', 'codec.v1', 'oneof.v1'), generator='python-oneof-reference.1')
    from taut import facts as _taut_facts
    from taut.descriptors import publish as _taut_publish, MessageDescriptor as _taut_MessageDescriptor
except ImportError as _taut_error:
    raise ImportError('taut_shape.swmr: compatible taut foundation required (owner=taut.python.foundation, descriptor=1, codec=1); supply compatible runtime and regenerate/rebind artifacts') from _taut_error

class SwmrMsgType(_taut_Enum):
    snapshot_push = 0
    delta_push = 1
    reset = 2
    seal = 3
    close = 4
    read = 5
    end_stream = 6
    timer_expired = 7
    read_response = 8
    set_timer = 9
    cancel_timer = 10
    producer_stop = 11
    diagnostic = 12

class SwmrState(_taut_Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    reset = 5

class SwmrErrorCode(_taut_Enum):
    unknown_swmr = 0
    producer_error = 1
    internal = 2

class SwmrStopReason(_taut_Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class SwmrResetReason(_taut_Enum):
    producer_requested = 0
    retention_exceeded = 1
    invalid_resume_seq = 2

class SwmrSeverity(_taut_Enum):
    warn = 0
    error = 1

class SwmrDiagCode(_taut_Enum):
    push_after_terminal = 0
    delta_before_snapshot = 1
    writer_conflict = 2
    retention_bound_exceeded = 3

@_taut_dataclass(slots=True)
class SwmrCursor:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int
    epoch: int

@_taut_dataclass(slots=True)
class SwmrSnapshot:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    seq: int
    payload: bytes

@_taut_dataclass(slots=True)
class SwmrDelta:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    base_seq: int
    seq: int
    payload: bytes

@_taut_dataclass(slots=True)
class SwmrError:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    code: SwmrErrorCode
    message: str | None

@_taut_dataclass(slots=True)
class SwmrSnapshotPush:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    writer_id: str
    payload: bytes

@_taut_dataclass(slots=True)
class SwmrDeltaPush:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    writer_id: str
    payload: bytes

@_taut_dataclass(slots=True)
class SwmrReset:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    writer_id: str
    reason: SwmrResetReason
    detail: bytes | None

@_taut_dataclass(slots=True)
class SwmrSeal:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]

@_taut_dataclass(slots=True)
class SwmrClose:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    error: SwmrError | None

@_taut_dataclass(slots=True)
class SwmrReadRequest:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    swmr_id: str
    stream_id: str
    cursor: SwmrCursor | None
    timeout_ms: int | None

@_taut_dataclass(slots=True)
class SwmrEndStream:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    swmr_id: str
    stream_id: str

@_taut_dataclass(slots=True)
class SwmrTimerExpired:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class SwmrReadResponse:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    swmr_id: str
    stream_id: str
    snapshot: SwmrSnapshot | None
    deltas: list[SwmrDelta]
    next_cursor: SwmrCursor | None
    state: SwmrState
    reset_reason: SwmrResetReason | None
    error: SwmrError | None
    reset_detail: bytes | None

@_taut_dataclass(slots=True)
class SwmrSetTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int
    ms: int

@_taut_dataclass(slots=True)
class SwmrCancelTimer:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    token: int

@_taut_dataclass(slots=True)
class SwmrProducerStop:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    reason: SwmrStopReason

@_taut_dataclass(slots=True)
class SwmrDiagnostic:
    DESCRIPTOR: _taut_ClassVar[_taut_MessageDescriptor]
    severity: SwmrSeverity
    code: SwmrDiagCode

SCHEMA = _taut_facts.freeze_schema(_taut_facts.Schema(enums={'SwmrMsgType': _taut_facts.EnumDef(name='SwmrMsgType', members={'snapshot_push': 0, 'delta_push': 1, 'reset': 2, 'seal': 3, 'close': 4, 'read': 5, 'end_stream': 6, 'timer_expired': 7, 'read_response': 8, 'set_timer': 9, 'cancel_timer': 10, 'producer_stop': 11, 'diagnostic': 12}, options={}), 'SwmrState': _taut_facts.EnumDef(name='SwmrState', members={'data': 0, 'would_block': 1, 'eof': 2, 'closed': 3, 'failed': 4, 'reset': 5}, options={}), 'SwmrErrorCode': _taut_facts.EnumDef(name='SwmrErrorCode', members={'unknown_swmr': 0, 'producer_error': 1, 'internal': 2}, options={}), 'SwmrStopReason': _taut_facts.EnumDef(name='SwmrStopReason', members={'last_reader_gone': 0, 'closed': 1, 'failed': 2}, options={}), 'SwmrResetReason': _taut_facts.EnumDef(name='SwmrResetReason', members={'producer_requested': 0, 'retention_exceeded': 1, 'invalid_resume_seq': 2}, options={}), 'SwmrSeverity': _taut_facts.EnumDef(name='SwmrSeverity', members={'warn': 0, 'error': 1}, options={}), 'SwmrDiagCode': _taut_facts.EnumDef(name='SwmrDiagCode', members={'push_after_terminal': 0, 'delta_before_snapshot': 1, 'writer_conflict': 2, 'retention_bound_exceeded': 3}, options={})}, messages={'SwmrCursor': _taut_facts.MessageDef(name='SwmrCursor', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='epoch', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrSnapshot': _taut_facts.MessageDef(name='SwmrSnapshot', fields=(_taut_facts.FieldDef(name='seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrDelta': _taut_facts.MessageDef(name='SwmrDelta', fields=(_taut_facts.FieldDef(name='base_seq', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='seq', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=3, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrError': _taut_facts.MessageDef(name='SwmrError', fields=(_taut_facts.FieldDef(name='code', tag=1, type=_taut_facts.EnumRef(name='SwmrErrorCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='message', tag=2, type=_taut_facts.Scalar(kind='str'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrSnapshotPush': _taut_facts.MessageDef(name='SwmrSnapshotPush', fields=(_taut_facts.FieldDef(name='writer_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrDeltaPush': _taut_facts.MessageDef(name='SwmrDeltaPush', fields=(_taut_facts.FieldDef(name='writer_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='payload', tag=2, type=_taut_facts.Scalar(kind='bytes'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrReset': _taut_facts.MessageDef(name='SwmrReset', fields=(_taut_facts.FieldDef(name='writer_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='reason', tag=2, type=_taut_facts.EnumRef(name='SwmrResetReason'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='detail', tag=3, type=_taut_facts.Scalar(kind='bytes'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrSeal': _taut_facts.MessageDef(name='SwmrSeal', fields=(), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrClose': _taut_facts.MessageDef(name='SwmrClose', fields=(_taut_facts.FieldDef(name='error', tag=1, type=_taut_facts.MsgRef(name='SwmrError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrReadRequest': _taut_facts.MessageDef(name='SwmrReadRequest', fields=(_taut_facts.FieldDef(name='swmr_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='cursor', tag=3, type=_taut_facts.MsgRef(name='SwmrCursor'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='timeout_ms', tag=4, type=_taut_facts.Scalar(kind='int'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrEndStream': _taut_facts.MessageDef(name='SwmrEndStream', fields=(_taut_facts.FieldDef(name='swmr_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrTimerExpired': _taut_facts.MessageDef(name='SwmrTimerExpired', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrReadResponse': _taut_facts.MessageDef(name='SwmrReadResponse', fields=(_taut_facts.FieldDef(name='swmr_id', tag=1, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='stream_id', tag=2, type=_taut_facts.Scalar(kind='str'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='snapshot', tag=3, type=_taut_facts.MsgRef(name='SwmrSnapshot'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='deltas', tag=4, type=_taut_facts.ListOf(elem=_taut_facts.MsgRef(name='SwmrDelta')), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='next_cursor', tag=5, type=_taut_facts.MsgRef(name='SwmrCursor'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='state', tag=6, type=_taut_facts.EnumRef(name='SwmrState'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='reset_reason', tag=7, type=_taut_facts.EnumRef(name='SwmrResetReason'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='error', tag=8, type=_taut_facts.MsgRef(name='SwmrError'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='reset_detail', tag=9, type=_taut_facts.Scalar(kind='bytes'), optional=True, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrSetTimer': _taut_facts.MessageDef(name='SwmrSetTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='ms', tag=2, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrCancelTimer': _taut_facts.MessageDef(name='SwmrCancelTimer', fields=(_taut_facts.FieldDef(name='token', tag=1, type=_taut_facts.Scalar(kind='int'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrProducerStop': _taut_facts.MessageDef(name='SwmrProducerStop', fields=(_taut_facts.FieldDef(name='reason', tag=1, type=_taut_facts.EnumRef(name='SwmrStopReason'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()),), reserved_tags=(), reserved_names=(), next_id=None, options={}), 'SwmrDiagnostic': _taut_facts.MessageDef(name='SwmrDiagnostic', fields=(_taut_facts.FieldDef(name='severity', tag=1, type=_taut_facts.EnumRef(name='SwmrSeverity'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=()), _taut_facts.FieldDef(name='code', tag=2, type=_taut_facts.EnumRef(name='SwmrDiagCode'), optional=False, transient=False, merge=None, options={}, oneof=None, cases=())), reserved_tags=(), reserved_names=(), next_id=None, options={})}, services={}, extensions=(), options={}))
SCHEMA_DESCRIPTOR, BINDING = _taut_publish(
    SCHEMA, {'SwmrCursor': SwmrCursor, 'SwmrSnapshot': SwmrSnapshot, 'SwmrDelta': SwmrDelta, 'SwmrError': SwmrError, 'SwmrSnapshotPush': SwmrSnapshotPush, 'SwmrDeltaPush': SwmrDeltaPush, 'SwmrReset': SwmrReset, 'SwmrSeal': SwmrSeal, 'SwmrClose': SwmrClose, 'SwmrReadRequest': SwmrReadRequest, 'SwmrEndStream': SwmrEndStream, 'SwmrTimerExpired': SwmrTimerExpired, 'SwmrReadResponse': SwmrReadResponse, 'SwmrSetTimer': SwmrSetTimer, 'SwmrCancelTimer': SwmrCancelTimer, 'SwmrProducerStop': SwmrProducerStop, 'SwmrDiagnostic': SwmrDiagnostic},
    {'SwmrMsgType': SwmrMsgType, 'SwmrState': SwmrState, 'SwmrErrorCode': SwmrErrorCode, 'SwmrStopReason': SwmrStopReason, 'SwmrResetReason': SwmrResetReason, 'SwmrSeverity': SwmrSeverity, 'SwmrDiagCode': SwmrDiagCode},
    identity='taut_shape.swmr', ir_version=2, external=(),
    attributes={'SwmrCursor': {'seq': 'seq', 'epoch': 'epoch'}, 'SwmrSnapshot': {'seq': 'seq', 'payload': 'payload'}, 'SwmrDelta': {'base_seq': 'base_seq', 'seq': 'seq', 'payload': 'payload'}, 'SwmrError': {'code': 'code', 'message': 'message'}, 'SwmrSnapshotPush': {'writer_id': 'writer_id', 'payload': 'payload'}, 'SwmrDeltaPush': {'writer_id': 'writer_id', 'payload': 'payload'}, 'SwmrReset': {'writer_id': 'writer_id', 'reason': 'reason', 'detail': 'detail'}, 'SwmrSeal': {}, 'SwmrClose': {'error': 'error'}, 'SwmrReadRequest': {'swmr_id': 'swmr_id', 'stream_id': 'stream_id', 'cursor': 'cursor', 'timeout_ms': 'timeout_ms'}, 'SwmrEndStream': {'swmr_id': 'swmr_id', 'stream_id': 'stream_id'}, 'SwmrTimerExpired': {'token': 'token'}, 'SwmrReadResponse': {'swmr_id': 'swmr_id', 'stream_id': 'stream_id', 'snapshot': 'snapshot', 'deltas': 'deltas', 'next_cursor': 'next_cursor', 'state': 'state', 'reset_reason': 'reset_reason', 'error': 'error', 'reset_detail': 'reset_detail'}, 'SwmrSetTimer': {'token': 'token', 'ms': 'ms'}, 'SwmrCancelTimer': {'token': 'token'}, 'SwmrProducerStop': {'reason': 'reason'}, 'SwmrDiagnostic': {'severity': 'severity', 'code': 'code'}})

__all__ = ['SwmrMsgType', 'SwmrState', 'SwmrErrorCode', 'SwmrStopReason', 'SwmrResetReason', 'SwmrSeverity', 'SwmrDiagCode', 'SwmrCursor', 'SwmrSnapshot', 'SwmrDelta', 'SwmrError', 'SwmrSnapshotPush', 'SwmrDeltaPush', 'SwmrReset', 'SwmrSeal', 'SwmrClose', 'SwmrReadRequest', 'SwmrEndStream', 'SwmrTimerExpired', 'SwmrReadResponse', 'SwmrSetTimer', 'SwmrCancelTimer', 'SwmrProducerStop', 'SwmrDiagnostic', 'SCHEMA', 'SCHEMA_DESCRIPTOR', 'BINDING']
