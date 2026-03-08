"""Static language helpers for Herald notifications."""

from __future__ import annotations

from .const import DEFAULT_SUMMARY_TITLES

LANGUAGE_LABELS = {
    "ru": "Russian",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
}

ACTION_FEEDBACK = {
    "ru": {
        "ack": "Уведомление отмечено как обработанное",
        "snooze": "Поток отложен на {minutes} мин.",
        "cleared": "Уведомление скрыто на устройстве",
    },
    "en": {
        "ack": "Notification acknowledged",
        "snooze": "Flow snoozed for {minutes} min.",
        "cleared": "Notification cleared on device",
    },
    "es": {
        "ack": "Notificacion confirmada",
        "snooze": "Flujo pospuesto durante {minutes} min.",
        "cleared": "Notificacion borrada del dispositivo",
    },
    "fr": {
        "ack": "Notification prise en compte",
        "snooze": "Flux reporte pendant {minutes} min.",
        "cleared": "Notification effacee de l'appareil",
    },
}

RUNTIME_FEEDBACK = {
    "ru": {
        "maintenance_on": "Herald перешел в режим обслуживания. Уведомления ниже уровня {level} временно отключены.",
        "maintenance_off": "Herald вышел из режима обслуживания. Обычная доставка уведомлений восстановлена.",
        "mute_all_on": "Herald включил глобальное беззвучие. Все уведомления ниже critical временно заглушены.",
        "mute_all_off": "Herald отключил глобальное беззвучие. Обычная доставка уведомлений восстановлена.",
    },
    "en": {
        "maintenance_on": "Herald entered maintenance mode. Notifications below {level} are temporarily disabled.",
        "maintenance_off": "Herald left maintenance mode. Normal notification delivery is restored.",
        "mute_all_on": "Herald enabled global mute. All notifications below critical are temporarily silenced.",
        "mute_all_off": "Herald disabled global mute. Normal notification delivery is restored.",
    },
    "es": {
        "maintenance_on": "Herald entro en modo de mantenimiento. Las notificaciones por debajo de {level} quedan desactivadas temporalmente.",
        "maintenance_off": "Herald salio del modo de mantenimiento. Se restauro la entrega normal de notificaciones.",
        "mute_all_on": "Herald activo el silencio global. Todas las notificaciones por debajo de critical quedan silenciadas temporalmente.",
        "mute_all_off": "Herald desactivo el silencio global. Se restauro la entrega normal de notificaciones.",
    },
    "fr": {
        "maintenance_on": "Herald est passe en mode maintenance. Les notifications sous le niveau {level} sont temporairement desactivees.",
        "maintenance_off": "Herald a quitte le mode maintenance. La diffusion normale des notifications est restauree.",
        "mute_all_on": "Herald a active le silence global. Toutes les notifications sous critical sont temporairement coupees.",
        "mute_all_off": "Herald a desactive le silence global. La diffusion normale des notifications est restauree.",
    },
}

RUNTIME_STATES = {
    "ru": {"enabled": "включен", "disabled": "выключен"},
    "en": {"enabled": "enabled", "disabled": "disabled"},
    "es": {"enabled": "activado", "disabled": "desactivado"},
    "fr": {"enabled": "active", "disabled": "desactive"},
}

RUNTIME_LEVELS = {
    "ru": {"info": "info", "warning": "warning", "critical": "critical"},
    "en": {"info": "info", "warning": "warning", "critical": "critical"},
    "es": {"info": "info", "warning": "warning", "critical": "critical"},
    "fr": {"info": "info", "warning": "warning", "critical": "critical"},
}

RUNTIME_LANGUAGES = {
    "ru": {"ru": "русский", "en": "английский", "es": "испанский", "fr": "французский"},
    "en": {"ru": "Russian", "en": "English", "es": "Spanish", "fr": "French"},
    "es": {"ru": "ruso", "en": "ingles", "es": "espanol", "fr": "frances"},
    "fr": {"ru": "russe", "en": "anglais", "es": "espagnol", "fr": "francais"},
}

RUNTIME_AUDIO_TARGETS = {
    "ru": {"auto": "авто", "alisa": "Алиса", "homepod": "HomePod", "tv": "телевизор"},
    "en": {"auto": "auto", "alisa": "Alice", "homepod": "HomePod", "tv": "TV"},
    "es": {"auto": "auto", "alisa": "Alice", "homepod": "HomePod", "tv": "TV"},
    "fr": {"auto": "auto", "alisa": "Alice", "homepod": "HomePod", "tv": "TV"},
}


