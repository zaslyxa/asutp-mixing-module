from __future__ import annotations

from typing import Any
from pathlib import Path
import sys
import json

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import yaml

if __package__ in (None, ""):
    # Support direct execution by Streamlit: `streamlit run src/mixing_module/ui.py`
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from mixing_module.cascade import DryCascadeConfig, run_dry_cascade
    from mixing_module.recipe_storage import load_recipe, save_recipe
    from mixing_module.recipes import get_recipe, recipe_names
    from mixing_module.material_db import get_component_by_code, init_material_db, list_components
    from mixing_module.homogenization_metrics import calc_online_homogenization_series, component_contributions
    from mixing_module.homogenization_opc import build_opc_payload
    from mixing_module.homogenization_plots import (
        component_contribution_dataframe,
        concentration_profile_dataframe,
        metrics_dataframe,
    )
    from mixing_module.homogenization_predictor import predict_endpoint, uncertainty_bands
    from mixing_module.homogenization_report import export_homogenization_report
    from mixing_module.h_kinetics import HMixConfig
    from mixing_module.mix_quality_runtime import MixQualityRuntime
    from mixing_module.historian import append_h_sample, init_historian_db, list_batches, load_batch_curve
    from mixing_module.io_contracts import mqtt_topics
    from mixing_module.integration_validation import build_publish_bundle, validate_opc_payload
    from mixing_module.quality_monitoring import confidence_score, drift_against_baseline, trend_alerts
    from mixing_module.recipe_changelog import generate_recipe_changelog
    from mixing_module.release_evidence import build_release_evidence_zip
    from mixing_module.recipe_versioning import (
        diff_recipe_revisions,
        list_recipe_revisions,
        load_recipe_revision,
        save_recipe_revision,
    )
    from mixing_module.scaling import RecipeRow, scaling_engine, update_recipe_cache
    from mixing_module.viz_config import load_and_migrate_viz_config
    from mixing_module.wet_model import WetCascadeConfig, run_wet_cascade
else:
    from .cascade import DryCascadeConfig, run_dry_cascade
    from .recipe_storage import load_recipe, save_recipe
    from .recipes import get_recipe, recipe_names
    from .material_db import get_component_by_code, init_material_db, list_components
    from .homogenization_metrics import calc_online_homogenization_series, component_contributions
    from .homogenization_opc import build_opc_payload
    from .homogenization_plots import (
        component_contribution_dataframe,
        concentration_profile_dataframe,
        metrics_dataframe,
    )
    from .homogenization_predictor import predict_endpoint, uncertainty_bands
    from .homogenization_report import export_homogenization_report
    from .h_kinetics import HMixConfig
    from .mix_quality_runtime import MixQualityRuntime
    from .historian import append_h_sample, init_historian_db, list_batches, load_batch_curve
    from .io_contracts import mqtt_topics
    from .integration_validation import build_publish_bundle, validate_opc_payload
    from .quality_monitoring import confidence_score, drift_against_baseline, trend_alerts
    from .recipe_changelog import generate_recipe_changelog
    from .release_evidence import build_release_evidence_zip
    from .recipe_versioning import (
        diff_recipe_revisions,
        list_recipe_revisions,
        load_recipe_revision,
        save_recipe_revision,
    )
    from .scaling import RecipeRow, scaling_engine, update_recipe_cache
    from .viz_config import load_and_migrate_viz_config
    from .wet_model import WetCascadeConfig, run_wet_cascade


def _build_dry_concentration_series(points: list) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for p in points:
        for idx, value in enumerate(p.concentrations, start=1):
            rows.append({"time_s": p.time_s, "cell": f"Cell {idx}", "concentration": value})
    return pd.DataFrame(rows)


def _build_temperature_series(points: list) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for p in points:
        for idx, value in enumerate(p.temperatures, start=1):
            rows.append({"time_s": p.time_s, "cell": f"Cell {idx}", "temperature_c": value})
    return pd.DataFrame(rows)


def _build_wet_component_series(points: list, n_components: int) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for p in points:
        outlet = p.components[-1]
        for j in range(n_components):
            rows.append(
                {
                    "time_s": p.time_s,
                    "component": f"Component {j+1}",
                    "outlet_concentration": outlet[j],
                }
            )
    return pd.DataFrame(rows)


def _build_wet_scalar_series(points: list) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for p in points:
        rows.append(
            {
                "time_s": p.time_s,
                "w_out": p.moisture[-1],
                "eta_out": p.eta[-1],
                "t_out": p.temperatures[-1],
                "reaction_out": p.reaction_rate_cells[-1],
            }
        )
    return pd.DataFrame(rows)


