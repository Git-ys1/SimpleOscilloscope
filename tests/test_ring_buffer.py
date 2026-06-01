from pc_app.scope_app.core.models import SampleFrame
from pc_app.scope_app.core.ring_buffer import WaveformRingBuffer


def sample(seq: int) -> SampleFrame:
    return SampleFrame(seq, seq * 10, float(seq), "SINE", 5, 1200, 1650)


def test_ring_buffer_wraps_in_order():
    buffer = WaveformRingBuffer(capacity=3)
    for seq in range(5):
        buffer.append(sample(seq))
    time_ms, value_mv, sequence = buffer.arrays()
    assert time_ms.tolist() == [20.0, 30.0, 40.0]
    assert value_mv.tolist() == [2.0, 3.0, 4.0]
    assert sequence.tolist() == [2, 3, 4]
