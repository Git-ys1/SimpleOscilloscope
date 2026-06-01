from __future__ import annotations


class SerialTransport:
    name = "serial"

    def __init__(self, port: str, baud: int) -> None:
        import serial

        self._serial = serial.Serial(port=port, baudrate=baud, timeout=0.25)

    def read(self, size: int = 512) -> bytes:
        return self._serial.read(size)

    def readline(self) -> bytes:
        return self._serial.readline()

    def write(self, data: bytes) -> None:
        self._serial.write(data)

    def close(self) -> None:
        self._serial.close()
