from __future__ import annotations

import socket


class TcpTransport:
    name = "tcp"

    def __init__(self, source: str) -> None:
        endpoint = source[len("tcp://") :]
        host, _, port_text = endpoint.partition(":")
        self._sock = socket.create_connection((host or "127.0.0.1", int(port_text or "8765")), timeout=3.0)
        self._sock.settimeout(0.25)
        self._readline_buffer = bytearray()

    def read(self, size: int = 512) -> bytes:
        try:
            return self._sock.recv(size)
        except socket.timeout:
            return b""

    def readline(self) -> bytes:
        while b"\n" not in self._readline_buffer:
            chunk = self.read(512)
            if not chunk:
                return b""
            self._readline_buffer.extend(chunk)
        index = self._readline_buffer.index(ord("\n")) + 1
        line = bytes(self._readline_buffer[:index])
        del self._readline_buffer[:index]
        return line

    def write(self, data: bytes) -> None:
        self._sock.sendall(data)

    def close(self) -> None:
        self._sock.close()
