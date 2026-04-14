from __future__ import annotations

from mixing_module.integration_validation import build_publish_bundle, validate_opc_payload


def test_validate_opc_payload_requires_schema() -> None:
    payload = {
        "MixQuality/RSD": 5.0,
        "MixQuality/LaceyIndex": 0.9,
        "MixQuality/H_rel": 0.85,
        "MixQuality/t_target": 20.0,
        "MixQuality/Profile_c": [0.1, 0.2],
        "MixQuality/Alarm_RSD_High": False,
    }
    result = validate_opc_payload(payload)
    assert not result["valid"]
    assert "schema_version" in result["missing_keys"]


def test_build_publish_bundle_snapshot() -> None:
    opc_payload = {
        "MixQuality/RSD": 4.2,
        "MixQuality/LaceyIndex": 0.93,
        "MixQuality/H_rel": 0.88,
        "MixQuality/t_target": 11.0,
        "MixQuality/Profile_c": [0.11, 0.12, 0.13],
        "MixQuality/Alarm_RSD_High": False,
        "schema_version": "1.1.0",
    }
    bundle = build_publish_bundle(
        mixer_id="mx-01",
        batch_id="b-1",
        h=0.88,
        w=0.14,
        t=29.0,
        k_mix=0.031,
        confidence=0.78,
        opc_payload=opc_payload,
    )
    assert bundle["schema_version"] == "1.1.0"
    assert bundle["state_topic"] == "model/mixer/mx-01/state"
    assert bundle["state_message"]["batch_id"] == "b-1"
