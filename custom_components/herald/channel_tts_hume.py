"""HumeAI-backed TTS delivery for Herald."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .models import ChannelConfig, NotificationContext


class HeraldHumeTTSChannel:
    """Render speech through HumeAI and play it on a Home Assistant media player."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        config = getattr(hass, "config", None)
        if config is not None and hasattr(config, "path"):
            self._cache_root = Path(config.path("www/herald/hume"))
        else:
            self._cache_root = Path("/tmp/herald/hume")

    async def async_deliver(
        self,
        *,
        channel: ChannelConfig,
        text: str,
        context: NotificationContext,
    ) -> dict[str, Any]:
        """Synthesize one audio payload and play it on the target media player."""
        api_key = str(channel.data.get("api_key", "")).strip()
        target_entity_id = channel.entity_id or channel.data.get("media_player")
        if not api_key:
            raise ValueError("HumeAI API key is required for tts_hume channels")
        if not target_entity_id:
            raise ValueError("media_player entity_id is required for tts_hume channels")

        audio_bytes = await self._async_synthesize(channel=channel, text=text)
        media_url = await self._async_store_audio(context.notification_id, audio_bytes)
        service_data = {
            "entity_id": target_entity_id,
            "media_content_id": media_url,
            "media_content_type": channel.data.get("media_content_type", "music"),
            "announce": bool(channel.data.get("announce", True)),
        }
        await self._hass.services.async_call(
            "media_player",
            "play_media",
            service_data,
            blocking=True,
        )
        return {
            "service": "media_player.play_media",
            "provider": "hume",
            "target_entity_id": target_entity_id,
            "media_url": media_url,
        }

    async def _async_synthesize(self, *, channel: ChannelConfig, text: str) -> bytes:
        from hume import AsyncHumeClient
        from hume.tts import (
            FormatMp3,
            PostedUtterance,
            PostedUtteranceVoiceWithName,  # type: ignore
        )

        client = AsyncHumeClient(api_key=str(channel.data["api_key"]).strip())
        utterance_kwargs: dict[str, Any] = {"text": text}
        if description := str(channel.data.get("description", "")).strip():
            utterance_kwargs["description"] = description
        if voice_name := str(channel.data.get("voice_name", "")).strip():
            utterance_kwargs["voice"] = PostedUtteranceVoiceWithName(name=voice_name)
        response = await client.tts.synthesize_json(
            utterances=[PostedUtterance(**utterance_kwargs)],
            format=FormatMp3(),
            num_generations=1,
        )
        if not response.generations:
            raise ValueError("HumeAI returned no audio generations")
        return base64.b64decode(response.generations[0].audio)

    async def _async_store_audio(self, notification_id: str, audio_bytes: bytes) -> str:
        self._cache_root.mkdir(parents=True, exist_ok=True)
        destination = self._cache_root / f"{notification_id}.mp3"
        await self._hass.async_add_executor_job(destination.write_bytes, audio_bytes)
        return f"/local/herald/hume/{destination.name}"
