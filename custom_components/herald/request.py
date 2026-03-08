"""Request parsing for the Herald notification pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HeraldAI:
    """AI settings supplied by the automation layer."""

    character: str | None = None
    context: dict[str, Any] | None = None


@dataclass(slots=True)
class HeraldRequest:
    """Thin automation-facing request for the Herald service layer."""

    event: str
    message: str
    level: str = "info"
    ai: HeraldAI | None = None
    context: dict[str, Any] | None = None
    entities: list[str] | None = None
    suppress: int | None = None
    group: str | None = None
    immediately: bool = True
    source: str = "manual"
    notification_id: str | None = None
    include_actions: bool = False
    rewrite: bool = True
    summarize: bool = True
    force: bool = False
    legacy_flow: str | None = None
    legacy_channels: list[str] = field(default_factory=list)
    legacy_user: str | None = None
    legacy_users: list[str] = field(default_factory=list)
    legacy_room: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_service_data(cls, raw: dict[str, Any]) -> "HeraldRequest":
        """Build a request from new-style or legacy service payloads."""
        payload = dict(raw)
        ai_payload = _as_mapping(payload.get("ai"))
        if not ai_payload and payload.get("personality"):
            ai_payload = {"character": payload.get("personality")}

        context = _as_mapping(payload.get("context"))
        metadata = _as_mapping(payload.get("metadata"))
        if metadata:
            context.setdefault("legacy_metadata", metadata)

        entities = _as_list_of_strings(payload.get("entities"))
        if device := payload.get("device"):
            entities.append(str(device))

        if not context:
            context = None
        if not entities:
            entities = None

        event = str(
            payload.get("event")
            or payload.get("title")
            or payload.get("flow")
            or payload.get("source")
            or "Herald"
        )
        group = payload.get("group") or payload.get("flow")
        suppress = payload.get("suppress")
        if suppress is None and payload.get("force"):
            suppress = 0

        return cls(
            event=event,
            message=str(payload["message"]),
            level=str(payload.get("level", "info")),
            ai=HeraldAI(
                character=_as_text(ai_payload.get("character")),
                context=dict(ai_payload.get("context") or {}) or None,
            )
            if ai_payload
            else None,
            context=context,
            entities=entities,
            suppress=int(suppress) if suppress is not None else None,
            group=_as_text(group),
            immediately=bool(payload.get("immediately", True)),
            source=str(payload.get("source", metadata.get("source", "manual"))),
            notification_id=_as_text(payload.get("notification_id")),
            include_actions=bool(payload.get("include_actions", False)),
            rewrite=bool(payload.get("rewrite", True)),
            summarize=bool(payload.get("summarize", True)),
            force=bool(payload.get("force", False)),
            legacy_flow=_as_text(payload.get("flow")),
            legacy_channels=_as_list_of_strings(payload.get("channels")),
            legacy_user=_as_text(payload.get("user")),
            legacy_users=_as_list_of_strings(payload.get("users")),
            legacy_room=_as_text(payload.get("room")),
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request for traces and diagnostics."""
        return {
            "event": self.event,
            "message": self.message,
            "level": self.level,
            "ai": None
            if self.ai is None
            else {
                "character": self.ai.character,
                "context": dict(self.ai.context or {}),
            },
            "context": dict(self.context or {}),
            "entities": list(self.entities or []),
            "suppress": self.suppress,
            "group": self.group,
            "immediately": self.immediately,
            "source": self.source,
            "notification_id": self.notification_id,
            "include_actions": self.include_actions,
            "rewrite": self.rewrite,
            "summarize": self.summarize,
            "force": self.force,
            "legacy_flow": self.legacy_flow,
            "legacy_channels": list(self.legacy_channels),
            "legacy_user": self.legacy_user,
            "legacy_users": list(self.legacy_users),
            "legacy_room": self.legacy_room,
            "metadata": dict(self.metadata),
        }


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _as_list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [text]
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [text]
    return [str(value)]
