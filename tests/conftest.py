"""Test bootstrap: make ``src/`` (this package) and the workspace ``taut``
codec importable without an install. The exact ``taut-proto`` pin is a
packaging detail (see ``tests/oracle/SOURCE.md``); in-workspace we resolve
``taut`` from the sibling ``taut/src`` unless it is already importable.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[1]                    # .../taut-shape-py
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Resolve taut from the sibling workspace if not already installed.
try:  # pragma: no cover - import probe
    import taut  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    _TAUT_SRC = _REPO_ROOT.parent / "taut" / "src"
    if _TAUT_SRC.exists():
        sys.path.insert(0, str(_TAUT_SRC))
