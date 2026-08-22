"""Whole-corpus conformance for the independent Python atom engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.atom import _generated as g
from taut_shape.atom.engine import AtomNode
from taut_shape.atom.wire import json_to_input, output_to_json
from taut_shape.log.engine import StopWhen


_CORPUS_PATH = Path(__file__).parents[2] / "taut-shape" / "corpus" / "atom.v1.json"
_CORPUS: dict[str, Any] = json.loads(_CORPUS_PATH.read_text())


def test_atom_corpus_is_pinned_and_complete() -> None:
    assert (_CORPUS["shape"], _CORPUS["version"], len(_CORPUS["vectors"])) == (
        "atom",
        "atom.oracle/v1",
        28,
    )


@pytest.mark.parametrize("vector", _CORPUS["vectors"], ids=lambda vector: vector["name"])
def test_atom_oracle_vector(vector: dict[str, Any]) -> None:
    stop_when = (
        StopWhen.EXPLICIT_ONLY
        if vector["node"]["stop_when"] == "explicit_only"
        else StopWhen.LAST_READER
    )
    node = AtomNode(stop_when=stop_when)
    actual = [
        {
            "in": step["in"],
            "out": [output_to_json(output) for output in node.handle(json_to_input(step["in"]))],
        }
        for step in vector["steps"]
    ]
    assert actual == vector["steps"]


def test_atom_releases_a_large_held_set_once_in_creation_order() -> None:
    node = AtomNode()
    for index in range(2_000):
        assert node.handle(
            g.AtomReadRequest(
                atom_id="atom-A",
                stream_id=f"s{index:04d}",
                version=g.AtomVersion(version=0),
                timeout_ms=None,
            )
        ) == []
    outputs = node.handle(g.AtomReplace(payload=b"ready"))
    assert len(outputs) == 2_000
    assert [output.stream_id for output in outputs if isinstance(output, g.AtomReadResponse)] == [
        f"s{index:04d}" for index in range(2_000)
    ]
