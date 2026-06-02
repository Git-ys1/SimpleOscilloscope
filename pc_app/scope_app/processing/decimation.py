from __future__ import annotations

import numpy as np


def decimate_for_display(x: np.ndarray, y: np.ndarray, max_points: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    if x.size <= max_points or max_points <= 0:
        return x, y
    bucket_count = max(1, max_points // 2)
    edges = np.linspace(0, x.size, bucket_count + 1, dtype=np.int64)
    out_x: list[float] = []
    out_y: list[float] = []
    for start, end in zip(edges[:-1], edges[1:]):
        if end <= start:
            continue
        segment = y[start:end]
        segment_x = x[start:end]
        min_index = int(np.argmin(segment))
        max_index = int(np.argmax(segment))
        ordered = sorted({min_index, max_index}, key=lambda index: float(segment_x[index]))
        for index in ordered:
            out_x.append(float(segment_x[index]))
            out_y.append(float(segment[index]))
    return np.asarray(out_x, dtype=x.dtype), np.asarray(out_y, dtype=y.dtype)
