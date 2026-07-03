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
from typing import BinaryIO, TextIO

from ..log import _generated as g
from ..log.engine import LogNode, StopWhen
from . import framing, oraclefmt

_USAGE = """\
taut-shape-tool (py) — Taut `log`-shape conformance/interop CLI

USAGE:
    python3 -m taut_shape.tool <MODE> [OPTIONS]

MODES:
    node      Run a LogNode behind the stdin/stdout framing
    client    Run the reading side (the cursor loop) against a node

`node` OPTIONS:
    --stop-when <last_reader|explicit>   ProducerStop policy (default: last_reader)
    --script FILE                        Inject scripted producer inputs after
                                         the k-th client input frame

`client` OPTIONS:
    --stream-id <S>       reader stream id (required)
    --from <SEQ>          starting cursor seq (required)
    --max-records <N>     per-read record cap (optional)

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


# ── node mode ────────────────────────────────────────────────────────────────

def _load_script(path: str) -> list[tuple[int, list[object]]]:
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
        msgs = [oraclefmt.json_to_msg(m) for m in entry.get("inputs", [])]
        out.append((k, msgs))
    return out


def run_node(
    args: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
) -> int:
    stop_when = StopWhen.LAST_READER            # task default: last_reader
    script_path: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--stop-when":
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
        else:
            stderr.write(f"taut-shape-tool node: unknown option {a!r}\n")
            return 2

    script = _load_script(script_path) if script_path is not None else []
    node = LogNode(log_id="log-A", stop_when=stop_when)

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
                    for out in node.handle(m):
                        framing.write_message(stdout, out)
                stdout.flush()
            else:
                remaining.append((k, msgs))
        pending[:] = remaining

    # An `after_frames: 0` injection fires before any client frame.
    _drain_injections()

    while True:
        try:
            frame = framing.read_frame(stdin)
        except framing.FrameError as fe:
            stderr.write(f"taut-shape-tool node: {fe}\n")
            stdout.flush()
            return 3
        if frame is None:
            stdout.flush()
            return 0
        try:
            msg = framing.decode_message(frame)
        except framing.FrameError as fe:
            stderr.write(f"taut-shape-tool node: {fe}\n")
            stdout.flush()
            return 3
        for out in node.handle(msg):
            framing.write_message(stdout, out)
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
    stream_id: str | None = None
    from_seq: int | None = None
    max_records: int | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--stream-id":
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
        else:
            stderr.write(f"taut-shape-tool client: unknown option {a!r}\n")
            return 2
    if stream_id is None or from_seq is None:
        stderr.write("taut-shape-tool client: --stream-id and --from are required\n")
        return 2

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
