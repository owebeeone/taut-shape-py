from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.log.engine import StopWhen
from taut_shape.snapshot_delta import (
    SnapshotDeltaNode,
    SnapshotDeltaRefreshRequired,
)
from taut_shape.swmr.engine import SwmrRecoveryPolicy
from taut_shape.swmr.wire import json_to_input, output_to_json

_CORPUS = (
    Path(__file__).parents[2]
    / "taut-shape"
    / "corpus"
    / "snapshot_delta.profile.v1.json"
)
_DOCUMENT = json.loads(_CORPUS.read_text())


def _output_json(output: Any) -> dict[str, Any]:
    if isinstance(output, SnapshotDeltaRefreshRequired):
        return {
            "type": "refresh_required",
            "swmr_id": output.swmr_id,
            "stream_id": output.stream_id,
            "reason": output.reason,
        }
    return output_to_json(output)


@pytest.mark.parametrize("vector", _DOCUMENT["vectors"], ids=lambda vector: vector["name"])
def test_snapshot_delta_profile_vector(vector: dict[str, Any]) -> None:
    node = SnapshotDeltaNode(
        stop_when=StopWhen(vector["node"]["stop_when"]),
        max_deltas=vector["node"]["max_deltas"],
    )
    assert node.recovery_policy is SwmrRecoveryPolicy.EXPIRE
    for step in vector["steps"]:
        assert [_output_json(output) for output in node.handle(json_to_input(step["in"]))] == step["out"]


def test_snapshot_delta_corpus_is_pinned() -> None:
    assert (_DOCUMENT["shape"], _DOCUMENT["core"], _DOCUMENT["version"]) == (
        "snapshot_delta",
        "swmr",
        "snapshot_delta.profile/v1",
    )
    assert len(_DOCUMENT["vectors"]) == 4
