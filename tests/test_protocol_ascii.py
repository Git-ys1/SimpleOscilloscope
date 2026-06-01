from pc_app.scope_app.core.models import DeviceStatus, SampleFrame
from pc_app.scope_app.protocol.ascii_protocol import AsciiProtocol


def test_parse_sample_frame():
    frame = AsciiProtocol().parse_line("OSC,42,420,2301,SINE,5,1200,1650")
    assert isinstance(frame, SampleFrame)
    assert frame.sequence == 42
    assert frame.value_mv == 2301
    assert frame.wave == "SINE"


def test_parse_status_frame():
    frame = AsciiProtocol().parse_line("STATUS,SQUARE,20,1200,1650,100,RUN")
    assert isinstance(frame, DeviceStatus)
    assert frame.wave == "SQUARE"
    assert frame.frequency_hz == 20
    assert frame.run_state == "RUN"
