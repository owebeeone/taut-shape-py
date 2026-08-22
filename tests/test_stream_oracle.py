"""Whole-corpus conformance for the independent Python stream engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.log.engine import StopWhen
from taut_shape.stream import _generated as g
from taut_shape.stream.engine import StreamNode
from taut_shape.stream.wire import json_to_input, output_to_json

_CORPUS = Path(__file__).parents[2] / "taut-shape" / "corpus" / "stream.v1.json"
_DOCUMENT = json.loads(_CORPUS.read_text())


def test_stream_corpus_is_pinned_and_complete() -> None:
    assert (_DOCUMENT["shape"], _DOCUMENT["version"], len(_DOCUMENT["vectors"])) == (
        "stream",
        "stream.oracle/v1",
        28,
    )


@pytest.mark.parametrize("vector", _DOCUMENT["vectors"], ids=lambda vector: vector["name"])
def test_stream_oracle_vector(vector: dict[str, Any]) -> None:
    config = vector["node"]
    node = StreamNode(
        capacity_records=int(config["capacity_records"]),
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


def test_stream_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        StreamNode(capacity_records=0)


def test_stream_releases_large_held_set_linearly() -> None:
    node = StreamNode()
    for index in range(2_000):
        assert node.handle(
            g.StreamReadRequest(
                stream_id=f"s{index:04}",
                max_records=None,
                max_bytes=None,
                timeout_ms=None,
            )
        ) == []
    outputs = node.handle(g.StreamPush(payload=b"ready"))
    assert len(outputs) == 2_000
    assert [output.stream_id for output in outputs if isinstance(output, g.StreamReadResponse)] == [
        f"s{index:04}" for index in range(2_000)
    ]
