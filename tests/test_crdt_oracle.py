from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from taut_shape.crdt import CrdtNode, project_text
from taut_shape.crdt.wire import json_to_input, message_to_json

ROOT = Path(__file__).parents[2] / "taut-shape" / "corpus"
CORPUS = json.loads((ROOT / "crdt.v1.json").read_text())
CONVERGENCE = json.loads((ROOT / "crdt.convergence.v1.json").read_text())
TEXT = json.loads((ROOT / "text_crdt.profile.v1.json").read_text())


@pytest.mark.parametrize("vector", CORPUS["vectors"], ids=lambda row: row["name"])
def test_crdt_mailbox_corpus(vector: dict[str, Any]) -> None:
    node = CrdtNode(max_pending=int(vector.get("node", {}).get("max_pending", 1024)))
    actual = []
    for step in vector["steps"]:
        outputs = node.handle(json_to_input(step["in"]))
        actual.append({"in": step["in"], "out": [message_to_json(output) for output in outputs]})
    assert actual == [{"in": step["in"], "out": step["out"]} for step in vector["steps"]]


def canonical(node: CrdtNode, diagnostics: list[dict[str, Any]], text: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "clock": message_to_json(json_to_input({"type": "read", "crdt_id": "c", "stream_id": "s", "cursor": node.clock}))["cursor"] if False else {"entries": [{"origin": e.origin, "seq": str(e.seq)} for e in node.clock.entries]},
        "ops": [message_to_json(json_to_input({"type": "apply", "op": {"origin": op.origin, "seq": str(op.seq), "deps": {"entries": [{"origin": e.origin, "seq": str(e.seq)} for e in op.deps.entries]}, "payload": __import__("base64").b64encode(op.payload).decode()}}))["op"] for op in node.operations],
        "diagnostics": sorted({(d["code"], d["origin"], d["seq"]) for d in diagnostics}),
    }
    # JSON changes tuples to arrays in the committed oracle.
    result["diagnostics"] = [list(row) for row in result["diagnostics"]]
    if text:
        projection = project_text(node)
        result["projection"] = {"text": projection.text, "diagnostics": list(projection.diagnostics)}
    return result


@pytest.mark.parametrize("corpus,is_text", [(CONVERGENCE, False), (TEXT, True)])
def test_all_replica_orders_converge(corpus: dict[str, Any], is_text: bool) -> None:
    for scenario in corpus["scenarios"]:
        for replica in scenario["replicas"]:
            node = CrdtNode(max_pending=scenario["max_pending"])
            diagnostics: list[dict[str, Any]] = []
            if scenario["bootstrap"] is not None:
                diagnostics += [message_to_json(out) for out in node.handle(json_to_input({"type": "install_bootstrap", "bootstrap": scenario["bootstrap"]}))]
            for index in replica["order"]:
                diagnostics += [message_to_json(out) for out in node.handle(json_to_input({"type": "apply", "op": scenario["ops"][index]}))]
            assert canonical(node, diagnostics, is_text) == scenario["expect"]


def test_large_reverse_causal_chain_drains_without_recursion() -> None:
    node = CrdtNode(max_pending=2000)
    from taut_shape.crdt import _generated as g
    for seq in range(2000, 0, -1):
        node.handle(g.CrdtApply(g.CrdtOp("a", seq, g.CrdtClock([]), b"x")))
    assert node.clock.entries == [g.CrdtClockEntry("a", 2000)]
