"""``taut-shape-tool`` (py) — the conformance/interop CLI.

Modes:
  * ``node``   — run a :class:`~taut_shape.log.engine.LogNode` behind the
    stdin/stdout framing (:mod:`.framing`). Read one input frame, ``handle`` it,
    write every resulting output frame in order, flush. EOF ⇒ exit 0. A
    malformed/unknown frame ⇒ one stderr line + exit 3.
    ``--stop-when last_reader|explicit`` selects the ProducerStop policy.
    ``--script FILE`` injects scripted producer inputs after the k-th *client*
    input frame (deterministic interop driving), writing their outputs too.
  * ``client`` — the reading side (the cursor loop). ``--stream-id S --from SEQ
    [--max-records N]``. Send a held ``LogReadRequest`` (no ``timeout_ms``), read
    response frames; on ``data`` advance the cursor and re-read; on ``expired``
    resume from ``next_cursor`` (the earliest resumable position, D9) and re-read;
    on the terminal ``eof|closed|failed`` emit the final state and exit 0. Every
    received response is mirrored as an OOB JSONL line on stderr.

The framing on the data channel is byte-for-byte identical to the rs reference
(see :mod:`.framing`), so a py node/client pairs with the rs (or any) tool.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any, BinaryIO, TextIO

from ..atom import _generated as ag
from ..atom import wire as atom_wire
from ..crdt import _generated as cg
from ..crdt import wire as crdt_wire
from ..crdt.engine import CrdtNode
from ..crdt.text import project_text
from ..log import _generated as g
from ..log.engine import StopWhen
from ..stream import _generated as sg
from ..stream import wire as stream_wire
from ..swmr import _generated as wg
from ..swmr import wire as swmr_wire
from ..value import _generated as vg
from ..value import wire as value_wire
from . import framing, oraclefmt
from .atom_adapter import AtomAdapter
from .crdt_adapter import CrdtAdapter
from .log_adapter import LogAdapter
from .runtime import (
    SUPPORTED_ENGINE_SHAPES,
    AdapterDiagnostic,
    EngineEmission,
    EngineRuntime,
    require_engine_shape,
)
from .stream_adapter import StreamAdapter
from .swmr_adapter import SwmrAdapter
from .value_adapter import ValueAdapter

_USAGE = f"""\
taut-shape-tool (py) — Taut `log`-shape conformance/interop CLI

USAGE:
    python3 -m taut_shape.tool <MODE> [OPTIONS]

MODES:
    node      Run a LogNode behind the stdin/stdout framing
    client    Run the reading side (the cursor loop) against a node

`node` OPTIONS:
    --shape <NAME>                       Engine shape (default: log)
    --stop-when <last_reader|explicit>   ProducerStop policy (default: last_reader)
    --script FILE                        Inject scripted producer inputs after
                                         the k-th client input frame
    --capacity-records <N>               Stream ring capacity (default: 64)
    --max-deltas <N>                     SWMR retained-delta bound (optional)
    --max-pending <N>                    CRDT causal pending bound (default: 1024)

`client` OPTIONS:
    --shape <NAME>        Engine shape (default: log)
    --stream-id <S>       reader stream id (required)
    --from <SEQ>          starting cursor seq (required)
    --max-records <N>     per-read record cap (optional)
    --max-bytes <N>       stream per-read byte cap (optional)
    --value-id <ID>       value register id (default: v-A)
    --reads <N>           immediate value reads to issue (default: 1)
    --atom-id <ID>        atom id (default: atom-A)
    --swmr-id <ID>        SWMR object id (default: swmr-A)
    --crdt-id <ID>        CRDT object id (default: crdt-A)
    --replica-script FILE local CRDT bootstrap/operations to sync
    --epoch <N>           SWMR cursor epoch (requires --from; default: 0)
    --extra-stream-id <S> add an atom/stream reader (repeatable)
    --timeout-ms <MS>     atom/stream read timeout (optional; 0 probes)
    --reconnect-dropped   rejoin once after a stream slow-reader drop
    --pause-stream-id <S> pause this stream after its first data response
    --resume-after-data <N> resume paused streams after N data responses

SUPPORTED ENGINE SHAPES:
    {", ".join(SUPPORTED_ENGINE_SHAPES)}

FRAMING (data channel, stdin↔stdout):
    one frame = u32-LE byte length, then 1 tag byte (LogMsgType wire value),
    then the message's CBOR body. `length` covers the tag byte + body.
