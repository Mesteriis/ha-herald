"""Tests for Herald request parsing."""

from __future__ import annotations

from custom_components.herald.request import HeraldRequest


def test_new_style_request_parses_thin_contract() -> None:
    request = HeraldRequest.from_service_data(
        {
            "event": "washing_cycle_finished",
            "message": "The washer has finished",
            "level": "info",
            "ai": {"character": "domovoy", "context": {"mode": "brief"}},
            "context": {"appliance": "washer"},
            "entities": ["sensor.washer_state"],
            "suppress": 120,
            "group": "laundry",
            "immediately": False,
        }
    )

    assert request.event == "washing_cycle_finished"
    assert request.ai is not None and request.ai.character == "domovoy"
    assert request.ai is not None and request.ai.context == {"mode": "brief"}
    assert request.entities == ["sensor.washer_state"]
    assert request.group == "laundry"
    assert request.immediately is False
    assert request.legacy_channels == []


def test_legacy_request_remains_backward_compatible() -> None:
    request = HeraldRequest.from_service_data(
        {
            "flow": "system_events",
            "title": "Legacy Title",
            "message": "Legacy path",
            "channels": ["mobile_macbook"],
            "users": ["person.aleksandr_meshcheriakov"],
            "room": "Гостиная",
            "personality": "HESTIA",
        }
    )

    assert request.event == "Legacy Title"
    assert request.legacy_flow == "system_events"
    assert request.legacy_channels == ["mobile_macbook"]
    assert request.legacy_users == ["person.aleksandr_meshcheriakov"]
    assert request.legacy_room == "Гостиная"
    assert request.ai is not None and request.ai.character == "HESTIA"


def test_request_parses_stringified_nested_payloads() -> None:
    request = HeraldRequest.from_service_data(
        {
            "event": "nested_contract_smoke",
            "message": "payload via service string",
            "ai": '{"character":"domovoy","context":{"mode":"brief","tone":"diagnostic"}}',
            "context": '{"test_case":"nested_contract"}',
            "entities": '["sensor.power","person.aleksandr_meshcheriakov"]',
            "users": '["person.aleksandr_meshcheriakov"]',
            "channels": '["persistent_default"]',
            "metadata": '{"source":"service_ui"}',
        }
    )

    assert request.ai is not None and request.ai.character == "domovoy"
    assert request.ai is not None and request.ai.context == {
        "mode": "brief",
        "tone": "diagnostic",
    }
    assert request.context == {
        "test_case": "nested_contract",
        "legacy_metadata": {"source": "service_ui"},
    }
    assert request.entities == ["sensor.power", "person.aleksandr_meshcheriakov"]
    assert request.legacy_users == ["person.aleksandr_meshcheriakov"]
    assert request.legacy_channels == ["persistent_default"]
