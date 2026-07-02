# taut-shape-py — Implementation Plan (Python)

Status: plan (v2 — mailbox engine model). Scope: phased plan, **Python-specific**.
Audience: contributors to `taut-shape-py`.

**This document SPECIALIZES the shared plan**
[`../../taut-shape/dev-docs/TautClientImplPlan.md`](../../taut-shape/dev-docs/TautClientImplPlan.md)
(v2 — the pure mailbox engine model). It mirrors that plan's phase names exactly
(Phase 0–5; Phase 6 deferred) and resolves every `«SPECIALIZE: …»` marker with a
concrete Python commitment. The design it implements is
[`../../taut-shape/dev-docs/TautShapeArchitecture.md`](../../taut-shape/dev-docs/TautShapeArchitecture.md)
(§4 contract summary, §5 backing, §6 mailbox engine + shells); the behavioral
contract is the oracle corpus owned by `taut-shape`.

Where the shared plan and this document disagree, **the shared plan governs the
contract and the oracle governs behavior** — this document only chooses Python
idioms for rendering them. Pinned decisions are cited by number (D1–D17, shared
plan §4).

v2 note: this revision replaces the v1 draft's "sync core + consumer `Store`
Protocol + `Readiness` hook + reader/writer split" with the shared plan's **pure
message-queue engine** (D1). Everything that was a callback or a seam is now a
message; held long-polls are engine state. §7.8 records which v1 open questions
the D-numbers resolved.

---

## 0. Python posture (why this repo exists, stated up front)

`taut-shape-py` is **pure Python — no Rust, no PyO3, no native extension**. The
engine is plain Python driven synchronously; the only concurrency is an
`asyncio` shell layered on top, and even that owns no I/O. This is a deliberate
contract-proving choice, not a performance one:

- **Clean-room is the point.** Python is implemented purely against the shared
  plan (§2–§4) and the oracle vectors — it does **not** mirror or port
  `taut-shape-rs`. A clean-room reimplementation that still reproduces every
  oracle vector is the strongest available evidence that **the oracle, not shared
  source, is the contract.** If a hand-written Python engine and an
  extracted-from-glade Rust engine converge on identical
  `(input messages) → (output messages)` transcripts, the behavioral parity is
  real and not an artifact of shared code. The clean-room applies to the
  **engine behavior**: the message *types* are shared **generated** artifacts
  (tautc-generated from `taut-shape/ir/shape_log.taut.py`, D17), exactly as the
  reused CBOR codec already was — sharing generated declarations does not
  weaken the evidence, because the oracle pins behavior, not type authorship.