"""

# Response states that terminate the client loop (no more data will come).
# `expired` is NOT terminal: per D9 the node's next_cursor is the earliest
# resumable position, so the client resumes from there (see run_client).
_TERMINAL_STATES = {
    g.LogState.eof,
    g.LogState.closed,
    g.LogState.failed,
}


def _select_shape(mode: str, shape: str, stderr: TextIO) -> bool:
    try:
        require_engine_shape(shape)
        return True
    except AdapterDiagnostic as error:
        stderr.write(f"taut-shape-tool {mode}: {error.code}: {error}\n")
        return False


# ── node mode ────────────────────────────────────────────────────────────────

def _load_script(
    path: str,
    decode: Callable[[dict[str, Any]], object],
) -> list[tuple[int, list[object]]]:
    """Parse a ``--script`` file into ``[(after_frames, [messages]), ...]``.

    Format: a JSON list of ``{"after_frames": k, "inputs": [<producer msgs in
    taut jsoncodec form>]}``. Each producer message is decoded through the same
    jsoncodec path the corpus uses.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out: list[tuple[int, list[object]]] = []
    for entry in raw:
        k = int(entry["after_frames"])
        msgs = [decode(m) for m in entry.get("inputs", [])]
        out.append((k, msgs))
    return out


def run_node(
    args: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
) -> int:
    shape = "log"
    stop_when = StopWhen.LAST_READER            # task default: last_reader
    script_path: str | None = None
    capacity_records = 64
    max_deltas: int | None = None
    max_pending = 1024
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--shape":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --shape needs a NAME\n")
                return 2
            shape = args[i + 1]
            i += 2
        elif a == "--stop-when":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --stop-when needs a value\n")
                return 2
            val = args[i + 1]
            if val == "last_reader":
                stop_when = StopWhen.LAST_READER
            elif val == "explicit":
                stop_when = StopWhen.EXPLICIT_ONLY
            else:
                stderr.write(
                    "taut-shape-tool node: --stop-when expects "
                    f"last_reader|explicit, got {val!r}\n"
                )
                return 2
            i += 2
        elif a == "--script":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --script needs a FILE\n")
                return 2
            script_path = args[i + 1]
            i += 2
        elif a == "--capacity-records":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --capacity-records needs a value\n")
                return 2
            capacity_records = int(args[i + 1])
            if capacity_records <= 0:
                stderr.write("taut-shape-tool node: --capacity-records must be positive\n")
                return 2
            i += 2
        elif a == "--max-deltas":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --max-deltas needs a value\n")
                return 2
            max_deltas = int(args[i + 1])
            if max_deltas < 0:
                stderr.write("taut-shape-tool node: --max-deltas must be non-negative\n")
                return 2
            i += 2
        elif a == "--max-pending":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool node: --max-pending needs a value\n")
                return 2
            max_pending = int(args[i + 1])
            if max_pending < 0:
                stderr.write("taut-shape-tool node: --max-pending must be non-negative\n")
                return 2
            i += 2
        else:
            stderr.write(f"taut-shape-tool node: unknown option {a!r}\n")
            return 2

    if not _select_shape("node", shape, stderr):
        return 2
    runtime: EngineRuntime[Any, Any, Any, Any]
    decode_script: Callable[[dict[str, Any]], object]
    write_message: Callable[[BinaryIO, Any], None]
    if shape in ("crdt", "text_crdt"):
        runtime = EngineRuntime(CrdtAdapter(max_pending=max_pending))
        decode_script = crdt_wire.json_to_input
        write_message = lambda stream, message: framing.write_frame(
            stream, *crdt_wire.encode_message(message)
        )
    elif shape == "log":
        runtime = EngineRuntime(LogAdapter(stop_when=stop_when))
        decode_script = oraclefmt.json_to_msg
        write_message = framing.write_message
    elif shape == "value":
        runtime = EngineRuntime(ValueAdapter())
        decode_script = value_wire.json_to_input
        write_message = lambda stream, message: value_wire.write_output(stream, message)
    elif shape == "stream":
        runtime = EngineRuntime(
            StreamAdapter(
                capacity_records=capacity_records,
                stop_when=stop_when,
            )
        )
        decode_script = stream_wire.json_to_input
        write_message = lambda stream, message: stream_wire.write_output(stream, message)
    elif shape in ("swmr", "snapshot_delta"):
        runtime = EngineRuntime(
            SwmrAdapter(
                stop_when=stop_when,
                max_deltas=max_deltas,
                expire_profile=shape == "snapshot_delta",
            )
        )
        decode_script = swmr_wire.json_to_input
        write_message = lambda stream, message: swmr_wire.write_output(stream, message)
    else:
        runtime = EngineRuntime(AtomAdapter(stop_when=stop_when))
        decode_script = atom_wire.json_to_input
        write_message = lambda stream, message: atom_wire.write_output(stream, message)
    script = (
        _load_script(script_path, decode_script) if script_path is not None else []
    )

    return _drive_node(stdin, stdout, stderr, runtime, script, write_message)


