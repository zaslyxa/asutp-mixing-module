from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DryCascadeConfig:
    duration_s: float = 120.0
    dt_s: float = 1.0
    cells: int = 3
    tau_s: float = 45.0
    kh: float = 0.02
    c_in: float = 1.0
    t_in: float = 25.0
    t_wall: float = 30.0
    c0: float = 0.0
    t0: float = 25.0


@dataclass(frozen=True)
class DryCascadePoint:
    time_s: float
    concentrations: tuple[float, ...]
    temperatures: tuple[float, ...]


def _validate(cfg: DryCascadeConfig) -> None:
    if cfg.duration_s <= 0:
        raise ValueError("duration_s must be > 0")
    if cfg.dt_s <= 0:
        raise ValueError("dt_s must be > 0")
    if cfg.cells < 1:
        raise ValueError("cells must be >= 1")
    if cfg.tau_s <= 0:
        raise ValueError("tau_s must be > 0")
    if cfg.kh < 0:
        raise ValueError("kh must be >= 0")


def run_dry_cascade(cfg: DryCascadeConfig) -> list[DryCascadePoint]:
    """Simulate CSTR-in-series dry mixing model with temperature channel.

    Model equations:
    - k = n / tau
    - dc1/dt = k * (c_in - c1)
    - dci/dt = k * (c_{i-1} - ci), i>=2
    - dT1/dt = k * (T_in - T1) + kh * (T_wall - T1)
    - dTi/dt = k * (T_{i-1} - Ti) + kh * (T_wall - Ti), i>=2
    """
    _validate(cfg)
    k = cfg.cells / cfg.tau_s
    steps = int(round(cfg.duration_s / cfg.dt_s))

    c = [cfg.c0 for _ in range(cfg.cells)]
    t = [cfg.t0 for _ in range(cfg.cells)]
    out: list[DryCascadePoint] = [DryCascadePoint(0.0, tuple(c), tuple(t))]

    for step in range(1, steps + 1):
        dc = [0.0 for _ in range(cfg.cells)]
        dt = [0.0 for _ in range(cfg.cells)]

        dc[0] = k * (cfg.c_in - c[0])
        dt[0] = k * (cfg.t_in - t[0]) + cfg.kh * (cfg.t_wall - t[0])

        for i in range(1, cfg.cells):
            dc[i] = k * (c[i - 1] - c[i])
            dt[i] = k * (t[i - 1] - t[i]) + cfg.kh * (cfg.t_wall - t[i])

        for i in range(cfg.cells):
            c[i] += cfg.dt_s * dc[i]
            t[i] += cfg.dt_s * dt[i]

        out.append(DryCascadePoint(step * cfg.dt_s, tuple(c), tuple(t)))

    return out
