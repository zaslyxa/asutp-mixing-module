from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_VIZ_CONFIG: dict[str, Any] = {
    "rsd_target_percent": 5.0,
    "alpha_seg": 0.3,
    "beta_hygro": 0.15,
    "gamma_seg": 0.01,
    "n_particles": 5000,
    "dashboard_update_hz": 1.0,
    "trend_update_hz": 0.5,
    "prediction_update_hz": 0.2,
    "risk_thresholds": {
        "material_config": {
            "hausner": {"ok_max": 1.18, "warn_max": 1.30},
            "span": {"ok_max": 1.40, "warn_max": 1.90},
            "segregation_idx": {"ok_max": 0.35, "warn_max": 0.60},
            "angle_repose_deg": {"ok_max": 34.0, "warn_max": 42.0},
            "moisture_warn_fraction": 0.90,
        },
        "status": {
            "rsd_warn_factor": 1.20,
            "h_warn_fraction": 0.92,
            "alarm_rsd_percent": 8.0,
            "reaction_rate_warn": 0.25,
        },
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def migrate_viz_config(raw: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    merged = _deep_merge(DEFAULT_VIZ_CONFIG, raw)
    migrated = merged != raw
    return merged, migrated


def validate_viz_config(cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def _num(path: str, value: Any, lo: float, hi: float) -> None:
        if not isinstance(value, (int, float)):
            errors.append(f"{path} must be numeric.")
            return
        if not (lo <= float(value) <= hi):
            errors.append(f"{path} out of range [{lo}, {hi}].")

    _num("rsd_target_percent", cfg.get("rsd_target_percent"), 0.1, 100.0)
    _num("alpha_seg", cfg.get("alpha_seg"), 0.0, 5.0)
    _num("beta_hygro", cfg.get("beta_hygro"), 0.0, 5.0)
    _num("gamma_seg", cfg.get("gamma_seg"), 0.0, 2.0)
    _num("n_particles", cfg.get("n_particles"), 1.0, 10_000_000.0)

    mat = cfg.get("risk_thresholds", {}).get("material_config", {})
    for name in ("hausner", "span", "segregation_idx", "angle_repose_deg"):
        block = mat.get(name, {})
        ok_max = block.get("ok_max")
        warn_max = block.get("warn_max")
        _num(f"risk_thresholds.material_config.{name}.ok_max", ok_max, -1_000_000, 1_000_000)
        _num(f"risk_thresholds.material_config.{name}.warn_max", warn_max, -1_000_000, 1_000_000)
        if isinstance(ok_max, (int, float)) and isinstance(warn_max, (int, float)) and warn_max < ok_max:
            errors.append(f"risk_thresholds.material_config.{name}: warn_max must be >= ok_max.")
    _num("risk_thresholds.material_config.moisture_warn_fraction", mat.get("moisture_warn_fraction"), 0.0, 2.0)

    status = cfg.get("risk_thresholds", {}).get("status", {})
    _num("risk_thresholds.status.rsd_warn_factor", status.get("rsd_warn_factor"), 1.0, 5.0)
    _num("risk_thresholds.status.h_warn_fraction", status.get("h_warn_fraction"), 0.0, 1.0)
    _num("risk_thresholds.status.alarm_rsd_percent", status.get("alarm_rsd_percent"), 0.1, 100.0)
    _num("risk_thresholds.status.reaction_rate_warn", status.get("reaction_rate_warn"), 0.0, 20.0)

    return errors


def load_and_migrate_viz_config(path: str | Path = "config/viz_params.yaml") -> tuple[dict[str, Any], bool, list[str]]:
    cfg_path = Path(path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any] = {}
    created = False
    if cfg_path.exists():
        parsed = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            raise ValueError("viz_params.yaml must contain a YAML mapping/object at root.")
        raw = parsed
    else:
        created = True
    migrated_cfg, migrated = migrate_viz_config(raw)
    errors = validate_viz_config(migrated_cfg)
    if migrated or created:
        cfg_path.write_text(yaml.safe_dump(migrated_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return migrated_cfg, (migrated or created), errors