def _inject_ui_css() -> None:
    st.markdown(
        """
        <style>
        div.sticky-kpi {
            position: sticky;
            top: 0.25rem;
            z-index: 20;
            background: rgba(14, 17, 23, 0.92);
            border: 1px solid rgba(151, 166, 195, 0.25);
            border-radius: 10px;
            padding: 0.4rem 0.6rem;
            margin-bottom: 0.6rem;
            backdrop-filter: blur(2px);
        }
        .risk-tag {
            display: inline-block;
            padding: 0.1rem 0.45rem;
            border-radius: 999px;
            font-size: 0.78rem;
            margin-left: 0.35rem;
            border: 1px solid transparent;
        }
        .risk-ok {
            color: #60d394;
            border-color: rgba(96, 211, 148, 0.35);
            background: rgba(96, 211, 148, 0.10);
        }
        .risk-warn {
            color: #ffca3a;
            border-color: rgba(255, 202, 58, 0.35);
            background: rgba(255, 202, 58, 0.10);
        }
        .risk-error {
            color: #ff595e;
            border-color: rgba(255, 89, 94, 0.35);
            background: rgba(255, 89, 94, 0.10);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _severity(level: str, message: str) -> None:
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.success(message)


def _best_known_templates() -> dict[str, dict[str, Any]]:
    return {
        "Fast dry blending": {
            "target_rsd": 4.0,
            "payload": {
                "model": "dry-cascade",
                "shared": {"duration_s": 90.0, "dt_s": 1.0, "cells": 4, "tau_s": 35.0, "kh": 0.03, "t_in": 25.0, "t_wall": 30.0},
            },
        },
        "Robust wet mixing": {
            "target_rsd": 5.0,
            "payload": {
                "model": "wet-cascade",
                "shared": {"duration_s": 140.0, "dt_s": 1.0, "cells": 4, "tau_s": 55.0, "kh": 0.03, "t_in": 24.0, "t_wall": 29.0},
                "wet": {"w_in": 0.12, "w0": 0.06, "q_liquid": 0.20, "b_q": 0.05, "ka": 0.025, "kb": 0.0012, "w_star": 0.15},
            },
        },
    }


def _render_onboarding() -> None:
    if st.session_state.get("onboarding_dismissed", False):
        return
    with st.expander("Operator quick start", expanded=True):
        st.markdown(
            "- 1) Select recipe and page layout in sidebar.\n"
            "- 2) Configure materials in left panel and validate risk tags.\n"
            "- 3) Run process in right panel, then check HomogenizationViz KPIs.\n"
            "- 4) Use Integration tab for OPC/MQTT payload validation and dry-run publish.\n"
            "- 5) Save recipe revision snapshots before applying production changes."
        )
        if st.button("Dismiss quick start", key="dismiss_onboarding_btn"):
            st.session_state["onboarding_dismissed"] = True
            st.rerun()


def _risk_level(value: float, *, good_max: float, warn_max: float) -> str:
    if value <= good_max:
        return "ok"
    if value <= warn_max:
        return "warn"
    return "error"


def _risk_tag(level: str) -> str:
    cls = {"ok": "risk-ok", "warn": "risk-warn", "error": "risk-error"}[level]
    text = {"ok": "OK", "warn": "Warning", "error": "Alarm"}[level]
    return f"<span class='risk-tag {cls}'>{text}</span>"


@st.cache_data(show_spinner=False)
def _load_viz_params(path: str = "config/viz_params.yaml") -> dict[str, Any]:
    try:
        payload, migrated, errors = load_and_migrate_viz_config(path)
        result = dict(payload)
        result["_meta"] = {"migrated": migrated, "errors": errors}
        return result
    except Exception as exc:
        return {"_meta": {"migrated": False, "errors": [str(exc)]}}


def _material_risk_thresholds() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "hausner": {"ok_max": 1.18, "warn_max": 1.30},
        "span": {"ok_max": 1.40, "warn_max": 1.90},
        "segregation_idx": {"ok_max": 0.35, "warn_max": 0.60},
        "angle_repose_deg": {"ok_max": 34.0, "warn_max": 42.0},
        "moisture_warn_fraction": 0.90,
    }
    cfg = _load_viz_params().get("risk_thresholds", {}).get("material_config", {})
    if isinstance(cfg, dict):
        for key, value in cfg.items():
            if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                defaults[key].update(value)
            elif key in defaults:
                defaults[key] = value
    return defaults


def _status_thresholds() -> dict[str, float]:
    defaults: dict[str, float] = {
        "rsd_warn_factor": 1.2,
        "h_warn_fraction": 0.92,
        "alarm_rsd_percent": 8.0,
        "reaction_rate_warn": 0.25,
    }
    cfg = _load_viz_params().get("risk_thresholds", {}).get("status", {})
    if isinstance(cfg, dict):
        for key, value in cfg.items():
            if key in defaults:
                defaults[key] = float(value)
    return defaults


def _threshold_profiles() -> dict[str, dict[str, Any]]:
    return {
        "normal": {
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
        "conservative": {
            "material_config": {
                "hausner": {"ok_max": 1.15, "warn_max": 1.24},
                "span": {"ok_max": 1.25, "warn_max": 1.65},
                "segregation_idx": {"ok_max": 0.25, "warn_max": 0.45},
                "angle_repose_deg": {"ok_max": 30.0, "warn_max": 37.0},
                "moisture_warn_fraction": 0.80,
            },
            "status": {
                "rsd_warn_factor": 1.10,
                "h_warn_fraction": 0.96,
                "alarm_rsd_percent": 6.0,
                "reaction_rate_warn": 0.18,
            },
        },
        "aggressive": {
            "material_config": {
                "hausner": {"ok_max": 1.22, "warn_max": 1.38},
                "span": {"ok_max": 1.60, "warn_max": 2.20},
                "segregation_idx": {"ok_max": 0.45, "warn_max": 0.75},
                "angle_repose_deg": {"ok_max": 36.0, "warn_max": 46.0},
                "moisture_warn_fraction": 0.95,
            },
            "status": {
                "rsd_warn_factor": 1.35,
                "h_warn_fraction": 0.88,
                "alarm_rsd_percent": 10.0,
                "reaction_rate_warn": 0.35,
            },
        },
    }


def _save_risk_thresholds(
    *,
    material_cfg: dict[str, Any],
    status_cfg: dict[str, float],
    path: str = "config/viz_params.yaml",
) -> None:
    cfg, _, _ = load_and_migrate_viz_config(path)
    risk = cfg.get("risk_thresholds", {})
    if not isinstance(risk, dict):
        risk = {}
    risk["material_config"] = material_cfg
    risk["status"] = status_cfg
    cfg["risk_thresholds"] = risk
    cfg_path = Path(path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    _load_viz_params.clear()


def _render_threshold_editor_sidebar() -> None:
    with st.expander("Risk thresholds editor", expanded=False):
        material_cfg = _material_risk_thresholds()
        status_cfg = _status_thresholds()
        st.caption("Adjust thresholds and save to config/viz_params.yaml")
        profiles = _threshold_profiles()
        profile_name = st.selectbox(
            "Threshold profile",
            options=["custom", "normal", "conservative", "aggressive"],
            index=0,
            key="threshold_profile_name",
            help="Use presets for quick switching, or keep custom.",
        )
        p1, p2, p3 = st.columns(3)
        with p1:
            if st.button("Apply profile", key="apply_threshold_profile") and profile_name != "custom":
                preset = profiles[profile_name]
                _save_risk_thresholds(material_cfg=preset["material_config"], status_cfg=preset["status"])
                st.success(f"Applied profile: {profile_name}")
                st.rerun()
        with p2:
            if st.button("Reset defaults", key="reset_threshold_profile"):
                preset = profiles["normal"]
                _save_risk_thresholds(material_cfg=preset["material_config"], status_cfg=preset["status"])
                st.success("Thresholds reset to normal defaults")
                st.rerun()
        with p3:
            export_obj = {
                "material_config": material_cfg,
                "status": status_cfg,
            }
            st.download_button(
                "Export profile",
                data=json.dumps(export_obj, indent=2, ensure_ascii=False),
                file_name="threshold-profile.json",
                mime="application/json",
                key="export_threshold_profile_btn",
            )
        uploaded = st.file_uploader("Import profile (.json)", type=["json"], key="threshold_import_file")
        if uploaded is not None and st.button("Import profile", key="import_threshold_profile_btn"):
            try:
                incoming = json.loads(uploaded.getvalue().decode("utf-8"))
                _save_risk_thresholds(
                    material_cfg=dict(incoming.get("material_config", {})),
                    status_cfg=dict(incoming.get("status", {})),
                )
                st.success("Threshold profile imported")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to import profile: {exc}")

        st.markdown("**MaterialConfig thresholds**")
        mc1, mc2 = st.columns(2)
        with mc1:
            hausner_ok = st.number_input("Hausner OK max", min_value=1.0, max_value=2.0, step=0.01, value=float(material_cfg["hausner"]["ok_max"]), key="thr_hausner_ok")
            span_ok = st.number_input("Span OK max", min_value=0.5, max_value=5.0, step=0.05, value=float(material_cfg["span"]["ok_max"]), key="thr_span_ok")
            seg_ok = st.number_input("Segregation OK max", min_value=0.0, max_value=1.0, step=0.01, value=float(material_cfg["segregation_idx"]["ok_max"]), key="thr_seg_ok")
            angle_ok = st.number_input("Angle OK max", min_value=10.0, max_value=80.0, step=0.5, value=float(material_cfg["angle_repose_deg"]["ok_max"]), key="thr_angle_ok")
        with mc2:
            hausner_warn = st.number_input("Hausner warning max", min_value=1.0, max_value=2.5, step=0.01, value=float(material_cfg["hausner"]["warn_max"]), key="thr_hausner_warn")
            span_warn = st.number_input("Span warning max", min_value=0.5, max_value=6.0, step=0.05, value=float(material_cfg["span"]["warn_max"]), key="thr_span_warn")
            seg_warn = st.number_input("Segregation warning max", min_value=0.0, max_value=1.5, step=0.01, value=float(material_cfg["segregation_idx"]["warn_max"]), key="thr_seg_warn")
            angle_warn = st.number_input("Angle warning max", min_value=10.0, max_value=90.0, step=0.5, value=float(material_cfg["angle_repose_deg"]["warn_max"]), key="thr_angle_warn")
        moisture_warn_fraction = st.number_input(
            "Moisture warning fraction",
            min_value=0.1,
            max_value=1.2,
            step=0.01,
            value=float(material_cfg["moisture_warn_fraction"]),
            key="thr_moisture_warn_fraction",
            help="Warning if w_initial > fraction * w_crit; alarm if w_initial > w_crit.",
        )

        st.markdown("**Status thresholds**")
        st1, st2 = st.columns(2)
        with st1:
            rsd_warn_factor = st.number_input(
                "RSD warning factor",
                min_value=1.0,
                max_value=3.0,
                step=0.05,
                value=float(status_cfg["rsd_warn_factor"]),
                key="thr_rsd_warn_factor",
                help="Warning when RSD > rsd_target * factor.",
            )
            h_warn_fraction = st.number_input(
                "H warning fraction",
                min_value=0.5,
                max_value=1.0,
                step=0.01,
                value=float(status_cfg["h_warn_fraction"]),
                key="thr_h_warn_fraction",
                help="Warning when H < h_target but >= h_target * fraction.",
            )
        with st2:
            alarm_rsd_percent = st.number_input(
                "Alarm RSD threshold, %",
                min_value=0.5,
                max_value=50.0,
                step=0.5,
                value=float(status_cfg["alarm_rsd_percent"]),
                key="thr_alarm_rsd_percent",
            )
            reaction_rate_warn = st.number_input(
                "Reaction warning rate",
                min_value=0.0,
                max_value=5.0,
                step=0.01,
                value=float(status_cfg["reaction_rate_warn"]),
                key="thr_reaction_rate_warn",
            )

        if st.button("Save thresholds", key="save_thresholds_btn"):
            if hausner_warn < hausner_ok or span_warn < span_ok or seg_warn < seg_ok or angle_warn < angle_ok:
                st.error("Warning max must be >= OK max for all material thresholds.")
            else:
                updated_material = {
                    "hausner": {"ok_max": float(hausner_ok), "warn_max": float(hausner_warn)},
                    "span": {"ok_max": float(span_ok), "warn_max": float(span_warn)},
                    "segregation_idx": {"ok_max": float(seg_ok), "warn_max": float(seg_warn)},
                    "angle_repose_deg": {"ok_max": float(angle_ok), "warn_max": float(angle_warn)},
                    "moisture_warn_fraction": float(moisture_warn_fraction),
                }
                updated_status = {
                    "rsd_warn_factor": float(rsd_warn_factor),
                    "h_warn_fraction": float(h_warn_fraction),
                    "alarm_rsd_percent": float(alarm_rsd_percent),
                    "reaction_rate_warn": float(reaction_rate_warn),
                }
                _save_risk_thresholds(material_cfg=updated_material, status_cfg=updated_status)
                st.success("Thresholds saved to config/viz_params.yaml")
                st.rerun()


def _ensure_default_state() -> None:
    defaults = {
        "selected_recipe_name": recipe_names()[0],
        "recipe_file_path": "recipes/current_recipe.json",
        "duration_s": 120.0,
        "dt_s": 1.0,
        "cells": 3,
        "tau_s": 45.0,
        "kh": 0.02,
        "t_in": 25.0,
        "t_wall": 30.0,
        "n_components": 3,
        "w_in": 0.10,
        "w0": 0.05,
        "eta0": 1.0,
        "q_liquid": 0.2,
        "b_q": 0.05,
        "j_add": 2,
        "ka": 0.02,
        "kb": 0.001,
        "w_star": 0.15,
        "reaction_enabled": False,
        "reaction_rate": 0.05,
        "effect_heat_release": True,
        "effect_precipitation": False,
        "effect_gas_evolution": False,
        "heat_release_gain": 5.0,
        "precipitation_gain": 0.02,
        "gas_strip_gain": 0.01,
        "material_db_path": "config/materials.db",
        "use_material_scaling": True,
        "rotor_speed": 1.0,
        "cell_volume_m3": 1.0,
        "q_l_target": 0.2,
        "material_row_count": 3,
        "n_particles": 5000,
        "alpha_seg": 0.3,
        "beta_hygro": 0.15,
        "gamma_seg": 0.01,
        "rsd_target": 5.0,
        "batch_id": "2026-001",
        "report_path": "reports/homogenization_report.txt",
        "historian_db_path": "config/historian.db",
        "mixer_id": "mx-01",
        "viz_mode": "online",
        "layout_mode": "Desktop (2:3)",
        "onboarding_dismissed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    for idx in range(10):
        st.session_state.setdefault(f"inlet_{idx}", 1.0 if idx == 0 else 0.0)
        st.session_state.setdefault(f"initial_{idx}", 0.0)


def _apply_loaded_recipe(payload: dict[str, Any]) -> None:
    model = payload.get("model", "dry-cascade")
    if model == "wet-cascade":
        st.session_state["selected_recipe_name"] = "Wet mixing"
    else:
        st.session_state["selected_recipe_name"] = "Dry mixing"

    shared = payload.get("shared", {})
    for key in ("duration_s", "dt_s", "cells", "tau_s", "kh", "t_in", "t_wall"):
        if key in shared:
            st.session_state[key] = shared[key]

    wet = payload.get("wet", {})
    if wet:
        inlet = wet.get("component_inlet", [])
        initial = wet.get("component_initial", [])
        st.session_state["n_components"] = max(len(inlet), len(initial), 1)
        for idx in range(st.session_state["n_components"]):
            if idx < len(inlet):
                st.session_state[f"inlet_{idx}"] = inlet[idx]
            if idx < len(initial):
                st.session_state[f"initial_{idx}"] = initial[idx]
        for key in (
            "w_in",
            "w0",
            "eta0",
            "q_liquid",
            "b_q",
            "j_add",
            "ka",
            "kb",
            "w_star",
            "reaction_enabled",
            "reaction_rate",
            "effect_heat_release",
            "effect_precipitation",
            "effect_gas_evolution",
            "heat_release_gain",
            "precipitation_gain",
            "gas_strip_gain",
        ):
            if key in wet:
                st.session_state[key] = wet[key]
    material = payload.get("material_config", {})
    if material:
        for key in ("use_material_scaling", "rotor_speed", "cell_volume_m3", "q_l_target"):
            if key in material:
                st.session_state[key] = material[key]
        rows = material.get("rows", [])
        if rows:
            st.session_state["material_row_count"] = len(rows)
            components = list_components(st.session_state.get("material_db_path"))
            by_code = {c.code: f"{c.name} ({c.code})" for c in components}
            for idx, row in enumerate(rows):
                if row.get("code") in by_code:
                    st.session_state[f"mat_name_{idx}"] = by_code[row["code"]]
                st.session_state[f"mat_mass_{idx}"] = float(row.get("mass_kg", 0.0))
    viz = payload.get("viz_config", {})
    if viz:
        for key in (
            "n_particles",
            "alpha_seg",
            "beta_hygro",
            "gamma_seg",
            "rsd_target",
            "batch_id",
            "report_path",
            "historian_db_path",
            "mixer_id",
            "viz_mode",
        ):
            if key in viz:
                st.session_state[key] = viz[key]


def _run_dry_view(
    duration_s: float,
    dt_s: float,
    cells: int,
    tau_s: float,
    kh: float,
    t_in: float,
    t_wall: float,
    auto_params: dict[str, float],
    material_payload: dict[str, Any],
) -> dict[str, Any]:
    if auto_params:
        tau_s = float(auto_params.get("tau_s", tau_s))
        kh = float(auto_params.get("kh", kh))
        st.info(f"MaterialConfig auto-scaling applied for dry model: tau={tau_s:.2f}, kh={kh:.4f}")

    cfg = DryCascadeConfig(
        duration_s=duration_s,
        dt_s=dt_s,
        cells=cells,
        tau_s=tau_s,
        kh=kh,
        t_in=t_in,
        t_wall=t_wall,
    )
    points = run_dry_cascade(cfg)
    c_df = _build_dry_concentration_series(points)
    t_df = _build_temperature_series(points)

    left, right = st.columns(2)
    with left:
        st.subheader("Concentration dynamics by cell")
        st.line_chart(c_df, x="time_s", y="concentration", color="cell")
    with right:
        st.subheader("Temperature dynamics by cell")
        st.line_chart(t_df, x="time_s", y="temperature_c", color="cell")

    nearest = points[-1]
    st.info(
        f"Dry outlet at t={nearest.time_s:.1f}s: "
        f"c_out={nearest.concentrations[-1]:.4f}, T_out={nearest.temperatures[-1]:.2f}C"
    )
    return {
        "model": "dry-cascade",
        "shared": {
            "duration_s": duration_s,
            "dt_s": dt_s,
            "cells": cells,
            "tau_s": tau_s,
            "kh": kh,
            "t_in": t_in,
            "t_wall": t_wall,
        },
        "material_config": material_payload,
    }


def _render_material_config(cells: int) -> tuple[dict[str, float], dict[str, Any]]:
    st.subheader("MaterialConfig")
    with st.expander("Data source", expanded=True):
        db_path = st.text_input("Material DB path", key="material_db_path")
    init_material_db(db_path)
    available = list_components(db_path)
    with st.expander("Material catalog", expanded=False):
        search_text = st.text_input("Search material", key="material_search_text")
        tags = sorted({c.type for c in available})
        selected_tags = st.multiselect("Tags", options=tags, default=tags, key="material_search_tags")
        filtered = [
            c
            for c in available
            if (not search_text or search_text.lower() in f"{c.name} {c.code}".lower())
            and (not selected_tags or c.type in selected_tags)
        ]
        st.caption(f"Catalog matches: {len(filtered)} / {len(available)}")
        if filtered:
            st.dataframe(
                pd.DataFrame([{"code": c.code, "name": c.name, "type": c.type, "d50_um": c.d50, "span": c.span} for c in filtered]),
                use_container_width=True,
                height=180,
            )

    names = [f"{c.name} ({c.code})" for c in available]
    name_to_code = {f"{c.name} ({c.code})": c.code for c in available}

    recipe_rows: list[RecipeRow] = []
    with st.expander("Recipe rows", expanded=True):
        st.caption("Select components from database and set masses for scaling")
        mat_count = st.slider("Material rows", 1, 8, 3, 1, key="material_row_count")
        for i in range(mat_count):
            col_l, col_r = st.columns([2, 1])
            with col_l:
                key_name = f"mat_name_{i}"
                if key_name not in st.session_state or st.session_state[key_name] not in names:
                    st.session_state[key_name] = names[0]
                selected = st.selectbox(
                    f"Material {i+1}",
                    options=names,
                    key=key_name,
                )
            with col_r:
                mass = st.number_input(
                    f"kg #{i+1}",
                    min_value=0.0,
                    value=10.0 if i == 0 else 0.0,
                    step=1.0,
                    key=f"mat_mass_{i}",
                )
            if mass > 0:
                code = name_to_code[selected]
                recipe_rows.append(RecipeRow(component=get_component_by_code(code, db_path), mass_kg=mass))

    if recipe_rows:
        st.markdown("**Selected components and characteristics**")
        total_mass = sum(r.mass_kg for r in recipe_rows)
        table_rows: list[dict[str, float | str]] = []
        for r in recipe_rows:
            c = r.component
            share = (r.mass_kg / total_mass * 100.0) if total_mass > 0 else 0.0
            table_rows.append(
                {
                    "code": c.code,
                    "name": c.name,
                    "type": c.type,
                    "mass_kg": round(r.mass_kg, 3),
                    "share_%": round(share, 2),
                    "d50_um": round(c.d50, 3),
                    "span": round(c.span, 3),
                    "rho_bulk": round(c.rho_bulk, 3),
                    "hausner": round(c.hausner_ratio, 3),
                    "w_initial_%": round(c.w_initial, 3),
                    "w_crit_%": round(c.w_crit, 3),
                    "w_eq_%": round(c.w_equilibrium, 3),
                    "cp_JkgK": round(c.cp, 3),
                    "angle_repose_deg": round(c.angle_repose, 3),
                    "segregation_idx": round(c.segregation_idx, 3),
                }
            )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=280)

        with st.expander("Component card", expanded=False):
            thresholds = _material_risk_thresholds()
            card_options = {f"{r.component.name} ({r.component.code})": r for r in recipe_rows}
            selected_name = st.selectbox("Select component", options=list(card_options.keys()), key="material_card_selected")
            selected_row = card_options[selected_name]
            component = selected_row.component
            st.markdown(f"**{component.name}** ({component.code})")
            st.caption(f"Type: {component.type}; Mass in recipe: {selected_row.mass_kg:.2f} kg")
            st.markdown(
                f"Risk legend: {_risk_tag('ok')} {_risk_tag('warn')} {_risk_tag('error')}",
                unsafe_allow_html=True,
            )
            st.caption("Hover metric labels for threshold tooltips.")
            hausner_level = _risk_level(
                component.hausner_ratio,
                good_max=float(thresholds["hausner"]["ok_max"]),
                warn_max=float(thresholds["hausner"]["warn_max"]),
            )
            span_level = _risk_level(
                component.span,
                good_max=float(thresholds["span"]["ok_max"]),
                warn_max=float(thresholds["span"]["warn_max"]),
            )
            segregation_level = _risk_level(
                component.segregation_idx,
                good_max=float(thresholds["segregation_idx"]["ok_max"]),
                warn_max=float(thresholds["segregation_idx"]["warn_max"]),
            )
            angle_level = _risk_level(
                component.angle_repose,
                good_max=float(thresholds["angle_repose_deg"]["ok_max"]),
                warn_max=float(thresholds["angle_repose_deg"]["warn_max"]),
            )
            moisture_warn_fraction = float(thresholds["moisture_warn_fraction"])
            moisture_level = (
                "error"
                if component.w_initial > component.w_crit
                else ("warn" if component.w_initial > component.w_crit * moisture_warn_fraction else "ok")
            )
            for label, value, level, help_text in [
                (
                    "Flowability (Hausner)",
                    f"{component.hausner_ratio:.2f}",
                    hausner_level,
                    f"OK <= {thresholds['hausner']['ok_max']}, warning <= {thresholds['hausner']['warn_max']}, else alarm.",
                ),
                (
                    "PSD spread (Span)",
                    f"{component.span:.2f}",
                    span_level,
                    f"OK <= {thresholds['span']['ok_max']}, warning <= {thresholds['span']['warn_max']}, else alarm.",
                ),
                (
                    "Segregation index",
                    f"{component.segregation_idx:.2f}",
                    segregation_level,
                    f"OK <= {thresholds['segregation_idx']['ok_max']}, warning <= {thresholds['segregation_idx']['warn_max']}, else alarm.",
                ),
                (
                    "Angle of repose, deg",
                    f"{component.angle_repose:.1f}",
                    angle_level,
                    f"OK <= {thresholds['angle_repose_deg']['ok_max']}, warning <= {thresholds['angle_repose_deg']['warn_max']}, else alarm.",
                ),
                (
                    "Initial/critical moisture, %",
                    f"{component.w_initial:.2f}/{component.w_crit:.2f}",
                    moisture_level,
                    f"Warning if w_initial > {moisture_warn_fraction:.2f} * w_crit, alarm if w_initial > w_crit.",
                ),
            ]:
                c_metric, c_tag = st.columns([4, 1])
                with c_metric:
                    st.metric(label=label, value=value, help=help_text)
                with c_tag:
                    st.markdown(_risk_tag(level), unsafe_allow_html=True)

    with st.expander("Auto-scaling", expanded=True):
        use_scaling = st.checkbox("Use auto scaling from material properties", key="use_material_scaling")
        rotor_speed = st.number_input("Rotor speed factor", min_value=0.1, max_value=10.0, step=0.1, key="rotor_speed")
        cell_volume_m3 = st.number_input("Cell volume, m3", min_value=0.001, max_value=20.0, step=0.1, key="cell_volume_m3")
        q_l_target = st.number_input("Target liquid flow qL", min_value=0.0, max_value=5.0, step=0.05, key="q_l_target")

    if not recipe_rows:
        st.warning("Add at least one material with mass > 0 to enable scaling")
        return {}, {"rows": [], "use_material_scaling": use_scaling}

    scaled = scaling_engine(
        recipe_rows,
        rotor_speed=rotor_speed,
        q_l_target=q_l_target,
        cell_volume_m3=cell_volume_m3,
    )
    mixture = scaled["mixture"]
    model = scaled["model"]
    with st.expander("Mixture properties", expanded=True):
        st.markdown("**Mixture effective properties**")
        st.write(
            {
                "rho_b_mix": round(mixture["rho_b_mix"], 3),
                "cp_mix": round(mixture["cp_mix"], 3),
                "w0_mix": round(mixture["w0_mix"], 3),
                "w_crit_mix": round(mixture["w_crit_mix"], 3),
                "hausner_mix": round(mixture["hausner_mix"], 3),
            }
        )
        if scaled["warnings"]:
            for warning in scaled["warnings"]:
                st.warning(warning)

    auto_params: dict[str, float] = {}
    if use_scaling:
        auto_params = {
            "tau_s": cells / max(model["k"], 1e-6),
            "kh": model["kh"],
            "ka": model["ka"],
            "b_q": model["b_q"],
            "w0": mixture["w0_mix"] / 100.0,
            "w_star": mixture["w_crit_mix"] / 100.0,
        }

    material_payload = {
        "use_material_scaling": use_scaling,
        "rotor_speed": rotor_speed,
        "cell_volume_m3": cell_volume_m3,
        "q_l_target": q_l_target,
        "rows": [{"code": r.component.code, "mass_kg": r.mass_kg} for r in recipe_rows],
        "scaled_model": model,
        "scaled_mixture": mixture,
    }
    update_recipe_cache(material_payload)
    return auto_params, material_payload


def _render_homogenization_viz(
    *,
    points: list,
    key_component_idx: int,
    component_inlet: list[float],
    tau_s: float,
    model_k: float,
    material_payload: dict[str, Any],
    reaction_enabled: bool,
    reaction_rate: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    st.subheader("HomogenizationViz - Mixing Quality")
    status_cfg = _status_thresholds()

    with st.expander("Viz parameters", expanded=True):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            n_particles = int(st.number_input("n_particles in sample", min_value=100, max_value=1_000_000, step=100, key="n_particles"))
            alpha_seg = float(st.number_input("alpha_seg", min_value=0.0, max_value=2.0, step=0.01, key="alpha_seg"))
            beta_hygro = float(st.number_input("beta_hygro", min_value=0.0, max_value=2.0, step=0.01, key="beta_hygro"))
            gamma_seg = float(st.number_input("gamma_seg", min_value=0.0, max_value=1.0, step=0.001, key="gamma_seg"))
        with p_col2:
            rsd_target = float(st.number_input("RSD target, %", min_value=0.5, max_value=30.0, step=0.5, key="rsd_target"))
            batch_id = st.text_input("Batch id", key="batch_id")
            historian_db_path = st.text_input("Historian DB path", key="historian_db_path")
            mixer_id = st.text_input("Mixer id", key="mixer_id")
            report_path = st.text_input("Report output path", key="report_path")
            viz_mode = st.radio("Default mode", options=["online", "post-batch", "predictive"], key="viz_mode", horizontal=True)
    init_historian_db(historian_db_path)

    times = [p.time_s for p in points]
    c_cells_series = [[p.components[i][key_component_idx] for i in range(len(p.components))] for p in points]
    moisture_out = [p.moisture[-1] for p in points]
    c_bar = max(component_inlet[key_component_idx], 1e-6)
    mixture = material_payload.get("scaled_mixture", {})
    seg_mix = float(mixture.get("segregation_idx_mix", 0.3))
    w_eq_mix = float(mixture.get("w_eq_mix", 0.0)) / 100.0

    series = calc_online_homogenization_series(
        times_s=times,
        concentration_by_time=c_cells_series,
        moisture_out_by_time=moisture_out,
        c_bar=c_bar,
        n_particles=n_particles,
        segregation_idx_mix=seg_mix,
        w_eq_mix=w_eq_mix,
        alpha_seg=alpha_seg,
        beta_hygro=beta_hygro,
    )
    df = metrics_dataframe(series)
    last = series[-1]

    h_cfg = HMixConfig(
        k0=max(model_k * 0.2, 0.001),
        k_n=0.0008,
        k_D=0.1,
        k_w=0.002,
        k_Q=0.0005,
        q_s0=0.5,
        h_target=1.0 - (rsd_target / 100.0) ** 2,
        ts_s=max(times[1] - times[0], 1.0) if len(times) > 1 else 1.0,
    )
    runtime = MixQualityRuntime(config=h_cfg)
    runtime.new_batch(batch_id=batch_id)
    for i, p in enumerate(points):
        n_sig = 400.0 + 50.0 * (i / max(len(points) - 1, 1))
        d_sig = 1.0 if i > 3 else 0.0
        w_sig = p.moisture[-1] * 100.0
        qs_sig = 0.5 + 0.05 * p.components[-1][key_component_idx]
        p_sig = 1.0 - 0.4 * min(p.time_s / max(times[-1], 1.0), 1.0)
        runtime.ingest(n=n_sig, d=d_sig, w=w_sig, q_s=qs_sig, p=p_sig)
    h_curve_df = pd.DataFrame([{"time_s": s.t_s, "H": s.h, "k_mix": s.k_mix} for s in runtime.samples])
    h_curve_df["RSD_backcalc"] = (1.0 - h_curve_df["H"]) * 100.0
    trend = trend_alerts(h_series=h_curve_df["H"].tolist(), rsd_series=h_curve_df["RSD_backcalc"].tolist())
    conf_score = confidence_score(
        h=runtime.h,
        rsd=(1.0 - runtime.h) * 100.0,
        rsd_target=rsd_target,
        h_slope=float(trend["h_slope"]),
        rsd_slope=float(trend["rsd_slope"]),
    )
    baseline_h_end: float | None = None
    baseline_rsd_end: float | None = None
    old_batches = list_batches(historian_db_path)
    if old_batches:
        base_curve = load_batch_curve(old_batches[0], historian_db_path)
        if base_curve:
            baseline_h_end = float(base_curve[-1].get("h", 0.0))
            baseline_rsd_end = (1.0 - baseline_h_end) * 100.0
    drift = drift_against_baseline(
        current_h_end=runtime.h,
        current_rsd_end=(1.0 - runtime.h) * 100.0,
        baseline_h_end=baseline_h_end,
        baseline_rsd_end=baseline_rsd_end,
    )
    if runtime.h < h_cfg.h_target:
        t_rem = max((-(1 - h_cfg.h_target) + (1 - runtime.h)), 0.0) / max(runtime.samples[-1].k_mix, 1e-6)
    else:
        t_rem = 0.0

    st.markdown("<div class='sticky-kpi'>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Current H", f"{runtime.h:.3f}")
    with kpi2:
        st.metric("Current RSD", f"{(1.0 - runtime.h) * 100.0:.2f}%")
    with kpi3:
        st.metric("Current k_mix", f"{runtime.samples[-1].k_mix:.4f} 1/s")
    with kpi4:
        st.metric("ETA to target, s", f"{t_rem:.1f}")
    with kpi5:
        st.metric("Confidence", f"{conf_score * 100.0:.1f}%")
    st.markdown("</div>", unsafe_allow_html=True)

    online_tab, post_batch_tab, predictive_tab = st.tabs(["Online", "Post-batch", "Predictive"])

    with online_tab:
        st.markdown("**Main chart: H(t)**")
        st.line_chart(h_curve_df, x="time_s", y="H")
        st.line_chart(pd.DataFrame({"time_s": h_curve_df["time_s"], "H_target": [h_cfg.h_target] * len(h_curve_df)}), x="time_s", y="H_target")
        if old_batches:
            overlay_batch = st.selectbox("Overlay batch", options=["None"] + old_batches)
            if overlay_batch != "None":
                old = load_batch_curve(overlay_batch, historian_db_path)
                if old:
                    old_df = pd.DataFrame(old).rename(columns={"h": "H_overlay", "t_s": "time_s"})
                    st.line_chart(old_df, x="time_s", y="H_overlay")
        if st.button("Store current H-curve to Historian"):
            for sample in runtime.samples:
                append_h_sample(batch_id, sample, historian_db_path)
            st.success("Batch curve stored")

    with post_batch_tab:
        batches = list_batches(historian_db_path)
        if not batches:
            st.info("No stored batches yet")
        else:
            selected = st.selectbox("Stored batch", options=batches)
            curve = load_batch_curve(selected, historian_db_path)
            if curve:
                curve_df = pd.DataFrame(curve).rename(columns={"t_s": "time_s", "h": "H"})
                st.line_chart(curve_df, x="time_s", y="H")
                st.line_chart(curve_df, x="time_s", y="k_mix")

    with predictive_tab:
        v_factor = st.slider("What-if rotor speed factor", 0.5, 2.0, 1.0, 0.05)
        q_factor = st.slider("What-if liquid flow factor", 0.5, 2.0, 1.0, 0.05)
        k_whatif = model_k * (v_factor**0.7) * (1.0 + 0.1 * (q_factor - 1.0))
        pred_h = predict_endpoint(
            k_mix=k_whatif,
            h_rel_current=runtime.h,
            h_rel_target=h_cfg.h_target,
            tau_s=tau_s,
            gamma_seg=gamma_seg,
            segregation_idx_mix=seg_mix,
        )
        st.line_chart(pd.DataFrame({"time_s": pred_h["times_s"], "H_pred": pred_h["h_pred"]}), x="time_s", y="H_pred")
        st.metric("Predicted time to target, s", f"{pred_h['t_remaining_s']:.1f}")

    mode_switch = st.radio("Display metric", options=["H(t)", "RSD(t)"])
    if mode_switch == "RSD(t)":
        st.line_chart(h_curve_df, x="time_s", y="RSD_backcalc")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("RSD", f"{last.rsd_percent:.2f}%")
        st.progress(min(last.rsd_percent / max(rsd_target, 1e-6), 1.0))
    with c2:
        st.metric("Lacey Index", f"{last.lacey_index:.3f}")
        st.progress(min(max(last.lacey_index, 0.0), 1.0))
    with c3:
        st.metric("H_rel", f"{last.h_rel:.3f}")
        st.progress(min(max(last.h_rel, 0.0), 1.0))

    st.markdown("**Trend: sigma2(t) with bounds**")
    st.line_chart(df, x="time_s", y=["sigma2", "sigma0_2", "sigma_r_eff_2"])

    st.markdown("**Profile: c_i along axis**")
    profile_df = concentration_profile_dataframe(c_cells_series[-1])
    st.bar_chart(profile_df, x="cell", y="concentration")

    pred = predict_endpoint(
        k_mix=model_k,
        h_rel_current=last.h_rel,
        h_rel_target=max(min(h_cfg.h_target, 0.99), 0.05),
        tau_s=tau_s,
        dt_s=max(times[1] - times[0], 1.0) if len(times) > 1 else 1.0,
        gamma_seg=gamma_seg,
        segregation_idx_mix=seg_mix,
    )
    pred_df = pd.DataFrame({"time_s": pred["times_s"], "h_pred": pred["h_pred"]})
    st.markdown("**Prediction: H_rel(t + Δt)**")
    st.line_chart(pred_df, x="time_s", y="h_pred")
    _severity(
        "success" if pred["t_remaining_s"] <= 0.0 else ("warning" if pred["t_remaining_s"] <= tau_s else "error"),
        f"Endpoint timer: time to target RSD<{rsd_target:.1f}% is {pred['t_remaining_s']:.1f} s",
    )

    bands = uncertainty_bands(df["rsd_percent"].tolist(), variance_rsd=0.04)
    bands_df = pd.DataFrame(
        {"time_s": df["time_s"], "rsd": df["rsd_percent"], "rsd_lower": bands["lower"], "rsd_upper": bands["upper"]}
    )
    st.markdown("**Uncertainty band (RSD ±2σ)**")
    st.line_chart(bands_df, x="time_s", y=["rsd", "rsd_lower", "rsd_upper"])

    st.subheader("Component analysis")
    last_by_cell = [list(p.components) for p in [points[-1]]][0]
    contribs = component_contributions(last_by_cell)
    contrib_df = component_contribution_dataframe(contribs)
    st.bar_chart(contrib_df, x="component", y="contribution")

    heat_rows: list[dict[str, float | str]] = []
    for i, cell in enumerate(last_by_cell, start=1):
        for j, val in enumerate(cell, start=1):
            avg = sum(r[j - 1] for r in last_by_cell) / len(last_by_cell)
            rel = abs(val - avg) / max(avg, 1e-6)
            heat_rows.append({"cell": f"Cell {i}", "component": f"Component {j}", "relative_dev": rel})
    st.dataframe(pd.DataFrame(heat_rows), use_container_width=True)

    rsd_level = (
        "success"
        if last.rsd_percent <= rsd_target
        else ("warning" if last.rsd_percent <= rsd_target * status_cfg["rsd_warn_factor"] else "error")
    )
    h_level = (
        "success"
        if runtime.h >= h_cfg.h_target
        else ("warning" if runtime.h >= h_cfg.h_target * status_cfg["h_warn_fraction"] else "error")
    )
    alarm_level = "error" if last.rsd_percent > status_cfg["alarm_rsd_percent"] else "success"
    reaction_level = "success"
    reaction_msg = "Reaction: disabled."
    if reaction_enabled:
        reaction_level = "warning" if reaction_rate > status_cfg["reaction_rate_warn"] else "success"
        reaction_msg = f"Reaction: enabled, rate={reaction_rate:.3f}."
    _severity(rsd_level, f"RSD status: {last.rsd_percent:.2f}% (target <= {rsd_target:.2f}%).")
    _severity(h_level, f"H status: {runtime.h:.3f} (target >= {h_cfg.h_target:.3f}).")
    _severity(
        alarm_level,
        f"Alarm status: {'active' if alarm_level == 'error' else 'normal'} (threshold {status_cfg['alarm_rsd_percent']:.2f}%).",
    )
    _severity(reaction_level, reaction_msg)
    _severity(trend["level"], f"Trend status: dH/dt={trend['h_slope']:.5f}, dRSD/dt={trend['rsd_slope']:.5f}")
    _severity(drift["level"], drift["message"])

    viz_payload = {
        "n_particles": n_particles,
        "alpha_seg": alpha_seg,
        "beta_hygro": beta_hygro,
        "gamma_seg": gamma_seg,
        "rsd_target": rsd_target,
        "batch_id": batch_id,
        "report_path": report_path,
        "historian_db_path": historian_db_path,
        "mixer_id": mixer_id,
        "viz_mode": viz_mode,
        "endpoint_prediction": pred,
    }
    integration_payload = {
        "batch_id": batch_id,
        "recipe_name": st.session_state.get("selected_recipe_name", "Unknown"),
        "mixer_id": mixer_id,
        "report_path": report_path,
        "last_rsd_percent": last.rsd_percent,
        "last_lacey_index": last.lacey_index,
        "last_h_rel": last.h_rel,
        "t_target_s": pred["t_remaining_s"],
        "profile_c": c_cells_series[-1],
        "h_curve_df": h_curve_df,
        "contribs": contribs,
        "key_component_idx": key_component_idx,
        "alarm_rsd_percent": status_cfg["alarm_rsd_percent"],
        "confidence": conf_score,
        "w_out": float(points[-1].moisture[-1]),
        "t_out": float(points[-1].temperatures[-1]),
        "k_mix": float(runtime.samples[-1].k_mix),
    }
    return viz_payload, integration_payload


def _render_integration_tab(payload: dict[str, Any]) -> dict[str, Any]:
    st.subheader("Integration")
    alarm_threshold = float(payload.get("alarm_rsd_percent", 8.0))
    schema_version = st.text_input("Payload schema version", value="1.0.0", key="schema_version")
    opc_payload = build_opc_payload(
        rsd=float(payload["last_rsd_percent"]),
        lacey=float(payload["last_lacey_index"]),
        h_rel=float(payload["last_h_rel"]),
        t_target_s=float(payload["t_target_s"]),
        profile_c=list(payload["profile_c"]),
        rsd_alarm_threshold=alarm_threshold,
    )
    opc_payload["schema_version"] = schema_version
    opc_alarm = bool(opc_payload.get("MixQuality/Alarm_RSD_High", False))
    _severity("error" if opc_alarm else "success", f"OPC alarm: {opc_alarm}")
    validation = validate_opc_payload(opc_payload)
    _severity(validation["level"], f"Payload validation: {'valid' if validation['valid'] else 'invalid'}")
    publish_bundle = build_publish_bundle(
        mixer_id=str(payload["mixer_id"]),
        batch_id=str(payload["batch_id"]),
        h=float(payload["last_h_rel"]),
        w=float(payload.get("w_out", 0.0)),
        t=float(payload.get("t_out", 0.0)),
        k_mix=float(payload.get("k_mix", 0.0)),
        confidence=float(payload.get("confidence", 0.0)),
        opc_payload=opc_payload,
    )
    contracts_tab, export_tab = st.tabs(["Contracts", "Export"])
    with contracts_tab:
        st.markdown("**OPC UA payload preview**")
        st.json(opc_payload)
        if validation["missing_keys"]:
            st.error(f"Missing keys: {validation['missing_keys']}")
        if validation["extra_keys"]:
            st.warning(f"Extra keys: {validation['extra_keys']}")
        st.markdown("**MQTT topics**")
        st.json(mqtt_topics(str(payload["mixer_id"])))
        if st.button("Apply Optimal (prepare setpoints payload)", key="integration_apply_optimal"):
            st.success("Setpoints prepared (dry-run): apply to controller integration layer.")
        if st.button("Simulate publish bundle", key="simulate_publish_bundle_btn"):
            st.success("Dry-run publish bundle prepared")
            st.json(publish_bundle)
    with export_tab:
        contribs = list(payload["contribs"])
        top_contrib_idx = max(range(len(contribs)), key=lambda x: contribs[x]) if contribs else 0
        if st.button("Export report", key="integration_export_report"):
            report_file = export_homogenization_report(
                output_path=str(payload["report_path"]),
                batch_id=str(payload["batch_id"]),
                rsd=float(payload["last_rsd_percent"]),
                lacey=float(payload["last_lacey_index"]),
                h_rel=float(payload["last_h_rel"]),
                t_target_s=float(payload["t_target_s"]),
                main_component=f"Component {int(payload['key_component_idx']) + 1}",
                top_contributor=f"Component {top_contrib_idx + 1}",
            )
            st.success(f"Report exported: {report_file}")
        if st.button("Export H-curve CSV and PNG", key="integration_export_h_curve"):
            export_dir = Path("reports")
            export_dir.mkdir(parents=True, exist_ok=True)
            csv_path = export_dir / f"{payload['batch_id']}_h_curve.csv"
            png_path = export_dir / f"{payload['batch_id']}_h_curve.png"
            h_curve_df = payload["h_curve_df"]
            h_curve_df.to_csv(csv_path, index=False)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(h_curve_df["time_s"], h_curve_df["H"], color="green", linewidth=2, label="H(t)")
            ax.set_xlabel("time_s")
            ax.set_ylabel("H")
            ax.set_ylim(0, 1.02)
            ax.legend()
            fig.tight_layout()
            fig.savefig(png_path)
            plt.close(fig)
            st.success(f"Exported: {csv_path} and {png_path}")
        if st.button("Export release evidence ZIP", key="integration_export_release_evidence"):
            changelog_path = generate_recipe_changelog(recipe_name=str(payload.get("recipe_name", "Unknown")))
            changelog_text = changelog_path.read_text(encoding="utf-8")
            thresholds = _load_viz_params().get("risk_thresholds", {})
            h_curve_csv = payload["h_curve_df"].to_csv(index=False)
            zip_path = build_release_evidence_zip(
                recipe_name=str(payload.get("recipe_name", "Unknown")),
                batch_id=str(payload["batch_id"]),
                mixer_id=str(payload["mixer_id"]),
                opc_payload=opc_payload,
                thresholds=thresholds,
                publish_bundle=publish_bundle,
                h_curve_csv=h_curve_csv,
                changelog_markdown=changelog_text,
            )
            st.success(f"Release evidence exported: {zip_path}")
    return {"opc_payload": opc_payload}


def _run_wet_view(
    duration_s: float,
    dt_s: float,
    cells: int,
    tau_s: float,
    kh: float,
    t_in: float,
    t_wall: float,
    auto_params: dict[str, float],
    material_payload: dict[str, Any],
) -> dict[str, Any]:
    if auto_params:
        tau_s = float(auto_params.get("tau_s", tau_s))
        kh = float(auto_params.get("kh", kh))

    st.subheader("Wet model setup")
    with st.expander("Recipe components", expanded=True):
        n_components = st.slider("Number of components in recipe", 1, 10, 3, 1, key="n_components")
        inlet: list[float] = []
        initial: list[float] = []
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**Inlet concentrations**")
            for idx in range(n_components):
                inlet.append(
                    st.number_input(
                        f"Component {idx+1} inlet concentration",
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        key=f"inlet_{idx}",
                    )
                )
        with c_right:
            st.markdown("**Initial concentrations in apparatus**")
            for idx in range(n_components):
                initial.append(
                    st.number_input(
                        f"Component {idx+1} initial concentration",
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        key=f"initial_{idx}",
                    )
                )

    with st.expander("Wet process parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            w_in = st.number_input("Inlet moisture w_in", min_value=0.0, max_value=1.0, step=0.01, key="w_in")
            w0 = st.number_input("Initial moisture w0", min_value=0.0, max_value=1.0, step=0.01, key="w0")
            eta0 = st.number_input("Initial eta0", min_value=0.0, max_value=5.0, step=0.05, key="eta0")
        with col2:
            q_liquid = st.number_input("Liquid flow q_L", min_value=0.0, max_value=5.0, step=0.05, key="q_liquid")
            b_q = st.number_input("Injection gain b_q", min_value=0.0, max_value=1.0, step=0.005, key="b_q")
            j_add = st.slider("Injection zone j_add", 1, cells, min(2, cells), 1, key="j_add")
        with col3:
            ka = st.number_input("Agglomeration Ka", min_value=0.0, max_value=1.0, step=0.001, key="ka")
            kb = st.number_input("Breakage Kb", min_value=0.0, max_value=1.0, step=0.001, key="kb")
            w_star = st.number_input("Reference moisture w*", min_value=0.0, max_value=1.0, step=0.01, key="w_star")

    if auto_params:
        ka = float(auto_params.get("ka", ka))
        b_q = float(auto_params.get("b_q", b_q))
        w0 = float(auto_params.get("w0", w0))
        w_star = float(auto_params.get("w_star", w_star))
        st.info(
            "MaterialConfig auto-scaling applied: "
            f"tau={tau_s:.2f}, kh={kh:.4f}, Ka={ka:.4f}, b_q={b_q:.6f}, w0={w0:.4f}, w*={w_star:.4f}"
        )

    with st.expander("Chemical reaction block", expanded=False):
        reaction_enabled = st.checkbox(
            "Chemical reaction occurs between components",
            key="reaction_enabled",
        )
        reaction_rate = 0.0
        effect_heat = False
        effect_precipitation = False
        effect_gas = False
        heat_gain = st.session_state["heat_release_gain"]
        precipitation_gain = st.session_state["precipitation_gain"]
        gas_strip_gain = st.session_state["gas_strip_gain"]
        if reaction_enabled:
            reaction_rate = st.number_input(
                "Reaction rate coefficient",
                min_value=0.0,
                max_value=5.0,
                step=0.01,
                key="reaction_rate",
            )
            default_effects = []
            if st.session_state.get("effect_heat_release"):
                default_effects.append("Heat release")
            if st.session_state.get("effect_precipitation"):
                default_effects.append("Precipitation")
            if st.session_state.get("effect_gas_evolution"):
                default_effects.append("Gas evolution")
            effects = st.multiselect(
                "Reaction accompanies",
                options=["Heat release", "Precipitation", "Gas evolution"],
                default=default_effects,
            )
            effect_heat = "Heat release" in effects
            effect_precipitation = "Precipitation" in effects
            effect_gas = "Gas evolution" in effects
            st.session_state["effect_heat_release"] = effect_heat
            st.session_state["effect_precipitation"] = effect_precipitation
            st.session_state["effect_gas_evolution"] = effect_gas
            if effect_heat:
                heat_gain = st.number_input("Heat release gain", min_value=0.0, max_value=50.0, step=0.5, key="heat_release_gain")
            if effect_precipitation:
                precipitation_gain = st.number_input(
                    "Precipitation gain",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.005,
                    key="precipitation_gain",
                )
            if effect_gas:
                gas_strip_gain = st.number_input("Gas stripping gain", min_value=0.0, max_value=1.0, step=0.005, key="gas_strip_gain")

    cfg = WetCascadeConfig(
        duration_s=duration_s,
        dt_s=dt_s,
        cells=cells,
        tau_s=tau_s,
        component_inlet=tuple(inlet),
        component_initial=tuple(initial),
        w_in=w_in,
        w0=w0,
        q_liquid=q_liquid,
        b_q=b_q,
        j_add=j_add,
        eta0=eta0,
        ka=ka,
        kb=kb,
        w_star=w_star,
        t_in=t_in,
        t_wall=t_wall,
        t0=t_in,
        kh=kh,
        reaction_enabled=reaction_enabled,
        reaction_rate=reaction_rate,
        effect_heat_release=effect_heat,
        effect_precipitation=effect_precipitation,
        effect_gas_evolution=effect_gas,
        heat_release_gain=heat_gain,
        precipitation_gain=precipitation_gain,
        gas_strip_gain=gas_strip_gain,
    )
    points = run_wet_cascade(cfg)
    comp_df = _build_wet_component_series(points, n_components=n_components)
    scalars_df = _build_wet_scalar_series(points)

    viz_payload: dict[str, Any] = {}
    integration_meta: dict[str, Any] = {}
    process_tab, quality_tab, integration_tab = st.tabs(["Process", "HomogenizationViz", "Integration"])
    with process_tab:
        left, right = st.columns(2)
        with left:
            st.subheader("Outlet concentrations by component")
            st.line_chart(comp_df, x="time_s", y="outlet_concentration", color="component")
        with right:
            st.subheader("Wet quality channels at outlet")
            st.line_chart(scalars_df, x="time_s", y=["w_out", "eta_out", "reaction_out"])
        st.subheader("Outlet temperature")
        st.line_chart(scalars_df, x="time_s", y="t_out")
        last = points[-1]
        st.info(
            f"Wet outlet at t={last.time_s:.1f}s: w_out={last.moisture[-1]:.4f}, "
            f"eta_out={last.eta[-1]:.4f}, T_out={last.temperatures[-1]:.2f}C"
        )

    with quality_tab:
        key_component_idx = st.selectbox(
            "Key component for homogenization metrics",
            options=list(range(n_components)),
            format_func=lambda x: f"Component {x + 1}",
            index=0,
        )
        viz_payload, integration_meta = _render_homogenization_viz(
            points=points,
            key_component_idx=key_component_idx,
            component_inlet=inlet,
            tau_s=tau_s,
            model_k=cfg.cells / max(cfg.tau_s, 1e-6),
            material_payload=material_payload,
            reaction_enabled=reaction_enabled,
            reaction_rate=reaction_rate,
        )
    with integration_tab:
        if integration_meta:
            integration_payload = _render_integration_tab(integration_meta)
            viz_payload["opc_payload"] = integration_payload["opc_payload"]
        else:
            st.info("Open HomogenizationViz tab first to calculate integration payloads.")
    return {
        "model": "wet-cascade",
        "shared": {
            "duration_s": duration_s,
            "dt_s": dt_s,
            "cells": cells,
            "tau_s": tau_s,
            "kh": kh,
            "t_in": t_in,
            "t_wall": t_wall,
        },
        "wet": {
            "component_inlet": inlet,
            "component_initial": initial,
            "w_in": w_in,
            "w0": w0,
            "eta0": eta0,
            "q_liquid": q_liquid,
            "b_q": b_q,
            "j_add": j_add,
            "ka": ka,
            "kb": kb,
            "w_star": w_star,
            "reaction_enabled": reaction_enabled,
            "reaction_rate": reaction_rate,
            "effect_heat_release": effect_heat,
            "effect_precipitation": effect_precipitation,
            "effect_gas_evolution": effect_gas,
            "heat_release_gain": heat_gain,
            "precipitation_gain": precipitation_gain,
            "gas_strip_gain": gas_strip_gain,
        },
        "material_config": material_payload,
        "viz_config": viz_payload,
    }


def run_app() -> None:
    st.set_page_config(page_title="ASUTP Mixing Visualizer", layout="wide")
    _inject_ui_css()
    st.title("ASUTP Mixing Module - Recipe Driven Simulation")
    st.caption("Select recipe -> model is chosen automatically -> provide process parameters")
    _ensure_default_state()
    _render_onboarding()
    viz_meta = _load_viz_params().get("_meta", {})
    if viz_meta.get("migrated"):
        st.info("viz_params.yaml migrated with defaults for missing fields.")
    if viz_meta.get("errors"):
        for err in viz_meta["errors"]:
            st.error(f"viz_params validation: {err}")

    with st.sidebar:
        st.subheader("Recipe storage")
        recipe_file_path = st.text_input("Recipe file (.json/.yaml)", key="recipe_file_path")
        if st.button("Load recipe from file"):
            try:
                payload = load_recipe(recipe_file_path)
                _apply_loaded_recipe(payload)
                st.success("Recipe loaded")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to load recipe: {exc}")
        if st.button("Save revision snapshot", key="save_recipe_revision_btn"):
            snapshot_payload = {
                "model": "wet-cascade" if st.session_state.get("selected_recipe_name") == "Wet mixing" else "dry-cascade",
                "shared": {
                    "duration_s": st.session_state["duration_s"],
                    "dt_s": st.session_state["dt_s"],
                    "cells": st.session_state["cells"],
                    "tau_s": st.session_state["tau_s"],
                    "kh": st.session_state["kh"],
                    "t_in": st.session_state["t_in"],
                    "t_wall": st.session_state["t_wall"],
                },
            }
            saved = save_recipe_revision(st.session_state["selected_recipe_name"], snapshot_payload, note="UI snapshot")
            st.success(f"Revision saved: {saved.name}")

        selected_recipe_name = st.selectbox("Recipe", options=recipe_names(), key="selected_recipe_name")
        recipe = get_recipe(selected_recipe_name)
        st.subheader("Model selection by recipe")
        st.write(f"Model: `{recipe.model}`")
        st.caption(recipe.note)
        with st.expander("Best-known templates", expanded=False):
            templates = _best_known_templates()
            tpl_name = st.selectbox("Template", options=list(templates.keys()), key="bkr_template_name")
            st.caption(f"Target RSD: {templates[tpl_name]['target_rsd']:.1f}%")
            if st.button("Apply template", key="apply_template_btn"):
                _apply_loaded_recipe(templates[tpl_name]["payload"])
                st.success(f"Template applied: {tpl_name}")
                st.rerun()
        with st.expander("Recipe revision history", expanded=False):
            revisions = list_recipe_revisions(recipe_name=selected_recipe_name)
            if not revisions:
                st.caption("No revisions yet.")
            else:
                selected_rev = st.selectbox("Revision", options=[r.revision_id for r in revisions], key="selected_revision_id")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("Load revision", key="load_revision_btn"):
                        rev = load_recipe_revision(selected_rev)
                        _apply_loaded_recipe(rev.payload)
                        st.success(f"Loaded revision: {selected_rev}")
                        st.rerun()
                with col_b:
                    if st.button("Diff with current", key="diff_revision_btn"):
                        rev = load_recipe_revision(selected_rev)
                        current_stub = {
                            "model": recipe.model,
                            "shared": {
                                "duration_s": st.session_state["duration_s"],
                                "dt_s": st.session_state["dt_s"],
                                "cells": st.session_state["cells"],
                                "tau_s": st.session_state["tau_s"],
                                "kh": st.session_state["kh"],
                                "t_in": st.session_state["t_in"],
                                "t_wall": st.session_state["t_wall"],
                            },
                        }
                        diff = diff_recipe_revisions(rev.payload, current_stub)
                        st.json(diff)
                with col_c:
                    if st.button("Generate changelog", key="generate_changelog_btn"):
                        changelog_path = generate_recipe_changelog(recipe_name=selected_recipe_name)
                        st.success(f"Changelog generated: {changelog_path}")
        st.subheader("Layout mode")
        layout_mode = st.radio(
            "Page layout",
            options=["Desktop (2:3)", "Balanced (1:1)", "Focus charts"],
            key="layout_mode",
        )
        _render_threshold_editor_sidebar()

        st.subheader("Shared simulation parameters")
        duration_s = st.slider("Duration, s", 10.0, 300.0, 120.0, 5.0, key="duration_s")
        dt_s = st.slider("Time step, s", 0.1, 5.0, 1.0, 0.1, key="dt_s")
        cells = st.slider("Number of cells", 1, 8, 3, 1, key="cells")
        tau_s = st.slider("Mean residence time tau, s", 5.0, 300.0, 45.0, 1.0, key="tau_s")
        kh = st.slider("Heat exchange kh, 1/s", 0.0, 0.3, 0.02, 0.005, key="kh")
        t_in = st.slider("Inlet temperature, C", 10.0, 80.0, 25.0, 1.0, key="t_in")
        t_wall = st.slider("Wall temperature, C", 10.0, 80.0, 30.0, 1.0, key="t_wall")

    layout_map = {
        "Desktop (2:3)": ([2, 3], "Configuration panel (~40% width)"),
        "Balanced (1:1)": ([1, 1], "Configuration panel (~50% width)"),
        "Focus charts": ([1, 4], "Compact configuration panel (~20% width)"),
    }
    layout_spec, caption = layout_map.get(layout_mode, ([2, 3], "Configuration panel (~40% width)"))
    left_panel, right_panel = st.columns(layout_spec, gap="large")
    with left_panel:
        st.caption(caption)
        auto_params, material_payload = _render_material_config(cells=cells)

    with right_panel:
        if recipe.model == "dry-cascade":
            current_payload = _run_dry_view(
                duration_s=duration_s,
                dt_s=dt_s,
                cells=cells,
                tau_s=tau_s,
                kh=kh,
                t_in=t_in,
                t_wall=t_wall,
                auto_params=auto_params,
                material_payload=material_payload,
            )
        else:
            current_payload = _run_wet_view(
                duration_s=duration_s,
                dt_s=dt_s,
                cells=cells,
                tau_s=tau_s,
                kh=kh,
                t_in=t_in,
                t_wall=t_wall,
                auto_params=auto_params,
                material_payload=material_payload,
            )

    with st.sidebar:
        if st.button("Save current recipe to file"):
            try:
                save_recipe(st.session_state["recipe_file_path"], current_payload)
                st.success("Recipe saved")
            except Exception as exc:
                st.error(f"Failed to save recipe: {exc}")
        if st.button("Save full recipe revision", key="save_full_revision_btn"):
            path = save_recipe_revision(st.session_state["selected_recipe_name"], current_payload, note="full payload")
            st.success(f"Saved revision: {path.name}")


def main() -> None:
    run_app()


if __name__ == "__main__":
    main()
