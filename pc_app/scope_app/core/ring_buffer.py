from __future__ import annotations

import numpy as np

from .models import SampleBlock, SampleFrame


class WaveformRingBuffer:
    def __init__(self, capacity: int = 200_000) -> None:
        self.capacity = int(capacity)
        self._time_ms = np.zeros(self.capacity, dtype=np.float64)
        self._value_mv = np.zeros(self.capacity, dtype=np.float64)
        self._sequence = np.zeros(self.capacity, dtype=np.uint64)
        self._write_index = 0
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def clear(self) -> None:
        self._write_index = 0
        self._size = 0

    def append(self, sample: SampleFrame) -> None:
        index = self._write_index
        self._time_ms[index] = sample.time_ms
        self._value_mv[index] = sample.value_mv
        self._sequence[index] = sample.sequence
        self._write_index = (index + 1) % self.capacity
        self._size = min(self._size + 1, self.capacity)

    def extend(self, samples: list[SampleFrame]) -> None:
        for sample in samples:
            self.append(sample)

    def append_block(self, block: SampleBlock, channel: int = 0) -> None:
        if block.point_count == 0:
            return
        if channel >= block.channel_count:
            raise ValueError(f"channel {channel} out of range for block with {block.channel_count} channel(s)")

        values = block.values_mv[channel] if block.values_mv.ndim == 2 else block.values_mv
        dt_ms = 1000.0 / float(block.sample_rate_hz)
        for offset, value in enumerate(values.tolist()):
            self.append(
                SampleFrame(
                    sequence=block.sequence + offset,
                    time_ms=int(block.start_time_ms + offset * dt_ms),
                    value_mv=float(value),
                    wave="BLOCK",
                    frequency_hz=0,
                    amplitude_mv=0,
                    offset_mv=0,
                )
            )

    def arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self._size == 0:
            return (
                np.array([], dtype=np.float64),
                np.array([], dtype=np.float64),
                np.array([], dtype=np.uint64),
            )

        start = (self._write_index - self._size) % self.capacity
        if start + self._size <= self.capacity:
            time_ms = self._time_ms[start : start + self._size]
            value_mv = self._value_mv[start : start + self._size]
            sequence = self._sequence[start : start + self._size]
        else:
            end_len = self.capacity - start
            time_ms = np.concatenate((self._time_ms[start:], self._time_ms[: self._size - end_len]))
            value_mv = np.concatenate((self._value_mv[start:], self._value_mv[: self._size - end_len]))
            sequence = np.concatenate((self._sequence[start:], self._sequence[: self._size - end_len]))

        return time_ms.copy(), value_mv.copy(), sequence.copy()
