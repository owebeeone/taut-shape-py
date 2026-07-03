"""The pure ``log`` engine (sync; no asyncio, no I/O, no clock in this subtree).

Public surface: ``LogNode`` + ``StopWhen`` (the engine), the message/value
types and the ``InMsg``/``OutMsg`` unions (from ``messages``). The ``_window``
and ``_sessions`` modules are internal (D2/D3) and not re-exported.
"""

from __future__ import annotations

from .engine import LogNode, StopWhen
from .messages import (
    InMsg,
    LogCancelTimer,
    LogClose,
    LogCursor,
    LogDiagCode,
    LogDiagnostic,
    LogEndStream,
    LogError,
    LogErrorCode,
    LogEvict,
    LogProducerStop,
    LogPush,
    LogReadRequest,
    LogReadResponse,
    LogRecord,
    LogSeal,
    LogSetTimer,
    LogSeverity,
    LogState,
    LogStopReason,
    LogTimerExpired,
    OutMsg,
)

__all__ = [
    "LogNode",
    "StopWhen",
    "InMsg",
    "OutMsg",
    "LogCursor",
    "LogRecord",
    "LogError",
    "LogState",
    "LogErrorCode",
    "LogStopReason",
    "LogSeverity",
    "LogDiagCode",
    "LogPush",
    "LogSeal",
    "LogClose",
    "LogReadRequest",
    "LogEndStream",
    "LogTimerExpired",
    "LogEvict",
    "LogReadResponse",
    "LogSetTimer",
    "LogCancelTimer",
    "LogProducerStop",
    "LogDiagnostic",
]
