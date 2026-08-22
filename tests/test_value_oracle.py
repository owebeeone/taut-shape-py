from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.value import ValueNode
from taut_shape.value import _generated as g


_CORPUS_PATH = Path(__file__).parents[2] / "taut-shape" / "corpus" / "value.v0.json"
_CORPUS = json.loads(_CORPUS_PATH.read_text())


def _bytes(value: str) -> bytes:
    return base64.b64decode(value)


def _input(message: dict[str, Any]) -> g.ValueSet | g.ValueReadRequest:
    if message["type"] == "set":
        return g.ValueSet(
            origin=message["origin"],
            seq=int(message["seq"]),
            lamport=int(message["lamport"]),
            prev=None if message.get("prev") is None else _bytes(message["prev"]),
            payload=_bytes(message["payload"]),
        )
    if message["type"] == "read":
        return g.ValueReadRequest(
            value_id=message["value_id"],
            stream_id=message["stream_id"],
        )
    raise AssertionError(f"unknown value input {message['type']!r}")


def _output(message: object) -> dict[str, Any]:
    if isinstance(message, g.ValueDiagnostic):
        return {
            "type": "diagnostic",
            "severity": message.severity.name,
            "code": message.code.name,
        }
    assert isinstance(message, g.ValueReadResponse)
    return {
        "type": "read_response",
        "value_id": message.value_id,
        "stream_id": message.stream_id,
        "value": None if message.value is None else base64.b64encode(message.value).decode(),
        "winner": None
        if message.winner is None
        else {
            "origin": message.winner.origin,
            "seq": str(message.winner.seq),
            "lamport": str(message.winner.lamport),
        },
        "state": message.state.name,
    }


def test_value_corpus_pin() -> None:
    assert (_CORPUS["shape"], _CORPUS["version"], len(_CORPUS["vectors"])) == (
        "value",
        "value.oracle/v0",
        13,
    )


@pytest.mark.parametrize("vector", _CORPUS["vectors"], ids=lambda vector: vector["name"])
def test_value_vector(vector: dict[str, Any]) -> None:
    node = ValueNode()
    actual = [
        {
            "in": step["in"],
            "out": [_output(output) for output in node.handle(_input(step["in"]))],
        }
        for step in vector["steps"]
    ]
    expected = [{"in": step["in"], "out": step["out"]} for step in vector["steps"]]
    assert actual == expected