- **Pure Python removes the hardest failure mode.** No Rust-async ↔ asyncio
  bridge, no `call_soon_threadsafe` wakeup, no cancel-across-PyO3. Per the
  architecture (§6 "Python stays pure"), those cross-runtime concerns live in
  the **consumer** (gwz's bridge), never here. The v2 engine makes this even
  cleaner than v1 did: the *whole protocol* — including held long-polls and
  timers — is drivable purely synchronously as `handle(msg) -> [outputs]`, so
  the entire contract surface is testable without an event loop in sight.
- **Precedent.** This follows taut's existing pure-Python wire codec
  (`taut/src/taut/wire/cbor.py`, hand-rolled, zero deps) and its golden-oracle
  test style. The oracle test
  `taut/src/tests/test_glade_folds.py` is the precedent pattern we copy:
  *reference vectors are the cross-language oracle; every other language must
  reproduce them; a lockstep test gates the committed corpus against the
  reference.* See `test_committed_oracle_in_lockstep_with_reference()` there —
  Phase 2 below is the same shape.

**Guiding constraint (inherited):** we are prioritizing getting the API right
over speed. Phase 1 (the engine surface) is the load-bearing decision; §7
renders it concretely and §7.9 lists the (now few, purely local) open questions
to settle before it calcifies.

---

## 1. Specialization resolutions (the checklist, answered)

Every marker from the shared plan §7, resolved for Python:

| Marker | Python commitment |
|---|---|
| Package manifest | `pyproject.toml`, PEP 621 metadata + `[build-system]`. Pure-Python wheel via `setuptools` + `setuptools-scm` (git-tag versioning, mirroring `taut`). **No Rust/PyO3 binding, no `maturin`/`setuptools-rust`.** |
| Build/test runner | `pytest`; `testpaths = ["tests"]`. `python -m taut_shape.tool` for the CLI. Lint/type via `ruff` + `mypy --strict` (advisory in CI to start). Python ≥ 3.10 (structural `match` is load-bearing, §7.1). |
| Golden framework | **`syrupy`** (pytest snapshot plugin) for transcript/CLI snapshots. But the **oracle JSON is the primary golden**: whole-transcript `==` against the committed corpus — no bespoke per-case asserts (mirrors `test_glade_folds.py`). syrupy covers *derived* surfaces only. See §1.1. |
| Engine rendering | Engine type `LogNode` (plain class, one per log); signature `handle(msg: InMsg) -> list[OutMsg]`; messages are the **tautc-generated frozen slotted dataclasses** (D17, next row) grouped by **hand-written PEP 604 unions** (`InMsg` / `OutMsg`), dispatched with `match`/`case` class patterns, exhaustiveness via `typing.assert_never`. States/error codes as `Enum`s with the D13 canonical strings as values. See §7.1–§7.3. |
| Generated message types | `tautc gen -l python --api-only` over the pinned `taut-shape/ir/shape_log.taut.py` (D17) emits the message/value dataclasses; the output is **vendored** as `src/taut_shape/log/_generated.py` — committed, regenerated on schema bump, never hand-edited — exactly gwz-py's `protocol/generated/api.py` pattern. `messages.py` re-exports them and adds the hand-written unions. |
| Shell & async idiom | `LogShell`, an asyncio pump: **same-loop cooperative scheduling *is* the D15 serialization** (no lock object); addressed `Response`s resolve per-stream `asyncio.Future`s; `SetTimer`/`CancelTimer` map to `loop.call_later` feeding back `TimerExpired`. Streaming sugar = an **async generator** issuing `Read` (no `timeout_ms` ⇒ hold, D14) and awaiting the addressed `Response`; `asyncio.CancelledError` ⇒ `EndStream` in `finally` (D4). See §7.5–§7.6. |
| Service form | `LogService`: a thin dict-of-nodes router keyed by minted `log_id`; unknown ids answered with a `failed` `Response` carrying `Error(code=UNKNOWN_LOG)` (message-based, no exception). See §7.7. |
| CBOR codec | **taut's pure-Python wire codec**, reused verbatim: `taut.wire.cbor` (`dumps`/`loads`) for the byte substrate and `taut.wire.codec` (`encode`/`decode`, schema-driven) for the `Log*` companion messages. No re-implementation, no Rust. Pinned via the `taut-proto` dependency (§2 S0.3). |
| Source to mirror | **Clean-room** — implemented against the shared plan + oracle only. Explicitly does **not** port `taut-shape-rs`. |
| Distribution | **PyPI dist name `taut-shape`** (`pip install taut-shape` → `import taut_shape`). Published per the `taut`/`taut-proto` precedent (setuptools-scm git tags). |
| docs/ layout | `docs/api/` — one spec per v2 surface (messages, engine, shell, streaming sugar, service). `docs/examples/` — runnable worked examples (drive the engine directly, resume + expired, tail-with-cancel, CLI interop). See §9. |

### 1.1 Golden strategy (recommendation, stated once)

**Recommendation: oracle-JSON-as-primary-golden + `syrupy` for derived surfaces.**

- The **oracle corpus** — pure `(input message sequence) → (expected output
  message sequence)` vectors per shared plan §5 — is loaded from `taut-shape`,
  replayed through `LogNode.handle`, and the **entire observed output sequence
  is compared with `==` to the expected** — exactly the
  `assert run(case) == case["expect"]` shape from `test_glade_folds.py`. No
  per-field asserts. Frozen dataclasses make this free: `==` over a list of
  messages *is* whole-output comparison. This is the contract test and it has
  no snapshot tool in the loop (the corpus *is* the snapshot, owned upstream).
- `syrupy` is used only where the golden is *generated by this repo* and has no
  upstream owner: CLI transcript snapshots (the OOB JSONL control channel),
  error-rendering snapshots, and example outputs. `inline-snapshot` was
  considered; `syrupy` is preferred because it stores snapshots as separate
  `.ambr` files (reviewable as artifacts, diff-friendly in PRs) and integrates
  as a plain pytest fixture. We keep one rule from the house style: **capture
  the whole output and diff; never write bespoke assertions over individual
  fields.**

---

## 2. Phase 0 — Scaffold & contract intake

Foundational repo setup. Parallel-friendly: S0.1/S0.2/S0.3 are independent.

- **S0.1 — Repo skeleton + manifest.** Create `pyproject.toml` (PEP 621), `README.md`,
  `LICENSE` (MIT, mirroring `taut`), `docs/api/`, `docs/examples/`, `src/taut_shape/`,
  `tests/`. Manifest as §1 (setuptools + setuptools-scm, pure-Python wheel, dist
  `taut-shape`). Wire `[project.scripts] taut-shape-tool = "taut_shape.tool:main"`.
  *(< 150 LOC of config.)*
- **S0.2 — Test runner + golden framework + CI.** `pytest` configured
  (`[tool.pytest.ini_options] testpaths = ["tests"]`); add `syrupy`, `ruff`,
  `mypy` dev-deps; a GitHub Actions workflow running `pytest`, `ruff check`,
  `mypy` on 3.10–3.13. Add a smoke test that imports the package. *(< 120 LOC.)*
- **S0.3 — Pin oracle + tool protocol + CBOR.** Declare the runtime dependency on
  `taut-proto` (for `taut.wire.cbor` / `taut.wire.codec`). Pin the **oracle corpus
  path/version** from `taut-shape` — record the resolution mechanism in
  `tests/oracle/SOURCE.md` (path to `taut-shape`'s corpus dir + the corpus
  version string the loader asserts). Pin the **tool-protocol version** (framing
  + JSONL schema + channel/fd assignment) likewise. Add the `Log*`
  companion-message schema (from `taut`, §4 of the architecture) as a vendored
  `*.taut.py` or a pinned import, loaded via `taut.ir.load.load_schema` so
  `codec.encode/decode` can drive it. **Generate the message types (D17):** run
  `tautc gen -l python --api-only` over the pinned
  `taut-shape/ir/shape_log.taut.py` and vendor the output as
  `src/taut_shape/log/_generated.py` (the gwz-py `protocol/generated/api.py`
  pattern); record the schema version next to the corpus pin in `SOURCE.md`.
  *(< 150 LOC.)*

**Exit:** `pytest` green on an empty suite; CLI entry point importable; oracle
corpus + CBOR codec + companion schema + generated `shape_log` message types
resolvable/importable from a test.

---

## 3. Phase 1 — The engine (foundational; the API to get right)

The load-bearing phase. Source: **clean-room** (§1). One `LogNode` per log
(D1); everything below is pure Python, sync, no I/O, no clock, no asyncio
import in the `log/` subtree. The store-core / session-table split (D2, D3) is
an **internal module boundary, not a public seam** — underscore-prefixed
modules, not exported.

- **S1.1 — Message unions over the generated types (shared §3.1–§3.3).** The
  `Cursor`/`Record`/`State`/`Error` value types plus every input (`Push`,
  `Seal`, `Close`, `Read`, `EndStream`, `TimerExpired`, `Evict`) and output
  (`Response`, `SetTimer`, `CancelTimer`, `ProducerStop`) are the
  **tautc-generated dataclasses vendored in S0.3** (D17) — not hand-written
  here. This step hand-writes only `src/taut_shape/log/messages.py`: the
  `InMsg`/`OutMsg` PEP 604 unions + re-exports over `_generated.py` (§7.1).
  `from __future__ import annotations`, full hints. *(< 80 LOC.)*
- **S1.2 — Store core: the bounded window.** `src/taut_shape/log/_window.py`
  (internal): `Push` append with `seq := head+1` (first record `seq = 1`, D8),
  `scan(from_seq, max_records, max_bytes)` with payload-bytes-only accounting
  and the forward-progress guarantee (D10), `head`/`floor`, `Evict` raising the
  floor (D2, D7). No stream concepts in this module. *(< 200 LOC.)*
- **S1.3 — Session table + read resolution (shared §3.4).**
  `src/taut_shape/log/_sessions.py` + the `Read` arm of
  `src/taut_shape/log/engine.py`: implicit stream creation on first `Read`
  (D4), held reads as engine state, supersede-on-new-`Read` (D5),
  `EndStream` cleanup (D4), the `expired` state with earliest-resumable
  `next_cursor` (D9), per-stream watermarks + `min_watermark` (D7),
  reader-count tracking and the ≥1→0 `ProducerStop` transition under
  `stop_when=last_reader` (D6), creation-order emission when one input
  releases several held reads (D16). *(< 300 LOC.)*
- **S1.4 — Lifecycle + timers.** `Seal` (held reads answered `eof`,
  idempotent), `Close`/`Close{error}` (held reads answered `closed`/`failed`
  + error, timers canceled, `ProducerStop` emitted — D12), `timeout_ms`
  semantics (`None` hold / `0` probe / `>0` hold + `SetTimer` — D14),
  `TimerExpired` answering `would_block` (late/canceled tokens are no-ops),
  monotonic timer tokens from 1 (D16). *(< 250 LOC.)*

**Exit:** the engine round-trips push→read→held-read-released-by-push→
seal/close→evict→expired-resume scenarios under direct synchronous unit tests
— `outputs = node.handle(msg)`, no event loop — with zero asyncio and zero I/O
in the subtree.

---

## 4. Phase 2 — Golden conformance

Reproduce the oracle. This is where clean-room pays off. Mirrors
`test_glade_folds.py` one-to-one.

- **S2.1 — Oracle-vector loader.** `tests/oracle/loader.py` reads the pinned
  `taut-shape` corpus (JSON), exposing `vectors()`. Message JSON ↔ dataclass
  mapping lives in `src/taut_shape/tool/oraclefmt.py` (shared with the tool's
  `gen`/`check` modes). The corpus JSON is the **taut jsoncodec** form of the
  messages (base64 bytes, i64-as-string — D17).
  *(< 200 LOC.)*
- **S2.2 — Replay vectors through the engine; whole-output golden.**
  `tests/test_oracle.py`: for each case, feed the input message sequence
  through a fresh `LogNode`, concatenate the outputs, and
  `assert observed == case["expect"]` — **whole-output `==`, no bespoke
  asserts** (the `test_glade_folds.py` shape; frozen-dataclass `==` does the
  work). Add `syrupy` snapshots only for the *human-readable* rendering of any
  failure diff, not the contract itself. *(< 150 LOC.)*
- **S2.3 — Lockstep gate.** A test that asserts the committed corpus is in sync
  with its declared version/manifest — the analogue of
  `test_committed_oracle_in_lockstep_with_reference()`: if the corpus version the
  loader pins ≠ the corpus on disk, fail with "oracle out of date — bump pin".
  This is the single cross-repo coordination point (a "corpus bump"). *(< 80 LOC.)*

**Exit:** every committed oracle vector reproduced by the clean-room engine; the
lockstep gate green.

---

## 5. Phase 3 — Shell & idiomatic stream surface

Thin asyncio shell over the pure engine. **No I/O, no executor beyond the loop,
no cross-thread anything.** Same-loop only.

- **S3.1 — The pump.** `src/taut_shape/shell/pump.py`: `LogShell` wraps one
  `LogNode`; `send(msg)` calls `handle` and dispatches outputs — addressed
  `Response`s resolve the per-stream pending `asyncio.Future` (≤1 outstanding
  per stream, D5, so a plain `dict[str, Future]` suffices); `SetTimer` →
  `loop.call_later(ms / 1000, …)` feeding back `TimerExpired{token}`;
  `CancelTimer` → cancel the timer handle; `ProducerStop` → the consumer's
  callback. Serialization (D15): every entry to the engine happens on one
  event loop from synchronous code, so cooperative scheduling is the lock.
  **Same-loop** assumption is explicit and documented; the cross-thread
  `call_soon_threadsafe` path is named as out of scope (consumer/gwz-bridge
  owns it). *(< 200 LOC.)*
- **S3.2 — Idiomatic streaming sugar + cancellation → `EndStream`.**
  `src/taut_shape/shell/stream.py`: `stream_responses(shell, …)` — an async
  generator that mints a `stream_id`, issues `Read` with **no `timeout_ms`**
  (hold indefinitely, D14), awaits the addressed `Response`, yields it,
  advances the cursor, and stops after any non-`data` state. Cancellation
  (`asyncio.CancelledError` at the `await`) and normal exit both send
  `EndStream{stream_id}` in `finally` (D4) — no close call, no producer
  callback: the engine emits `ProducerStop` itself when the policy says so
  (D6). *(< 150 LOC.)*

**Exit:** an async consumer tails a live log through the sugar, sees
backpressure via `max_*`, and cancelling the consuming task visibly produces
`EndStream` → (`stop_when=last_reader`) → `ProducerStop` — all on a single
event loop, verified by a deterministic async test + snapshot.

---

## 6. Phase 4 — Conformance / interop CLI tool

The subprocess tool, following taut's `test_kotlin.py` convention (a Python
driver spawns the tool and asserts on structured output). By design the tool is
little more than the engine + framing.

