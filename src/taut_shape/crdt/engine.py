"""Payload-agnostic causal op-set engine implementing ``crdt.oracle/v1``."""

from __future__ import annotations

from typing import TypeAlias

from . import _generated as g

CrdtInput: TypeAlias = g.CrdtApply | g.CrdtInstallBootstrap | g.CrdtSeal | g.CrdtClose | g.CrdtReadRequest
CrdtOutput: TypeAlias = g.CrdtReadResponse | g.CrdtDiagnostic
_Key = tuple[str, int]


def _clock_map(clock: g.CrdtClock) -> dict[str, int] | None:
    result: dict[str, int] = {}
    previous: str | None = None
    for entry in clock.entries:
        if not entry.origin or entry.seq <= 0 or (previous is not None and entry.origin <= previous):
            return None
        previous = entry.origin
        result[entry.origin] = entry.seq
    return result


def _clock(clock: dict[str, int]) -> g.CrdtClock:
    return g.CrdtClock([g.CrdtClockEntry(origin, seq) for origin, seq in sorted(clock.items()) if seq > 0])


def _key(op: g.CrdtOp) -> _Key:
    return op.origin, op.seq


def _variant(op: g.CrdtOp) -> tuple[tuple[tuple[str, int], ...], bytes]:
    deps = _clock_map(op.deps)
    assert deps is not None
    return tuple(sorted(deps.items())), op.payload


def _copy_op(op: g.CrdtOp) -> g.CrdtOp:
    return g.CrdtOp(op.origin, op.seq, g.CrdtClock(list(op.deps.entries)), bytes(op.payload))


