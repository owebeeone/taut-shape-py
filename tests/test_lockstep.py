"""Lockstep gate — the committed corpus must match the pinned version.

The analogue of taut's ``test_committed_oracle_in_lockstep_with_reference``: the
corpus ``version`` string this repo pins (``loader.PINNED_VERSION``) must equal
the committed corpus on disk. Pin ≠ corpus ⇒ fail with the bump message. This is
the single cross-repo coordination point (shared plan §6 / TautShapeOracle §6).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle.loader import PINNED_VERSION, corpus_path, load_corpus  # noqa: E402


def test_corpus_present() -> None:
    assert corpus_path().exists(), f"oracle corpus not found at {corpus_path()}"


def test_committed_corpus_in_lockstep_with_pin() -> None:
    committed = load_corpus()
    assert committed["version"] == PINNED_VERSION, (
        "oracle out of date — bump pin "
        f"(committed={committed['version']!r}, pinned={PINNED_VERSION!r})"
    )
    assert committed["shape"] == "log"
