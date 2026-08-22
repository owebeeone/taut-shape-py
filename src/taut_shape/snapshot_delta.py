"""The fixed expiry-profile projection over the shared SWMR core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .log.engine import StopWhen
from .swmr import _generated as g
from .swmr.engine import (
    SwmrInput,
    SwmrNode,
    SwmrOutput,
    SwmrRecoveryPolicy,
)


@dataclass(frozen=True, slots=True)
class SnapshotDeltaRefreshRequired:
    """Out-of-band request to reacquire a fresh application snapshot."""

    swmr_id: str
    stream_id: str
    reason: str


SnapshotDeltaOutput: TypeAlias = SwmrOutput | SnapshotDeltaRefreshRequired


def _refresh_reason(reason: g.SwmrResetReason | None) -> str:
    if reason is g.SwmrResetReason.retention_exceeded:
        return "retention_expired"
    if reason is g.SwmrResetReason.invalid_resume_seq:
        return "invalid_cursor"
    return "source_changed"


def project_snapshot_delta_output(output: SwmrOutput) -> SnapshotDeltaOutput:
    """Hide in-band SWMR reset/repair behind the expiry profile boundary."""

    if isinstance(output, g.SwmrReadResponse) and output.state is g.SwmrState.reset:
        return SnapshotDeltaRefreshRequired(
            swmr_id=output.swmr_id,
            stream_id=output.stream_id,
            reason=_refresh_reason(output.reset_reason),
        )
    return output


class SnapshotDeltaNode:
    """One SWMR core configured with the fixed ``expire`` recovery profile."""

    def __init__(
        self,
        *,
        stop_when: StopWhen = StopWhen.LAST_READER,
        max_deltas: int = 64,
    ) -> None:
        if max_deltas <= 0:
            raise ValueError("snapshot_delta max_deltas must be positive")
        self._core = SwmrNode(
            stop_when=stop_when,
            max_deltas=max_deltas,
            recovery_policy=SwmrRecoveryPolicy.EXPIRE,
        )

    @property
    def recovery_policy(self) -> SwmrRecoveryPolicy:
        return self._core.recovery_policy

    def handle(self, message: SwmrInput) -> list[SnapshotDeltaOutput]:
        return [project_snapshot_delta_output(output) for output in self._core.handle(message)]
