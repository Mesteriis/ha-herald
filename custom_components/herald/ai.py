"""Async AI helpers for Herald notification rewriting and summarization."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant

from .characters import CharacterManager
from .const import DEFAULT_PERSONALITY
from .controls import HeraldControlManager
from .models import HeraldConfig, NotificationContext
from .translations import LANGUAGE_LABELS, default_summary_title

_LOGGER = logging.getLogger(__name__)


class HeraldAIClient:
    """Ollama-backed rewrite and summary client."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        config: HeraldConfig,
        character_manager: CharacterManager,
        controls: HeraldControlManager,
    ) -> None:
        self._hass = hass
        self._session = session
        self._config = config
        self._character_manager = character_manager
        self._controls = controls

    @property
    def enabled(self) -> bool:
        """Return whether AI rewriting is enabled globally."""
        return bool(self._config.ollama.get("enabled", True)) and self._controls.is_ai_enabled()

    def should_use_ai(self, level: str) -> bool:
        """Return whether AI is enabled for the requested severity level."""
        return self.enabled and self._controls.is_ai_enabled(level)

    async def async_rewrite_payload(
        self,
        *,
        title: str,
        message: str,
        level: str,
        language: str,
        character: str | None,
        rewrite: bool,
        render_context: dict[str, Any],
    ) -> dict[str, str]:
        """Rewrite and optionally translate a single notification payload."""
        if not rewrite:
            return {"title": title, "message": message}
        if not self.should_use_ai(level):
            return {"title": title, "message": message}

        prompt = self._build_notification_prompt(
            title=title,
            message=message,
            level=level,
            language=language,
            character=character,
            render_context=render_context,
        )
        response = await self._async_generate_json(prompt)
        if not response:
            return {"title": title, "message": message}
        new_title = str(response.get("title", title)).strip() or title
        new_message = str(response.get("message", message)).strip() or message
        return {"title": new_title, "message": new_message}

    async def async_summarize_notifications(
        self,
        notifications: list[NotificationContext],
        *,
        language: str,
        character: str | None,
        render_context: dict[str, Any],
    ) -> dict[str, str]:
        """Summarize a group of notifications into one payload."""
        title = default_summary_title(language)
        lines = [
            {
                "event": item.event or item.title,
                "level": item.level,
                "message": item.message,
                "entities": list(item.entities),
                "context": dict(item.context_data),
            }
            for item in notifications
        ]
        if not self.should_use_ai(notifications[0].level if notifications else "info"):
            return {"title": title, "message": self._static_summary(lines, language)}

        prompt = self._build_summary_prompt(
            language=language,
            character=character,
            notifications=lines,
            render_context=render_context,
        )
        response = await self._async_generate_json(prompt)
        if not response:
            return {"title": title, "message": self._static_summary(lines, language)}
        return {
            "title": str(response.get("title", title)).strip() or title,
            "message": str(response.get("message", self._static_summary(lines, language))).strip()
            or self._static_summary(lines, language),
        }

    def _build_notification_prompt(
        self,
        *,
        title: str,
        message: str,
        level: str,
        language: str,
        character: str | None,
        render_context: dict[str, Any],
    ) -> str:
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        template_context = {
            **render_context,
            "event": render_context.get("event") or title,
            "message": message,
            "level": level,
            "language": target_language,
        }
        system_prompt = self._character_manager.render_prompt(character, "system.jinja", template_context)
        template_name = "critical.jinja" if level in {"critical", "security"} else "notification.jinja"
        notification_prompt = self._character_manager.render_prompt(character, template_name, template_context)
        if system_prompt and notification_prompt:
            return f"{system_prompt}\n\n{notification_prompt}"

        personality_prompt = self._resolve_personality_prompt(character)
        return (
            "Return valid JSON only with keys title and message. "
            f"Rewrite this smart-home notification for {target_language}. "
            "Keep every factual detail, stay concise, and avoid markdown.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            f"Severity: {level}\n"
            f"Original title: {title}\n"
            f"Original message: {message}\n"
            f"Context: {json.dumps(render_context, ensure_ascii=False)}\n"
        )

    def _build_summary_prompt(
        self,
        *,
        language: str,
        character: str | None,
        notifications: list[dict[str, Any]],
        render_context: dict[str, Any],
    ) -> str:
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        template_context = {
            **render_context,
            "language": target_language,
            "notifications": notifications,
        }
        system_prompt = self._character_manager.render_prompt(character, "system.jinja", template_context)
        summary_prompt = self._character_manager.render_prompt(character, "short.jinja", template_context)
        if system_prompt and summary_prompt:
            return f"{system_prompt}\n\n{summary_prompt}"

        personality_prompt = self._resolve_personality_prompt(character)
        return (
            "Return valid JSON only with keys title and message. "
            f"Summarize simultaneous smart-home events in {target_language}. "
            "Preserve all critical facts, keep the result short, clear, and useful for TTS.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            f"Events: {json.dumps(notifications, ensure_ascii=False)}\n"
            f"Context: {json.dumps(render_context, ensure_ascii=False)}\n"
        )

    def _resolve_personality_prompt(self, character: str | None) -> str:
        """Resolve the configured personality prompt."""
        key = character or DEFAULT_PERSONALITY
        return self._config.personalities.get(key, self._config.personalities[DEFAULT_PERSONALITY])

    async def _async_generate_json(self, prompt: str) -> dict[str, Any] | None:
        """Call the Ollama generate endpoint and parse a JSON response."""
        url = str(self._config.ollama.get("host", "")).rstrip("/") + "/api/generate"
        payload = {
            "model": self._config.ollama.get("model"),
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.35},
            "prompt": prompt,
        }
        try:
            async with self._session.post(url, json=payload, timeout=20) as response:
                response.raise_for_status()
                data = await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Herald AI call failed: %s", err)
            return None

        raw_response = str(data.get("response", "")).strip()
        if not raw_response:
            return None
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            _LOGGER.debug("Herald AI returned non-JSON payload: %s", raw_response)
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    def _static_summary(self, notifications: list[dict[str, Any]], language: str) -> str:
        """Fallback static summary when AI is unavailable."""
        compact_lines = [item.get("message", "") for item in notifications[:4] if item.get("message")]
        if language == "es":
            return "Mientras estabas fuera ocurrieron varios eventos: " + "; ".join(compact_lines)
        if language == "fr":
            return "Pendant votre absence, plusieurs événements se sont produits: " + "; ".join(compact_lines)
        if language == "en":
            return "While you were away, several events happened: " + "; ".join(compact_lines)
        return "Пока вас не было произошло несколько событий: " + "; ".join(compact_lines)
