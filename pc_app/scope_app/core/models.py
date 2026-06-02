from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class RunState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True)
class ConnectionConfig:
    source: str
    baud: int = 115200


@dataclass(frozen=True)
class SignalConfig:
    wave: str = "SINE"
    frequency_hz: int = 5
    amplitude_mv: int = 1200
    offset_mv: int = 1650
    sample_rate_hz: int = 100


@dataclass(frozen=True)
class DisplayConfig:
    time_per_div_s: float = 0.1
    volt_per_div_mv: float = 500.0
    horizontal_offset_s: float = 0.0
    vertical_center_mv: float = 1650.0
    auto_range: bool = True


@dataclass(frozen=True)
class TriggerConfig:
    mode: str = "Auto"
    edge: str = "Rising"
    level_mv: float = 1650.0
    pretrigger_ratio: float = 0.2


@dataclass(frozen=True)
class RecordConfig:
    sample_rate_hz: int = 10_000
    record_length: int = 1024
    trigger_position: float = 0.2


@dataclass(frozen=True)
class SampleFrame:
    sequence: int
    time_ms: int
    value_mv: float
    wave: str
    frequency_hz: int
    amplitude_mv: int
    offset_mv: int


@dataclass(frozen=True)
class SampleBlock:
    sequence: int
    start_time_ms: float
    sample_rate_hz: int
    channel_count: int
    values_mv: np.ndarray

    @property
    def point_count(self) -> int:
        return int(self.values_mv.shape[-1])


@dataclass(frozen=True)
class DeviceStatus:
    wave: str
    frequency_hz: int
    amplitude_mv: int
    offset_mv: int
    sample_rate_hz: int
    run_state: str


@dataclass(frozen=True)
class DeviceIdentity:
    name: str
    target: str
    version: str
    transport: str
    output: str = ""


@dataclass(frozen=True)
class AckFrame:
    key: str


@dataclass(frozen=True)
class ErrorFrame:
    reason: str


@dataclass(frozen=True)
class TextFrame:
    kind: str
    payload: str


@dataclass(frozen=True)
class AcquisitionStats:
    received_samples: int = 0
    received_blocks: int = 0
    lost_samples: int = 0
    sample_rate_hz: float = 0.0
    frames_per_second: float = 0.0


@dataclass(frozen=True)
class MeasurementSnapshot:
    points: int
    v_min_mv: float
    v_max_mv: float
    v_pp_mv: float
    v_avg_mv: float
    v_rms_dc_mv: float
    v_rms_ac_mv: float
    frequency_hz: float
    period_ms: float = 0.0
    duty_cycle_percent: float = 0.0

    @property
    def v_rms_mv(self) -> float:
        return self.v_rms_dc_mv
