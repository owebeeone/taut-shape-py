# taut-shape (Python)

`pip install taut-shape` → `import taut_shape`.

A **pure-Python** implementation of the Taut `atom`, `log`, `stream`, and `value` delivery shapes. No Rust,
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
- Phase 4 — the `taut-shape-tool` CLI (`node`/`client` modes over stdin/stdout
  framing, `python3 -m taut_shape.tool`; see `src/taut_shape/tool/main.py`). ✓
- Phase 5 — interop matrix participation (`taut-shape/matrix/driver.py` runs
  this tool as the `py` language). ✓
- Phase 3 (an `asyncio` shell) — not built; the engine has no built-in
  concurrency layer beyond the CLI's synchronous read/handle/write loop.

## Layout

```
src/taut_shape/log/
  _generated.py   # tautc-generated message/value types (vendored, do NOT edit)
  messages.py     # InMsg/OutMsg unions + re-exports
  _window.py      # store core: bounded window, head/floor, evict (internal)
  _sessions.py    # session table: held reads, timers, watermarks (internal)
  engine.py       # LogNode.handle + read-only accessors
src/taut_shape/value/
  _generated.py   # tautc-generated value messages (vendored, do NOT edit)
  engine.py       # attributed LWW ValueNode
src/taut_shape/atom/
  _generated.py   # tautc-generated atom messages (vendored, do NOT edit)
  engine.py       # latest-state AtomNode
src/taut_shape/stream/
  _generated.py   # tautc-generated stream messages (vendored, do NOT edit)
  engine.py       # bounded live-only StreamNode
```

## Tool (node / client)

Run the framing CLI as a module. Both modes accept exact `--shape <NAME>`
selection and default to `log`; the implemented registry contains `atom`, `log`,
`stream`, and `value`.

```
PYTHONPATH=../taut/src:src python3 -m taut_shape.tool node --shape log
PYTHONPATH=../taut/src:src python3 -m taut_shape.tool client --shape log \
  --stream-id s1 --from 0
PYTHONPATH=../taut/src:src python3 -m taut_shape.tool client --shape value \
  --value-id value-A --stream-id s1 --reads 1
PYTHONPATH=../taut/src:src python3 -m taut_shape.tool client --shape atom \
  --atom-id atom-A --stream-id s1 --from 0
PYTHONPATH=../taut/src:src python3 -m taut_shape.tool client --shape stream \
  --stream-id live-metrics
```

An unsupported name exits 2 with `TAUT_SHAPE_UNSUPPORTED_SHAPE` before stdin is
read or a client request is written.

## Running the tests

The `taut` codec is a workspace sibling; point `PYTHONPATH` at it:

```
PYTHONPATH=../taut/src:src pytest
```