- **S4.1 — Framing.** `src/taut_shape/tool/framing.py`: the **data channel** is
  **length-prefixed CBOR** taut companion messages (`u32` big-endian length +
  `cbor.dumps` body, reusing `taut.wire.cbor`) — the real wire, under test; the
  **control/result channel** is **OOB JSONL** (one JSON object per line —
  scenario in, observed transcript out). Two separate channels per shared plan
  §5; the concrete fd assignment follows the tool-protocol spec pinned in S0.3.
  *(< 200 LOC.)*
- **S4.2 — Modes `gen` / `check` / `node` / `client`.** `taut_shape/tool/main.py`
  with an `argparse` subcommand per mode:
  - `gen` — emit oracle vectors. **For the reference implementation only**; for
    `-py` (clean-room, non-reference) `gen` is a *self-emit* used to cross-check
    against the committed corpus, not to author it.
  - `check` — replay the committed oracle through the engine, report pass/fail
    as JSONL (the in-process Phase 2 path, exposed as a CLI).
  - `node` — run a `LogNode` + `LogService` behind stdin/stdout framing: decode
    frames → `service.handle` → encode addressed outputs.
  - `client` — run the reading side (the cursor loop) against a node over the
    pipes, emitting its observed transcript as JSONL.
  *(< 300 LOC.)*

