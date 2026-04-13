from mixing_module.homogenization_metrics import (
    calc_h_rel,
    calc_lacey_index,
    calc_online_homogenization_series,
    calc_rsd,
    calc_sigma2,
    component_contributions,
)


def test_basic_metric_formulas() -> None:
    samples = [0.2, 0.3, 0.4]
    sigma2 = calc_sigma2(samples)
    assert sigma2 > 0
    rsd = calc_rsd(samples, c_bar=0.3)
    assert rsd > 0
    lacey, sigma0_2, sigma_r_eff_2 = calc_lacey_index(
        sigma2=sigma2,
        c_bar=0.3,
        n_particles=5000,
        segregation_idx_mix=0.3,
        w_mix=0.1,
        w_eq_mix=0.08,
    )
    assert 0 <= lacey <= 1
    assert sigma0_2 > sigma_r_eff_2
    assert 0 <= calc_h_rel(sigma2, sigma0_2) <= 1


def test_online_series_and_contributions() -> None:
    series = calc_online_homogenization_series(
        times_s=[0, 1, 2],
        concentration_by_time=[[0.1, 0.2, 0.3], [0.12, 0.22, 0.32], [0.14, 0.24, 0.34]],
        moisture_out_by_time=[0.05, 0.06, 0.07],
        c_bar=0.2,
        n_particles=1000,
        segregation_idx_mix=0.2,
        w_eq_mix=0.05,
    )
    assert len(series) == 3
    contrib = component_contributions([[0.3, 0.2], [0.32, 0.21], [0.31, 0.24]])
    assert len(contrib) == 2
    assert abs(sum(contrib) - 1.0) < 1e-6
