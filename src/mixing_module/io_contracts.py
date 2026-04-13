from __future__ import annotations


def mqtt_topics(mixer_id: str) -> dict[str, list[str]]:
    return {
        "inputs": [
            f"telemetry/mixer/{mixer_id}/speed",
            f"telemetry/mixer/{mixer_id}/current",
            f"telemetry/mixer/{mixer_id}/temperature",
            f"telemetry/mixer/{mixer_id}/humidity",
            f"telemetry/mixer/{mixer_id}/flow_solid",
            f"telemetry/mixer/{mixer_id}/flow_liquid",
            f"telemetry/mixer/{mixer_id}/deagglomerator",
        ],
        "outputs": [
            f"model/mixer/{mixer_id}/state",
            f"model/mixer/{mixer_id}/ready",
            f"model/mixer/{mixer_id}/graph_data",
        ],
    }


def build_state_message(*, timestamp: str, batch_id: str, h: float, w: float, t: float, k_mix: float, confidence: float) -> dict:
    return {
        "timestamp": timestamp,
        "batch_id": batch_id,
        "H": h,
        "w": w,
        "T": t,
        "k_mix": k_mix,
        "confidence": confidence,
    }