**Exit:** `python -m taut_shape.tool check` reproduces the oracle; a pytest
driver (the `test_kotlin.py` shape) spawns `node | client` and snapshots the
JSONL transcript.

---

## 7. The shared §2–§3 API, rendered concretely in Python

> This is the most important section. The shared plan §2–§3 is normative and
> language-neutral; below is its idiomatic Python rendering. Signatures are real
> and intended to be implemented as written, subject to §7.9 open questions.

### 7.1 Message types — generated frozen dataclasses + hand-written unions

> **Generated, not hand-written (D17).** Every message/value type below is
> emitted by `tautc gen -l python --api-only` from the payload-agnostic schema
> `taut-shape/ir/shape_log.taut.py` and vendored as
> `taut_shape/log/_generated.py` — exactly like gwz-py's
> `protocol/generated/api.py`. The rendering below is therefore the **expected
> shape of the generated code**, shown for review — not a hand-authoring task.
> Hand-written per D17: only the `InMsg`/`OutMsg` unions (end of this section),
> the engine (§7.2), and the shell (§7.5).

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


@dataclass(frozen=True, slots=True, order=True)
class Cursor:
    """'Records strictly after `seq` are unseen.' Named type (not a bare int)
    so it can grow (`byte_offset` reserved for partial-record delivery)."""
    seq: int


START: Final[Cursor] = Cursor(seq=0)   # D8: first record seq=1; START={seq:0}


@dataclass(frozen=True, slots=True)
class Record:
    """One append. Carries its own `seq` (D11); `payload` is the method's
    **append-type message, already taut-encoded** (the glade `Op.payload`
    pattern, D17) — opaque, NUL-safe bytes (CBOR major-type-2) that the shape
    runtime never interprets."""
    seq: int
    payload: bytes


class State(Enum):                     # D13: canonical state strings as values
    DATA = "data"
    WOULD_BLOCK = "would_block"
    EOF = "eof"                        # sealed and drained
    CLOSED = "closed"                  # D12: Close{} → closed
    FAILED = "failed"                  # D12: Close{error} → failed (+error)
    EXPIRED = "expired"                # D9: a STATE, never an exception


class ErrorCode(Enum):
    UNKNOWN_LOG = "unknown_log"        # service-level only (§7.7 / shared §3.5)
    PRODUCER_ERROR = "producer_error"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class Error:
    """A value on a failed Response — NOT a Python exception. There is no
    `canceled` code: client cancellation is `EndStream`, which needs no
    response (shared §3.1)."""
    code: ErrorCode
    message: str | None = None
```

Inputs (shared §3.2) — producer-side, stream-side, environment:

```python
@dataclass(frozen=True, slots=True)
class Push:
    payload: bytes                     # already taut-encoded append-type msg (D17); seq := head+1 (D8)

@dataclass(frozen=True, slots=True)
class Seal:
    """Finite log complete; held reads answered `eof`. Idempotent."""

@dataclass(frozen=True, slots=True)
class Close:
    error: Error | None = None         # D12: None → closed; error → failed