def _drive_node(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    runtime: EngineRuntime[Any, Any, Any, Any],
    script: list[tuple[int, list[object]]],
    write_message: Callable[[BinaryIO, Any], None],
) -> int:

    def _write(emissions: list[EngineEmission[object, object]]) -> None:
        for emission in emissions:
            write_message(stdout, emission.effect.frame)

    # `after_frames: k` fires once, after the k-th client input frame has been
    # processed. Bucket injections by their trigger count for a deterministic,
    # order-preserving sweep after each client frame.
    pending = list(script)
    client_frames = 0

    def _drain_injections() -> None:
        remaining: list[tuple[int, list[object]]] = []
        for k, msgs in pending:
            if k == client_frames:
                for m in msgs:
                    _write(runtime.dispatch(m))
                stdout.flush()
            else:
                remaining.append((k, msgs))
        pending[:] = remaining

    # An `after_frames: 0` injection fires before any client frame.
    _drain_injections()

    while True:
        try:
            frame = framing.read_frame(stdin)
        except (framing.FrameError, AdapterDiagnostic) as fe:
            stderr.write(f"taut-shape-tool node: {fe}\n")
            stdout.flush()
            return 3
        if frame is None:
            _write(runtime.finish())
            stdout.flush()
            return 0
        try:
            _write(runtime.process(frame))
        except (framing.FrameError, AdapterDiagnostic) as fe:
            stderr.write(f"taut-shape-tool node: {fe}\n")
            stdout.flush()
            return 3
        stdout.flush()
        client_frames += 1
        _drain_injections()


# ── client mode ──────────────────────────────────────────────────────────────

