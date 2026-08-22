"""GENERATED native Python types — do not edit.

Source: taut-shape/ir/shape_stream.taut.py
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class StreamMsgType(Enum):
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

class StreamState(Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    dropped = 5

class StreamErrorCode(Enum):
    unknown_stream = 0
    producer_error = 1
    internal = 2
    slow_consumer = 3

class StreamStopReason(Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class StreamSeverity(Enum):
    warn = 0
    error = 1

class StreamDiagCode(Enum):
    push_after_terminal = 0

@dataclass(slots=True)
class StreamPosition:
    seq: int

@dataclass(slots=True)
class StreamRecord:
    seq: int
    payload: bytes

@dataclass(slots=True)
class StreamError:
    code: StreamErrorCode
    message: str | None

@dataclass(slots=True)
class StreamPush:
    payload: bytes

@dataclass(slots=True)
class StreamSeal:
    pass

@dataclass(slots=True)
class StreamClose:
    error: StreamError | None

@dataclass(slots=True)
class StreamReadRequest:
    stream_id: str
    max_records: int | None
    max_bytes: int | None
    timeout_ms: int | None

@dataclass(slots=True)
class StreamEndStream:
    stream_id: str

@dataclass(slots=True)
class StreamTimerExpired:
    token: int

@dataclass(slots=True)
class StreamReadResponse:
    stream_id: str
    records: list[StreamRecord]
    next_position: StreamPosition
    state: StreamState
    error: StreamError | None

@dataclass(slots=True)
class StreamSetTimer:
    token: int
    ms: int

@dataclass(slots=True)
class StreamCancelTimer:
    token: int

@dataclass(slots=True)
class StreamProducerStop:
    reason: StreamStopReason

@dataclass(slots=True)
class StreamDiagnostic:
    severity: StreamSeverity
    code: StreamDiagCode
