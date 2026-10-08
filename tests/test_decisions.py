"""Explanation tests use recorded snapshots and never perform delivery or AI."""

from __future__ import annotations

from copy import deepcopy

import pytest

from custom_components.herald.decisions import explain_outcome, explain_route


def _preview(channels=None):
    channels = ["push"] if channels is None else channels
    return {
        "requested": {"event": "test", "message": "private notification text"},
        "prechecks": {"blocked_reason": None, "will_deliver": bool(channels)},
        "presence": {"quiet_hours": False, "nobody_home": False},
        "resolved": {"final_channels": list(channels)},
        "deliveries": [{"channel": channel, "status": "planned"} for channel in channels],
        "channel_decisions": [],
        "resolution_trace": [],
    }


@pytest.mark.parametrize(
    "reason, detail",
    [
        ("notification_policy_disabled", "отключено его правилом"),
        ("level_disabled", "уровень важности отключён"),
        ("flow_disabled", "поток отключён"),
        ("conditions_not_met", "условия потока"),
        ("mute_all", "общая тишина"),
        ("flow_cooldown", "пауза после предыдущей"),
        ("deduplicated", "периода подавления повторов"),
    ],
)
def test_admission_blocker_overrides_planned_channels(reason, detail) -> None:
    preview = _preview()
    preview["prechecks"]["blocked_reason"] = reason
    result = explain_route(preview)

    assert result["status"] == "blocked"
    assert result["reason"] == reason
    assert detail in result["summary"]
    assert result["channels"] == []
    assert "проверка запрещает отправку" in result["steps"][-1]["detail"]
    assert "без отправки" in result["warnings"][0]


def test_ready_preview_is_a_plan_and_includes_transport_limit() -> None:
    result = explain_route(_preview(["push", "persistent"]))
    assert result["status"] == "deliver"
    assert result["reason"] == "route_ready"
    assert result["channels"] == ["push", "persistent"]
    assert "Отправка не выполнялась" in result["summary"]
    assert "Доступность сервисов доставки" in result["warnings"][0]
    assert "private notification text" not in str(result)


def test_maintenance_explains_final_redirect_after_policy() -> None:
    preview = _preview(["persistent_default", "system_log_default"])
    preview["prechecks"]["maintenance_redirect"] = True
    preview["policy"] = {"delivery_mode": "custom", "channels": ["voice"]}
    preview["resolution_trace"] = [{"stage": "explicit_bypass", "channels": ["persistent_default", "system_log_default"]}]
    result = explain_route(preview)

    assert result["reason"] == "maintenance_redirect"
    assert result["channels"] == ["persistent_default", "system_log_default"]
    assert any("заменяет обычный маршрут" in step["detail"] for step in result["steps"])
    assert not any(step["label"] == "Прямой маршрут" for step in result["steps"])


def test_quiet_hours_explains_removed_voice_while_text_remains() -> None:
    preview = _preview(["text"])
    preview["presence"]["quiet_hours"] = True
    preview["scenario"] = "quiet_hours"
    preview["resolution_trace"] = [
        {"stage": "initial", "channels": ["voice", "text"]},
        {"stage": "presence", "channels": ["voice", "text"]},
        {"stage": "quiet_hours", "channels": ["text"]},
        {"stage": "final", "channels": ["text"]},
    ]
    result = explain_route(preview)

    assert result["status"] == "deliver"
    assert result["channels"] == ["text"]
    assert any(step["label"] == "Тихие часы" and "исключило: voice" in step["detail"] for step in result["steps"])
    assert result["steps"][0]["label"] == "Сценарий"


def test_quiet_hours_can_leave_no_target() -> None:
    preview = _preview([])
    preview["resolution_trace"] = [
        {"stage": "initial", "channels": ["voice"]},
        {"stage": "quiet_hours", "channels": []},
        {"stage": "final", "channels": []},
    ]
    result = explain_route(preview)
    assert result["status"] == "no_targets"
    assert result["reason"] == "quiet_hours"
    assert "тихих часов" in result["summary"]


def test_text_only_policy_is_explained_from_explicit_policy_evidence() -> None:
    preview = _preview(["text"])
    preview["policy"] = {"delivery_mode": "text_only"}
    result = explain_route(preview)
    assert any("только текстовые каналы, без голоса и TV" in step["detail"] for step in result["steps"])
    assert result["channels"] == ["text"]
    assert "только текстовые" not in str(explain_route(_preview(["text"])))


def test_unavailable_delivery_is_not_a_usable_target_even_if_selected() -> None:
    preview = _preview(["voice"])
    preview["deliveries"] = [{"channel": "voice", "status": "dropped", "reason": "room_audio_unavailable"}]
    result = explain_route(preview)

    assert result["status"] == "no_targets"
    assert result["reason"] == "room_audio_unavailable"
    assert result["channels"] == []
    assert "нет доступного голосового устройства" in result["summary"]


def test_channel_availability_and_audience_reasons_remain_specific() -> None:
    preview = _preview([])
    preview["channel_decisions"] = [
        {"channel": "voice", "selected": False, "reason": "channel_disabled"},
        {"channel": "other_person", "selected": False, "reason": "user_filter"},
    ]
    result = explain_route(preview)
    assert result["status"] == "no_targets"
    assert "канал отключён" in result["steps"][0]["detail"]
    assert "не соответствует получателям" in result["steps"][1]["detail"]


