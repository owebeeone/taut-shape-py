"""Conformance/interop tooling. ``oraclefmt`` maps corpus JSON <-> engine
messages; ``framing`` is the length-prefixed tagged-CBOR data channel; ``main``
is the CLI (``node`` / ``client`` modes), reachable as ``python3 -m
taut_shape.tool`` or the ``taut-shape-tool`` console script.
"""

from __future__ import annotations

from .main import main

__all__ = ["main"]
