from __future__ import annotations

from mixing_module.quality_monitoring import confidence_score, drift_against_baseline, trend_alerts


def test_trend_alerts_success_path() -> None:
    h_series = [0.1, 0.2, 0.32, 0.45, 0.6]
    rsd_series = [25.0, 20.0, 16.0, 12.0, 9.0]
    result = trend_alerts(h_series=h_series, rsd_series=rsd_series)
    assert result["level"] == "success"


def test_drift_detection_warns() -> None:
    drift = drift_against_baseline(
        current_h_end=0.72,
        current_rsd_end=7.4,
        baseline_h_end=0.85,
        baseline_rsd_end=4.8,
    )
    assert drift["level"] in {"warning", "error"}


def test_confidence_score_bounded() -> None:
    score = confidence_score(h=0.8, rsd=6.0, rsd_target=5.0, h_slope=0.01, rsd_slope=-0.3)
    assert 0.0 <= score <= 1.0


def test_trend_alerts_long_series_performance() -> None:
    h_series = [min(1.0, i * 0.0002) for i in range(20_000)]
    rsd_series = [max(0.0, 25.0 - i * 0.001) for i in range(20_000)]
    result = trend_alerts(h_series=h_series, rsd_series=rsd_series)
    assert result["level"] in {"success", "warning", "error"}
