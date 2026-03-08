"""Async AI helpers for Herald notification rewriting and summarization."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import DEFAULT_PERSONALITY
from .models import HeraldConfig, NotificationContext
from .translations import LANGUAGE_LABELS, default_summary_title

_LOGGER = logging.getLogger(__name__)

class HeraldAIClient:
    """Ollama-backed rewrite and summary client."""

    def __init__(self, session: ClientSession, config: HeraldConfig) -> None:
        self._session = session
        self._config = config

    @property
    def enabled(self) -> bool:
        """Return whether AI rewriting is enabled."""
        return bool(self._config.ollama.get("enabled", True))

    async def async_rewrite_payload(
        self,
        *,
        title: str,
        message: str,
        level: str,
        language: str,
        personality: str | None,
        rewrite: bool,
    ) -> dict[str, str]:
        """Rewrite and optionally translate a single notification payload."""
        if not self.enabled or (not rewrite and language == "ru"):
            return {"title": title, "message": message}

        personality_prompt = self._resolve_personality_prompt(personality)
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        prompt = (
            "Return valid JSON only with keys title and message. "
            f"Rewrite this smart-home notification for {target_language}. "
            "Keep every factual detail, stay concise, and avoid markdown.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            f"Severity: {level}\n"
            f"Original title: {title}\n"
            f"Original message: {message}\n"
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
        personality: str | None,
    ) -> dict[str, str]:
        """Summarize a group of notifications into one payload."""
        title = default_summary_title(language)
        lines = [
            f"- [{item.level}] {item.title}: {item.message}"
            for item in notifications
        ]
        if not self.enabled:
            return {"title": title, "message": self._static_summary(lines, language)}

        personality_prompt = self._resolve_personality_prompt(personality)
        target_language = LANGUAGE_LABELS.get(language, "Russian")
        prompt = (
            "Return valid JSON only with keys title and message. "
            f"Summarize simultaneous smart-home events in {target_language}. "
            "Preserve all critical facts, keep the result short, clear, and useful for TTS.\n\n"
            f"Persona instructions: {personality_prompt}\n"
            "Events:\n"
            + "\n".join(lines)
        )
        response = await self._async_generate_json(prompt)
        if not response:
            return {"title": title, "message": self._static_summary(lines, language)}
        return {
            "title": str(response.get("title", title)).strip() or title,
            "message": str(response.get("message", self._static_summary(lines, language))).strip()
            or self._static_summary(lines, language),
        }

    def _resolve_personality_prompt(self, personality: str | None) -> str:
        """Resolve the configured personality prompt."""
        key = personality or DEFAULT_PERSONALITY
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

    def _static_summary(self, lines: list[str], language: str) -> str:
        """Fallback static summary when AI is unavailable."""
        compact_lines = [line.split(": ", maxsplit=1)[1] for line in lines[:4]]
        if language == "es":
            return "Mientras estabas fuera ocurrieron varios eventos: " + "; ".join(compact_lines)
        if language == "fr":
            return "Pendant votre absence, plusieurs événements se sont produits: " + "; ".join(compact_lines)
        if language == "en":
            return "While you were away, several events happened: " + "; ".join(compact_lines)
        return "Пока вас не было произошло несколько событий: " + "; ".join(compact_lines)
