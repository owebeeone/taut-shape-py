"""Deterministic text projection over a common :class:`CrdtNode`."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from .engine import CrdtNode


@dataclass(frozen=True, slots=True)
class TextProjection:
    text: str
    diagnostics: tuple[str, ...]


def encode_text_insert(atom_id: str, after: str | None, text: str) -> bytes:
    return _json_bytes({"kind": "insert", "atom_id": atom_id, "after": after, "text": text})


def encode_text_delete(atom_id: str) -> bytes:
    return _json_bytes({"kind": "delete", "atom_id": atom_id})


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def project_text(node: CrdtNode) -> TextProjection:
    atoms: dict[str, tuple[str | None, str, tuple[str, int]]] = {}
    deleted: set[str] = set()
    diagnostics: set[str] = set()
    if node.bootstrap is not None:
        try:
            rows = json.loads(node.bootstrap.state)["atoms"]
            if not isinstance(rows, list):
                raise ValueError
            for row in rows:
                atom_id, after, text, is_deleted = row["atom_id"], row["after"], row["text"], row["deleted"]
                if not isinstance(atom_id, str) or not atom_id or (after is not None and not isinstance(after, str)) or not isinstance(text, str) or not text or not isinstance(is_deleted, bool):
                    raise ValueError
                atoms[atom_id] = (after, text, ("", 0))
                if is_deleted:
                    deleted.add(atom_id)
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            diagnostics.add("invalid_bootstrap")
    for op in node.operations:
        key = (op.origin, op.seq)
        try:
            payload = json.loads(op.payload)
            kind, atom_id = payload["kind"], payload["atom_id"]
            if not isinstance(atom_id, str) or not atom_id:
                raise ValueError
            if kind == "delete" and set(payload) == {"kind", "atom_id"}:
                deleted.add(atom_id)
            elif kind == "insert" and set(payload) == {"kind", "atom_id", "after", "text"}:
                after, text = payload["after"], payload["text"]
                if (after is not None and not isinstance(after, str)) or not isinstance(text, str) or not text:
                    raise ValueError
                candidate = (after, text, key)
                previous = atoms.get(atom_id)
                if previous is not None and previous != candidate:
                    diagnostics.add(f"atom_equivocation:{atom_id}")
                    atoms[atom_id] = min(previous, candidate, key=lambda item: ("" if item[0] is None else item[0], item[1], item[2]))
                else:
                    atoms[atom_id] = candidate
            else:
                raise ValueError
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            diagnostics.add(f"invalid_payload:{key[0]}:{key[1]}")
    children: dict[str | None, list[str]] = {}
    for atom_id, (after, _text, _key) in atoms.items():
        if after is not None and after not in atoms:
            diagnostics.add(f"missing_parent:{atom_id}:{after}")
            continue
        children.setdefault(after, []).append(atom_id)
    for ids in children.values():
        ids.sort()
    output: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(atom_id: str) -> None:
        if atom_id in visiting:
            diagnostics.add(f"cycle:{atom_id}")
            return
        if atom_id in visited:
            return
        visiting.add(atom_id)
        if atom_id not in deleted:
            output.append(atoms[atom_id][1])
        for child in children.get(atom_id, []):
            visit(child)
        visiting.remove(atom_id)
        visited.add(atom_id)

    for root in children.get(None, []):
        visit(root)
    for atom_id in sorted(set(atoms) - visited):
        if atoms[atom_id][0] in atoms:
            visit(atom_id)
    return TextProjection("".join(output), tuple(sorted(diagnostics)))
