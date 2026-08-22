"""GENERATED native Python types — do not edit.

Source: taut-shape/ir/shape_crdt.taut.py
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class CrdtMsgType(Enum):
    apply = 0
    install_bootstrap = 1
    seal = 2
    close = 3
    read = 4
    read_response = 5
    diagnostic = 6

class CrdtState(Enum):
    data = 0
    empty = 1
    eof = 2
    closed = 3
    failed = 4
    bootstrap_required = 5
    invalid_cursor = 6

class CrdtErrorCode(Enum):
    unknown_crdt = 0
    producer_error = 1
    internal = 2

class CrdtSeverity(Enum):
    warn = 0
    error = 1

class CrdtDiagCode(Enum):
    apply_after_terminal = 0
    invalid_operation = 1
    equivocation = 2
    bootstrap_conflict = 3
    pending_bound_exceeded = 4

@dataclass(slots=True)
class CrdtClockEntry:
    origin: str
    seq: int

@dataclass(slots=True)
class CrdtClock:
    entries: list[CrdtClockEntry]

@dataclass(slots=True)
class CrdtOp:
    origin: str
    seq: int
    deps: CrdtClock
    payload: bytes

@dataclass(slots=True)
class CrdtBootstrap:
    clock: CrdtClock
    state: bytes

@dataclass(slots=True)
class CrdtError:
    code: CrdtErrorCode
    message: str | None

@dataclass(slots=True)
class CrdtApply:
    op: CrdtOp

@dataclass(slots=True)
class CrdtInstallBootstrap:
    bootstrap: CrdtBootstrap

@dataclass(slots=True)
class CrdtSeal:
    pass

@dataclass(slots=True)
class CrdtClose:
    error: CrdtError | None

@dataclass(slots=True)
class CrdtReadRequest:
    crdt_id: str
    stream_id: str
    cursor: CrdtClock | None

@dataclass(slots=True)
class CrdtReadResponse:
    crdt_id: str
    stream_id: str
    bootstrap: CrdtBootstrap | None
    ops: list[CrdtOp]
    next_cursor: CrdtClock
    state: CrdtState
    error: CrdtError | None

@dataclass(slots=True)
class CrdtDiagnostic:
    severity: CrdtSeverity
    code: CrdtDiagCode
    origin: str | None
    seq: int | None
