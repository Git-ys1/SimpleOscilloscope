from __future__ import annotations

import time

from ..core.models import AcquisitionStats, SampleBlock, SampleFrame


class AcquisitionStatistics:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.received_samples = 0
        self.lost_samples = 0
        self._last_sequence: int | None = None
        self._window_started = time.monotonic()
        self._window_samples = 0
        self._window_frames = 0
        self._sample_rate_hz = 0.0
        self._frames_per_second = 0.0

    def update_sample(self, sample: SampleFrame) -> AcquisitionStats:
        return self._update(sequence=sample.sequence, point_count=1)

    def update_block(self, block: SampleBlock) -> AcquisitionStats:
        return self._update(sequence=block.sequence, point_count=block.point_count)

    def _update(self, sequence: int, point_count: int) -> AcquisitionStats:
        now = time.monotonic()
        point_count = max(1, int(point_count))
        self.received_samples += point_count
        self._window_samples += point_count
        self._window_frames += 1
        if self._last_sequence is not None and sequence > self._last_sequence + 1:
            self.lost_samples += sequence - self._last_sequence - 1
        self._last_sequence = sequence + point_count - 1

        elapsed = now - self._window_started
        if elapsed >= 1.0:
            self._sample_rate_hz = self._window_samples / elapsed
            self._frames_per_second = self._window_frames / elapsed
            self._window_samples = 0
            self._window_frames = 0
            self._window_started = now
        return self.snapshot()

    def snapshot(self) -> AcquisitionStats:
        return AcquisitionStats(
            received_samples=self.received_samples,
            lost_samples=self.lost_samples,
            sample_rate_hz=self._sample_rate_hz,
            frames_per_second=self._frames_per_second,
        )