def run_client(
    args: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
) -> int:
    shape = "log"
    stream_id: str | None = None
    from_seq: int | None = None
    max_records: int | None = None
    value_id = "v-A"
    atom_id = "atom-A"
    swmr_id = "swmr-A"
    crdt_id = "crdt-A"
    replica_script: str | None = None
    epoch: int | None = None
    extra_stream_ids: list[str] = []
    atom_timeout_ms: int | None = None
    max_bytes: int | None = None
    reconnect_dropped = False
    pause_stream_ids: set[str] = set()
    resume_after_data: int | None = None
    reads = 1
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--shape":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --shape needs a NAME\n")
                return 2
            shape = args[i + 1]
            i += 2
        elif a == "--stream-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --stream-id needs a value\n")
                return 2
            stream_id = args[i + 1]
            i += 2
        elif a == "--from":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --from needs a value\n")
                return 2
            from_seq = int(args[i + 1])
            i += 2
        elif a == "--max-records":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --max-records needs a value\n")
                return 2
            max_records = int(args[i + 1])
            i += 2
        elif a == "--max-bytes":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --max-bytes needs a value\n")
                return 2
            max_bytes = int(args[i + 1])
            if max_bytes < 0:
                stderr.write("taut-shape-tool client: --max-bytes must be non-negative\n")
                return 2
            i += 2
        elif a == "--value-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --value-id needs a value\n")
                return 2
            value_id = args[i + 1]
            i += 2
        elif a == "--reads":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --reads needs a value\n")
                return 2
            reads = int(args[i + 1])
            if reads <= 0:
                stderr.write("taut-shape-tool client: --reads must be positive\n")
                return 2
            i += 2
        elif a == "--atom-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --atom-id needs a value\n")
                return 2
            atom_id = args[i + 1]
            i += 2
        elif a == "--swmr-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --swmr-id needs a value\n")
                return 2
            swmr_id = args[i + 1]
            i += 2
        elif a == "--crdt-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --crdt-id needs a value\n")
                return 2
            crdt_id = args[i + 1]
            i += 2
        elif a == "--replica-script":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --replica-script needs a FILE\n")
                return 2
            replica_script = args[i + 1]
            i += 2
        elif a == "--epoch":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --epoch needs a value\n")
                return 2
            epoch = int(args[i + 1])
            if epoch < 0:
                stderr.write("taut-shape-tool client: --epoch must be non-negative\n")
                return 2
            i += 2
        elif a == "--extra-stream-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --extra-stream-id needs a value\n")
                return 2
            extra_stream_ids.append(args[i + 1])
            i += 2
        elif a == "--timeout-ms":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --timeout-ms needs a value\n")
                return 2
            atom_timeout_ms = int(args[i + 1])
            if atom_timeout_ms < 0:
                stderr.write("taut-shape-tool client: --timeout-ms must be non-negative\n")
                return 2
            i += 2
        elif a == "--reconnect-dropped":
            reconnect_dropped = True
            i += 1
        elif a == "--pause-stream-id":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --pause-stream-id needs a value\n")
                return 2
            pause_stream_ids.add(args[i + 1])
            i += 2
        elif a == "--resume-after-data":
            if i + 1 >= len(args):
                stderr.write("taut-shape-tool client: --resume-after-data needs a value\n")
                return 2
            resume_after_data = int(args[i + 1])
            if resume_after_data <= 0:
                stderr.write("taut-shape-tool client: --resume-after-data must be positive\n")
                return 2
            i += 2
        else:
            stderr.write(f"taut-shape-tool client: unknown option {a!r}\n")
            return 2
    if not _select_shape("client", shape, stderr):
        return 2
    if stream_id is None:
        stderr.write("taut-shape-tool client: --stream-id is required\n")
        return 2
    if shape in ("crdt", "text_crdt"):
        if replica_script is None:
            stderr.write("taut-shape-tool client: --replica-script is required for CRDT\n")
            return 2
        return _run_crdt_client(
            stdin,
            stdout,
            stderr,
            crdt_id=crdt_id,
            stream_id=stream_id,
            replica_script=replica_script,
            text_profile=shape == "text_crdt",
        )
    if shape == "value":
        return _run_value_client(
            stdin,
            stdout,
            stderr,
            value_id=value_id,
            stream_id=stream_id,
            reads=reads,
        )
    if shape == "stream":
        return _run_stream_client(
            stdin,
            stdout,
            stderr,
            stream_ids=[stream_id, *extra_stream_ids],
            max_records=max_records,
            max_bytes=max_bytes,
            timeout_ms=atom_timeout_ms,
            reconnect_dropped=reconnect_dropped,
            pause_stream_ids=pause_stream_ids,
            resume_after_data=resume_after_data,
        )
    if shape in ("swmr", "snapshot_delta"):
        if epoch is not None and from_seq is None:
            stderr.write("taut-shape-tool client: --epoch requires --from\n")
            return 2
        if from_seq is not None and from_seq < 0:
            stderr.write("taut-shape-tool client: --from must be non-negative for swmr\n")
            return 2
        return _run_swmr_client(
            stdin,
            stdout,
            stderr,
            swmr_id=swmr_id,
            stream_ids=[stream_id, *extra_stream_ids],
            initial_cursor=None
            if from_seq is None
            else wg.SwmrCursor(seq=from_seq, epoch=epoch or 0),
            timeout_ms=atom_timeout_ms,
            expire_profile=shape == "snapshot_delta",
        )
    if from_seq is None:
        stderr.write(f"taut-shape-tool client: --from is required for {shape}\n")
        return 2
    if shape == "atom":
        return _run_atom_client(
            stdin,
            stdout,
            stderr,
            atom_id=atom_id,
            stream_ids=[stream_id, *extra_stream_ids],
            from_version=from_seq,
            timeout_ms=atom_timeout_ms,
        )

    cursor_seq = from_seq

    def _send_read() -> None:
        # Held read: no timeout_ms (indefinite hold on the node until data or a
        # terminal state). log_id is the shared "log-A" the node echoes back.
        req = g.LogReadRequest(
            log_id="log-A",
            stream_id=stream_id,
            cursor=g.LogCursor(seq=cursor_seq),
            max_records=max_records,
            max_bytes=None,
            timeout_ms=None,
        )
        framing.write_message(stdout, req)
        stdout.flush()

    _send_read()

    while True:
        try:
            frame = framing.read_frame(stdin)
        except framing.FrameError as fe:
            stderr.write(f"taut-shape-tool client: {fe}\n")
            return 3
        if frame is None:
            # Node hung up before a terminal response: emit final state and exit.
            stderr.write(json.dumps({"final": "eof_channel", "next_seq": cursor_seq}) + "\n")
            stderr.flush()
            return 0
        try:
            msg = framing.decode_message(frame)
        except framing.FrameError as fe:
            stderr.write(f"taut-shape-tool client: {fe}\n")
            return 3
        if not isinstance(msg, g.LogReadResponse):
            # The node addresses the client only with read responses; anything
            # else on this channel is ignored (mirrored for the transcript).
            stderr.write(json.dumps(oraclefmt.msg_to_json(msg)) + "\n")
            stderr.flush()
            continue

        # OOB transcript: every received response, one JSONL object per line.
        stderr.write(json.dumps(oraclefmt.msg_to_json(msg)) + "\n")
        stderr.flush()

        state = msg.state
        if state is g.LogState.data:
            cursor_seq = msg.next_cursor.seq
            _send_read()
            continue
        if state is g.LogState.would_block:
            # Held reads never answer would_block; a probe answer just re-reads.
            _send_read()
            continue
        if state is g.LogState.expired:
            # A cursor invalidated by eviction is a state, not an error (D9): the
            # node's next_cursor is the earliest resumable position. Resume from
            # there rather than exiting, so an evict mid-stream is survivable.
            cursor_seq = msg.next_cursor.seq
            _send_read()
            continue
        if state in _TERMINAL_STATES:
            stderr.write(
                json.dumps({"final": state.name, "next_seq": msg.next_cursor.seq}) + "\n"
            )
            stderr.flush()
            return 0
        _send_read()