def normalize_language(raw: str | None) -> str:
    """Normalize helper state values to a supported Herald language code."""
    if not raw:
        return "ru"
    lowered = raw.strip().lower()
    if lowered.startswith("es"):
        return "es"
    if lowered.startswith("fr"):
        return "fr"
    if lowered.startswith("en"):
        return "en"
    return "ru"


def default_summary_title(language: str) -> str:
    """Return a static summary title for the requested language."""
    return DEFAULT_SUMMARY_TITLES.get(language, DEFAULT_SUMMARY_TITLES["en"])


def action_feedback_text(
    *,
    language: str,
    kind: str,
    minutes: int | None = None,
) -> str:
    """Return localized callback or follow-up text for actions."""
    templates = ACTION_FEEDBACK.get(language, ACTION_FEEDBACK["en"])
    template = templates.get(kind, ACTION_FEEDBACK["en"]["ack"])
    if "{minutes}" in template:
        return template.format(minutes=minutes or 0)
    return template


def runtime_feedback_text(
    *,
    language: str,
    kind: str,
    level: str | None = None,
) -> str:
    """Return localized Herald runtime self-announcement text."""
    templates = RUNTIME_FEEDBACK.get(language, RUNTIME_FEEDBACK["en"])
    template = templates.get(kind, RUNTIME_FEEDBACK["en"]["maintenance_off"])
    if "{level}" in template:
        return template.format(level=level or "critical")
    return template


