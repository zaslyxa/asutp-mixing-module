from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WetCascadeConfig:
    duration_s: float = 120.0
    dt_s: float = 1.0
    cells: int = 3
    tau_s: float = 45.0
    component_inlet: tuple[float, ...] = (1.0, 0.0)
    component_initial: tuple[float, ...] = (0.0, 0.0)
    w_in: float = 0.1
    w0: float = 0.05
    q_liquid: float = 0.2
    b_q: float = 0.05
    j_add: int = 2
    eta0: float = 1.0
    ka: float = 0.02
    kb: float = 0.001
    w_star: float = 0.15
    t_in: float = 25.0
    t_wall: float = 30.0
    t0: float = 25.0
    kh: float = 0.02
    reaction_enabled: bool = False
    reaction_rate: float = 0.0
    effect_heat_release: bool = False
    effect_precipitation: bool = False
    effect_gas_evolution: bool = False
    heat_release_gain: float = 5.0
    precipitation_gain: float = 0.02
    gas_strip_gain: float = 0.01


@dataclass(frozen=True)
class WetCascadePoint:
    time_s: float
    components: tuple[tuple[float, ...], ...]
    moisture: tuple[float, ...]
    eta: tuple[float, ...]
    temperatures: tuple[float, ...]
    reaction_rate_cells: tuple[float, ...]


def _validate(cfg: WetCascadeConfig) -> None:
    if cfg.duration_s <= 0:
        raise ValueError("duration_s must be > 0")
    if cfg.dt_s <= 0:
        raise ValueError("dt_s must be > 0")
    if cfg.cells < 1:
        raise ValueError("cells must be >= 1")
    if cfg.tau_s <= 0:
        raise ValueError("tau_s must be > 0")
    if len(cfg.component_inlet) == 0:
        raise ValueError("at least one component is required")
    if len(cfg.component_inlet) != len(cfg.component_initial):
        raise ValueError("component_inlet and component_initial lengths must match")
    if not 1 <= cfg.j_add <= cfg.cells:
        raise ValueError("j_add must be between 1 and cells")
    if cfg.kh < 0:
        raise ValueError("kh must be >= 0")
    if cfg.ka < 0 or cfg.kb < 0:
        raise ValueError("ka and kb must be >= 0")


def _reaction_intensity(
    component_row: list[float],
    moisture: float,
    cfg: WetCascadeConfig,
) -> float:
    if not cfg.reaction_enabled or cfg.reaction_rate <= 0:
        return 0.0
    reagent = max(min(component_row), 0.0)
    return cfg.reaction_rate * reagent * max(moisture, 0.0)


def run_wet_cascade(cfg: WetCascadeConfig) -> list[WetCascadePoint]:
    """Simulate wet granular mixing with reduced PBM quality state.

    States per cell:
    - component concentrations for N recipe components;
    - moisture w;
    - PBM proxy eta (zero-moment deviation);
    - temperature T.
    """
    _validate(cfg)
    k = cfg.cells / cfg.tau_s
    steps = int(round(cfg.duration_s / cfg.dt_s))
    n_comp = len(cfg.component_inlet)

    comps = [[cfg.component_initial[j] for j in range(n_comp)] for _ in range(cfg.cells)]
    moist = [cfg.w0 for _ in range(cfg.cells)]
    eta = [cfg.eta0 for _ in range(cfg.cells)]
    temp = [cfg.t0 for _ in range(cfg.cells)]

    out: list[WetCascadePoint] = [
        WetCascadePoint(
            time_s=0.0,
            components=tuple(tuple(row) for row in comps),
            moisture=tuple(moist),
            eta=tuple(eta),
            temperatures=tuple(temp),
            reaction_rate_cells=tuple(0.0 for _ in range(cfg.cells)),
        )
    ]

    for step in range(1, steps + 1):
        dcomps = [[0.0 for _ in range(n_comp)] for _ in range(cfg.cells)]
        dw = [0.0 for _ in range(cfg.cells)]
        deta = [0.0 for _ in range(cfg.cells)]
        dt = [0.0 for _ in range(cfg.cells)]
        reaction_cells = [0.0 for _ in range(cfg.cells)]

        for i in range(cfg.cells):
            prev_i = i - 1
            source_w = cfg.b_q * cfg.q_liquid if i == (cfg.j_add - 1) else 0.0

            if i == 0:
                for j in range(n_comp):
                    dcomps[i][j] = k * (cfg.component_inlet[j] - comps[i][j])
                dw[i] = k * (cfg.w_in - moist[i]) + source_w
                dt[i] = k * (cfg.t_in - temp[i]) + cfg.kh * (cfg.t_wall - temp[i])
                deta[i] = -(cfg.ka + cfg.kb * max(moist[i] - cfg.w_star, 0.0)) * eta[i]
            else:
                for j in range(n_comp):
                    dcomps[i][j] = k * (comps[prev_i][j] - comps[i][j])
                dw[i] = k * (moist[prev_i] - moist[i]) + source_w
                dt[i] = k * (temp[prev_i] - temp[i]) + cfg.kh * (cfg.t_wall - temp[i])
                deta[i] = (
                    k * (eta[prev_i] - eta[i])
                    - (cfg.ka + cfg.kb * max(moist[i] - cfg.w_star, 0.0)) * eta[i]
                )

            reaction = _reaction_intensity(comps[i], moist[i], cfg)
            reaction_cells[i] = reaction

            for j in range(n_comp):
                dcomps[i][j] -= reaction

            if cfg.effect_heat_release:
                dt[i] += cfg.heat_release_gain * reaction

            if cfg.effect_precipitation:
                deta[i] -= cfg.precipitation_gain * reaction * eta[i]

            if cfg.effect_gas_evolution:
                dw[i] -= cfg.gas_strip_gain * reaction

        for i in range(cfg.cells):
            for j in range(n_comp):
                comps[i][j] = max(comps[i][j] + cfg.dt_s * dcomps[i][j], 0.0)
            moist[i] = max(moist[i] + cfg.dt_s * dw[i], 0.0)
            eta[i] = max(eta[i] + cfg.dt_s * deta[i], 0.0)
            temp[i] = temp[i] + cfg.dt_s * dt[i]

        out.append(
            WetCascadePoint(
                time_s=step * cfg.dt_s,
                components=tuple(tuple(row) for row in comps),
                moisture=tuple(moist),
                eta=tuple(eta),
                temperatures=tuple(temp),
                reaction_rate_cells=tuple(reaction_cells),
            )
        )

    return out
