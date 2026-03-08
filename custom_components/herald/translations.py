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
