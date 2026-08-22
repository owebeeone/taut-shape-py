"""The stdin/stdout data channel: length-prefixed, tagged CBOR frames.

Byte-for-byte identical to the rs reference
(``taut-shape-rs/crates/taut-shape-tool/src/framing.rs``). One frame is exactly
three parts, back to back::

    ┌────────────────┬──────────┬───────────────────────────┐
    │ u32-LE length  │ tag byte │ CBOR body (`length - 1`)   │
    └────────────────┴──────────┴───────────────────────────┘
          4 bytes       1 byte          length - 1 bytes

* **length** — a little-endian ``u32`` byte count of everything after the length
  prefix: the 1 tag byte **plus** the CBOR body. Body length is ``length - 1``;
  total wire size is ``4 + length``.
* **tag** — the selected shape's message-type wire value as a single byte.
* **body** — the message's deterministic-CBOR encoding (taut ``codec.encode``).

Truncated tail (a partial frame at EOF) is tolerated: a short read while reading
the length prefix or the body returns EOF (``None``), so a producer that dies
mid-frame drains cleanly rather than erroring. A fully present but malformed
frame (unknown tag, undecodable body, zero length) raises :class:`FrameError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from taut.wire import codec

from ..log import _generated as g
from . import oraclefmt

# Valid wire tag bytes: the twelve LogMsgType members (push..diagnostic).
_TAG_TO_DISC: dict[int, str] = {m.value: m.name for m in g.LogMsgType}


class FrameError(Exception):
    """A frame was fully present on the wire but malformed."""

    code = "TAUT_SHAPE_MALFORMED_MESSAGE"


class UnknownMessageTagError(FrameError):
    """A complete frame used no tag in the selected shape's registry."""

    code = "TAUT_SHAPE_UNKNOWN_TAG"

    def __init__(self, tag: int) -> None:
        super().__init__(f"unknown frame tag byte {tag}")
        self.tag = tag


@dataclass(slots=True)
class Frame:
    """A decoded frame: the message kind (as its wire tag byte) and CBOR body."""

    tag: int          # LogMsgType wire value (0..=11)
    body: bytes       # raw CBOR body bytes


def _read_exact_or_eof(r: BinaryIO, n: int) -> bytes | None:
    """Read exactly ``n`` bytes. Return ``None`` on a clean EOF (0 bytes, or a
    short read that ends at EOF) — the truncated-tail tolerance."""
    buf = bytearray()
    while len(buf) < n:
        chunk = r.read(n - len(buf))
        if not chunk:
            return None            # EOF; partial fill is a tolerated truncated tail
        buf.extend(chunk)
    return bytes(buf)


def read_frame(r: BinaryIO) -> Frame | None:
    """Read one frame from ``r``.

    * returns a :class:`Frame` — a complete, well-formed frame.
    * returns ``None`` — clean EOF (between frames, or a truncated tail).
    * raises :class:`FrameError` — a fully-present but malformed frame.
    """
    len_buf = _read_exact_or_eof(r, 4)
    if len_buf is None:
        return None
    length = int.from_bytes(len_buf, "little")
    if length == 0:
        raise FrameError(f"bad frame length {length} (min 1 for the tag byte)")

    frame_buf = _read_exact_or_eof(r, length)
    if frame_buf is None:
        return None                # truncated tail
    tag_byte = frame_buf[0]
    body = frame_buf[1:]
    return Frame(tag=tag_byte, body=bytes(body))


def write_frame(w: BinaryIO, tag: int, body: bytes) -> None:
    """Write one frame: ``u32-LE (1 + len(body))``, the tag byte, then body."""
    length = len(body) + 1
    w.write(length.to_bytes(4, "little"))
    w.write(bytes([tag]))
    w.write(body)


# ── message ↔ frame ─────────────────────────────────────────────────────────

def decode_message(frame: Frame) -> object:
    """Decode a frame's ``(tag, CBOR body)`` into an engine message dataclass.

    Raises :class:`FrameError` on an undecodable body.
    """
    try:
        disc = _TAG_TO_DISC[frame.tag]
    except KeyError as error:
        raise UnknownMessageTagError(frame.tag) from error
    name, cls = oraclefmt._BY_TYPE[disc]
    try:
        native = codec.decode(oraclefmt._SCHEMA, name, frame.body)
    except Exception as e:                       # noqa: BLE001 - any decode fault
        raise FrameError(f"malformed frame body: {e}") from e
    return oraclefmt._from_native(cls, native)


def encode_message(msg: object) -> tuple[int, bytes]:
    """Encode an engine message dataclass into its ``(tag byte, CBOR body)``."""
    disc, name = oraclefmt._BY_CLASS[type(msg)]
    native = oraclefmt._to_native(msg)
    body = codec.encode(oraclefmt._SCHEMA, name, native)
    tag = g.LogMsgType[disc].value
    return tag, body


def write_message(w: BinaryIO, msg: object) -> None:
    tag, body = encode_message(msg)
    write_frame(w, tag, body)
