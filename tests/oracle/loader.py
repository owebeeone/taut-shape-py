"""Oracle-vector loader — reads the pinned ``taut-shape`` corpus.

Resolution (see ``SOURCE.md``): the sibling ``taut-shape/corpus/log.v0.json``,
overridable via ``TAUT_SHAPE_CORPUS``. The pinned version string
``PINNED_VERSION`` is the single cross-repo coordination point (shared plan §6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

PINNED_VERSION = "log.oracle/v0"


def corpus_path() -> Path:
    override = os.environ.get("TAUT_SHAPE_CORPUS")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    repo_root = here.parents[2]                      # .../taut-shape-py
    return repo_root.parent / "taut-shape" / "corpus" / "log.v0.json"


def load_corpus() -> dict[str, Any]:
    return json.loads(corpus_path().read_text())


def vectors() -> list[dict[str, Any]]:
    return load_corpus()["vectors"]
