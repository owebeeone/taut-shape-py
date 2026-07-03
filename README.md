# taut-shape (Python)

`pip install taut-shape` → `import taut_shape`.

A **pure-Python** implementation of Taut delivery shapes (`log` first). No Rust,
no PyO3, no native extension. The engine is a synchronous **mailbox endpoint**
(`LogNode.handle(msg) -> [outputs]`); the only concurrency is an optional
`asyncio` shell layered on top (not yet built).

This is a **clean-room** implementation: written against the shared plan
(`taut-shape/dev-docs/TautClientImplPlan.md`, D1–D19) and the behavioral oracle
(`taut-shape/corpus/log.v0.json`) only — it does not mirror `taut-shape-rs`. A
hand-written engine that still reproduces every oracle vector is the evidence
that **the oracle, not shared source, is the contract**.

## Status

- Phase 0 — scaffold + vendored generated message types. ✓
- Phase 1 — the `LogNode` mailbox engine (pure, sync). ✓
- Phase 2 — oracle conformance (`tests/test_oracle.py`, whole-transcript `==`). ✓
- Phases 3–5 (shell, CLI tool, interop matrix) — not built yet.

## Layout

```
src/taut_shape/log/
  _generated.py   # tautc-generated message/value types (vendored, do NOT edit)
  messages.py     # InMsg/OutMsg unions + re-exports
  _window.py      # store core: bounded window, head/floor, evict (internal)
  _sessions.py    # session table: held reads, timers, watermarks (internal)
  engine.py       # LogNode.handle + read-only accessors
```

## Running the tests

The `taut` codec is a workspace sibling; point `PYTHONPATH` at it:

```
PYTHONPATH=../taut/src:src python3 -m pytest
```