def test_local_selection_is_explained_as_priority_not_unavailability() -> None:
    preview = _preview(["alisa"])
    preview["resolution_trace"] = [
        {"stage": "initial", "channels": ["alisa", "homepod", "tv"]},
        {"stage": "local_target", "channels": ["alisa"]},
    ]
    result = explain_route(preview)
    local = next(step for step in result["steps"] if step["label"] == "Локальное устройство")
    assert "Алиса → HomePod → TV" in local["detail"]
    assert "homepod, tv" in local["detail"]
    assert "недоступ" not in local["detail"]


def test_empty_or_incomplete_preview_never_claims_delivery() -> None:
    assert explain_route({})["status"] == "no_targets"
    preview = _preview()
    preview.pop("deliveries")
    result = explain_route(preview)
    assert result["status"] == "no_targets"
    assert result["channels"] == []
    assert any("план отправки по ним отсутствует" in warning for warning in result["warnings"])


def test_preview_does_not_accept_actual_sent_field_as_transport_evidence() -> None:
    preview = _preview()
    preview["deliveries"][0]["status"] = "sent"
    result = explain_route(preview)
    assert result["status"] == "no_targets"
    assert result["channels"] == []
    assert "передано сервису" not in str(result)


def test_unknown_reason_and_raw_error_do_not_leak_notification_or_provider_text() -> None:
    preview = _preview([])
    preview["deliveries"] = [{"channel": "voice", "status": "error", "reason": "unknown_backend_reason", "error": "secret transport details"}]
    result = explain_route(preview)
    assert result["reason"] == "unknown_backend_reason"
    assert "причина не уточнена" in result["summary"]
    assert "secret transport details" not in str(result)
    assert "private notification text" not in str(result)


def test_explanations_do_not_mutate_or_return_input_lists() -> None:
    preview = _preview(["push"])
    preview["warnings"] = ["Условие зависит от состояния дома."]
    original = deepcopy(preview)
    result = explain_route(preview)
    result["channels"].append("other")
    result["warnings"].clear()
    result["steps"][0]["detail"] = "changed"
    assert preview == original


@pytest.mark.parametrize(
    "results, expected",
    [
        ([], "no_targets"),
        ([{"channel": "push", "status": "planned"}], "no_targets"),
        ([{"channel": "push", "status": "sent"}], "sent"),
        ([{"channel": "push", "status": "sent"}, {"channel": "voice", "status": "error"}], "partial"),
        ([{"channel": "push", "status": "sent"}, {"channel": "voice", "status": "dropped"}], "partial"),
        ([{"channel": "push", "status": "error"}], "error"),
        ([{"channel": "push", "status": "dropped", "reason": "channel_disabled"}], "no_targets"),
    ],
)
def test_actual_outcome_derives_truth_from_per_channel_results(results, expected) -> None:
    original = deepcopy(results)
    result = explain_outcome("sent", results=results)
    assert result["status"] == expected
    assert result["channels"] == (["push"] if expected in {"sent", "partial"} else [])
    assert results == original
    if expected in {"sent", "partial"}:
        assert "не подтверждает получение" in result["warnings"][0]


def test_queue_is_not_a_sent_receipt_and_dropped_reason_is_explained() -> None:
    channels = ["push"]
    queued = explain_outcome("queued", channels=channels)
    assert queued["status"] == "queued"
    assert "отправка ещё не завершена" in queued["summary"]
    queued["channels"].append("voice")
    assert channels == ["push"]
    dropped = explain_outcome("dropped", reason="deduplicated")
    assert dropped["status"] == "dropped"
    assert dropped["channels"] == []
    assert "периода подавления повторов" in dropped["summary"]


def test_error_outcome_omits_raw_provider_exception() -> None:
    result = explain_outcome("error", results=[{"channel": "voice", "status": "error", "error": "private provider exception"}])
    assert result["status"] == "error"
    assert result["reason"] == "delivery_error"
    assert "private provider exception" not in str(result)


def test_unknown_outcome_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        explain_outcome("planned")


def test_sent_status_without_channel_is_not_a_receipt() -> None:
    result = explain_outcome("sent", results=[{"status": "sent"}])
    assert result["status"] == "no_targets"
    assert "передано сервису" not in str(result)


@pytest.mark.parametrize("blocked_reason", [None, "level_disabled"])
def test_actual_history_can_omit_plan_only_steps_and_keep_exclusions(blocked_reason) -> None:
    preview = _preview(["push"])
    preview["prechecks"]["blocked_reason"] = blocked_reason
    preview["channel_decisions"] = [{"channel": "offline", "selected": False, "reason": "channel_disabled"}]
    preview["deliveries"].append({"channel": "voice", "status": "error", "reason": "tts_target_missing"})
    full = explain_route(preview)
    history = explain_route(preview, include_planned_steps=False)

    assert any(step["label"] == "Канал push" for step in full["steps"])
    assert not any(step["label"] == "Канал push" for step in history["steps"])
    assert any(step["label"] == "Канал offline" for step in history["steps"])
    assert any(step["label"] == "Канал voice" for step in history["steps"])
    assert history["status"] == full["status"]
    assert history["channels"] == full["channels"]
    if blocked_reason:
        assert history["steps"][0]["label"] == "Предварительная проверка"
