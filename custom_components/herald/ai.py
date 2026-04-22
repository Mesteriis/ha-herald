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
from .translations import LANGUAGE_LABELS, default_summary_title, normalize_notification_text

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
            return self._passthrough_payload(
                title=title,
                message=message,
                language=language,
                reason="rewrite_disabled",
                character=character,
            )
        if not self.should_use_ai(level):
            return self._passthrough_payload(
                title=title,
                message=message,
                language=language,
                reason="ai_disabled_for_level",
                character=character,
            )

        prompt, prompt_source = self._build_notification_prompt(
            title=title,
            message=message,
            level=level,
            language=language,
            character=character,
            render_context=render_context,
        )
        response, failure_reason = await self._async_generate_json(prompt)
        if not response:
            return self._passthrough_payload(
                title=title,
                message=message,
                language=language,
                reason=failure_reason or "ai_empty_response",
                character=character,
                prompt_source=prompt_source,
            )
        new_title = self._normalize_for_language(str(response.get("title", title)).strip() or title, language)
        new_message = self._normalize_for_language(
            str(response.get("message", message)).strip() or message,
            language,
        )
        return {
            "title": new_title,
            "message": new_message,
            "_herald_ai_status": "rewritten" if (new_title != title or new_message != message) else "unchanged",
            "_herald_ai_reason": "ai_rewrite",
            "_herald_ai_character": character or "",
            "_herald_ai_prompt_source": prompt_source,
        }

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
        static_summary = self._static_summary(lines := [
            {
                "event": item.event or item.title,
                "level": item.level,
                "message": item.message,
                "entities": list(item.entities),
                "context": dict(item.context_data),
            }
            for item in notifications
        ], language)
        if not self.should_use_ai(notifications[0].level if notifications else "info"):
            return self._passthrough_payload(
                title=title,
                message=static_summary,
                language=language,
                reason="ai_disabled_for_summary",
                character=character,
            )

        prompt, prompt_source = self._build_summary_prompt(
            language=language,
            character=character,
            notifications=lines,
            render_context=render_context,
        )
        response, failure_reason = await self._async_generate_json(prompt)
        if not response:
            return self._passthrough_payload(
                title=title,
                message=static_summary,
                language=language,
                reason=failure_reason or "ai_summary_empty_response",
                character=character,
                prompt_source=prompt_source,
            )
        return {
            "title": self._normalize_for_language(
                str(response.get("title", title)).strip() or title,
                language,
            ),
            "message": self._normalize_for_language(
                str(response.get("message", static_summary)).strip() or static_summary,
                language,
            ),
            "_herald_ai_status": "rewritten",
            "_herald_ai_reason": "ai_summary",
            "_herald_ai_character": character or "",
            "_herald_ai_prompt_source": prompt_source,
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
    ) -> tuple[str, str]:
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        template_context = {
            **render_context,
            "title": title,
            "event": render_context.get("event") or title,
            "message": message,
            "level": level,
            "language": target_language,
        }
        system_prompt = self._character_manager.render_prompt(character, "system.jinja", template_context)
        template_name = "critical.jinja" if level in {"critical", "security"} else "notification.jinja"
        notification_prompt = self._character_manager.render_prompt(character, template_name, template_context)
        if system_prompt and notification_prompt:
            return f"{system_prompt}\n\n{notification_prompt}", "character_template"

        personality_prompt = self._resolve_personality_prompt(character)
        return (
            "Return valid JSON only with keys title and message. "
            f"Rewrite this smart-home notification into natural spoken {target_language}. "
            "Always paraphrase the wording, keep every factual detail, avoid markdown, "
            "and prefer human-friendly names over raw entity ids whenever possible.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            f"Severity: {level}\n"
            f"Original title: {title}\n"
            f"Original message: {message}\n"
            f"Context: {json.dumps(render_context, ensure_ascii=False)}\n"
        ), "personality_fallback"

    def _build_summary_prompt(
        self,
        *,
        language: str,
        character: str | None,
        notifications: list[dict[str, Any]],
        render_context: dict[str, Any],
    ) -> tuple[str, str]:
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        template_context = {
            **render_context,
            "time": render_context.get("time", ""),
            "person": render_context.get("person")
            or next(iter(render_context.get("people", []) or []), None),
            "language": target_language,
            "notifications": notifications,
        }
        system_prompt = self._character_manager.render_prompt(character, "system.jinja", template_context)
        summary_prompt = self._character_manager.render_prompt(character, "short.jinja", template_context)
        if system_prompt and summary_prompt:
            return f"{system_prompt}\n\n{summary_prompt}", "character_template"

        personality_prompt = self._resolve_personality_prompt(character)
        return (
            "Return valid JSON only with keys title and message. "
            f"Summarize simultaneous smart-home events in natural spoken {target_language}. "
            "Preserve all critical facts, keep the result short, clear, and useful for TTS.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            f"Events: {json.dumps(notifications, ensure_ascii=False)}\n"
            f"Context: {json.dumps(render_context, ensure_ascii=False)}\n"
        ), "personality_fallback"

    def _resolve_personality_prompt(self, character: str | None) -> str:
        """Resolve the configured personality prompt."""
        key = character or DEFAULT_PERSONALITY
        return self._config.personalities.get(key, self._config.personalities[DEFAULT_PERSONALITY])

    async def _async_generate_json(self, prompt: str) -> tuple[dict[str, Any] | None, str | None]:
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
            return None, "ai_request_failed"

        raw_response = str(data.get("response", "")).strip()
        if not raw_response:
            return None, "ai_empty_response"
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            _LOGGER.debug("Herald AI returned non-JSON payload: %s", raw_response)
            return None, "ai_invalid_json"
        if not isinstance(parsed, dict):
            return None, "ai_invalid_payload"
        return parsed, None

    def _passthrough_payload(
        self,
        *,
        title: str,
        message: str,
        language: str,
        reason: str,
        character: str | None,
        prompt_source: str = "",
    ) -> dict[str, str]:
        """Build a passthrough payload that still exposes AI diagnostics."""
        return {
            "title": self._normalize_for_language(title, language),
            "message": self._normalize_for_language(message, language),
            "_herald_ai_status": "passthrough" if reason.startswith("ai_disabled") or reason == "rewrite_disabled" else "fallback",
            "_herald_ai_reason": reason,
            "_herald_ai_character": character or "",
            "_herald_ai_prompt_source": prompt_source,
        }

    def _normalize_for_language(self, text: str, language: str) -> str:
        """Apply small language-specific fixes to spoken AI output."""
        return normalize_notification_text(text, language)

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