def _run_value_client(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    value_id: str,
    stream_id: str,
    reads: int,
) -> int:
    def send_read() -> None:
        value_wire.write_read(
            stdout,
            vg.ValueReadRequest(value_id=value_id, stream_id=stream_id),
        )
        stdout.flush()

    send_read()
    responses = 0
    while True:
        try:
            frame = framing.read_frame(stdin)
            if frame is None:
                stderr.write(json.dumps({"type": "client_final", "state": "eof"}) + "\n")
                return 0
            message = value_wire.decode_output(frame)
        except framing.FrameError as error:
            stderr.write(f"taut-shape-tool value client: {error}\n")
            return 3
        stderr.write(json.dumps(value_wire.output_to_json(message)) + "\n")
        stderr.flush()
        if isinstance(message, vg.ValueDiagnostic):
            continue
        responses += 1
        if responses == reads:
            stderr.write(json.dumps({"type": "client_final", "state": "done"}) + "\n")
            stderr.flush()
            return 0
        send_read()


def _run_atom_client(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    atom_id: str,
    stream_ids: list[str],
    from_version: int,
    timeout_ms: int | None,
) -> int:
    versions = {stream_id: from_version for stream_id in stream_ids}
    active = set(stream_ids)

    def send_read(stream_id: str) -> None:
        atom_wire.write_read(
            stdout,
            ag.AtomReadRequest(
                atom_id=atom_id,
                stream_id=stream_id,
                version=ag.AtomVersion(version=versions[stream_id]),
                timeout_ms=timeout_ms,
            ),
        )
        stdout.flush()

    for stream_id in stream_ids:
        send_read(stream_id)
    while True:
        try:
            frame = framing.read_frame(stdin)
            if frame is None:
                stderr.write(json.dumps({"type": "client_final", "state": "eof_channel"}) + "\n")
                return 0
            message = atom_wire.decode_output(frame)
        except framing.FrameError as error:
            stderr.write(f"taut-shape-tool atom client: {error}\n")
            return 3
        stderr.write(json.dumps(atom_wire.output_to_json(message)) + "\n")
        stderr.flush()
        if not isinstance(message, ag.AtomReadResponse):
            continue
        if message.stream_id not in active:
            stderr.write(
                "taut-shape-tool atom client: response for inactive stream "
                f"{message.stream_id!r}\n"
            )
            return 3
        versions[message.stream_id] = message.next_version.version
        if message.state is ag.AtomState.data:
            send_read(message.stream_id)
            continue
        if message.state is ag.AtomState.would_block:
            active.remove(message.stream_id)
        if message.state in (ag.AtomState.eof, ag.AtomState.closed, ag.AtomState.failed):
            active.remove(message.stream_id)
        if not active:
            stderr.write(json.dumps({"type": "client_final", "state": "done"}) + "\n")
            stderr.flush()
            return 0


