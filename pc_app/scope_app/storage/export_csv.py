from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def export_csv(path: str | Path, time_ms: np.ndarray, value_mv: np.ndarray) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_ms", "value_mv"])
        writer.writerows(zip(time_ms.tolist(), value_mv.tolist()))
