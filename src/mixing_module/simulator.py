from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    duration_s: float = 60.0
    dt_s: float = 1.0
    tank_volume_m3: float = 5.0
    initial_concentration: float = 0.0
    inlet_a_flow_m3_s: float = 0.05
    inlet_b_flow_m3_s: float = 0.05
    inlet_a_concentration: float = 1.0
    inlet_b_concentration: float = 0.0
    outlet_flow_m3_s: float = 0.1


@dataclass(frozen=True)
class SimulationPoint:
    time_s: float
    concentration: float
    volume_m3: float


def _next_state(volume: float, concentration: float, cfg: SimulationConfig) -> tuple[float, float]:
    inflow = cfg.inlet_a_flow_m3_s + cfg.inlet_b_flow_m3_s
    outflow = cfg.outlet_flow_m3_s

    d_volume = (inflow - outflow) * cfg.dt_s
    next_volume = max(volume + d_volume, 0.001)

    inlet_mass_rate = (
        cfg.inlet_a_flow_m3_s * cfg.inlet_a_concentration
        + cfg.inlet_b_flow_m3_s * cfg.inlet_b_concentration
    )
    current_mass = concentration * volume
    d_mass = (inlet_mass_rate - outflow * concentration) * cfg.dt_s
    next_mass = max(current_mass + d_mass, 0.0)

    next_concentration = next_mass / next_volume
    return next_volume, next_concentration


def run_simulation(cfg: SimulationConfig) -> list[SimulationPoint]:
    if cfg.dt_s <= 0:
        raise ValueError("dt_s must be > 0")
    if cfg.duration_s <= 0:
        raise ValueError("duration_s must be > 0")
    if cfg.tank_volume_m3 <= 0:
        raise ValueError("tank_volume_m3 must be > 0")

    volume = cfg.tank_volume_m3
    concentration = cfg.initial_concentration
    timeline: list[SimulationPoint] = [SimulationPoint(0.0, concentration, volume)]

    steps = int(cfg.duration_s / cfg.dt_s)
    for step in range(1, steps + 1):
        volume, concentration = _next_state(volume, concentration, cfg)
        timeline.append(SimulationPoint(step * cfg.dt_s, concentration, volume))

    return timeline
