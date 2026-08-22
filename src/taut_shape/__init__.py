"""taut-shape (Python) — pure-Python delivery-shape engine (`log` first).

The public entry point is :class:`taut_shape.log.LogNode`. See ``README.md`` and
``dev-docs/InitialPlan.md``. The CLI tool (:mod:`taut_shape.tool`, Phase 4) and
its cross-language interop matrix participation (Phase 5) are built; Phase 3
(an ``asyncio`` shell) is not.
"""

from __future__ import annotations

from .log import LogNode, StopWhen
from .value import ValueNode
from .atom import AtomNode
from .stream import StreamNode
from .swmr import SwmrNode
from .snapshot_delta import SnapshotDeltaNode

__all__ = [
    "AtomNode",
    "LogNode",
    "SnapshotDeltaNode",
    "StopWhen",
    "StreamNode",
    "SwmrNode",
    "ValueNode",
]
