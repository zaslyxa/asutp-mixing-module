from mixing_module.io_contracts import build_state_message, mqtt_topics


def test_mqtt_topics_contains_required_channels() -> None:
    topics = mqtt_topics("mx-01")
    assert any("speed" in t for t in topics["inputs"])
    assert any("state" in t for t in topics["outputs"])


def test_state_message_has_required_fields() -> None:
    msg = build_state_message(
        timestamp="2026-01-01T00:00:00Z",
        batch_id="B-1",
        h=0.8,
        w=0.1,
        t=25.0,
        k_mix=0.03,
        confidence=0.95,
    )
    assert msg["batch_id"] == "B-1"
    assert "H" in msg
