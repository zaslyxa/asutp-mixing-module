from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .material_db import MaterialComponent


@dataclass(frozen=True)
class RecipeRow:
    component: MaterialComponent
    mass_kg: float


def _weighted(rows: list[RecipeRow], attr: str) -> float:
    total = sum(r.mass_kg for r in rows)
    if total <= 0:
        raise ValueError("total mass must be > 0")
    return sum((r.mass_kg / total) * float(getattr(r.component, attr)) for r in rows)


def _hausner_factor(hausner: float) -> float:
    if hausner <= 1.25:
        return 1.0
    return max(0.4, 1.0 - 0.8 * (hausner - 1.25))


def scaling_engine(
    rows: list[RecipeRow],
    *,
    k_ref: float = 0.0667,
    pe_ref: float = 3.0,
    ka0: float = 0.02,
    beta: float = 0.08,
    kh0: float = 0.02,
    rho_ref: float = 1450.0,
    cp_ref: float = 900.0,
    angle_ref: float = 35.0,
    rotor_speed_ref: float = 1.0,
    rotor_speed: float = 1.0,
    q_l_target: float = 0.2,
    cell_volume_m3: float = 1.0,
) -> dict:
    if not rows:
        raise ValueError("recipe must contain at least one component")

    rho_mix = _weighted(rows, "rho_bulk")
    cp_mix = _weighted(rows, "cp")
    w0_mix = _weighted(rows, "w_initial")
    span_mix = _weighted(rows, "span")
    angle_mix = _weighted(rows, "angle_repose")
    hausner_mix = _weighted(rows, "hausner_ratio")
    segregation_mix = _weighted(rows, "segregation_idx")
    w_eq_mix = _weighted(rows, "w_equilibrium")
    w_crit_mix = min(r.component.w_crit for r in rows)

    k = k_ref * (rho_ref / rho_mix) ** 0.3 * _hausner_factor(hausner_mix)
    pe = pe_ref * (1.0 / max(span_mix, 1e-6)) ** 0.5 * (angle_ref / max(angle_mix, 1e-6))
    ka = ka0 * (2.718281828459045 ** (beta * (w0_mix / max(w_crit_mix, 1e-6))))
    kh = kh0 * (max(rotor_speed, 1e-6) / max(rotor_speed_ref, 1e-6)) ** 0.5 * (cp_mix / cp_ref) ** (-0.4)
    b = q_l_target / max(cell_volume_m3 * rho_mix, 1e-9)

    warnings: list[str] = []
    if w0_mix > 0.8 * w_crit_mix:
        warnings.append("Moisture is close to critical transition threshold")
    if hausner_mix > 1.4:
        warnings.append("Poor flowability (Hausner > 1.4), increase rotor speed or pre-dry")

    return {
        "mixture": {
            "rho_b_mix": rho_mix,
            "cp_mix": cp_mix,
            "w0_mix": w0_mix,
            "w_crit_mix": w_crit_mix,
            "hausner_mix": hausner_mix,
            "span_mix": span_mix,
            "angle_repose_mix": angle_mix,
            "segregation_idx_mix": segregation_mix,
            "w_eq_mix": w_eq_mix,
        },
        "model": {
            "k": k,
            "pe": pe,
            "ka": ka,
            "kh": kh,
            "b_q": b,
        },
        "warnings": warnings,
    }


def update_recipe_cache(payload: dict, path: str | Path = "config/recipe_cache.json") -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        current = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        current = {}
    current[digest] = payload
    cache_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return digest
