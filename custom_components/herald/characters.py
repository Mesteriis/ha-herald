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
            "Character: Hestia.\n"
            "Be calm, factual, and concise. Preserve every concrete fact.\n"
            "Time: {{ time }}\n"
            "Person: {{ person }}\n"
            "Room: {{ room }}\n"
        ),
        "notification.jinja": (
            "Rewrite the notification in {{ language }}.\n"
            "Event: {{ event }}\n"
            "Level: {{ level }}\n"
            "Message: {{ message }}\n"
            "Entities: {{ entities }}\n"
            "Context: {{ context }}\n"
            "Return JSON with keys title and message only.\n"
        ),
        "short.jinja": (
            "Summarize grouped notifications in {{ language }}.\n"
            "Events: {{ notifications }}\n"
            "Return JSON with keys title and message only.\n"
        ),
        "critical.jinja": (
            "Rewrite a critical smart-home alert in {{ language }}.\n"
            "Event: {{ event }}\n"
            "Message: {{ message }}\n"
            "Preserve urgency, keep it brief, return JSON with title and message only.\n"
        ),
        "vocabulary.yaml": "aliases: {}\n",
    },
    "domovoy": {
        "character.yaml": "name: Domovoy\ndescription: Warm but disciplined house guardian\n",
        "system.jinja": (
            "You are Herald AI Notification Center.\n"
            "Character: Domovoy.\n"
            "Sound warm and grounded, but never vague.\n"
            "Time: {{ time }}\n"
            "Person: {{ person }}\n"
            "Room: {{ room }}\n"
        ),
        "notification.jinja": (
            "Rewrite the home notification in {{ language }} with quiet confidence.\n"
            "Event: {{ event }}\n"
            "Level: {{ level }}\n"
            "Message: {{ message }}\n"
            "Entities: {{ entities }}\n"
            "Context: {{ context }}\n"
            "Return JSON with keys title and message only.\n"
        ),
        "short.jinja": (
            "Summarize grouped home notifications in {{ language }}.\n"
            "Events: {{ notifications }}\n"
            "Return JSON with keys title and message only.\n"
        ),
        "critical.jinja": (
            "Rewrite a critical alert in {{ language }} with calm urgency.\n"
            "Event: {{ event }}\n"
            "Message: {{ message }}\n"
            "Return JSON with keys title and message only.\n"
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
        return profile.render(template_name, context)

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
