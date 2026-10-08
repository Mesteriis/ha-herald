"""Bounded local configuration checks without delivery or credential inspection."""

from __future__ import annotations

import re
from collections.abc import Mapping
from itertools import islice
from typing import Any

from .const import CONF_MAINTENANCE_MODE_ENTITY, SEVERITY_RANK
from .controls import CHANNEL_FAMILY_TYPES
from .models import HeraldConfig, PresenceSnapshot
from .policy_rules import normalize_room

MAX_CHANNELS = 100
MAX_CHECKS = 20
MAX_TARGETS = 20
_IDENTIFIER = re.compile(r"[a-z0-9_]+\.[a-z0-9_]+")
_SOURCES = {"yaml", "entry", "options", "default", "runtime", "restored", "unknown"}
_SERVICES = {"persistent_notification": "persistent_notification.create", "system_log": "system_log.write",
             "logbook": "logbook.log", "telegram": "telegram_bot.send_message", "tts_hume": "media_player.play_media"}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) and len(value) <= 255 else ""


class _Checks:
    """Keep work and output bounded independently of user-supplied target counts."""

    def __init__(self, hass) -> None:
        self.hass = hass
        self.items: list[dict[str, str]] = []
        self.truncated = False

    def add(self, code: str, status: str, message: str) -> None:
        if len(self.items) >= MAX_CHECKS - 1:
            self.truncated = True
            return
        self.items.append({"code": code, "status": status, "message": message})

    def service(self, value: Any) -> None:
        if len(self.items) >= MAX_CHECKS - 1:
            self.truncated = True
            return
        service = _text(value)
        if not service:
            self.add("service_missing", "error", "Не указан сервис доставки.")
        elif _IDENTIFIER.fullmatch(service) is None:
            self.add("service_invalid", "error", "Имя сервиса должно иметь формат domain.service.")
        elif not self.hass.services.has_service(*service.split(".", 1)):
            self.add("service_missing", "error", f"Сервис {service} не зарегистрирован в Home Assistant.")
        else:
            self.add("service_registered", "ok", f"Сервис {service} зарегистрирован в Home Assistant.")

    def entity(self, value: Any, *, active_only: bool = False, engine: bool = False, domain: str | None = None) -> None:
        if len(self.items) >= MAX_CHECKS - 1:
            self.truncated = True
            return
        entity_id = _text(value)
        prefix = "tts_engine" if engine else "target"
        if not entity_id or _IDENTIFIER.fullmatch(entity_id) is None:
            self.add(f"{prefix}_missing", "error", "Не указан корректный TTS engine_entity_id." if engine else "Не указана корректная сущность цели.")
            return
        if engine and not entity_id.startswith("tts."):
            self.add("tts_engine_invalid", "error", "engine_entity_id должен указывать на сущность домена tts.")
            return
        if domain and not entity_id.startswith(f"{domain}."):
            self.add("target_domain_invalid", "error", f"Для этого способа доставки нужна цель домена {domain}.")
            return
        state = self.hass.states.get(entity_id)
        if state is None:
            self.add(f"{prefix}_missing", "error", f"Сущность {entity_id} отсутствует в Home Assistant.")
        elif state.state in {"unknown", "unavailable"}:
            self.add(f"{prefix}_unavailable", "warning", f"Состояние {entity_id} недоступно; готовность цели не подтверждена.")
        elif not engine and (state.state == "off" or active_only and state.state in {"idle", "standby"}):
            self.add("target_inactive", "warning", f"Цель {entity_id} неактивна; её выбор зависит от способа доставки.")
        else:
            self.add(f"{prefix}_available", "ok", f"Сущность {entity_id} существует и имеет известное состояние.")

    def targets(self, value: Any, *, single: bool = False, active_only: bool = False, domain: str | None = None) -> None:
        values = value if isinstance(value, list) else [value]
        if not values or single and not isinstance(value, str):
            self.add("target_invalid", "error", "Для этого способа доставки нужна одна конкретная цель." if single else "Список целей пуст.")
            return
        self.truncated |= len(values) > MAX_TARGETS
        for item in values[:MAX_TARGETS]:
            self.entity(item, active_only=active_only, domain=domain)

    def finish(self) -> tuple[str, list[dict[str, str]]]:
        if self.truncated:
            self.items.append({"code": "checks_truncated", "status": "not_checked", "message": "Часть целей или проверок не показана из-за ограничения размера отчёта."})
        statuses = {item["status"] for item in self.items}
        status = "attention" if statuses & {"error", "warning"} else "not_checked" if "not_checked" in statuses else "configured"
        return status, self.items


