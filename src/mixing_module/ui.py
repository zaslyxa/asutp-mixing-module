from __future__ import annotations

from typing import Any
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

if __package__ in (None, ""):
    # Support direct execution by Streamlit: `streamlit run src/mixing_module/ui.py`
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from mixing_module.cascade import DryCascadeConfig, run_dry_cascade
    from mixing_module.recipe_storage import load_recipe, save_recipe
    from mixing_module.recipes import get_recipe, recipe_names
    from mixing_module.material_db import get_component_by_code, init_material_db, list_components
    from mixing_module.scaling import RecipeRow, scaling_engine, update_recipe_cache
    from mixing_module.wet_model import WetCascadeConfig, run_wet_cascade
else:
    from .cascade import DryCascadeConfig, run_dry_cascade
    from .recipe_storage import load_recipe, save_recipe
    from .recipes import get_recipe, recipe_names
    from .material_db import get_component_by_code, init_material_db, list_components
    from .scaling import RecipeRow, scaling_engine, update_recipe_cache
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
        st.session_state["selected_recipe_name"] = "Wet granulation with binder"
    else:
        st.session_state["selected_recipe_name"] = "Dry powder blending"

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


def _run_dry_view(duration_s: float, dt_s: float, cells: int, tau_s: float, kh: float, t_in: float, t_wall: float) -> dict[str, Any]:
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
    }


def _render_material_config(cells: int) -> tuple[dict[str, float], dict[str, Any]]:
    st.subheader("MaterialConfig")
    db_path = st.text_input("Material DB path", key="material_db_path")
    init_material_db(db_path)
    available = list_components(db_path)
    names = [f"{c.name} ({c.code})" for c in available]
    name_to_code = {f"{c.name} ({c.code})": c.code for c in available}

    st.caption("Select components from database and set masses for scaling")
    recipe_rows: list[RecipeRow] = []
    mat_count = st.slider("Material rows", 1, 8, 3, 1, key="material_row_count")
    for i in range(mat_count):
        col_l, col_r = st.columns([3, 1])
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
            mass = st.number_input(f"kg #{i+1}", min_value=0.0, value=10.0 if i == 0 else 0.0, step=1.0, key=f"mat_mass_{i}")
        if mass > 0:
            code = name_to_code[selected]
            recipe_rows.append(RecipeRow(component=get_component_by_code(code, db_path), mass_kg=mass))

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


def _run_wet_view(
    duration_s: float,
    dt_s: float,
    cells: int,
    tau_s: float,
    kh: float,
    t_in: float,
    t_wall: float,
) -> dict[str, Any]:
    auto_params, material_payload = _render_material_config(cells=cells)
    if auto_params:
        tau_s = float(auto_params.get("tau_s", tau_s))
        kh = float(auto_params.get("kh", kh))

    st.subheader("Recipe components")
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

    st.subheader("Wet process parameters")
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

    st.subheader("Chemical reaction block")
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
    }


def run_app() -> None:
    st.set_page_config(page_title="ASUTP Mixing Visualizer", layout="wide")
    st.title("ASUTP Mixing Module - Recipe Driven Simulation")
    st.caption("Select recipe -> model is chosen automatically -> provide process parameters")
    _ensure_default_state()

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

        selected_recipe_name = st.selectbox("Recipe", options=recipe_names(), key="selected_recipe_name")
        recipe = get_recipe(selected_recipe_name)
        st.subheader("Model selection by recipe")
        st.write(f"Model: `{recipe.model}`")
        st.caption(recipe.note)

        st.subheader("Shared simulation parameters")
        duration_s = st.slider("Duration, s", 10.0, 300.0, 120.0, 5.0, key="duration_s")
        dt_s = st.slider("Time step, s", 0.1, 5.0, 1.0, 0.1, key="dt_s")
        cells = st.slider("Number of cells", 1, 8, 3, 1, key="cells")
        tau_s = st.slider("Mean residence time tau, s", 5.0, 300.0, 45.0, 1.0, key="tau_s")
        kh = st.slider("Heat exchange kh, 1/s", 0.0, 0.3, 0.02, 0.005, key="kh")
        t_in = st.slider("Inlet temperature, C", 10.0, 80.0, 25.0, 1.0, key="t_in")
        t_wall = st.slider("Wall temperature, C", 10.0, 80.0, 30.0, 1.0, key="t_wall")

    if recipe.model == "dry-cascade":
        current_payload = _run_dry_view(
            duration_s=duration_s,
            dt_s=dt_s,
            cells=cells,
            tau_s=tau_s,
            kh=kh,
            t_in=t_in,
            t_wall=t_wall,
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
        )

    with st.sidebar:
        if st.button("Save current recipe to file"):
            try:
                save_recipe(st.session_state["recipe_file_path"], current_payload)
                st.success("Recipe saved")
            except Exception as exc:
                st.error(f"Failed to save recipe: {exc}")


def main() -> None:
    run_app()


if __name__ == "__main__":
    main()