@dataclass(frozen=True, slots=True)
class Read:
    stream_id: str                     # D3: the correlation; D4: first use creates
    cursor: Cursor | None = None       # None ⇒ START (D8)
    max_records: int | None = None
    max_bytes: int | None = None       # payload bytes only (D10)
    timeout_ms: int | None = None      # D14: None=hold; 0=probe; >0=hold+timer

@dataclass(frozen=True, slots=True)
class EndStream:
    stream_id: str                     # D4: adapters inject on transport death

@dataclass(frozen=True, slots=True)
class TimerExpired:
    token: int                         # late/canceled tokens are no-ops

@dataclass(frozen=True, slots=True)
class Evict:
    up_to_seq: int                     # D2/D7: consumer-driven retention
```

Outputs (shared §3.3):

```python
@dataclass(frozen=True, slots=True)
class Response:
    stream_id: str                     # D3: responses addressed by stream_id
    records: tuple[Record, ...]
    next_cursor: Cursor                # ALWAYS present, even when empty
    state: State
    error: Error | None = None         # attached when state is FAILED (D12)

@dataclass(frozen=True, slots=True)
class SetTimer:
    token: int                         # D16: monotonic from 1
    ms: int

@dataclass(frozen=True, slots=True)
class CancelTimer:
    token: int

class StopReason(Enum):
    LAST_READER_GONE = "last_reader_gone"
    CLOSED = "closed"
    FAILED = "failed"

@dataclass(frozen=True, slots=True)
class ProducerStop:                    # D6: an OUTPUT message, not a callback
    reason: StopReason


# Hand-written (D17): the closed unions over the generated types.
InMsg = Push | Seal | Close | Read | EndStream | TimerExpired | Evict
OutMsg = Response | SetTimer | CancelTimer | ProducerStop
```

**Rationale for the message idiom.** One frozen slotted dataclass per message
(the tautc generator's Python output shape, D17) + a hand-written PEP 604
union, rather than a class hierarchy or a single tagged struct:

- **`match`/`case` class patterns** (Python ≥ 3.10) are the idiomatic
  closed-tagged-union dispatch; dataclasses provide `__match_args__` for free.
  With a union type, `mypy` proves exhaustiveness via `typing.assert_never` in
  the fall-through arm — a hierarchy with `isinstance` chains cannot be proven
  exhaustive. The vocabulary is closed and oracle-pinned, so a closed union is
  the honest model.
- **Frozen + slots** gives immutability (messages are values), memory economy,
  and — decisively — structural `__eq__`/`__repr__`, which makes the Phase 2
  whole-output golden a plain `==` over `list[OutMsg]` and failure diffs
  readable.
- No shared behavior exists to inherit, so a common base class would be
  ceremony; the unions are the type-level grouping.

### 7.2 The engine — `LogNode`

```python
from typing import assert_never


class StopWhen(Enum):                  # D6: construction knob
    LAST_READER = "last_reader"
    EXPLICIT_ONLY = "explicit_only"


class LogNode:
    """Pure mailbox engine, ONE per log (D1). No I/O, no clock, no executor,
    no locks — the shell owns serialization (D15). Held long-polls are engine
    state: a tail Read that cannot be answered is parked and answered when a
    later input (Push/Seal/Close/TimerExpired/EndStream) releases it. Outputs
    are a deterministic function of the input history (D16)."""

    def __init__(self, *, stop_when: StopWhen = StopWhen.EXPLICIT_ONLY) -> None:
        ...

    def handle(self, msg: InMsg) -> list[OutMsg]:
        match msg:
            case Push(payload):        return self._on_push(payload)
            case Seal():               return self._on_seal()
            case Close(error):         return self._on_close(error)
            case Read():               return self._on_read(msg)     # shared §3.4
            case EndStream(sid):       return self._on_end_stream(sid)
            case TimerExpired(token):  return self._on_timer_expired(token)
            case Evict(up_to_seq):     return self._on_evict(up_to_seq)
            case _:                    assert_never(msg)

    # Read-only accessors — permitted conveniences for in-process shells
    # (never mutating, never part of the wire contract; shared §2.1):
    @property
    def head(self) -> int: ...          # 0 when empty (D8)
    @property
    def floor(self) -> int: ...
    @property
    def min_watermark(self) -> int | None: ...   # D7: safe-eviction floor
    @property
    def stream_count(self) -> int: ...
```

**Rationale.** A plain class with one `handle` method (not a `send()`/`poll()`
pair): returning `list[OutMsg]` directly is simpler and keeps the
input→outputs causality visible in tests and oracle replay. The accessors are
properties (attribute-like reads of never-mutating state). `handle` returning a
mutable `list` (not `tuple`) is deliberate — callers immediately consume it;
messages inside are frozen.

### 7.3 Internal split — store core + session table (not a public seam)

Per D2/D3 the engine is internally split; in Python this is **two
underscore-private modules composed by `LogNode`**, invisible to consumers:

```python
# taut_shape/log/_window.py — the store core. No stream concepts.
class _Window:
    def append(self, payload: bytes) -> int: ...       # returns seq (head+1, D8)
    def scan(
        self, from_seq: int, max_records: int | None, max_bytes: int | None
    ) -> tuple[Record, ...]:
        """Records with seq > from_seq. max_bytes counts raw payload bytes
        only; forward progress: ≥1 record when any is available (D10)."""
    @property
    def head(self) -> int: ...
    @property
    def floor(self) -> int: ...
    def evict(self, up_to_seq: int) -> None: ...        # raises the floor (D2/D7)
    # plus sealed / closed / failed lifecycle flags (D12)


