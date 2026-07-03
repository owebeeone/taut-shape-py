"""taut-shape (Python) — pure-Python delivery-shape engine (`log` first).

The public entry point is :class:`taut_shape.log.LogNode`. See ``README.md`` and
``dev-docs/InitialPlan.md``. Phases 3–5 (shell, CLI tool, interop) are not built
yet.
"""

from __future__ import annotations

from .log import LogNode, StopWhen

__all__ = ["LogNode", "StopWhen"]
