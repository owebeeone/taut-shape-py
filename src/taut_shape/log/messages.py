"""Message vocabulary: re-exports of the generated types + hand-written unions.

Per D17, only the ``InMsg`` / ``OutMsg`` unions are hand-written here; every
message and value type is the tautc-generated dataclass vendored in
``_generated.py``. The union names use the taut wire names (``Log*``) verbatim
so there is exactly one spelling of each message across the engine, the tests,
and the wire.

Dispatch is by structural ``match``/``case`` on these dataclasses; the closed
union lets ``mypy`` prove exhaustiveness via ``typing.assert_never`` in the
engine's fall-through arm.
"""

from __future__ import annotations

from ._generated import (
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
)

# Hand-written (D17): the closed unions over the generated types.
InMsg = (
    LogPush
    | LogSeal
    | LogClose
    | LogReadRequest
    | LogEndStream
    | LogTimerExpired
    | LogEvict
)
OutMsg = (
    LogReadResponse | LogSetTimer | LogCancelTimer | LogProducerStop | LogDiagnostic
)

__all__ = [
    # value types
    "LogCursor",
    "LogRecord",
    "LogError",
    # enums
    "LogState",
    "LogErrorCode",
    "LogStopReason",
    "LogSeverity",
    "LogDiagCode",
    # inputs
    "LogPush",
    "LogSeal",
    "LogClose",
    "LogReadRequest",
    "LogEndStream",
    "LogTimerExpired",
    "LogEvict",
    # outputs
    "LogReadResponse",
    "LogSetTimer",
    "LogCancelTimer",
    "LogProducerStop",
    "LogDiagnostic",
    # unions
    "InMsg",
    "OutMsg",
]
