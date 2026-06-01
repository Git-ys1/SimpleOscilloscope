from __future__ import annotations

import time

from ..core.models import AcquisitionStats, SampleFrame


class AcquisitionStatistics:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.received_samples = 0
        self.lost_samples = 0
        self._last_sequence: int | None = None
        self._window_started = time.monotonic()
        self._window_samples = 0
        self._sample_rate_hz = 0.0
        self._frames_per_second = 0.0

    def update_sample(self, sample: SampleFrame) -> AcquisitionStats:
        now = time.monotonic()
        self.received_samples += 1
        self._window_samples += 1
        if self._last_sequence is not None and sample.sequence > self._last_sequence + 1:
            self.lost_samples += sample.sequence - self._last_sequence - 1
        self._last_sequence = sample.sequence

        elapsed = now - self._window_started
        if elapsed >= 1.0:
            self._sample_rate_hz = self._window_samples / elapsed
            self._frames_per_second = self._sample_rate_hz
            self._window_samples = 0
            self._window_started = now
        return self.snapshot()

    def snapshot(self) -> AcquisitionStats:
        return AcquisitionStats(
            received_samples=self.received_samples,
            lost_samples=self.lost_samples,
            sample_rate_hz=self._sample_rate_hz,
            frames_per_second=self._frames_per_second,
        )