# taut_shape/log/_sessions.py — the session table. No byte/retention concepts.
@dataclass(slots=True)
class _Session:
    stream_id: str
    created: int                # creation-order tick — D16 emission order
    held: Read | None           # ≤1 outstanding; new Read supersedes (D5)
    timer_token: int | None     # canceled on supersede/EndStream/Close
    watermark: int              # last seq delivered (D7)
```

There is **no consumer-provided `Store` Protocol** in v2 (v1's seam is
deleted): v0 bytes live in this engine-internal bounded window and retention is
the `Evict` input (D2). Disk/network-backed stores are the shared plan §9
`ScanRequest`/`ScanResult` **additive extension** — new messages, opt-in at
construction — not a v0 surface, and not built until a consumer needs it.

### 7.4 Read resolution (shared §3.4) — where it lives

The `_on_read` arm implements the four pinned rules verbatim: data-available
batching (D10), caught-up dispatch on `timeout_ms` (D14: `None` hold / `0`
probe / `>0` hold + `SetTimer`), invalid-cursor → `expired` with the
earliest-resumable `next_cursor` (`{floor − 1}` below the floor, `{head}`
beyond head — D9), and re-readable terminal states. Multi-release emission is
in stream-creation order (D16). No new API here — it is all behavior behind
`handle`, pinned by the oracle.

### 7.5 The shell — `LogShell` (asyncio pump)

```python
import asyncio
from typing import AsyncIterator, Callable


class LogShell:
    """asyncio pump around ONE LogNode. SAME-LOOP only: every entry to the
    engine happens on one event loop from synchronous code, so cooperative
    scheduling IS the D15 serialization — no lock object. Cross-thread
    producers must hop onto the loop first (loop.call_soon_threadsafe) — a
    CONSUMER concern (the gwz bridge), never this library."""

    def __init__(
        self,
        node: LogNode,
        *,
        on_producer_stop: Callable[[ProducerStop], None] | None = None,
    ) -> None: ...

    def send(self, msg: InMsg) -> None:
        """handle() + dispatch, synchronously:
        - Response      → resolve the addressed stream's pending Future (D3);
        - SetTimer      → loop.call_later(ms/1000, …) feeding back
                          TimerExpired{token};
        - CancelTimer   → cancel the loop timer handle;
        - ProducerStop  → the on_producer_stop callback (shell-level consumer
                          wiring — the ENGINE emits a message, D6)."""

    async def request(self, read: Read) -> Response:
        """send() a Read and await its addressed Response. ≤1 outstanding
        Read per stream (D5) makes the pending map a plain
        dict[str, asyncio.Future[Response]] keyed by stream_id."""

    def new_stream_id(self) -> str:
        """Mint a fresh stream instance id (see §7.9 LQ1)."""
```

**Rationale.** v1's `Readiness` (`asyncio.Event`) is gone because v2 deleted
the concept: a held read is *engine state*, so what the shell awaits is the
**addressed `Response`**, and an `asyncio.Future` per stream is the exact
primitive — one waiter, one result, correlation by `stream_id`. Timers become
`loop.call_later`, the only place wall-clock time exists (the engine never
reads a clock, D14). `send` is synchronous by design: producers (`Push`) and
adapters (`EndStream`) need no await to feed the engine.

### 7.6 Idiomatic streaming sugar — async generator, cancellation → `EndStream`

```python
async def stream_responses(
    shell: LogShell,
    *,
    cursor: Cursor = START,
    max_records: int | None = None,
    max_bytes: int | None = None,
) -> AsyncIterator[Response]:
    """Tail one log as an async generator (shared §6.S3.2):
        issue Read (NO timeout_ms ⇒ hold indefinitely, D14)
          → await the addressed Response → yield → advance → repeat.
    Every Response is yielded — including the terminal one — so the caller
    sees eof/closed/failed (+error) and expired (with its earliest-resumable
    next_cursor, D9; whether to continue lossy is the CALLER's decision).
    Iteration ends after any non-data state. Cancellation (CancelledError at
    the await) and normal exit both send EndStream in `finally` (D4)."""
    stream_id = shell.new_stream_id()
    try:
        while True:
            resp = await shell.request(Read(
                stream_id=stream_id, cursor=cursor,
                max_records=max_records, max_bytes=max_bytes,
            ))
            cursor = resp.next_cursor
            yield resp
            if resp.state is not State.DATA:
                return
    finally:
        shell.send(EndStream(stream_id=stream_id))
```

**Rationale for the async idioms.** An **async generator** remains the most
idiomatic Python streaming surface — consumers
`async for resp in stream_responses(shell)` and get backpressure for free (the
generator only issues the next `Read` when pulled). Cancellation is delivered
by asyncio as `CancelledError` at the `await`; the `finally` maps "the consumer
dropped the iterator" onto exactly one message — `EndStream` — which the engine
turns into held-read cleanup, watermark removal, and (under
`stop_when=last_reader`) `ProducerStop` (D4/D6). This replaces v1's
"cancellation → `close(reason='canceled')`" entirely: there is no close call
from the reader side and no `Canceled` error anywhere (shared §3.1).
`WOULD_BLOCK` never appears in this loop (no `timeout_ms` is sent); probing
consumers use `shell.request(Read(..., timeout_ms=0))` directly.

### 7.7 The service — `LogService` (log_id routing)

```python
class LogService:
    """Thin multi-log router (shared §3.5). Owns LogNodes keyed by minted
    log_id; the taut companion messages (LogReadRequest, LogEndStream,
    LogReadResponse — node messages plus log_id) are its wire vocabulary,
    mapped in wire/companion.py. Producer-side inputs are node-local in v0."""

    def create(self, *, stop_when: StopWhen = StopWhen.EXPLICIT_ONLY) -> str:
        """Mint a log_id and construct its LogNode."""

    def node(self, log_id: str) -> LogNode:
        """In-process access to a node (KeyError on unknown id — programmer
        error in-process; the message path below never raises)."""

    def drop(self, log_id: str) -> None: ...

    def handle(self, log_id: str, msg: InMsg) -> list[OutMsg]:
        """Route to the node. Unknown log_id + Read ⇒
        [Response(stream_id=msg.stream_id, records=(),
                   next_cursor=msg.cursor or START, state=State.FAILED,
                   error=Error(ErrorCode.UNKNOWN_LOG))];
        unknown + EndStream ⇒ [] (no response, like the engine's no-op)."""
