from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class HomogenizationPoint:
    time_s: float
    sigma2: float
    rsd_percent: float
    lacey_index: float
    h_rel: float
    sigma0_2: float
    sigma_r_eff_2: float


def calc_sigma2(samples: list[float]) -> float:
    if not samples:
        return 0.0
    mean = sum(samples) / len(samples)
    return sum((x - mean) ** 2 for x in samples) / len(samples)


def calc_rsd(samples: list[float], c_bar: float) -> float:
    if c_bar <= 0:
        return 0.0
    sigma2 = calc_sigma2(samples)
    return math.sqrt(max(sigma2, 0.0)) / c_bar * 100.0


def calc_lacey_index(
    sigma2: float,
    c_bar: float,
    n_particles: int,
    segregation_idx_mix: float,
    w_mix: float,
    w_eq_mix: float,
    *,
    alpha_seg: float = 0.3,
    beta_hygro: float = 0.15,
) -> tuple[float, float, float]:
    sigma0_2 = c_bar * max(1.0 - c_bar, 0.0)
    sigma_r_2 = sigma0_2 / max(float(n_particles), 1.0)
    sigma_r_eff_2 = sigma_r_2 * (1.0 + alpha_seg * segregation_idx_mix) * (
        1.0 + beta_hygro * abs(w_mix - w_eq_mix)
    )
    denom = max(sigma0_2 - sigma_r_eff_2, 1e-9)
    lacey = (sigma0_2 - sigma2) / denom
    lacey = min(max(lacey, 0.0), 1.0)
    return lacey, sigma0_2, sigma_r_eff_2


def calc_h_rel(sigma2: float, sigma0_2: float) -> float:
    if sigma0_2 <= 0:
        return 0.0
    return min(max(1.0 - sigma2 / sigma0_2, 0.0), 1.0)


def calc_online_homogenization_series(
    *,
    times_s: list[float],
    concentration_by_time: list[list[float]],
    moisture_out_by_time: list[float],
    c_bar: float,
    n_particles: int,
    segregation_idx_mix: float,
    w_eq_mix: float,
    alpha_seg: float = 0.3,
    beta_hygro: float = 0.15,
) -> list[HomogenizationPoint]:
    out: list[HomogenizationPoint] = []
    for idx, time_s in enumerate(times_s):
        c_cells = concentration_by_time[idx]
        w_mix = moisture_out_by_time[idx] if idx < len(moisture_out_by_time) else 0.0
        sigma2 = calc_sigma2(c_cells)
        rsd = calc_rsd(c_cells, c_bar)
        lacey, sigma0_2, sigma_r_eff_2 = calc_lacey_index(
            sigma2=sigma2,
            c_bar=c_bar,
            n_particles=n_particles,
            segregation_idx_mix=segregation_idx_mix,
            w_mix=w_mix,
            w_eq_mix=w_eq_mix,
            alpha_seg=alpha_seg,
            beta_hygro=beta_hygro,
        )
        out.append(
            HomogenizationPoint(
                time_s=time_s,
                sigma2=sigma2,
                rsd_percent=rsd,
                lacey_index=lacey,
                h_rel=calc_h_rel(sigma2, sigma0_2),
                sigma0_2=sigma0_2,
                sigma_r_eff_2=sigma_r_eff_2,
            )
        )
    return out


def component_contributions(last_components_by_cell: list[list[float]]) -> list[float]:
    if not last_components_by_cell:
        return []
    n_cells = len(last_components_by_cell)
    n_comp = len(last_components_by_cell[0])
    contribs = [0.0 for _ in range(n_comp)]
    total = 0.0
    for j in range(n_comp):
        vals = [last_components_by_cell[i][j] for i in range(n_cells)]
        avg = sum(vals) / n_cells
        var = sum((v - avg) ** 2 for v in vals) / n_cells
        contribs[j] = max(var, 0.0)
        total += contribs[j]
    if total <= 0:
        return [0.0 for _ in contribs]
    return [c / total for c in contribs]
