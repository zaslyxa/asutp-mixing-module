from mixing_module.h_kinetics import HMixConfig
from mixing_module.mix_quality_runtime import MixQualityRuntime


def test_runtime_batch_and_ready_signal() -> None:
    cfg = HMixConfig(h_target=0.6, ts_s=1.0)
    rt = MixQualityRuntime(config=cfg)
    rt.new_batch("B-1")
    assert rt.active is True
    for _ in range(200):
        sample = rt.ingest(n=450, d=1, w=5, q_s=0.5, p=0.9)
        if sample.ready:
            break
    assert rt.ready is True
    assert rt.elapsed_s >= 1.0
