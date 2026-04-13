from __future__ import annotations

import json
from pathlib import Path


def load_mixer_template(path: str | Path) -> dict:
    file_path = Path(path)
    return json.loads(file_path.read_text(encoding="utf-8"))


def estimate_k0_from_curve(times_s: list[float], h_values: list[float]) -> float:
    if len(times_s) < 2 or len(h_values) < 2:
        return 0.02
    num = 0.0
    den = 0.0
    for i in range(1, min(len(times_s), len(h_values))):
        dt = max(times_s[i] - times_s[i - 1], 1e-6)
        dh = h_values[i] - h_values[i - 1]
        h_prev = min(max(h_values[i - 1], 0.0), 0.999)
        x = 1.0 - h_prev
        y = dh / dt
        num += x * y
        den += x * x
    if den <= 0:
        return 0.02
    return max(num / den, 0.001)
