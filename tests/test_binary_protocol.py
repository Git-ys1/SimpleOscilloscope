import numpy as np
import pytest

from pc_app.scope_app.protocol.binary_protocol import BinaryProtocol, crc16_ccitt
from pc_app.scope_app.protocol.stream_decoder import ProtocolStreamDecoder
from pc_app.scope_app.core.models import AckFrame, ErrorFrame, SampleBlock, TextFrame


def test_crc16_ccitt_known_vector():
    assert crc16_ccitt(b"123456789") == 0x29B1


def test_binary_data_frame_round_trip():
    protocol = BinaryProtocol()
    values_adc = np.array([[0, 2048, 4095]], dtype=np.uint16)
    frame = protocol.build_data_frame(sequence=100, sample_rate_hz=10_000, values_adc=values_adc)
    block = protocol.parse_frame(frame, start_time_ms=12.5)
    assert block.sequence == 100
    assert block.sample_rate_hz == 10_000
    assert block.channel_count == 1
    assert block.point_count == 3
    assert block.values_mv[0, 0] == pytest.approx(0.0)
    assert block.values_mv[0, 2] == pytest.approx(3300.0)


def test_stream_decoder_accepts_mixed_ascii_and_binary_frames():
    protocol = BinaryProtocol()
    decoder = ProtocolStreamDecoder()
    values_adc = np.array([0, 2048, 4095], dtype=np.uint16)
    frame = protocol.build_data_frame(sequence=10, sample_rate_hz=1000, values_adc=values_adc)

    events = decoder.feed(b"BOOT,SimpleOscilloscope,0.7.0,FAKE,115200\n" + frame[:5])
    events += decoder.feed(frame[5:] + b"OK,FORMAT\n")

    assert isinstance(events[0], TextFrame)
    assert isinstance(events[1], SampleBlock)
    assert isinstance(events[2], AckFrame)
    assert events[1].sequence == 10
    assert events[1].start_time_ms == pytest.approx(9.0)


def test_ring_buffer_keeps_sub_millisecond_binary_timing():
    from pc_app.scope_app.core.ring_buffer import WaveformRingBuffer

    protocol = BinaryProtocol()
    frame = protocol.build_data_frame(sequence=1, sample_rate_hz=20_000, values_adc=np.array([0, 1, 2], dtype=np.uint16))
    decoder = ProtocolStreamDecoder()
    block = next(event for event in decoder.feed(frame) if isinstance(event, SampleBlock))
    buffer = WaveformRingBuffer(capacity=8)
    buffer.append_block(block)
    time_ms, _value_mv, _sequence = buffer.arrays()

    assert time_ms.tolist() == pytest.approx([0.0, 0.05, 0.1])


def test_stream_decoder_reports_crc_error():
    protocol = BinaryProtocol()
    decoder = ProtocolStreamDecoder()
    frame = bytearray(protocol.build_data_frame(sequence=10, sample_rate_hz=1000, values_adc=np.array([1000], dtype=np.uint16)))
    frame[-1] ^= 0xFF
    events = decoder.feed(bytes(frame))
    assert any(isinstance(event, ErrorFrame) and event.reason.startswith("binary:crc mismatch") for event in events)
