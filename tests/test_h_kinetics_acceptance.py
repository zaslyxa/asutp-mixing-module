from mixing_module.h_kinetics import HMixConfig, step_h


def test_speed_step_accelerates_h_growth() -> None:
    cfg = HMixConfig(ts_s=1.0)
    h1 = 0.0
    h2 = 0.0
    h1_next, _ = step_h(cfg, h_prev=h1, n=250, d=1, w=5, q_s=0.5, p=0.95)
    h2_next, _ = step_h(cfg, h_prev=h2, n=450, d=1, w=5, q_s=0.5, p=0.95)
    dh1 = h1_next - h1
    dh2 = h2_next - h2
    assert dh2 > dh1
