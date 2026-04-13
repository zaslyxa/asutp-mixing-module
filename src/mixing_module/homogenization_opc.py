from __future__ import annotations


def build_opc_payload(
    *,
    rsd: float,
    lacey: float,
    h_rel: float,
    t_target_s: float,
    profile_c: list[float],
    rsd_alarm_threshold: float = 8.0,
) -> dict:
    payload = {
        "MixQuality/RSD": float(rsd),
        "MixQuality/LaceyIndex": float(lacey),
        "MixQuality/H_rel": float(h_rel),
        "MixQuality/t_target": float(t_target_s),
        "MixQuality/Profile_c": [float(v) for v in profile_c],
        "MixQuality/Alarm_RSD_High": bool(rsd > rsd_alarm_threshold),
    }
    return payload
