from __future__ import annotations

import zipfile

from mixing_module.release_evidence import build_release_evidence_zip


def test_build_release_evidence_zip_contains_expected_files(tmp_path) -> None:
    out = build_release_evidence_zip(
        recipe_name="Wet mixing",
        batch_id="b-001",
        mixer_id="mx-01",
        opc_payload={"schema_version": "1.0.0", "MixQuality/RSD": 4.2},
        thresholds={"status": {"alarm_rsd_percent": 8.0}},
        publish_bundle={"state_topic": "model/mixer/mx-01/state"},
        h_curve_csv="time_s,H\n0,0.1\n1,0.2\n",
        changelog_markdown="# changelog\n",
        output_path=tmp_path / "evidence.zip",
    )
    assert out.exists()
    with zipfile.ZipFile(out, "r") as zf:
        names = set(zf.namelist())
    assert "manifest.json" in names
    assert "opc_payload.json" in names
    assert "publish_bundle.json" in names
    assert "threshold_profile.json" in names
    assert "h_curve.csv" in names
    assert "recipe_changelog.md" in names
