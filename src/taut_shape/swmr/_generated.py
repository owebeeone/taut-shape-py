"""GENERATED native Python types — do not edit.

Source: taut-shape/ir/shape_swmr.taut.py
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class SwmrMsgType(Enum):
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

class SwmrState(Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    reset = 5

class SwmrErrorCode(Enum):
    unknown_swmr = 0
    producer_error = 1
    internal = 2

class SwmrStopReason(Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class SwmrResetReason(Enum):
    producer_requested = 0
    retention_exceeded = 1
    invalid_resume_seq = 2

class SwmrSeverity(Enum):
    warn = 0
    error = 1

class SwmrDiagCode(Enum):
    push_after_terminal = 0
    delta_before_snapshot = 1
    writer_conflict = 2
    retention_bound_exceeded = 3

@dataclass(slots=True)
class SwmrCursor:
    seq: int
    epoch: int

@dataclass(slots=True)
class SwmrSnapshot:
    seq: int
    payload: bytes

@dataclass(slots=True)
class SwmrDelta:
    base_seq: int
    seq: int
    payload: bytes

@dataclass(slots=True)
class SwmrError:
    code: SwmrErrorCode
    message: str | None

@dataclass(slots=True)
class SwmrSnapshotPush:
    writer_id: str
    payload: bytes

@dataclass(slots=True)
class SwmrDeltaPush:
    writer_id: str
    payload: bytes

@dataclass(slots=True)
class SwmrReset:
    writer_id: str
    reason: SwmrResetReason
    detail: bytes | None

@dataclass(slots=True)
class SwmrSeal:
    pass

@dataclass(slots=True)
class SwmrClose:
    error: SwmrError | None

@dataclass(slots=True)
class SwmrReadRequest:
    swmr_id: str
    stream_id: str
    cursor: SwmrCursor | None
    timeout_ms: int | None

@dataclass(slots=True)
class SwmrEndStream:
    swmr_id: str
    stream_id: str

@dataclass(slots=True)
class SwmrTimerExpired:
    token: int

@dataclass(slots=True)
class SwmrReadResponse:
    swmr_id: str
    stream_id: str
    snapshot: SwmrSnapshot | None
    deltas: list[SwmrDelta]
    next_cursor: SwmrCursor | None
    state: SwmrState
    reset_reason: SwmrResetReason | None
    error: SwmrError | None
    reset_detail: bytes | None

@dataclass(slots=True)
class SwmrSetTimer:
    token: int
    ms: int

@dataclass(slots=True)
class SwmrCancelTimer:
    token: int

@dataclass(slots=True)
class SwmrProducerStop:
    reason: SwmrStopReason

@dataclass(slots=True)
class SwmrDiagnostic:
    severity: SwmrSeverity
    code: SwmrDiagCode
