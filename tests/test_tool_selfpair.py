"""Self-pair the tool over real pipes: a py ``node`` serves a py ``client``.

Data channel: crossed pipes carrying ``u32-LE len | tag byte | CBOR`` frames
(byte-for-byte the rs reference framing). The client owns stdin; a ``--script``
drives the producer side of the node deterministically. We assert on the
client's OOB JSONL transcript (stderr) — the records it observed, in order.

Also covers the in-process framing round-trip and node pump directly (no spawn).
"""

from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from taut_shape.log import _generated as g
from taut_shape.log.engine import LogNode, StopWhen
import importlib

from taut_shape.tool import framing

# `taut_shape.tool.__init__` re-exports the `main` *function*, which shadows the
# `main` *submodule* on the package namespace. Reach the module explicitly.
tool_main = importlib.import_module("taut_shape.tool.main")

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
_TAUT_SRC = _REPO.parent / "taut" / "src"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    pp = os.pathsep.join([str(_SRC), str(_TAUT_SRC), env.get("PYTHONPATH", "")])
    env["PYTHONPATH"] = pp.rstrip(os.pathsep)
    return env


# ── in-process framing / message round-trip ─────────────────────────────────

def test_frame_roundtrip_bytes() -> None:
    buf = io.BytesIO()
    framing.write_message(buf, g.LogPush(payload=b"hello"))
    buf.seek(0)
    frame = framing.read_frame(buf)
    assert frame is not None
    # tag byte == LogMsgType.push wire value; body is deterministic CBOR.
    assert frame.tag == g.LogMsgType.push.value
    msg = framing.decode_message(frame)
    assert isinstance(msg, g.LogPush) and msg.payload == b"hello"
    # exact wire bytes: u32-LE len (1 tag + 8 body) | tag 0 | cbor(a1 01 45 hello)
    assert buf.getvalue() == bytes([0x09, 0, 0, 0, 0x00]) + bytes.fromhex("a1014568656c6c6f")


def test_seal_empty_map_body() -> None:
    tag, body = framing.encode_message(g.LogSeal())
    assert tag == g.LogMsgType.seal.value
    assert body == bytes.fromhex("a0")            # empty CBOR map, like the rs ref


def test_read_frame_clean_eof() -> None:
    assert framing.read_frame(io.BytesIO(b"")) is None
    # truncated tail (partial length prefix) tolerated as clean EOF
    assert framing.read_frame(io.BytesIO(b"\x07\x00")) is None


def test_read_frame_unknown_tag() -> None:
    raw = bytes([2, 0, 0, 0, 99, 0xA0])
    frame = framing.read_frame(io.BytesIO(raw))
    assert frame is not None and frame.tag == 99
    with pytest.raises(framing.UnknownMessageTagError):
        framing.decode_message(frame)


# ── in-process node pump ─────────────────────────────────────────────────────

def test_node_pump_push_then_read() -> None:
    """Feed a push then a probe read straight through run_node; assert the
    response frame comes back with the record."""
    inp = io.BytesIO()
    framing.write_message(inp, g.LogPush(payload=b"x"))
    framing.write_message(
        inp,
        g.LogReadRequest(
            log_id="log-A", stream_id="s1", cursor=g.LogCursor(seq=0),
            max_records=None, max_bytes=None, timeout_ms=0,
        ),
    )
    inp.seek(0)
    out = io.BytesIO()
    code = tool_main.run_node(["--shape", "log"], inp, out, sys.stderr)
    assert code == 0
    out.seek(0)
    frame = framing.read_frame(out)
    assert frame is not None
    resp = framing.decode_message(frame)
    assert isinstance(resp, g.LogReadResponse)
    assert resp.state is g.LogState.data
    assert [r.seq for r in resp.records] == [1]
    assert resp.records[0].payload == b"x"
    assert framing.read_frame(out) is None        # no further frames


# ── spawned self-pair over crossed pipes ─────────────────────────────────────

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _spawn(mode_args: list[str], **popen_kw):  # type: ignore[no-untyped-def]
    return subprocess.Popen(
        [sys.executable, "-m", "taut_shape.tool", *mode_args],
        env=_env(),
        **popen_kw,
    )


def test_selfpair_push_seal_drain(tmp_path: Path) -> None:
    """node(py) <== crossed pipes ==> client(py).

    A --script pushes three records after the client's first read frame, then
    seals. The client drains all three (state=data) and finishes on eof.
    """
    script = [
        {
            "after_frames": 1,
            "inputs": [
                {"type": "push", "payload": _b64(b"one")},
                {"type": "push", "payload": _b64(b"two")},
                {"type": "push", "payload": _b64(b"three")},
                {"type": "seal"},
            ],
        }
    ]
    script_path = tmp_path / "script.json"
    script_path.write_text(json.dumps(script))

    node = _spawn(
        ["node", "--shape", "log", "--stop-when", "last_reader", "--script", str(script_path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    client = _spawn(
        ["client", "--shape", "log", "--stream-id", "s1", "--from", "0"],
        stdin=node.stdout, stdout=node.stdin, stderr=subprocess.PIPE,
    )
    # Parent doesn't need the crossed ends now that both children hold them.
    assert node.stdout is not None and node.stdin is not None
    node.stdout.close()
    node.stdin.close()

    client_err = client.communicate(timeout=20)[1].decode()
    client_rc = client.returncode
    node.wait(timeout=20)

    lines = [json.loads(x) for x in client_err.splitlines() if x.strip()]
    responses = [obj for obj in lines if obj.get("type") == "read_response"]
    finals = [obj for obj in lines if "final" in obj]

    # every observed record, flattened in order
    seen: list[tuple[int, bytes]] = []
    for r in responses:
        for rec in r["records"]:
            seen.append((int(rec["seq"]), base64.b64decode(rec["payload"])))
    assert seen == [(1, b"one"), (2, b"two"), (3, b"three")]
    assert finals and finals[-1]["final"] == "eof"
    assert client_rc == 0


def test_selfpair_close_failed(tmp_path: Path) -> None:
    """A scripted close(error) drives the client to a `failed` terminal state."""
    script = [
        {
            "after_frames": 1,
            "inputs": [
                {"type": "push", "payload": _b64(b"a")},
                {"type": "close", "error": {"code": "producer_error", "message": "boom"}},
            ],
        }
    ]
    script_path = tmp_path / "script.json"
    script_path.write_text(json.dumps(script))

    node = _spawn(
        ["node", "--script", str(script_path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    client = _spawn(
        ["client", "--stream-id", "s1", "--from", "0"],
        stdin=node.stdout, stdout=node.stdin, stderr=subprocess.PIPE,
    )
    assert node.stdout is not None and node.stdin is not None
    node.stdout.close()
    node.stdin.close()

    client_err = client.communicate(timeout=20)[1].decode()
    node.wait(timeout=20)

    lines = [json.loads(x) for x in client_err.splitlines() if x.strip()]
    seen = [
        (int(rec["seq"]), base64.b64decode(rec["payload"]))
        for obj in lines if obj.get("type") == "read_response"
        for rec in obj["records"]
    ]
    finals = [obj for obj in lines if "final" in obj]
    assert seen == [(1, b"a")]
    assert finals and finals[-1]["final"] == "failed"
    assert client.returncode == 0
