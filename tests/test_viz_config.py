from __future__ import annotations

from mixing_module.viz_config import load_and_migrate_viz_config, validate_viz_config


def test_viz_config_migration_adds_missing_defaults(tmp_path) -> None:
    cfg_path = tmp_path / "viz_params.yaml"
    cfg_path.write_text("rsd_target_percent: 4.0\n", encoding="utf-8")
    cfg, migrated, errors = load_and_migrate_viz_config(cfg_path)
    assert migrated
    assert cfg["risk_thresholds"]["status"]["alarm_rsd_percent"] == 8.0
    assert errors == []


def test_viz_config_validation_detects_bad_ranges() -> None:
    cfg = {
        "rsd_target_percent": 5.0,
        "alpha_seg": 0.3,
        "beta_hygro": 0.1,
        "gamma_seg": 0.01,
        "n_particles": 5000,
        "risk_thresholds": {
            "material_config": {
                "hausner": {"ok_max": 1.4, "warn_max": 1.2},
                "span": {"ok_max": 1.2, "warn_max": 1.5},
                "segregation_idx": {"ok_max": 0.2, "warn_max": 0.3},
                "angle_repose_deg": {"ok_max": 30.0, "warn_max": 40.0},
                "moisture_warn_fraction": 0.9,
            },
            "status": {
                "rsd_warn_factor": 1.2,
                "h_warn_fraction": 0.9,
                "alarm_rsd_percent": 8.0,
                "reaction_rate_warn": 0.25,
            },
        },
    }
    errors = validate_viz_config(cfg)
    assert any("hausner" in item.lower() for item in errors)
