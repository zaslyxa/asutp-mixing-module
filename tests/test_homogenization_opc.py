from mixing_module.homogenization_opc import build_opc_payload


def test_build_opc_payload_schema() -> None:
    payload = build_opc_payload(
        rsd=4.2,
        lacey=0.92,
        h_rel=0.88,
        t_target_s=21.5,
        profile_c=[0.1, 0.2, 0.3],
        rsd_alarm_threshold=5.0,
    )
    assert payload["MixQuality/RSD"] == 4.2
    assert payload["MixQuality/Alarm_RSD_High"] is False
    assert len(payload["MixQuality/Profile_c"]) == 3
