from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class HMixConfig:
    k0: float = 0.02
    k_n: float = 0.0008
    k_D: float = 0.1
    k_w: float = 0.002
    k_Q: float = 0.0005
    q_s0: float = 0.5
    h_target: float = 0.95
    ts_s: float = 1.0
    k_min: float = 0.001
    k_max: float = 0.5
    torque_fusion_gain: float = 0.2
    p0: float = 1.0
    p_inf: float = 0.6


@dataclass(frozen=True)
class HMixSample:
    t_s: float
    h: float
    k_mix: float
    n: float
    d: float
    w: float
    q_s: float
    p: float
    ready: bool


def calc_k_mix(cfg: HMixConfig, *, n: float, d: float, w: float, q_s: float) -> float:
    k = cfg.k0 + cfg.k_n * n + cfg.k_D * d - cfg.k_w * w - cfg.k_Q * (q_s - cfg.q_s0)
    if not isfinite(k):
        k = cfg.k_min
    return min(max(k, cfg.k_min), cfg.k_max)


def calc_h_from_torque(cfg: HMixConfig, p: float) -> float:
    denom = cfg.p0 - cfg.p_inf
    if abs(denom) < 1e-9:
        return 0.0
    h = 1.0 - (p - cfg.p_inf) / denom
    return min(max(h, 0.0), 1.0)


def step_h(
    cfg: HMixConfig,
    *,
    h_prev: float,
    n: float,
    d: float,
    w: float,
    q_s: float,
    p: float | None = None,
) -> tuple[float, float]:
    k_mix = calc_k_mix(cfg, n=n, d=d, w=w, q_s=q_s)
    h_model = h_prev + cfg.ts_s * k_mix * (1.0 - h_prev)
    h_model = min(max(h_model, 0.0), 1.0)
    if p is None:
        return h_model, k_mix
    h_torque = calc_h_from_torque(cfg, p)
    h = (1.0 - cfg.torque_fusion_gain) * h_model + cfg.torque_fusion_gain * h_torque
    return min(max(h, 0.0), 1.0), k_mix
