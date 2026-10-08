"""Pure, human-readable explanations of routing plans and recorded outcomes."""

from __future__ import annotations

from typing import Any

_REASON_TEXT = {
    "notification_policy_no_recipients": "среди текущих получателей нет выбранных правилом людей",
    "policy_someone_home": "правило разрешает отправку, только когда кто-то дома",
    "policy_nobody_home": "правило разрешает отправку, только когда никого нет дома",
    "policy_quiet_hours": "правило запрещает отправку в тихие часы",
    "policy_target_room": "канал не имеет подходящего устройства в выбранной правилом комнате",
    "policy_text_only": "в тихие часы правило разрешает только текст, без голоса и TV",
    "policy_unknown_user": "выбранный правилом получатель отсутствует в текущем списке людей",
    "policy_unknown_room": "выбранная правилом комната отсутствует в текущем списке комнат",
    "policy_invalid_presence": "в правиле задано неизвестное условие присутствия",
    "policy_invalid_quiet_hours": "в правиле задано неизвестное условие тихих часов",
    "policy_route_changed": "условия маршрута изменились во время обработки уведомления",
    "notification_policy_disabled": "уведомление отключено его правилом",
    "level_disabled": "этот уровень важности отключён",
    "flow_disabled": "поток отключён или временно отложен",
    "conditions_not_met": "условия потока сейчас не выполнены",
    "mute_all": "включена общая тишина",
    "flow_cooldown": "ещё действует пауза после предыдущей отправки",
    "deduplicated": "такое уведомление уже принято в пределах периода подавления повторов",
    "missing_channel": "канал отсутствует в конфигурации",
    "channel_disabled": "канал отключён",
    "channel_family_disabled": "этот тип каналов отключён",
    "channel_min_level": "важность уведомления ниже порога канала",
    "user_filter": "канал не соответствует получателям или их режиму тишины",
    "presence_policy": "канал не подходит по присутствию получателя дома",
    "mobile_zone_filter": "устройство не соответствует выбранной зоне",
    "room_audio_unavailable": "в выбранной комнате нет доступного голосового устройства",
    "tv_inactive": "телевизор неактивен",
    "tv_target_missing": "для телевизора не задана цель отправки",
    "tts_target_missing": "для голосового канала не задана цель отправки",
    "hume_api_key_missing": "для голосового канала не настроен ключ Hume",
    "quiet_hours": "каналы исключены правилом тихих часов",
    "presence": "каналы исключены по присутствию дома",
    "device": "маршрут ограничен указанным устройством",
    "local_target": "выбрано другое локальное устройство комнаты",
    "no_channels": "подходящих каналов не осталось",
    "delivery_error": "сервис доставки вернул ошибку",
    "unconfirmed_delivery": "нет подтверждённой передачи сервису доставки",
}
_POLICY_TEXT = {
    "inherit": "Используются каналы, заданные запросом или потоком.",
    "disabled": "Уведомление отключено.",
    "text_only": "Задано правило: только текстовые каналы, без голоса и TV.",
    "push_only": "Задано правило: только мобильные уведомления и Telegram.",
    "voice_only": "Задано правило: только голосовые каналы и TV.",
    "custom": "Задан собственный список каналов.",
}
_STAGE_LABELS = {
    "device": "Устройство",
    "presence": "Присутствие",
    "quiet_hours": "Тихие часы",
    "severity": "Важность",
    "activity": "Занятие дома",
    "room": "Комната",
    "local_target": "Локальное устройство",
    "final": "Итоговый отбор",
}
_STAGE_REMOVALS = {
    "device": "Оставлены каналы указанного устройства. Исключены",
    "presence": "Правило присутствия исключило",
    "quiet_hours": "Правило тихих часов исключило",
    "local_target": "Выбрано одно локальное устройство комнаты по приоритету Алиса → HomePod → TV. Исключены",
}
_PREVIEW_WARNING = (
    "Это расчёт маршрута без отправки. Доступность сервисов доставки и получение уведомления устройствами не проверялись."
)
_RECEIPT_WARNING = "Успех вызова сервиса не подтверждает получение или прочтение уведомления на устройстве."


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _records(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return list(dict.fromkeys(item for item in value if isinstance(item, str) and item)) if isinstance(value, list) else []


def _reason(value: Any, default: str) -> str:
    """Keep reason codes machine-readable without echoing arbitrary error text."""
    if isinstance(value, str) and value and len(value) <= 80 and all(char.isascii() and (char.isalnum() or char == "_") for char in value):
        return value
    return default


def _reason_text(reason: str) -> str:
    return _REASON_TEXT.get(reason, "причина не уточнена")


def _channels_text(channels: list[str]) -> str:
    return ", ".join(channels) if channels else "нет"


def _result_step(item: dict[str, Any], *, preview: bool) -> dict[str, str]:
    channel = item.get("channel")
    label = f"Канал {channel}" if isinstance(channel, str) and channel else "Канал"
    status = item.get("status")
    if preview and status == "planned":
        detail = "Запланирован; отправка не выполнялась."
    elif preview and status == "blocked":
        detail = "Маршрут канала рассчитан, но предварительная проверка запрещает отправку."
    elif not preview and status == "sent" and isinstance(channel, str) and channel:
        detail = "Уведомление передано сервису доставки."
    elif status == "dropped":
        detail = f"Пропущен: {_reason_text(_reason(item.get('reason'), 'no_channels'))}."
    elif status == "error":
        detail = f"Ошибка: {_reason_text(_reason(item.get('reason'), 'delivery_error'))}."
    else:
        detail = "Нет подтверждённого результата отправки."
    return {"label": label, "detail": detail}


def explain_route(preview: dict[str, Any], *, include_planned_steps: bool = True) -> dict[str, Any]:
    """Explain a preview without sending, invoking AI or mutating its snapshot.

    ``channels`` contains only channels with a planned delivery and is empty
    when admission is blocked. Optional ``policy``, ``scenario`` and ``warnings``
    enrich the explanation but never serve as evidence of an actual delivery.
    Set ``include_planned_steps=False`` when appending actual channel outcomes
    later; exclusion and precheck steps remain part of the explanation.
    """
    preview = _mapping(preview)
    prechecks = _mapping(preview.get("prechecks"))
    deliveries = _records(preview.get("deliveries"))
    steps: list[dict[str, str]] = []
    warnings = [_PREVIEW_WARNING, *_strings(preview.get("warnings"))]
    scenario = preview.get("scenario")
    if isinstance(scenario, str) and scenario in {"quiet_hours", "away"}:
        name = "Тихие часы" if scenario == "quiet_hours" else "Никого нет дома"
        steps.append({"label": "Сценарий", "detail": f"Расчёт для сценария «{name}»."})
    policy = _mapping(preview.get("policy"))
    mode = policy.get("delivery_mode")
    policy_detail = _POLICY_TEXT.get(mode) if isinstance(mode, str) else None
    if policy_detail:
        steps.append({"label": "Правило уведомления", "detail": policy_detail})
    if isinstance(policy.get("users"), list):
        steps.append({"label": "Получатели", "detail": "Правило ограничивает текущих получателей выбранными людьми; новых получателей не добавляет."})
        warnings.append("Общие каналы Home Assistant и журнала видны всем их пользователям; правило получателей не делает их личными.")
    if policy.get("target_room"):
        steps.append({"label": "Комната по правилу", "detail": f"Голос и TV допускаются только в комнате «{policy['target_room']}»."})
    if policy.get("presence") in {"someone_home", "nobody_home"}:
        detail = "Кто-то должен быть дома." if policy["presence"] == "someone_home" else "Дома никого не должно быть."
        steps.append({"label": "Присутствие по правилу", "detail": detail})
    if policy.get("quiet_hours") in {"text_only", "mute"}:
        detail = "В тихие часы разрешён только текст." if policy["quiet_hours"] == "text_only" else "В тихие часы отправка запрещена."
        steps.append({"label": "Тихие часы по правилу", "detail": detail})
    if prechecks.get("maintenance_redirect"):
        steps.append({"label": "Обслуживание", "detail": "Режим обслуживания заменяет обычный маршрут уведомлением в Home Assistant и записью в журнал."})

    excluded_reasons: list[str] = []
    for item in _records(preview.get("channel_decisions")):
        if item.get("selected") is False:
            reason = _reason(item.get("reason"), "no_channels")
            excluded_reasons.append(reason)
            steps.append(_result_step({**item, "status": "dropped", "reason": reason}, preview=True))

    previous: list[str] | None = None
    for stage in _records(preview.get("resolution_trace")):
        name = stage.get("stage")
        current = _strings(stage.get("channels"))
        if name == "explicit_bypass":
            if not prechecks.get("maintenance_redirect"):
                steps.append({"label": "Прямой маршрут", "detail": "Указанные каналы выбраны с обходом обычных ограничений."})
        elif name == "initial":
            steps.append({"label": "Доступные каналы", "detail": f"После проверки настроек: {_channels_text(current)}."})
        elif isinstance(name, str) and name in _STAGE_LABELS and previous is not None:
            removed = [channel for channel in previous if channel not in current]
            if removed:
                excluded_reasons.append(name)
                detail = f"{_STAGE_REMOVALS.get(name, 'На этом этапе исключены')}: {_channels_text(removed)}."
                steps.append({"label": _STAGE_LABELS[name], "detail": detail})
            elif current != previous and current:
                steps.append({"label": _STAGE_LABELS[name], "detail": f"Порядок каналов: {_channels_text(current)}."})
            elif name == "quiet_hours" and _mapping(preview.get("presence")).get("quiet_hours"):
                steps.append({"label": "Тихие часы", "detail": f"Включены; после проверки остались: {_channels_text(current)}."})
        previous = current

    planned = _strings([item.get("channel") for item in deliveries if item.get("status") == "planned"])
    blocked = prechecks.get("blocked_reason")
    for item in deliveries:
        if item.get("status") == "error" or item.get("status") == "dropped":
            excluded_reasons.append(_reason(item.get("reason"), "delivery_error" if item.get("status") == "error" else "no_channels"))
        if include_planned_steps or item.get("status") != "planned":
            plan = {**item, "status": "blocked"} if blocked and item.get("status") == "planned" else item
            steps.append(_result_step(plan, preview=True))
    if blocked:
        status = "blocked"
        reason = _reason(blocked, "admission_blocked")
        summary = f"Не будет отправлено: {_reason_text(reason)}."
        planned = []
        steps.insert(0, {"label": "Предварительная проверка", "detail": summary})
    elif planned:
        status = "deliver"
        reason = "maintenance_redirect" if prechecks.get("maintenance_redirect") else "route_ready"
        summary = f"Маршрут готов: {_channels_text(planned)}. Отправка не выполнялась."
    else:
        status = "no_targets"
        reason = excluded_reasons[-1] if excluded_reasons else "no_channels"
        summary = f"Отправка не запланирована: {_reason_text(reason)}."
    if not deliveries and _strings(_mapping(preview.get("resolved")).get("final_channels")):
        warnings.append("Каналы выбраны, но план отправки по ним отсутствует; готовность маршрута не подтверждена.")
    return {"status": status, "reason": reason, "summary": summary, "steps": steps,
            "channels": planned, "warnings": list(dict.fromkeys(warnings))}


def explain_outcome(
    status: str,
    *,
    reason: str | None = None,
    results: list[dict[str, Any]] | None = None,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Explain actual admission or per-channel results without overstating receipt.

    For ``sent``/``error`` inputs, results determine the status: sent, partial,
    error or no_targets. Only an explicit sent channel result confirms a send.
    Raw provider error text is deliberately excluded from the explanation.
    """
    if status not in {"dropped", "queued", "sent", "error"}:
        raise ValueError("Unsupported Herald outcome status")
    records = _records(results)
    steps = [_result_step(item, preview=False) for item in records]
    warnings: list[str] = []
    selected: list[str] = []
    if status == "queued":
        selected = _strings(channels)
        code = "queued"
        summary = "Уведомление принято в очередь; отправка ещё не завершена."
    elif status == "dropped":
        code = _reason(reason, "notification_dropped")
        summary = f"Уведомление пропущено: {_reason_text(code)}."
    else:
        sent = [item for item in records if item.get("status") == "sent" and isinstance(item.get("channel"), str) and item["channel"]]
        errors = [item for item in records if item.get("status") == "error"]
        selected = _strings([item.get("channel") for item in sent])
        if sent:
            status = "sent" if len(sent) == len(records) else "partial"
            code = "sent" if status == "sent" else "partial_delivery"
            summary = (
                f"Уведомление передано сервисам доставки: {_channels_text(selected)}."
                if status == "sent" else "Часть каналов приняла уведомление; остальные пропущены или завершились без подтверждения."
            )
            warnings.append(_RECEIPT_WARNING)
        elif errors or status == "error":
            status = "error"
            code = _reason(reason or (errors[0].get("reason") if errors else None), "delivery_error")
            summary = f"Отправка завершилась ошибкой: {_reason_text(code)}."
        else:
            status = "no_targets"
            code = _reason(reason or (records[0].get("reason") if records else None), "unconfirmed_delivery")
            summary = f"Нет подтверждённых отправок: {_reason_text(code)}."
    if not steps:
        steps.append({"label": "Результат", "detail": summary})
    return {"status": status, "reason": code, "summary": summary, "steps": steps,
            "channels": selected, "warnings": warnings}