class CrdtNode:
    """Immediate anti-entropy mailbox with bounded causal buffering."""

    def __init__(self, *, max_pending: int = 1024) -> None:
        if max_pending < 0:
            raise ValueError("max_pending must be non-negative")
        self.max_pending = max_pending
        self._clock: dict[str, int] = {}
        self._floor: dict[str, int] = {}
        self._bootstrap: g.CrdtBootstrap | None = None
        self._ops: dict[_Key, g.CrdtOp] = {}
        self._integrated: set[_Key] = set()
        self._equivocated: set[_Key] = set()
        self._sealed = False
        self._closed = False
        self._error: g.CrdtError | None = None

    @property
    def clock(self) -> g.CrdtClock:
        return _clock(self._clock)

    @property
    def bootstrap(self) -> g.CrdtBootstrap | None:
        return self._bootstrap

    @property
    def operations(self) -> tuple[g.CrdtOp, ...]:
        return tuple(_copy_op(self._ops[key]) for key in sorted(self._integrated))

    @property
    def equivocations(self) -> tuple[_Key, ...]:
        return tuple(sorted(self._equivocated))

    def handle(self, message: CrdtInput) -> list[CrdtOutput]:
        if isinstance(message, g.CrdtApply):
            return self._apply(message.op)
        if isinstance(message, g.CrdtInstallBootstrap):
            return self._install_bootstrap(message.bootstrap)
        if isinstance(message, g.CrdtSeal):
            if not self._closed:
                self._sealed = True
            return []
        if isinstance(message, g.CrdtClose):
            if not self._closed:
                self._closed = True
                self._error = message.error
            return []
        if isinstance(message, g.CrdtReadRequest):
            return [self._read(message)]
        raise TypeError(f"unsupported CRDT input {type(message).__name__}")

    def _diag(self, code: g.CrdtDiagCode, op: g.CrdtOp | None = None) -> g.CrdtDiagnostic:
        return g.CrdtDiagnostic(
            severity=g.CrdtSeverity.warn if code is g.CrdtDiagCode.apply_after_terminal else g.CrdtSeverity.error,
            code=code,
            origin=None if op is None else op.origin,
            seq=None if op is None else op.seq,
        )

    def _valid(self, op: g.CrdtOp) -> bool:
        deps = _clock_map(op.deps)
        return bool(op.origin) and op.seq > 0 and deps is not None and deps.get(op.origin, 0) < op.seq

    def _apply(self, op: g.CrdtOp) -> list[CrdtOutput]:
        if self._sealed or self._closed:
            return [self._diag(g.CrdtDiagCode.apply_after_terminal, op)]
        if not self._valid(op):
            return [self._diag(g.CrdtDiagCode.invalid_operation, op)]
        key = _key(op)
        if op.seq <= self._floor.get(op.origin, 0):
            return []
        previous = self._ops.get(key)
        if previous is not None:
            if previous == op:
                return []
            outputs: list[CrdtOutput] = []
            if key not in self._equivocated:
                self._equivocated.add(key)
                outputs.append(self._diag(g.CrdtDiagCode.equivocation, op))
            if _variant(op) < _variant(previous):
                self._ops[key] = _copy_op(op)
            self._drain()
            return outputs
        pending = len(self._ops) - len(self._integrated)
        if not self._ready(op) and pending >= self.max_pending:
            return [self._diag(g.CrdtDiagCode.pending_bound_exceeded, op)]
        self._ops[key] = _copy_op(op)
        self._drain()
        return []

    def _ready(self, op: g.CrdtOp) -> bool:
        if op.seq > self._clock.get(op.origin, 0) + 1:
            return False
        deps = _clock_map(op.deps)
        assert deps is not None
        return all(self._clock.get(origin, 0) >= seq for origin, seq in deps.items())

    def _drain(self) -> None:
        while True:
            ready = sorted(
                key for key, op in self._ops.items() if key not in self._integrated and self._ready(op)
            )
            if not ready:
                return
            for key in ready:
                self._integrated.add(key)
                self._clock[key[0]] = max(self._clock.get(key[0], 0), key[1])

    def _install_bootstrap(self, bootstrap: g.CrdtBootstrap) -> list[CrdtOutput]:
        if self._sealed or self._closed:
            return [self._diag(g.CrdtDiagCode.apply_after_terminal)]
        parsed = _clock_map(bootstrap.clock)
        if parsed is None:
            return [self._diag(g.CrdtDiagCode.invalid_operation)]
        if self._bootstrap == bootstrap:
            return []
        if self._bootstrap is not None or self._ops:
            return [self._diag(g.CrdtDiagCode.bootstrap_conflict)]
        self._bootstrap = g.CrdtBootstrap(g.CrdtClock(list(bootstrap.clock.entries)), bytes(bootstrap.state))
        self._floor = dict(parsed)
        self._clock = dict(parsed)
        return []

    def _read(self, request: g.CrdtReadRequest) -> g.CrdtReadResponse:
        cursor = {} if request.cursor is None else _clock_map(request.cursor)
        if cursor is None or any(seq > self._clock.get(origin, 0) for origin, seq in cursor.items()):
            return self._response(request, g.CrdtState.invalid_cursor)
        below_floor = any(cursor.get(origin, 0) < seq for origin, seq in self._floor.items())
        if request.cursor is not None and below_floor:
            bootstrap = self._bootstrap
            base = self._floor
            state = g.CrdtState.bootstrap_required
        else:
            bootstrap = self._bootstrap if request.cursor is None else None
            base = cursor
            state = g.CrdtState.data
        ops = [_copy_op(self._ops[key]) for key in sorted(self._integrated) if key[1] > base.get(key[0], 0)]
        if bootstrap is not None or ops:
            return self._response(request, state, bootstrap=bootstrap, ops=ops)
        if self._closed:
            return self._response(
                request,
                g.CrdtState.failed if self._error is not None else g.CrdtState.closed,
                error=self._error,
            )
        if self._sealed:
            return self._response(request, g.CrdtState.eof)
        return self._response(request, g.CrdtState.empty)

    def _response(
        self,
        request: g.CrdtReadRequest,
        state: g.CrdtState,
        *,
        bootstrap: g.CrdtBootstrap | None = None,
        ops: list[g.CrdtOp] | None = None,
        error: g.CrdtError | None = None,
    ) -> g.CrdtReadResponse:
        return g.CrdtReadResponse(
            crdt_id=request.crdt_id,
            stream_id=request.stream_id,
            bootstrap=bootstrap,
            ops=[] if ops is None else ops,
            next_cursor=self.clock,
            state=state,
            error=error,
        )
