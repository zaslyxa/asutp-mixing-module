from mixing_module.homogenization_predictor import predict_endpoint, uncertainty_bands


def test_predict_endpoint_returns_positive_horizon() -> None:
    result = predict_endpoint(
        k_mix=0.06,
        h_rel_current=0.4,
        h_rel_target=0.9,
        tau_s=45,
        dt_s=1.0,
        gamma_seg=0.01,
        segregation_idx_mix=0.2,
    )
    assert result["t_remaining_s"] >= 0
    assert len(result["times_s"]) == len(result["h_pred"])


def test_uncertainty_bands_shape() -> None:
    base = [3.0, 2.8, 2.5]
    bands = uncertainty_bands(base, variance_rsd=0.04)
    assert len(bands["lower"]) == len(base)
    assert len(bands["upper"]) == len(base)
