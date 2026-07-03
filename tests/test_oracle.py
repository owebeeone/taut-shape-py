"""Oracle conformance — the clean-room engine reproduces every corpus vector.

The ``test_glade_folds.py`` shape: replay each vector's input message sequence
through a fresh ``LogNode``, convert observed outputs back to the corpus's taut
jsoncodec form, and assert **whole-transcript equality** — no per-field asserts.
Frozen-value ``==`` over the reconstructed step list does the work.

Run with the taut codec + this package on the path, e.g.:
    PYTHONPATH=../taut/src:src python3 -m pytest
"""

from __future__ import annotations

from typing import Any

import pytest

from taut_shape.log import LogNode, StopWhen
from taut_shape.tool.oraclefmt import json_to_msg, msg_to_json

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle.loader import vectors  # noqa: E402


_STOP_WHEN = {sw.value: sw for sw in StopWhen}


def _make_node(case: dict[str, Any]) -> LogNode:
    node_cfg = case.get("node") or {}
    stop_when = _STOP_WHEN[node_cfg.get("stop_when", StopWhen.EXPLICIT_ONLY.value)]
    # log_id is a wire field on addressed messages; the corpus uses "log-A".
    return LogNode(log_id="log-A", stop_when=stop_when)


def run(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Replay the vector; return the observed step transcript in corpus form."""
    node = _make_node(case)
    observed: list[dict[str, Any]] = []
    for step in case["steps"]:
        in_msg = json_to_msg(step["in"])
        outs = node.handle(in_msg)
        observed.append({"in": step["in"], "out": [msg_to_json(o) for o in outs]})
    return observed


def _expected(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"in": step["in"], "out": step["out"]} for step in case["steps"]]


@pytest.mark.parametrize("case", vectors(), ids=lambda c: c["name"])
def test_vector_matches_oracle(case: dict[str, Any]) -> None:
    assert run(case) == _expected(case), f"oracle mismatch for {case['name']}"


def test_all_vectors_present() -> None:
    # Guardrail: the catalog is non-trivial (25 vectors after the D20-clamp
    # vector 24 `evict_beyond_head_clamps`).
    assert len(vectors()) == 25
