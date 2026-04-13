from mixing_module.wet_model import WetCascadeConfig, run_wet_cascade


def test_wet_model_timeline_and_dimensions() -> None:
    cfg = WetCascadeConfig(
        duration_s=20,
        dt_s=1,
        cells=3,
        component_inlet=(1.0, 0.5, 0.2),
        component_initial=(0.0, 0.0, 0.0),
    )
    points = run_wet_cascade(cfg)
    assert len(points) == 21
    assert len(points[-1].components[-1]) == 3


def test_wet_model_liquid_injection_raises_moisture() -> None:
    cfg = WetCascadeConfig(
        duration_s=60,
        dt_s=1,
        cells=3,
        component_inlet=(1.0, 0.0),
        component_initial=(0.0, 0.0),
        q_liquid=0.3,
        b_q=0.08,
    )
    points = run_wet_cascade(cfg)
    assert points[-1].moisture[-1] > points[0].moisture[-1]


def test_reaction_heat_effect_increases_temperature() -> None:
    base_cfg = WetCascadeConfig(
        duration_s=50,
        dt_s=1,
        cells=3,
        component_inlet=(1.0, 0.8),
        component_initial=(0.2, 0.2),
        reaction_enabled=False,
    )
    rx_cfg = WetCascadeConfig(
        duration_s=50,
        dt_s=1,
        cells=3,
        component_inlet=(1.0, 0.8),
        component_initial=(0.2, 0.2),
        reaction_enabled=True,
        reaction_rate=0.1,
        effect_heat_release=True,
        heat_release_gain=10.0,
    )
    base_points = run_wet_cascade(base_cfg)
    rx_points = run_wet_cascade(rx_cfg)
    assert rx_points[-1].temperatures[-1] > base_points[-1].temperatures[-1]