def _run_stream_client(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    stream_ids: list[str],
    max_records: int | None,
    max_bytes: int | None,
    timeout_ms: int | None,
    reconnect_dropped: bool,
    pause_stream_ids: set[str],
    resume_after_data: int | None,
) -> int:
    active = set(stream_ids)
    paused: set[str] = set()
    reconnected: set[str] = set()
    data_responses = 0

    def send_read(stream_id: str) -> None:
        stream_wire.write_read(
            stdout,
            sg.StreamReadRequest(
                stream_id=stream_id,
                max_records=max_records,
                max_bytes=max_bytes,
                timeout_ms=timeout_ms,
            ),
        )
        stdout.flush()

    for stream_id in stream_ids:
        send_read(stream_id)
    while active:
        try:
            frame = framing.read_frame(stdin)
            if frame is None:
                stderr.write(json.dumps({"type": "client_final", "state": "eof_channel"}) + "\n")
                return 0
            message = stream_wire.decode_output(frame)
        except framing.FrameError as error:
            stderr.write(f"taut-shape-tool stream client: {error}\n")
            return 3
        stderr.write(json.dumps(stream_wire.output_to_json(message)) + "\n")
        stderr.flush()
        if not isinstance(message, sg.StreamReadResponse):
            continue
        if message.stream_id not in active:
            stderr.write(
                "taut-shape-tool stream client: response for inactive stream "
                f"{message.stream_id!r}\n"
            )
            return 3
        if message.state is sg.StreamState.data:
            data_responses += 1
            if message.stream_id in pause_stream_ids:
                paused.add(message.stream_id)
            else:
                send_read(message.stream_id)
            if resume_after_data is not None and data_responses >= resume_after_data:
                for paused_id in sorted(paused):
                    send_read(paused_id)
                paused.clear()
            continue
        if (
            message.state is sg.StreamState.dropped
            and reconnect_dropped
            and message.stream_id not in reconnected
        ):
            reconnected.add(message.stream_id)
            send_read(message.stream_id)
            continue
        if message.state in (
            sg.StreamState.would_block,
            sg.StreamState.eof,
            sg.StreamState.closed,
            sg.StreamState.failed,
            sg.StreamState.dropped,
        ):
            active.remove(message.stream_id)
    stderr.write(json.dumps({"type": "client_final", "state": "done"}) + "\n")
    stderr.flush()
    return 0


def _run_swmr_client(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    swmr_id: str,
    stream_ids: list[str],
    initial_cursor: wg.SwmrCursor | None,
    timeout_ms: int | None,
    expire_profile: bool,
) -> int:
    active = set(stream_ids)
    cursors = {stream_id: initial_cursor for stream_id in stream_ids}

    def send_read(stream_id: str) -> None:
        swmr_wire.write_read(
            stdout,
            wg.SwmrReadRequest(
                swmr_id=swmr_id,
                stream_id=stream_id,
                cursor=cursors[stream_id],
                timeout_ms=timeout_ms,
            ),
        )
        stdout.flush()

    for stream_id in stream_ids:
        send_read(stream_id)
    while active:
        try:
            frame = framing.read_frame(stdin)
            if frame is None:
                stderr.write(
                    json.dumps({"type": "client_final", "state": "eof_channel"})
                    + "\n"
                )
                return 0
            message = swmr_wire.decode_output(frame)
        except framing.FrameError as error:
            stderr.write(f"taut-shape-tool swmr client: {error}\n")
            return 3
        if not isinstance(message, wg.SwmrReadResponse):
            stderr.write(json.dumps(swmr_wire.output_to_json(message)) + "\n")
            stderr.flush()
            continue
        if message.stream_id not in active:
            stderr.write(
                "taut-shape-tool swmr client: response for inactive stream "
                f"{message.stream_id!r}\n"
            )
            return 3
        if expire_profile and message.state is wg.SwmrState.reset:
            reason = {
                wg.SwmrResetReason.retention_exceeded: "retention_expired",
                wg.SwmrResetReason.invalid_resume_seq: "invalid_cursor",
                wg.SwmrResetReason.producer_requested: "source_changed",
                None: "source_changed",
            }[message.reset_reason]
            stderr.write(
                json.dumps(
                    {
                        "type": "refresh_required",
                        "swmr_id": message.swmr_id,
                        "stream_id": message.stream_id,
                        "reason": reason,
                    }
                )
                + "\n"
            )
            stderr.flush()
            active.remove(message.stream_id)
            continue
        stderr.write(json.dumps(swmr_wire.output_to_json(message)) + "\n")
        stderr.flush()
        if message.state in (wg.SwmrState.data, wg.SwmrState.reset):
            cursors[message.stream_id] = message.next_cursor
            send_read(message.stream_id)
            continue
        if message.state in (
            wg.SwmrState.would_block,
            wg.SwmrState.eof,
            wg.SwmrState.closed,
            wg.SwmrState.failed,
        ):
            active.remove(message.stream_id)
    stderr.write(json.dumps({"type": "client_final", "state": "done"}) + "\n")
    stderr.flush()
    return 0