def _setting(current: Any, key: str, settings: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only scalar provenance for these two fields; reject stale snapshots."""
    stored = settings.get(key)
    if not isinstance(stored, Mapping) or type(stored.get("value")) is not type(current) or stored["value"] != current:
        return {"value": current, "source": "unknown", "inherited": None, "inherited_source": "unknown"}
    inherited = stored.get("inherited")
    source, inherited_source = stored.get("source"), stored.get("inherited_source")
    return {"value": current, "source": source if isinstance(source, str) and source in _SOURCES else "unknown",
            "inherited": inherited if type(inherited) is type(current) else None,
            "inherited_source": inherited_source if isinstance(inherited_source, str) and inherited_source in _SOURCES else "unknown"}


def _channel_checks(channel, checks: _Checks) -> list[str]:
    """Inspect allowlisted transport fields; never iterate or copy channel.data."""
    kind = channel.channel_type
    data = channel.data if isinstance(channel.data, Mapping) else {}
    rooms: set[str] = set()
    if room := normalize_room(channel.room) if isinstance(channel.room, str) else "":
        rooms.add(room)
    mappings = {}
    for key in ("room_targets", "audio_targets", "notify_services"):
        raw = data.get(key, {}) if kind in {"tts", "tv", "tts_hume"} else {}
        used = kind == "tts" and key != "notify_services" or kind == "tv" and key != "audio_targets"
        if not used:
            if raw:
                checks.add("target_mapping_ignored", "warning", f"Параметр {key} не используется способом доставки {kind}.")
            mappings[key] = []
            continue
        if not isinstance(raw, Mapping):
            checks.add("target_mapping_invalid", "error", f"Параметр {key} должен быть словарём комнат.")
            mappings[key] = []
            continue
        entries = list(islice(raw.items(), MAX_TARGETS))
        checks.truncated |= len(raw) > MAX_TARGETS
        seen: set[str] = set()
        for room_name, _ in entries:
            room = normalize_room(room_name) if isinstance(room_name, str) else ""
            if not room or room in {"all", "auto"}:
                checks.add("room_mapping_invalid", "warning", "В карте целей есть пустая комната или общее указание auto/all.")
            elif room in seen:
                checks.add("room_mapping_ambiguous", "warning", f"Несколько названий комнаты {room} совпадают после нормализации.")
            else:
                rooms.add(room)
                seen.add(room)
        mappings[key] = entries

    if kind in {"tts", "tv", "tts_hume"}:
        single = kind == "tv" or kind == "tts" and channel.service == "tts.speak"
        domain = "media_player" if single or kind == "tts_hume" else None
        configured_target = channel.entity_id
        if kind == "tts_hume":
            configured_target = configured_target or data.get("media_player")
        if configured_target is not None:
            checks.targets(configured_target, single=single, domain=domain, active_only=kind == "tv" and bool(data.get("active_only", True)))
        for _, target in mappings["room_targets"]:
            checks.targets(target, single=single, domain=domain, active_only=kind == "tv" and bool(data.get("active_only", True)))
        for _, targets in mappings["audio_targets"]:
            if not isinstance(targets, list) or not targets:
                checks.add("audio_targets_invalid", "error", "Комната должна содержать непустой список аудиоцелей.")
                continue
            checks.truncated |= len(targets) > MAX_TARGETS
            for item in targets[:MAX_TARGETS]:
                if not isinstance(item, Mapping):
                    checks.add("audio_target_invalid", "error", "Аудиоцель должна содержать параметры устройства.")
                    continue
                service = item.get("service") or channel.service or "tts.yandex_station_say"
                checks.targets(item.get("entity_id"), single=service == "tts.speak", domain="media_player" if service == "tts.speak" else None, active_only=bool(item.get("active_only", False)))
                checks.service(service)
                if service == "tts.speak":
                    checks.entity(item.get("engine_entity_id") or data.get("engine_entity_id"), engine=True)
        if configured_target is None and (kind == "tts_hume" or not mappings["room_targets"] and (kind == "tv" or not mappings["audio_targets"])):
            checks.add("target_missing", "error", "Явная цель доставки не настроена.")

    if kind == "tts":
        if channel.entity_id is not None or mappings["room_targets"] or not mappings["audio_targets"]:
            service = channel.service or "tts.yandex_station_say"
            checks.service(service)
            if service == "tts.speak":
                if channel.entity_id is not None and not isinstance(channel.entity_id, str):
                    checks.add("target_invalid", "error", "tts.speak требует одну цель media_player.")
                checks.entity(data.get("engine_entity_id"), engine=True)
    elif kind == "tv":
        for _, service in mappings["notify_services"]:
            checks.service(service)
        if channel.service or not mappings["notify_services"]:
            checks.service(channel.service)
        if channel.service == "tts.speak" or any(service == "tts.speak" for _, service in mappings["notify_services"]):
            checks.entity(data.get("engine_entity_id"), engine=True)
    elif kind == "mobile_app":
        checks.service(channel.service)
        if not channel.user:
            checks.add("owner_not_configured", "warning", "У персонального канала не указан владелец; правила с выбранными людьми могут исключать этот канал.")
    elif kind in _SERVICES:
        service = channel.service or _SERVICES[kind] if kind == "telegram" else _SERVICES[kind]
        checks.service(service)
        if kind == "telegram" and service == "notify.send_message":
            checks.targets(channel.entity_id, single=True, domain="notify")
    elif kind == "dashboard":
        checks.add("internal_feed", "ok", "Внутренний канал ленты Herald настроен.")
    else:
        checks.add("channel_type_unknown", "warning", "Тип канала не распознан; текущий маршрутизатор использует запись в системный журнал.")
        checks.service("system_log.write")
    if kind == "tts_hume":
        checks.add("provider_not_checked", "not_checked", "Учётные данные Hume, доступность провайдера и воспроизведение не проверялись.")
    elif kind == "telegram":
        checks.add("recipient_not_checked", "not_checked", "Авторизация Telegram и адресат не проверялись; личные идентификаторы не читались.")
    checks.truncated |= len(rooms) > MAX_TARGETS
    return sorted(rooms)[:MAX_TARGETS]


def build_configuration_report(
    hass, config: HeraldConfig, controls, presence: PresenceSnapshot, *, control_entities: dict[str, str],
    checked_at: str, effective_settings: dict[str, Any] | None = None, maintenance_active: bool | None = None,
) -> dict[str, Any]:
    """Describe local setup only, using already published scalar provenance if given."""
    restrictions: list[dict[str, str]] = []

    def restrict(code: str, title: str, detail: str, key: str | None = None) -> None:
        entry = {"code": code, "title": title, "detail": detail}
        if key and control_entities.get(key):
            entry["entity_id"] = control_entities[key]
        restrictions.append(entry)

    if controls.is_mute_all_enabled():
        restrict("mute_all", "Обычные уведомления отключены", "Общее отключение ограничивает обычные события; критические события и принудительные запросы могут проходить.", "mute_all")
    internal_maintenance = controls.maintenance_mode_enabled()
    if maintenance_active is None:
        external = _text(config.router.get(CONF_MAINTENANCE_MODE_ENTITY))
        state = hass.states.get(external) if external else None
        maintenance_active = internal_maintenance or state is not None and state.state == "on"
    if maintenance_active:
        restrict("maintenance", "Режим обслуживания", "Обычные каналы заменяются уведомлением Home Assistant и системным журналом.", "maintenance_mode" if internal_maintenance else None)
    if presence.quiet_hours:
        restrict("quiet_hours", "Сейчас тихие часы", "Обычные голосовые и TV-каналы зависят от своей политики тихих часов. Критические события имеют исключения; правила событий могут быть строже.")
    if presence.nobody_home:
        restrict("away", "Никого нет дома", "Маршрут ограничивается каналами для отсутствия дома; без отдельной настройки голос и TV исключаются.")
    labels = {"voice": "Голос", "push": "Личные сообщения", "tv": "TV"}
    for family in CHANNEL_FAMILY_TYPES:
        if not bool(controls.value(f"channel_family:{family}", True)):
            restrict(f"family_disabled:{family}", f"Семейство «{labels[family]}» отключено", "Обычные уведомления не используют каналы этого семейства.", f"channel_family:{family}")
    for level, label in (("info", "Информационные"), ("warning", "Предупреждения"), ("critical", "Критические")):
        if not controls.is_level_enabled(level):
            restrict(f"level_disabled:{level}", f"Уровни «{label}» отключены", "Ограничение действует на обычный приём событий соответствующей группы уровней; force может его обойти.", f"level_enabled:{level}")

    settings = effective_settings or {}
    channels = []
    truncated = len(config.channels) > MAX_CHANNELS
    enabled_count = 0
    for index, (name, channel) in enumerate(sorted(config.channels.items())):
        enabled_key, level_key = f"channel_enabled:{name}", f"channel_min_level:{name}"
        enabled = bool(controls.value(enabled_key, channel.enabled))
        enabled_count += int(enabled)
        if index >= MAX_CHANNELS:
            continue
        minimum = _text(controls.value(level_key, channel.min_level))
        checks = _Checks(hass)
        if not enabled:
            checks.add("channel_disabled", "ok", "Канал выключен настройкой; это не ошибка конфигурации.")
        if minimum not in SEVERITY_RANK:
            checks.add("min_level_invalid", "warning", "Минимальный уровень не распознан; проверьте настройку канала.")
        if channel.quiet_hours_policy not in {"default", "allow", "block"}:
            checks.add("quiet_hours_policy_invalid", "warning", "Политика тихих часов не распознана; будет применено стандартное поведение типа канала.")
        rooms = _channel_checks(channel, checks)
        status, items = checks.finish()
        truncated |= checks.truncated
        channels.append({"name": name, "type": channel.channel_type, "enabled": enabled, "min_level": minimum,
                         "quiet_hours_policy": channel.quiet_hours_policy, "user": channel.user, "rooms": rooms,
                         "controls": {"enabled": control_entities.get(enabled_key), "min_level": control_entities.get(level_key)},
                         "settings": {"enabled": _setting(enabled, enabled_key, settings), "min_level": _setting(minimum, level_key, settings)},
                         "status": status, "checks": items})
    limitations = ["Проверены только локальная настройка и состояния Home Assistant. Доставка уведомлений не выполнялась и не подтверждена.",
                   "Авторизация и доступность внешних провайдеров не проверялись. Конкретный маршрут также зависит от события, его правил и текущей аудитории."]
    if truncated:
        limitations.append("Отчёт ограничен по размеру. Общее число и число включённых учитывают все каналы; не показанные каналы включены в число непроверенных. Внутри каналов часть целей может быть не проверена.")
    return {"schema_version": 1, "checked_at": checked_at, "restrictions": restrictions, "channels": channels,
            "summary": {"total": len(config.channels), "enabled": enabled_count,
                        "attention": sum(item["status"] == "attention" for item in channels),
                        "not_checked": sum(item["status"] == "not_checked" for item in channels) + max(0, len(config.channels) - MAX_CHANNELS)},
            "limitations": limitations, "truncated": truncated}
