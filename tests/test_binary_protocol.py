import numpy as np
import pytest

from pc_app.scope_app.protocol.binary_protocol import BinaryProtocol, crc16_ccitt


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
