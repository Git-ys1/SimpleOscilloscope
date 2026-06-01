from __future__ import annotations

import socket


class TcpTransport:
    name = "tcp"

    def __init__(self, source: str) -> None:
        endpoint = source[len("tcp://") :]
        host, _, port_text = endpoint.partition(":")
        self._sock = socket.create_connection((host or "127.0.0.1", int(port_text or "8765")), timeout=3.0)
        self._sock.settimeout(0.25)
        self._file = self._sock.makefile("rwb", buffering=0)

    def readline(self) -> bytes:
        try:
            return self._file.readline()
        except socket.timeout:
            return b""

    def write(self, data: bytes) -> None:
        self._file.write(data)

    def close(self) -> None:
        try:
            self._file.close()
        finally:
            self._sock.close()
