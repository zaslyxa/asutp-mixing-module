from mixing_module.h_kinetics import HMixConfig, calc_h_from_torque, calc_k_mix, step_h


def test_calc_k_mix_bounds() -> None:
    cfg = HMixConfig(k_min=0.001, k_max=0.5)
    k = calc_k_mix(cfg, n=1000, d=1, w=0, q_s=0.1)
    assert 0.001 <= k <= 0.5


def test_step_h_increases_toward_one() -> None:
    cfg = HMixConfig()
    h = 0.0
    for _ in range(20):
        h, _ = step_h(cfg, h_prev=h, n=350, d=1, w=5, q_s=0.5, p=0.9)
    assert h > 0.1


def test_torque_mapping_range() -> None:
    cfg = HMixConfig(p0=1.0, p_inf=0.6)
    h = calc_h_from_torque(cfg, p=0.8)
    assert 0 <= h <= 1