```

**Rationale.** `unknown_log` is service-level and message-shaped (shared §3.1)
— the remote path cannot catch exceptions, so the service answers with a
`failed` `Response` exactly as the wire would carry it; v1's `UnknownLog`
exception is deleted. The service adds no behavior beyond routing and minting
— all semantics stay in the engine where the oracle pins them.

### 7.8 v1 open questions — resolved by the pinned decisions

The v1 draft carried eight open API questions (its §7.7). D1–D16 answer six;
the shared plan's conformance section answers a seventh. For the record:

- **Q1 (`Cursor` shape)** — resolved by shared §3.1: named `Cursor{seq}`,
  `byte_offset` reserved; ship `seq`-only (as v1 leaned).
- **Q2 (`Record.seq` presence)** — **resolved by D11**: `Record` carries its
  `seq`.
- **Q3 (expired: state vs exception)** — **resolved by D9**: `expired` is a
  **state**, never thrown, and the response carries the earliest-resumable
  `next_cursor`. The v1 `Expired` exception is deleted.
- **Q4 (`max_bytes` accounting unit)** — **resolved by D10**: raw payload
  bytes only.
- **Q5 (where `close` lives / reader `close()`)** — **resolved by D1/D4**: the
  engine owns lifecycle; `Close` is a producer-side input; the reader side
  never closes anything — consumer cancellation maps to `EndStream`.
- **Q6 (one runtime object vs two cores / `LogRuntime` facade)** — **resolved
  by D1/D2/D3**: one `LogNode` engine; the reader/writer split and the
  `LogRuntime` facade dissolve; the internal split is window/session-table,
  private.
- **Q7 (CLI channel separation)** — resolved by shared §5: data =
  length-prefixed CBOR, control = OOB JSONL, two separate channels; the fd
  assignment comes from the tool-protocol spec pinned in S0.3.
- **Q8 (forward progress under `max_bytes`)** — **resolved by D10**: return at
  least one record when any is available.

Also superseded wholesale from v1 (no D-number needed — the concepts left the
design): the consumer `Store` Protocol + `InMemoryStore` (window is internal,
D2; external store is the §9 extension), `Readiness`/notify hooks (held reads
are engine state, D1), `aiter_log`-over-reader (now sugar over the shell,
§7.6), the `LogError`/`UnknownLog`/`Expired`/`Canceled` exception hierarchy
(errors are `Error` values on `failed` responses, D12; `unknown_log` is
service-level; cancellation is `EndStream`).

### 7.9 Remaining OPEN questions (genuinely Python-local)

- **LQ1 — `stream_id` minting in the shell.** `new_stream_id()`: a per-shell
  monotonic counter (`"s1"`, `"s2"`, …) or `uuid4`? Counters are deterministic
  (good for tests/snapshots) and sufficient in-process; uuids only matter when
  multiple independent minters share one node (the remote/adapter case, where
  the adapter mints anyway). *Lean: per-shell counter; adapters own their own
  scheme.*
- **LQ2 — Re-entrancy in `LogShell.send`.** If `on_producer_stop`
  synchronously `send`s (e.g. reacts to `ProducerStop` by `Close`-ing another
  input path), `handle` re-enters mid-dispatch. Options: an internal
  queue-and-drain in `send` (inputs enqueued during dispatch run after), or
  document "callbacks must not send synchronously". *Lean: queue-and-drain —
  cheap, and it preserves D16 output ordering under composition.*
- **LQ3 — A `Msg` marker base.** Pure unions (as rendered) vs. also giving
  messages an empty common base class for `isinstance` checks at framing
  boundaries. *Lean: pure unions + `assert_never`; the tool's decode path can
  validate against an explicit registry instead.*
- **LQ4 — `mypy --strict` gating.** When the advisory CI job becomes required
  (candidate: end of Phase 1, once the message/engine surfaces exist). Process,
  not API.

---

## 8. Repository structure (nominated)

```
taut-shape-py/
├─ README.md                      # what it is, pure-Python posture, quickstart
├─ LICENSE                        # MIT (mirrors taut)
├─ pyproject.toml                 # PEP 621; setuptools + setuptools-scm; dist `taut-shape`
├─ dev-docs/
│  └─ InitialPlan.md              # this document
├─ docs/
│  ├─ api/                        # API specs (see §9)
│  └─ examples/                   # worked examples (see §9)
├─ src/
│  └─ taut_shape/
│     ├─ __init__.py
│     ├─ log/                     # the pure engine (sync, no asyncio, no I/O, no clock)
│     │  ├─ _generated.py         # tautc-generated message/value types from shape_log.taut.py (vendored, D17 — do NOT hand-edit)
│     │  ├─ messages.py           # re-exports + hand-written InMsg/OutMsg unions (§7.1)
│     │  ├─ engine.py             # LogNode.handle + accessors (§7.2, §7.4)
│     │  ├─ _window.py            # store core: window/head/floor/evict (internal, §7.3)
│     │  └─ _sessions.py          # session table: held reads/timers/watermarks (internal)
│     ├─ shell/                   # the asyncio shell (the ONLY async subtree)
│     │  ├─ pump.py               # LogShell: serialize/dispatch/timers (§7.5)
│     │  └─ stream.py             # stream_responses async generator (§7.6)
│     ├─ service.py               # LogService: log_id routing, unknown_log (§7.7)
│     ├─ wire/                    # thin reuse of taut.wire (companion-msg codec glue)
│     │  └─ companion.py          # Log* encode/decode via taut.wire.codec
│     └─ tool/                    # the conformance/interop CLI
│        ├─ __init__.py
│        ├─ framing.py            # length-prefixed CBOR + OOB JSONL
│        ├─ oraclefmt.py          # message JSON ↔ dataclass mapping (oracle format)
│        └─ main.py               # gen / check / node / client
└─ tests/
   ├─ oracle/
   │  ├─ SOURCE.md                # pinned taut-shape corpus path + version
   │  └─ loader.py                # vectors() over the pinned corpus
   ├─ test_oracle.py              # whole-output == (the test_glade_folds shape)
   ├─ test_lockstep.py            # committed-corpus-in-sync gate
   ├─ test_engine_unit.py         # direct sync engine tests (handle in/out)
   ├─ test_shell.py               # pump + sugar: tail, cancel→EndStream, timers
   ├─ test_service.py             # routing + unknown_log
   ├─ test_tool.py                # subprocess driver (the test_kotlin.py shape)
   └─ __snapshots__/              # syrupy .ambr snapshots (derived surfaces only)
