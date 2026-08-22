# VENDORED GENERATED CODE — DO NOT EDIT.
# Source: taut-shape/ir/shape_value.taut.py
# Schema sha256: 405278e2797ac5f0935b92c40b99a6c87b7edbfa288b640cca45c2c2ce1c3e8c
# Command: PYTHONPATH=../taut/src python3 -m taut.cli gen
#   ir/shape_value.taut.py -o <out> -l python --api-only
"""GENERATED native Python types — do not edit."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ValueMsgType(Enum):
    set = 0
    read = 1
    read_response = 2
    diagnostic = 3

class ValueState(Enum):
    data = 0
    empty = 1

class ValueSeverity(Enum):
    warn = 0
    error = 1

class ValueDiagCode(Enum):
    equivocation = 0

@dataclass(slots=True)
class ValueStamp:
    origin: str
    seq: int
    lamport: int

@dataclass(slots=True)
class ValueSet:
    origin: str
    seq: int
    lamport: int
    prev: bytes | None
    payload: bytes

@dataclass(slots=True)
class ValueReadRequest:
    value_id: str
    stream_id: str

@dataclass(slots=True)
class ValueReadResponse:
    value_id: str
    stream_id: str
    value: bytes | None
    winner: ValueStamp | None
    state: ValueState

@dataclass(slots=True)
class ValueDiagnostic:
    severity: ValueSeverity
    code: ValueDiagCode
