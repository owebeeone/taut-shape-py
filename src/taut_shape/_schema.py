"""Read immutable codec facts emitted during development; no authoring loader."""

from __future__ import annotations

from importlib import import_module

from taut.facts import Schema


def load_packaged_schema(shape: str) -> Schema:
    """Return one generated schema's static facts without executing ``.taut.py``."""

    if shape not in ("atom", "crdt", "log", "stream", "swmr", "value"):
        raise ValueError(f"unknown shape {shape!r}")
    return import_module(f"taut_shape.{shape}._generated").SCHEMA
