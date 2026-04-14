from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .io_contracts import build_state_message, mqtt_topics

REQUIRED_OPC_KEYS = {
    "MixQuality/RSD",
    "MixQuality/LaceyIndex",
    "MixQuality/H_rel",
    "MixQuality/t_target",
    "MixQuality/Profile_c",
    "MixQuality/Alarm_RSD_High",
    "schema_version",
}


def validate_opc_payload(payload: dict[str, Any]) -> dict[str, Any]:
    keys = set(payload.keys())
    missing = sorted(REQUIRED_OPC_KEYS - keys)
    extra = sorted(keys - REQUIRED_OPC_KEYS)
    level = "success" if not missing else "error"
    return {
        "valid": not missing,
        "level": level,
        "missing_keys": missing,
        "extra_keys": extra,
    }


def build_publish_bundle(
    *,
    mixer_id: str,
    batch_id: str,
    h: float,
    w: float,
    t: float,
    k_mix: float,
    confidence: float,
    opc_payload: dict[str, Any],
) -> dict[str, Any]:
    topics = mqtt_topics(mixer_id)
    state_message = build_state_message(
        timestamp=datetime.now(timezone.utc).isoformat(),
        batch_id=batch_id,
        h=h,
        w=w,
        t=t,
        k_mix=k_mix,
        confidence=confidence,
    )
    return {
        "state_topic": topics["outputs"][0],
        "state_message": state_message,
        "opc_payload": opc_payload,
        "schema_version": opc_payload.get("schema_version", "1.0.0"),
    }
