from mixing_module.cascade import DryCascadeConfig, run_dry_cascade


def test_dry_cascade_returns_full_timeline() -> None:
    cfg = DryCascadeConfig(duration_s=10, dt_s=1, cells=3, tau_s=30)
    points = run_dry_cascade(cfg)
    assert len(points) == 11
    assert points[0].time_s == 0
    assert points[-1].time_s == 10


def test_cascade_outlet_concentration_rises() -> None:
    cfg = DryCascadeConfig(duration_s=120, dt_s=1, cells=3, tau_s=45, c_in=1.0, c0=0.0)
    points = run_dry_cascade(cfg)
    assert points[-1].concentrations[-1] > points[0].concentrations[-1]


def test_cascade_temperature_moves_to_wall_and_inlet_balance() -> None:
    cfg = DryCascadeConfig(
        duration_s=100,
        dt_s=1,
        cells=3,
        tau_s=45,
        kh=0.03,
        t_in=20.0,
        t_wall=35.0,
        t0=20.0,
    )
    points = run_dry_cascade(cfg)
    assert points[-1].temperatures[-1] > points[0].temperatures[-1]
