import numpy as np

from pc_app.scope_app.core.models import SampleBlock
from pc_app.scope_app.core.ring_buffer import WaveformRingBuffer
from pc_app.scope_app.acquisition.statistics import AcquisitionStatistics


def test_ring_buffer_accepts_sample_block():
    block = SampleBlock(
        sequence=10,
        start_time_ms=100.0,
        sample_rate_hz=1000,
        channel_count=1,
        values_mv=np.array([[1000.0, 1100.0, 1200.0]]),
    )
    buffer = WaveformRingBuffer(capacity=10)
    buffer.append_block(block)
    time_ms, value_mv, sequence = buffer.arrays()
    assert time_ms.tolist() == [100.0, 101.0, 102.0]
    assert value_mv.tolist() == [1000.0, 1100.0, 1200.0]
    assert sequence.tolist() == [10, 11, 12]


def test_statistics_count_sample_block_points():
    stats = AcquisitionStatistics()
    block = SampleBlock(
        sequence=20,
        start_time_ms=0.0,
        sample_rate_hz=1000,
        channel_count=1,
        values_mv=np.array([[1000.0, 1100.0, 1200.0, 1300.0]]),
    )
    snapshot = stats.update_block(block)
    assert snapshot.received_samples == 4
    assert snapshot.lost_samples == 0
