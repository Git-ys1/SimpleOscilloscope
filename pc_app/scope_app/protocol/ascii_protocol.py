from __future__ import annotations

from ..core.models import AckFrame, DeviceIdentity, DeviceStatus, ErrorFrame, SampleFrame, TextFrame


class AsciiProtocol:
    def parse_line(self, line: str) -> object | None:
        text = line.strip()
        if not text:
            return None

        parts = text.split(",")
        kind = parts[0]

        try:
            if kind == "OSC" and len(parts) == 8:
                return SampleFrame(
                    sequence=int(parts[1]),
                    time_ms=int(parts[2]),
                    value_mv=float(parts[3]),
                    wave=parts[4],
                    frequency_hz=int(parts[5]),
                    amplitude_mv=int(parts[6]),
                    offset_mv=int(parts[7]),
                )
            if kind == "STATUS" and len(parts) == 7:
                return DeviceStatus(
                    wave=parts[1],
                    frequency_hz=int(parts[2]),
                    amplitude_mv=int(parts[3]),
                    offset_mv=int(parts[4]),
                    sample_rate_hz=int(parts[5]),
                    run_state=parts[6],
                )
            if kind == "ID" and len(parts) >= 5:
                return DeviceIdentity(
                    name=parts[1],
                    target=parts[2],
                    version=parts[3],
                    transport=parts[4],
                    output=parts[5] if len(parts) > 5 else "",
                )
            if kind == "BOOT":
                return TextFrame("BOOT", text)
            if kind == "OK" and len(parts) >= 2:
                return AckFrame(parts[1])
            if kind == "ERR" and len(parts) >= 2:
                return ErrorFrame(parts[1])
            if kind in {"PONG", "HELP"}:
                return TextFrame(kind, text)
        except ValueError as exc:
            return ErrorFrame(f"parse:{exc}")

        return TextFrame("RAW", text)
