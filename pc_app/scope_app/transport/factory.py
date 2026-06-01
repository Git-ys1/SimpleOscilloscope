from __future__ import annotations

from ..core.models import ConnectionConfig
from .fake_transport import FakeTransport
from .serial_transport import SerialTransport
from .tcp_transport import TcpTransport


def open_transport(config: ConnectionConfig):
    source = config.source.strip()
    if source.startswith("tcp://"):
        return TcpTransport(source)
    if source.startswith("fake://"):
        return FakeTransport(source)
    return SerialTransport(source, config.baud)
