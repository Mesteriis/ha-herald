"""Character loading and prompt rendering for Herald AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from homeassistant.core import HomeAssistant
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

DEFAULT_CHARACTER_SCAFFOLDS: dict[str, dict[str, str]] = {
    "hestia": {
        "character.yaml": "name: Hestia\ndescription: Calm, precise smart-home caretaker\ndefault: true\n",
        "system.jinja": (
            "You are Herald AI Notification Center.\n"
            "Character key: {{ character_key }}.\n"
            "Character name: {{ character_name }}.\n"
            "Character description: {{ character_description }}.\n"
            "Write natural spoken {{ language }} for smart-home delivery.\n"
            "Preserve every concrete fact, urgency, and location.\n"
            "Do not invent facts, emotions, honorifics, nicknames, or extra narrative.\n"
            "Do not mix languages. Keep the output in {{ language }} only.\n"
            "Keep titles stable unless the source title is empty or unclear.\n"
            "Prefer human-friendly names over raw entity ids whenever possible.\n"
            "Preferred aliases: {{ character_aliases }}\n"
            "Time: {{ time }}\n"
            "Person: {{ person }}\n"
            "Room: {{ room }}\n"
        ),
        "notification.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Rewrite this smart-home notification for a real person in {{ language }}.\n"
            "Make it sound human, calm, and suitable for TTS.\n"
            "Keep every fact. Do not use markdown.\n"
            "Replace technical wording with natural speech whenever the meaning stays exact.\n"
            "Do not add greetings, roleplay, poetry, mixed languages, or invented details.\n"
            "Do not change names, rooms, counts, times, or urgency.\n"
            "Reuse the source title unless it is missing or unclear.\n"
            "Original title: {{ title }}\n"
            "Event: {{ event }}\n"
            "Level: {{ level }}\n"
            "Original message: {{ message }}\n"
            "Entities: {{ entities }}\n"
            "Context: {{ context }}\n"
            "Additional AI context: {{ ai_context }}\n"
        ),
        "short.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Summarize grouped smart-home notifications in natural spoken {{ language }}.\n"
            "Keep important facts, rooms, and urgency. Avoid robotic phrasing.\n"
            "Do not add greetings, mixed languages, or invented advice.\n"
            "Events: {{ notifications }}\n"
        ),
        "critical.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Rewrite this critical smart-home alert in natural spoken {{ language }}.\n"
            "Preserve urgency, keep it brief, and do not copy the original wording verbatim.\n"
            "Original title: {{ title }}\n"
            "Event: {{ event }}\n"
            "Original message: {{ message }}\n"
            "Context: {{ context }}\n"
        ),
        "vocabulary.yaml": "aliases: {}\n",
    },
    "domovoy": {
        "character.yaml": "name: Domovoy\ndescription: Warm but disciplined house guardian\n",
        "system.jinja": (
            "You are Herald AI Notification Center.\n"
            "Character key: {{ character_key }}.\n"
            "Character name: {{ character_name }}.\n"
            "Character description: {{ character_description }}.\n"
            "Write natural spoken {{ language }} for smart-home delivery.\n"
            "Sound warm and grounded, but never vague.\n"
            "Do not invent facts, honorifics, nicknames, folklore phrases, or extra narrative.\n"
            "Do not mix languages. Keep the output in {{ language }} only.\n"
            "Keep titles stable unless the source title is empty or unclear.\n"
            "Prefer human-friendly names over raw entity ids whenever possible.\n"
            "Preferred aliases: {{ character_aliases }}\n"
            "Time: {{ time }}\n"
            "Person: {{ person }}\n"
            "Room: {{ room }}\n"
        ),
        "notification.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Rewrite this home notification in {{ language }} with quiet confidence.\n"
            "Make it sound human and suitable for TTS. Keep every fact.\n"
            "Do not add greetings, pet names, honorifics, poetry, folklore, or mixed languages.\n"
            "Do not change names, rooms, counts, times, or urgency.\n"
            "Reuse the source title unless it is missing or unclear.\n"
            "Original title: {{ title }}\n"
            "Event: {{ event }}\n"
            "Level: {{ level }}\n"
            "Original message: {{ message }}\n"
            "Entities: {{ entities }}\n"
            "Context: {{ context }}\n"
            "Additional AI context: {{ ai_context }}\n"
        ),
        "short.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Summarize grouped home notifications in natural spoken {{ language }}.\n"
            "Keep important facts and avoid robotic phrasing.\n"
            "Do not add greetings, mixed languages, or invented advice.\n"
            "Events: {{ notifications }}\n"
        ),
        "critical.jinja": (
            "Return valid JSON only with keys title and message.\n"
            "Rewrite this critical alert in {{ language }} with calm urgency.\n"
            "Keep every fact, keep it brief, and do not repeat the original wording verbatim.\n"
            "Original title: {{ title }}\n"
            "Event: {{ event }}\n"
            "Original message: {{ message }}\n"
            "Context: {{ context }}\n"
        ),
        "vocabulary.yaml": "aliases: {}\n",
    },
}


@dataclass(slots=True)
class CharacterProfile:
    """One AI character loaded from /config/herald/<character>."""

    key: str
    path: Path
    config: dict[str, Any] = field(default_factory=dict)
    vocabulary: dict[str, Any] = field(default_factory=dict)

    def render(self, template_name: str, context: dict[str, Any]) -> str | None:
        """Render one template file when it exists."""
        environment = Environment(
            loader=FileSystemLoader(str(self.path)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        try:
            template = environment.get_template(template_name)
        except TemplateNotFound:
            return None
        return template.render(**context).strip()


class CharacterManager:
    """Load and scaffold Herald AI characters."""

    def __init__(self, hass: HomeAssistant, root: Path | None = None) -> None:
        self._hass = hass
        self._root = root or Path(hass.config.path("herald"))
        self._characters: dict[str, CharacterProfile] = {}

    @property
    def root(self) -> Path:
        return self._root

    @property
    def characters(self) -> dict[str, CharacterProfile]:
        return dict(self._characters)

    async def async_initialize(self) -> None:
        """Ensure default scaffolds and refresh in-memory profiles."""
        await self._hass.async_add_executor_job(self._ensure_default_scaffold)
        self._characters = await self._hass.async_add_executor_job(self._load_characters)

    def list_character_keys(self) -> list[str]:
        """Return sorted character ids."""
        return sorted(self._characters)

    def get(self, key: str | None) -> CharacterProfile | None:
        """Get one character profile by key."""
        if key and key in self._characters:
            return self._characters[key]
        for item in self._characters.values():
            if item.config.get("default"):
                return item
        return next(iter(self._characters.values()), None)

    def render_prompt(
        self,
        key: str | None,
        template_name: str,
        context: dict[str, Any],
    ) -> str | None:
        """Render a prompt template for a selected character."""
        profile = self.get(key)
        if profile is None:
            return None
        config = dict(profile.config)
        vocabulary = dict(profile.vocabulary)
        render_context = {
            "title": context.get("title") or context.get("event") or "",
            "event": context.get("event") or context.get("title") or "",
            "message": context.get("message", ""),
            "level": context.get("level", ""),
            "person": context.get("person") or next(iter(context.get("people", []) or []), None),
            "people": list(context.get("people", [])),
            "room": context.get("room"),
            "time": context.get("time", ""),
            "language": context.get("language", ""),
            "entities": list(context.get("entities", [])),
            "context": dict(context.get("context", {})),
            "ai_context": dict(context.get("ai_context", {})),
            "notifications": list(context.get("notifications", [])),
            **context,
            "character_key": profile.key,
            "character_name": str(config.get("name", profile.key)),
            "character_description": str(config.get("description", "")).strip(),
            "character_config": config,
            "character_vocabulary": vocabulary,
            "character_aliases": dict(vocabulary.get("aliases", {})),
        }
        return profile.render(template_name, render_context)

    def _ensure_default_scaffold(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        for character_key, files in DEFAULT_CHARACTER_SCAFFOLDS.items():
            directory = self._root / character_key
            directory.mkdir(parents=True, exist_ok=True)
            for filename, content in files.items():
                path = directory / filename
                if not path.exists():
                    path.write_text(content, encoding="utf-8")

    def _load_characters(self) -> dict[str, CharacterProfile]:
        characters: dict[str, CharacterProfile] = {}
        if not self._root.exists():
            return characters
        for item in sorted(self._root.iterdir()):
            if not item.is_dir():
                continue
            config = _load_yaml(item / "character.yaml")
            vocabulary = _load_yaml(item / "vocabulary.yaml")
            characters[item.name] = CharacterProfile(
                key=item.name,
                path=item,
                config=config,
                vocabulary=vocabulary,
            )
        return characters


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}
