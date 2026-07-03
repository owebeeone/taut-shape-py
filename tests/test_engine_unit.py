"""Direct synchronous engine tests — ``outputs = node.handle(msg)``, no loop.

These complement the oracle (the contract): they pin behaviors the corpus does
not directly exercise (accessors, watermarks, the refined-D6 no-op paths) and
document the engine's intended semantics in-repo.
"""

from __future__ import annotations

from taut_shape.log import (
    LogClose,
    LogCursor,
    LogEndStream,
    LogError,
    LogErrorCode,
    LogEvict,
    LogNode,
    LogProducerStop,
    LogPush,
    LogReadRequest,
    LogSeal,
    LogState,
    LogStopReason,
    StopWhen,
)


def _read(sid: str, seq: int, **kw: object) -> LogReadRequest:
    return LogReadRequest(
        log_id="log-A", stream_id=sid, cursor=LogCursor(seq=seq),
        max_records=kw.get("max_records"), max_bytes=kw.get("max_bytes"),
        timeout_ms=kw.get("timeout_ms"),
    )


def test_head_and_accessors_track_pushes() -> None:
    node = LogNode()
    assert node.head == 0 and node.floor == 1 and node.stream_count == 0
    node.handle(LogPush(payload=b"a"))
    node.handle(LogPush(payload=b"b"))
    assert node.head == 2
    node.handle(_read("s1", 0, timeout_ms=0))
    assert node.stream_count == 1


def test_watermark_and_min_watermark() -> None:
    node = LogNode()
    for p in (b"a", b"b", b"c"):
        node.handle(LogPush(payload=p))
    node.handle(_read("s1", 0, max_records=1, timeout_ms=0))   # delivers seq 1
    node.handle(_read("s2", 0, timeout_ms=0))                  # delivers up to 3
    assert node.min_watermark == 1                              # s1 behind s2


def test_refined_d6_repeated_close_emits_nothing() -> None:
    node = LogNode(stop_when=StopWhen.LAST_READER)
    first = node.handle(LogClose(error=None))
    assert first == [LogProducerStop(reason=LogStopReason.closed)]
    assert node.handle(LogClose(error=None)) == []             # already terminal
    assert node.handle(LogClose(error=LogError(code=LogErrorCode.producer_error,
                                               message="x"))) == []


def test_refined_d6_close_after_seal_is_a_transition() -> None:
    node = LogNode(stop_when=StopWhen.LAST_READER)
    assert node.handle(LogSeal()) == []                        # seal: no stop
    out = node.handle(LogClose(error=None))                    # Sealed -> Closed
    assert out == [LogProducerStop(reason=LogStopReason.closed)]
    assert node.handle(LogClose(error=None)) == []             # now a no-op


def test_evict_then_expired_then_resume() -> None:
    node = LogNode()
    for p in (b"1", b"2", b"3"):
        node.handle(LogPush(payload=p))
    node.handle(LogEvict(up_to_seq=2))
    assert node.floor == 3
    expired = node.handle(_read("s1", 0, timeout_ms=0))[0]
    assert expired.state is LogState.expired
    assert expired.next_cursor.seq == 2                        # floor - 1 (D9)
    data = node.handle(_read("s1", 2, timeout_ms=0))[0]
    assert data.state is LogState.data
    assert [r.seq for r in data.records] == [3]


def test_end_stream_unknown_is_noop() -> None:
    node = LogNode(stop_when=StopWhen.LAST_READER)
    assert node.handle(LogEndStream(log_id="log-A", stream_id="ghost")) == []


def test_explicit_only_never_stops_on_reader_loss() -> None:
    node = LogNode(stop_when=StopWhen.EXPLICIT_ONLY)
    node.handle(_read("s1", 0, timeout_ms=0))
    assert node.handle(LogEndStream(log_id="log-A", stream_id="s1")) == []
