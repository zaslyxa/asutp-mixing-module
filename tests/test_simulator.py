from mixing_module.simulator import SimulationConfig, run_simulation


def test_simulation_returns_timeline() -> None:
    cfg = SimulationConfig(duration_s=10, dt_s=1)
    points = run_simulation(cfg)
    assert len(points) == 11
    assert points[0].time_s == 0
    assert points[-1].time_s == 10


def test_concentration_increases_with_feed_a() -> None:
    cfg = SimulationConfig(duration_s=20, dt_s=1, inlet_a_concentration=1.0, inlet_b_concentration=0.0)
    points = run_simulation(cfg)
    assert points[-1].concentration > points[0].concentration
