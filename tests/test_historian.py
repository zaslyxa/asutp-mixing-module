from mixing_module.h_kinetics import HMixSample
from mixing_module.historian import append_h_sample, init_historian_db, list_batches, load_batch_curve


def test_historian_store_and_load(tmp_path) -> None:
    db = tmp_path / "hist.db"
    init_historian_db(db)
    sample = HMixSample(t_s=1.0, h=0.1, k_mix=0.02, n=300, d=1, w=5, q_s=0.5, p=0.9, ready=False)
    append_h_sample("B-42", sample, db)
    batches = list_batches(db)
    assert "B-42" in batches
    curve = load_batch_curve("B-42", db)
    assert len(curve) == 1
