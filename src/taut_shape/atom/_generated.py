"""GENERATED native Python types — do not edit.

Source: taut-shape/ir/shape_atom.taut.py
Schema sha256: see taut-shape/ir/shape_atom.ir.json
Regenerate with ``tautc gen ... --api-only`` and replace this file.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class AtomMsgType(Enum):
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

class AtomState(Enum):
    data = 0
    would_block = 1
    eof = 2
    closed = 3
    failed = 4

class AtomErrorCode(Enum):
    unknown_atom = 0
    producer_error = 1
    internal = 2

class AtomStopReason(Enum):
    last_reader_gone = 0
    closed = 1
    failed = 2

class AtomSeverity(Enum):
    warn = 0
    error = 1

class AtomDiagCode(Enum):
    replace_after_terminal = 0

@dataclass(slots=True)
class AtomVersion:
    version: int

@dataclass(slots=True)
class AtomValue:
    version: int
    payload: bytes

@dataclass(slots=True)
class AtomError:
    code: AtomErrorCode
    message: str | None

@dataclass(slots=True)
class AtomReplace:
    payload: bytes

@dataclass(slots=True)
class AtomSeal:
    pass

@dataclass(slots=True)
class AtomClose:
    error: AtomError | None

@dataclass(slots=True)
class AtomReadRequest:
    atom_id: str
    stream_id: str
    version: AtomVersion | None
    timeout_ms: int | None

@dataclass(slots=True)
class AtomEndStream:
    atom_id: str
    stream_id: str

@dataclass(slots=True)
class AtomTimerExpired:
    token: int

@dataclass(slots=True)
class AtomReadResponse:
    atom_id: str
    stream_id: str
    value: AtomValue | None
    next_version: AtomVersion
    state: AtomState
    error: AtomError | None

@dataclass(slots=True)
class AtomSetTimer:
    token: int
    ms: int

@dataclass(slots=True)
class AtomCancelTimer:
    token: int

@dataclass(slots=True)
class AtomProducerStop:
    reason: AtomStopReason

@dataclass(slots=True)
class AtomDiagnostic:
    severity: AtomSeverity
    code: AtomDiagCode
