"""taut-shape (Python) — pure-Python delivery-shape engine (`log` first).

The public entry point is :class:`taut_shape.log.LogNode`. See ``README.md`` and
``dev-docs/InitialPlan.md``. The CLI tool (:mod:`taut_shape.tool`, Phase 4) and
its cross-language interop matrix participation (Phase 5) are built; Phase 3
(an ``asyncio`` shell) is not.
"""

from __future__ import annotations

from importlib import import_module


def __getattr__(name):
    modules = {"LogNode": "log", "StopWhen": "log", "ValueNode": "value",
               "AtomNode": "atom", "StreamNode": "stream", "SwmrNode": "swmr",
               "SnapshotDeltaNode": "snapshot_delta"}
    if name not in modules:
        raise AttributeError(name)
    value = getattr(import_module(f".{modules[name]}", __name__), name)
    globals()[name] = value
    return value

__all__ = [
    "AtomNode",
    "LogNode",
    "SnapshotDeltaNode",
    "StopWhen",
    "StreamNode",
    "SwmrNode",
    "ValueNode",
]
