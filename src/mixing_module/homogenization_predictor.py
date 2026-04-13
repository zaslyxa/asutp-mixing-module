from __future__ import annotations

import math


def predict_endpoint(
    *,
    k_mix: float,
    h_rel_current: float,
    h_rel_target: float,
    tau_s: float,
    dt_s: float = 1.0,
    gamma_seg: float = 0.01,
    segregation_idx_mix: float = 0.0,
) -> dict:
    k_eff = max(k_mix - gamma_seg * segregation_idx_mix, 1e-6)
    current = min(max(h_rel_current, 0.0), 0.999999)
    target = min(max(h_rel_target, current), 0.999999)
    if current >= target:
        t_remaining = 0.0
    else:
        t_remaining = max((math.log(1 - current) - math.log(1 - target)) / k_eff, 0.0)

    horizon = max(int(3 * tau_s / max(dt_s, 1e-6)), 1)
    times = [i * dt_s for i in range(horizon + 1)]
    h_pred = [1.0 - (1.0 - current) * math.exp(-k_eff * t) for t in times]
    return {
        "t_remaining_s": t_remaining,
        "k_eff": k_eff,
        "times_s": times,
        "h_pred": [min(max(h, 0.0), 1.0) for h in h_pred],
    }


def uncertainty_bands(rsd_series: list[float], variance_rsd: float) -> dict:
    sigma = math.sqrt(max(variance_rsd, 0.0))
    lower = [max(v - 2 * sigma, 0.0) for v in rsd_series]
    upper = [v + 2 * sigma for v in rsd_series]
    return {"lower": lower, "upper": upper, "sigma": sigma}
