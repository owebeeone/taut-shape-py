"""Whole-corpus conformance for the independent Python SWMR engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.log.engine import StopWhen
from taut_shape.swmr import _generated as g
from taut_shape.swmr.engine import SwmrNode
from taut_shape.swmr.wire import json_to_input, output_to_json

_CORPUS = Path(__file__).parents[2] / "taut-shape" / "corpus" / "swmr.v1.json"
_DOCUMENT = json.loads(_CORPUS.read_text())


def test_swmr_corpus_is_pinned_and_complete() -> None:
    assert (_DOCUMENT["shape"], _DOCUMENT["version"], len(_DOCUMENT["vectors"])) == (
        "swmr",
        "swmr.oracle/v1",
        33,
    )


@pytest.mark.parametrize("vector", _DOCUMENT["vectors"], ids=lambda vector: vector["name"])
def test_swmr_oracle_vector(vector: dict[str, Any]) -> None:
    config = vector["node"]
    node = SwmrNode(
        max_deltas=config.get("max_deltas"),
        stop_when=(
            StopWhen.EXPLICIT_ONLY
            if config["stop_when"] == "explicit_only"
            else StopWhen.LAST_READER
        ),
    )
    actual = []
    for step in vector["steps"]:
        actual.append(
            {
                "in": step["in"],
                "out": [output_to_json(output) for output in node.handle(json_to_input(step["in"]))],
            }
        )
    assert actual == vector["steps"]


def test_swmr_releases_large_held_set_linearly() -> None:
    node = SwmrNode()
    for index in range(2_000):
        assert node.handle(
            g.SwmrReadRequest("swmr-A", f"s{index:04}", None, None)
        ) == []
    outputs = node.handle(g.SwmrSnapshotPush("writer-A", b"ready"))
    assert len(outputs) == 2_000
    assert [
        output.stream_id
        for output in outputs
        if isinstance(output, g.SwmrReadResponse)
    ] == [f"s{index:04}" for index in range(2_000)]