def runtime_control_change_text(
    *,
    language: str,
    key: str,
    value: object,
) -> str | None:
    """Return localized speech text for one Herald control-plane change."""
    language = normalize_language(language)
    states = RUNTIME_STATES.get(language, RUNTIME_STATES["en"])
    levels = RUNTIME_LEVELS.get(language, RUNTIME_LEVELS["en"])
    languages = RUNTIME_LANGUAGES.get(language, RUNTIME_LANGUAGES["en"])
    audio_targets = RUNTIME_AUDIO_TARGETS.get(language, RUNTIME_AUDIO_TARGETS["en"])
    enabled_text = states["enabled"] if bool(value) else states["disabled"]

    if key == "maintenance_mode":
        return runtime_feedback_text(
            language=language,
            kind="maintenance_on" if bool(value) else "maintenance_off",
        )
    if key == "mute_all":
        return runtime_feedback_text(
            language=language,
            kind="mute_all_on" if bool(value) else "mute_all_off",
        )
    if key == "dashboard_sidebar":
        return _by_language(
            language,
            ru=f"Herald: dashboard в боковой панели {enabled_text}.",
            en=f"Herald: dashboard in the sidebar {enabled_text}.",
            es=f"Herald: dashboard en la barra lateral {enabled_text}.",
            fr=f"Herald: dashboard dans la barre laterale {enabled_text}.",
        )
    if key == "ai_enabled":
        return _by_language(
            language,
            ru=f"Herald: глобальный AI {enabled_text}.",
            en=f"Herald: global AI {enabled_text}.",
            es=f"Herald: AI global {enabled_text}.",
            fr=f"Herald: AI global {enabled_text}.",
        )
    if key.startswith("ai_level:"):
        level = key.split(":", maxsplit=1)[1]
        return _by_language(
            language,
            ru=f"Herald: AI для уровня {levels.get(level, level)} {enabled_text}.",
            en=f"Herald: AI for {levels.get(level, level)} level {enabled_text}.",
            es=f"Herald: AI para el nivel {levels.get(level, level)} {enabled_text}.",
            fr=f"Herald: AI pour le niveau {levels.get(level, level)} {enabled_text}.",
        )
    if key.startswith("level_enabled:"):
        level = key.split(":", maxsplit=1)[1]
        return _by_language(
            language,
            ru=f"Herald: уровень {levels.get(level, level)} {enabled_text}.",
            en=f"Herald: level {levels.get(level, level)} {enabled_text}.",
            es=f"Herald: nivel {levels.get(level, level)} {enabled_text}.",
            fr=f"Herald: niveau {levels.get(level, level)} {enabled_text}.",
        )
    if key.startswith("channel_family:"):
        family = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: семейство каналов {family} {enabled_text}.",
            en=f"Herald: channel family {family} {enabled_text}.",
            es=f"Herald: familia de canales {family} {enabled_text}.",
            fr=f"Herald: famille de canaux {family} {enabled_text}.",
        )
    if key == "maintenance_min_level":
        level = levels.get(str(value), str(value))
        return _by_language(
            language,
            ru=f"Herald: минимальный уровень обслуживания {level}.",
            en=f"Herald: maintenance minimum level set to {level}.",
            es=f"Herald: nivel minimo de mantenimiento ajustado a {level}.",
            fr=f"Herald: niveau minimum de maintenance regle sur {level}.",
        )
    if key.startswith("room_presence:"):
        room = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: fallback-присутствие комнаты {room} {enabled_text}.",
            en=f"Herald: room fallback presence for {room} {enabled_text}.",
            es=f"Herald: presencia fallback de la habitacion {room} {enabled_text}.",
            fr=f"Herald: presence de secours pour la piece {room} {enabled_text}.",
        )
    if key.startswith("room_audio_target:"):
        room = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        target = audio_targets.get(str(value), str(value))
        return _by_language(
            language,
            ru=f"Herald: устройство уведомлений для комнаты {room} переключено на {target}.",
            en=f"Herald: notification device for room {room} set to {target}.",
            es=f"Herald: dispositivo de notificacion para la habitacion {room} ajustado a {target}.",
            fr=f"Herald: appareil de notification pour la piece {room} regle sur {target}.",
        )
    if key.startswith("user_language:"):
        user = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        target_language = languages.get(str(value), str(value))
        return _by_language(
            language,
            ru=f"Herald: язык пользователя {user} переключен на {target_language}.",
            en=f"Herald: language for user {user} set to {target_language}.",
            es=f"Herald: idioma del usuario {user} ajustado a {target_language}.",
            fr=f"Herald: langue de l'utilisateur {user} reglee sur {target_language}.",
        )
    if key.startswith("user_character:"):
        user = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: персонаж пользователя {user} переключен на {value}.",
            en=f"Herald: character for user {user} set to {value}.",
            es=f"Herald: personaje del usuario {user} ajustado a {value}.",
            fr=f"Herald: personnage de l'utilisateur {user} regle sur {value}.",
        )
    if key.startswith("user_silent:"):
        user = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: тихий режим пользователя {user} {enabled_text}.",
            en=f"Herald: silent mode for user {user} {enabled_text}.",
            es=f"Herald: modo silencioso del usuario {user} {enabled_text}.",
            fr=f"Herald: mode silencieux pour l'utilisateur {user} {enabled_text}.",
        )
    if key.startswith("flow_enabled:"):
        flow = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: поток {flow} {enabled_text}.",
            en=f"Herald: flow {flow} {enabled_text}.",
            es=f"Herald: flujo {flow} {enabled_text}.",
            fr=f"Herald: flux {flow} {enabled_text}.",
        )
    if key.startswith("flow_summary_window:"):
        flow = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: окно summary потока {flow} установлено на {value} секунд.",
            en=f"Herald: summary window for flow {flow} set to {value} seconds.",
            es=f"Herald: ventana de resumen del flujo {flow} ajustada a {value} segundos.",
            fr=f"Herald: fenetre de resume du flux {flow} reglee sur {value} secondes.",
        )
    if key.startswith("flow_dedup_window:"):
        flow = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: окно dedup потока {flow} установлено на {value} секунд.",
            en=f"Herald: dedup window for flow {flow} set to {value} seconds.",
            es=f"Herald: ventana de deduplicacion del flujo {flow} ajustada a {value} segundos.",
            fr=f"Herald: fenetre de deduplication du flux {flow} reglee sur {value} secondes.",
        )
    if key.startswith("flow_cooldown:"):
        flow = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: cooldown потока {flow} установлен на {value} секунд.",
            en=f"Herald: cooldown for flow {flow} set to {value} seconds.",
            es=f"Herald: cooldown del flujo {flow} ajustado a {value} segundos.",
            fr=f"Herald: cooldown du flux {flow} regle sur {value} secondes.",
        )
    if key.startswith("channel_enabled:"):
        channel = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        return _by_language(
            language,
            ru=f"Herald: канал {channel} {enabled_text}.",
            en=f"Herald: channel {channel} {enabled_text}.",
            es=f"Herald: canal {channel} {enabled_text}.",
            fr=f"Herald: canal {channel} {enabled_text}.",
        )
    if key.startswith("channel_min_level:"):
        channel = _humanize_runtime_token(key.split(":", maxsplit=1)[1])
        level = levels.get(str(value), str(value))
        return _by_language(
            language,
            ru=f"Herald: минимальный уровень канала {channel} установлен на {level}.",
            en=f"Herald: minimum level for channel {channel} set to {level}.",
            es=f"Herald: nivel minimo del canal {channel} ajustado a {level}.",
            fr=f"Herald: niveau minimum du canal {channel} regle sur {level}.",
        )
    return None


def _by_language(language: str, *, ru: str, en: str, es: str, fr: str) -> str:
    if language == "ru":
        return ru
    if language == "es":
        return es
    if language == "fr":
        return fr
    return en


def _humanize_runtime_token(value: str) -> str:
    return value.replace("_", " ").strip().title()
