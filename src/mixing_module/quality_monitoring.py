from __future__ import annotations

from typing import Any


def moving_slope(values: list[float], window: int = 5) -> float:
    if len(values) < 2:
        return 0.0
    n = max(2, min(window, len(values)))
    segment = values[-n:]
    return (segment[-1] - segment[0]) / max(n - 1, 1)


def trend_alerts(
    *,
    h_series: list[float],
    rsd_series: list[float],
    h_min_slope: float = 0.0005,
    rsd_max_slope: float = -0.0005,
) -> dict[str, Any]:
    h_slope = moving_slope(h_series)
    rsd_slope = moving_slope(rsd_series)
    stalled_h = h_slope < h_min_slope
    bad_rsd = rsd_slope > rsd_max_slope
    return {
        "h_slope": h_slope,
        "rsd_slope": rsd_slope,
        "h_alert": stalled_h,
        "rsd_alert": bad_rsd,
        "level": "error" if stalled_h and bad_rsd else ("warning" if stalled_h or bad_rsd else "success"),
    }


def drift_against_baseline(
    *,
    current_h_end: float,
    current_rsd_end: float,
    baseline_h_end: float | None,
    baseline_rsd_end: float | None,
    h_tol: float = 0.05,
    rsd_tol: float = 1.0,
) -> dict[str, Any]:
    if baseline_h_end is None or baseline_rsd_end is None:
        return {"level": "warning", "message": "No baseline batch for drift check."}
    h_delta = current_h_end - baseline_h_end
    rsd_delta = current_rsd_end - baseline_rsd_end
    level = "success"
    if abs(h_delta) > h_tol or abs(rsd_delta) > rsd_tol:
        level = "warning"
    if h_delta < -2 * h_tol or rsd_delta > 2 * rsd_tol:
        level = "error"
    return {
        "level": level,
        "h_delta": h_delta,
        "rsd_delta": rsd_delta,
        "message": f"Drift vs baseline: dH={h_delta:+.3f}, dRSD={rsd_delta:+.2f}%",
    }


def confidence_score(
    *,
    h: float,
    rsd: float,
    rsd_target: float,
    h_slope: float,
    rsd_slope: float,
) -> float:
    h_term = min(max(h, 0.0), 1.0)
    rsd_term = 1.0 - min(max(rsd / max(rsd_target * 1.5, 1e-6), 0.0), 1.0)
    trend_term = 0.5
    if h_slope >= 0 and rsd_slope <= 0:
        trend_term = 1.0
    elif h_slope < 0 and rsd_slope > 0:
        trend_term = 0.0
    score = 0.45 * h_term + 0.35 * rsd_term + 0.20 * trend_term
    return max(0.0, min(score, 1.0))
