from pc_app.scope_app.protocol.stream_decoder import ProtocolStreamDecoder
from pc_app.scope_app.transport.fake_transport import FakeTransport
from pc_app.scope_app.core.models import DeviceCapabilities, SampleBlock


def _first_block(source: str) -> SampleBlock:
    transport = FakeTransport(source)
    decoder = ProtocolStreamDecoder()
    for _ in range(8):
        for event in decoder.feed(transport.read()):
            if isinstance(event, SampleBlock):
                return event
    raise AssertionError(f"{source} did not produce a SampleBlock")


def test_fake_sources_produce_binary_sample_blocks():
    for source in ["fake://sine", "fake://square", "fake://triangle", "fake://noise", "fake://mixed"]:
        block = _first_block(source)
        assert block.point_count > 0
        assert block.sample_rate_hz > 0


def test_fake_source_advertises_v093_capabilities():
    transport = FakeTransport("fake://sine")
    decoder = ProtocolStreamDecoder()
    transport.write(b"CAP?\n")
    events = []
    for _ in range(4):
        events += decoder.feed(transport.read())

    caps = [event for event in events if isinstance(event, DeviceCapabilities)]
    assert caps
    assert caps[-1].rate_max == 20_000
    assert caps[-1].freq_max == 5_000
    assert caps[-1].baud == 921600
    assert caps[-1].block_points == 64


def test_fake_source_accepts_1khz_and_20ksa():
    transport = FakeTransport("fake://sine")
    decoder = ProtocolStreamDecoder()
    transport.write(b"SET FREQ 1000\nSET RATE 20000\n")
    block = None
    for _ in range(8):
        for event in decoder.feed(transport.read()):
            if isinstance(event, SampleBlock):
                block = event
                break
        if block is not None:
            break

    assert block is not None
    assert block.sample_rate_hz == 20_000
    assert block.point_count == 64


def test_fake_source_defaults_to_20ksa_for_smooth_1khz_demo():
    block = _first_block("fake://sine")

    assert block.sample_rate_hz == 20_000
