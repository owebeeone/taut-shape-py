# ---------------------------------------------------------------------------
# VENDORED — GENERATED CODE, DO NOT HAND-EDIT.
#
# Provenance (InitialPlan.md S0.3 / D17):
#   source schema : taut-shape/ir/shape_log.taut.py
#   sha256        : 3e1224747430e12188beab3ece4d8ebe44decbcae3fe4b86c2731136617863a9
#   generator     : taut  (python3 -m taut.cli gen ... -l python --api-only)
#   command       : cd taut-shape && PYTHONPATH=../taut/src \
#                     python3 -m taut.cli gen ir/shape_log.taut.py -o <out> \
#                     -l python --api-only
#
# Regenerate on a schema bump; re-run the oracle/lockstep gates afterward.
# The corpus version this repo conforms to and the schema pin live in
# tests/oracle/SOURCE.md.
# ---------------------------------------------------------------------------
"""GENERATED native Python types — do not edit."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class LogMsgType(Enum):
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

class LogState(Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4
    expired = 5

class LogErrorCode(Enum):
    unknown_log = 0
    producer_error = 1
    internal = 2

class LogStopReason(Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class LogSeverity(Enum):
    warn = 0
    error = 1

class LogDiagCode(Enum):
    push_after_terminal = 0

@dataclass(slots=True)
class LogCursor:
    seq: int

@dataclass(slots=True)
class LogRecord:
    seq: int
    payload: bytes

@dataclass(slots=True)
class LogError:
    code: LogErrorCode
    message: str | None

@dataclass(slots=True)
class LogPush:
    payload: bytes

@dataclass(slots=True)
class LogSeal:
    pass

@dataclass(slots=True)
class LogClose:
    error: LogError | None

@dataclass(slots=True)
class LogReadRequest:
    log_id: str
    stream_id: str
    cursor: LogCursor | None
    max_records: int | None
    max_bytes: int | None
    timeout_ms: int | None

@dataclass(slots=True)
class LogEndStream:
    log_id: str
    stream_id: str

@dataclass(slots=True)
class LogTimerExpired:
    token: int

@dataclass(slots=True)
class LogEvict:
    up_to_seq: int

@dataclass(slots=True)
class LogReadResponse:
    log_id: str
    stream_id: str
    records: list[LogRecord]
    next_cursor: LogCursor
    state: LogState
    error: LogError | None

@dataclass(slots=True)
class LogSetTimer:
    token: int
    ms: int

@dataclass(slots=True)
class LogCancelTimer:
    token: int

@dataclass(slots=True)
class LogProducerStop:
    reason: LogStopReason

@dataclass(slots=True)
class LogDiagnostic:
    severity: LogSeverity
    code: LogDiagCode

