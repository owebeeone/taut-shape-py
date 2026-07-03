# Oracle & schema pins

The single cross-repo coordination point (shared plan §6 / TautShapeOracle §6).

## Corpus (the behavioral oracle)

- **Source repo**: `taut-shape` (workspace sibling).
- **Path**: `taut-shape/corpus/log.v0.json`.
- **Pinned version string**: `log.oracle/v0` — the loader asserts the committed
  corpus's `"version"` equals this. Pin ≠ corpus ⇒ fail with
  "oracle out of date — bump pin".
- **Pinned sha256** (informational; the version string is the gate):
  `8ca9dfb74cfc02577d5c9d5f7906c0cf252de7b7bbb3eaf85a5398e31e6e6fd8`
  (25 vectors, includes the D20-clamp vector 24 `evict_beyond_head_clamps`).

Resolution mechanism: `tests/oracle/loader.py` resolves the corpus relative to
this repo (`../taut-shape/corpus/log.v0.json`), overridable via the
`TAUT_SHAPE_CORPUS` environment variable.

## Message schema (D17 — generated types)

- **Source**: `taut-shape/ir/shape_log.taut.py`.
- **sha256**: `3e1224747430e12188beab3ece4d8ebe44decbcae3fe4b86c2731136617863a9`.
- **IR JSON** (`shape_log.ir.json`) sha256:
  `a9d24d3bc98ea9e8e71a1a6d8aafa5b3c2a2cc4cb58ae855d0e8a377ec97a3db`.
- Generated Python vendored at `src/taut_shape/log/_generated.py` (provenance
  header there). Regenerate on a schema bump.

## taut codec (runtime dependency)

- Dist name `taut-proto`, import name `taut`. Reused verbatim:
  `taut.wire.jsoncodec` (corpus JSON form), `taut.ir.load.load_schema`
  (drives the codec from the pinned schema).
- **Packaging note**: the exact `taut-proto` version pin is a packaging detail
  left to publication time. In this workspace, tests resolve `taut` via
  `PYTHONPATH=../taut/src`. The schema is loaded from the sibling
  `taut-shape/ir/shape_log.taut.py` (overridable via `TAUT_SHAPE_SCHEMA`).

## Tool protocol (Phase 4)

Framing + JSONL schema + channel/fd assignment: not pinned yet — Phase 4 is not
built in this milestone.