```

The `log/` subtree imports **no** asyncio, performs **no** I/O, and reads **no**
clock — this is the clean-room pure engine, embeddable and synchronously
drivable. `shell/` is the single async surface. `tool/` and `wire/` are the
only places that touch process I/O and the taut codec respectively.

## 9. docs/ deliverables

### docs/api/ — one spec per v2 surface
- `messages.md` — the vocabulary (§7.1): value types and every input/output
  message (tautc-generated from `shape_log.taut.py`, D17), invariants
  (`next_cursor` always present; `payload` = the method's append-type message
  already taut-encoded — D17; `Record.seq` — D11; canonical state strings —
  D13; error-as-value, no exceptions).
- `engine.md` — `LogNode.handle` (§7.2): the read-resolution rules (shared
  §3.4 / D8–D10, D14), held-read/supersede/EndStream semantics (D4/D5),
  lifecycle (D12), `ProducerStop` policy (D6), determinism (D16), the
  read-only accessors, and the "pure: no I/O/clock/locks" contract (D1/D15).
- `shell.md` — `LogShell` (§7.5): the pump, per-stream futures, timer mapping,
  `ProducerStop` routing, the **same-loop** rule + the explicit non-goal of
  cross-thread wakeup (pointing at the gwz bridge).
- `streaming.md` — `stream_responses` (§7.6): the tail loop, terminal states,
  expired-and-caller-decides (D9), cancellation → `EndStream`.
- `service.md` — `LogService` (§7.7): log_id minting/routing, `unknown_log` as
  a message, the companion-message mapping.

### docs/examples/ — runnable worked examples
- `01_engine_direct.py` — drive `LogNode.handle` synchronously: `Push` a few
  records, `Read` them back, watch a held `Read` released by a later `Push` —
  the whole protocol with no event loop; the minimal end-to-end.
- `02_resume_and_expired.py` — read a prefix, resume from `next_cursor`
  (no-dup/no-skip), then `Evict` past the cursor and show the `expired`
  response with its earliest-resumable `next_cursor` (D9).
- `03_tail_with_cancel.py` — `async for` over `stream_responses` on a live
  log, then cancel the task and show `EndStream` → `ProducerStop`
  (`stop_when=last_reader`) — single loop.
- `04_cli_interop.md` — drive `node | client` over the pipes and read the JSONL
  transcript; the local mirror of the interop matrix.

Each example is exercised by a test (snapshotting its output via `syrupy`) so
the docs cannot rot.

## 10. Phase 5 — Interop matrix participation

- **S5.1 — `node(X) ⊗ client(Y)` pairings vs. every other language.** Provide
  the `node`/`client` modes so `taut-shape`'s matrix driver can pair
  `node(py) ⊗ client(rs/ts)` and `node(rs/ts) ⊗ client(py)` over pipes;
  snapshot the resulting transcripts. No `-py`-specific logic beyond Phase 4's
  tool — this phase is participation, driven upstream. *(< 100 LOC of glue +
  matrix wiring upstream.)*

## 11. Phase 6 — `stream` shape (deferred)

Out of scope until `log` lands across all languages (per shared plan §6).
Listed only for completeness.

## 12. Non-goals (Python-specific)

- **No Rust/PyO3 binding, ever, in this repo.** Cross-runtime wakeup, cancel-
  across-PyO3, and backpressure-across-the-boundary live in the **consumer**
  (gwz's bridge) — explicitly not here (architecture §6).
- **No external store in v0.** The shared plan §9 `ScanRequest`/`ScanResult`
  extension is designed and additive; it is not built until a real consumer
  needs it.
- **No production transport/framing** beyond the CLI tool's test framing.
- **No performance optimization** — pure Python first; revisit only on
  profiling evidence (architecture §6/§9).
- **No mirroring of `taut-shape-rs`** — clean-room is a deliverable property,
  not an accident.
