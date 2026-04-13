from mixing_module.calibration import estimate_k0_from_curve


def test_estimate_k0_positive() -> None:
    times = [0, 1, 2, 3, 4]
    h_vals = [0.0, 0.1, 0.18, 0.24, 0.29]
    k0 = estimate_k0_from_curve(times, h_vals)
    assert k0 > 0
