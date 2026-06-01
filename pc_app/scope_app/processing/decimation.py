from __future__ import annotations

import numpy as np


def decimate_for_display(x: np.ndarray, y: np.ndarray, max_points: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    if x.size <= max_points or max_points <= 0:
        return x, y
    step = int(np.ceil(x.size / max_points))
    return x[::step], y[::step]
