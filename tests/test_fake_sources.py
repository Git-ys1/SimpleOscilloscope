from pc_app.scope_app.protocol.stream_decoder import ProtocolStreamDecoder
from pc_app.scope_app.transport.fake_transport import FakeTransport
from pc_app.scope_app.core.models import SampleBlock


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
