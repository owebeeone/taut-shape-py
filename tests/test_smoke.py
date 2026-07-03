"""Smoke test: the package and its engine import and round-trip a trivial op."""

from __future__ import annotations


def test_import_and_basic_push_read() -> None:
    from taut_shape.log import LogNode, LogPush, LogReadRequest, LogCursor, LogState

    node = LogNode(log_id="log-A")
    assert node.head == 0
    assert node.handle(LogPush(payload=b"hi")) == []
    outs = node.handle(
        LogReadRequest(
            log_id="log-A", stream_id="s1", cursor=LogCursor(seq=0),
            max_records=10, max_bytes=None, timeout_ms=0,
        )
    )
    assert len(outs) == 1
    resp = outs[0]
    assert resp.state is LogState.data
    assert [r.payload for r in resp.records] == [b"hi"]
    assert resp.next_cursor.seq == 1