def _run_crdt_client(
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    crdt_id: str,
    stream_id: str,
    replica_script: str,
    text_profile: bool,
) -> int:
    with open(replica_script, encoding="utf-8") as source:
        raw_inputs = json.load(source)
    node = CrdtNode()
    diagnostics: set[tuple[str, str | None, int | None]] = set()

    def collect(outputs: list[cg.CrdtReadResponse | cg.CrdtDiagnostic]) -> None:
        for output in outputs:
            if isinstance(output, cg.CrdtDiagnostic):
                diagnostics.add((output.code.name, output.origin, output.seq))

    for raw in raw_inputs:
        input_ = crdt_wire.json_to_input(raw)
        if not isinstance(input_, (cg.CrdtApply, cg.CrdtInstallBootstrap)):
            stderr.write("taut-shape-tool CRDT client: replica script accepts only apply/bootstrap\n")
            return 2
        collect(node.handle(input_))
        tag, body = crdt_wire.encode_message(input_)
        framing.write_frame(stdout, tag, body)
    stdout.flush()

    def send_read() -> None:
        tag, body = crdt_wire.encode_message(
            cg.CrdtReadRequest(crdt_id=crdt_id, stream_id=stream_id, cursor=node.clock)
        )
        framing.write_frame(stdout, tag, body)
        stdout.flush()

    send_read()
    while True:
        try:
            frame = framing.read_frame(stdin)
            if frame is None:
                break
            output = crdt_wire.decode_output(frame)
        except framing.FrameError as error:
            stderr.write(f"taut-shape-tool CRDT client: {error}\n")
            return 3
        stderr.write(json.dumps(crdt_wire.message_to_json(output)) + "\n")
        stderr.flush()
        if isinstance(output, cg.CrdtDiagnostic):
            diagnostics.add((output.code.name, output.origin, output.seq))
            continue
        if output.bootstrap is not None:
            collect(node.handle(cg.CrdtInstallBootstrap(output.bootstrap)))
        for operation in output.ops:
            collect(node.handle(cg.CrdtApply(operation)))
        if output.state in (cg.CrdtState.data, cg.CrdtState.bootstrap_required):
            send_read()
            continue
        break
    final: dict[str, Any] = {
        "type": "replica_final",
        "clock": {"entries": [{"origin": entry.origin, "seq": str(entry.seq)} for entry in node.clock.entries]},
        "ops": [crdt_wire.message_to_json(cg.CrdtApply(operation))["op"] for operation in node.operations],
        "diagnostics": [
            {"code": code, "origin": origin, "seq": None if seq is None else str(seq)}
            for code, origin, seq in sorted(diagnostics, key=lambda row: (row[0], row[1] or "", row[2] or -1))
        ],
    }
    if text_profile:
        projection = project_text(node)
        final["text"] = projection.text
        final["text_diagnostics"] = list(projection.diagnostics)
    stderr.write(json.dumps(final) + "\n")
    stderr.flush()
    return 0


# ── entry ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.stderr.write(_USAGE)
        return 2
    mode, rest = args[0], args[1:]
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    stderr = sys.stderr
    if mode == "node":
        return run_node(rest, stdin, stdout, stderr)
    if mode == "client":
        return run_client(rest, stdin, stdout, stderr)
    sys.stderr.write(f"taut-shape-tool: unknown mode {mode!r}\n\n")
    sys.stderr.write(_USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
