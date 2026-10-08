"""HumeAI-backed TTS delivery for Herald."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .models import ChannelConfig, NotificationContext

_LOGGER = logging.getLogger(__name__)
_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60
_CACHE_CLEANUP_INTERVAL = 60 * 60
_CACHE_MAX_FILES = 100
_CACHE_MAX_BYTES = 100 * 1024 * 1024


class HeraldHumeTTSChannel:
    """Render speech through HumeAI and play it on a Home Assistant media player."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._cache_lock = asyncio.Lock()
        self._cleanup_unsub: Callable[[], None] | None = None
        self._closed = False
        config = getattr(hass, "config", None)
        if config is not None and hasattr(config, "path"):
            self._config_root = Path(config.path(""))
            self._cache_root = Path(config.path("www/herald/hume"))
        else:
            self._config_root = Path("/tmp")
            self._cache_root = self._config_root / "herald/hume"

    async def async_setup(self) -> None:
        """Prune audio from earlier runs and maintain retention while idle."""
        await self._async_cleanup()
        self._schedule_cleanup()

    async def async_shutdown(self) -> None:
        """Stop cache maintenance before the config entry is unloaded."""
        self._closed = True
        if self._cleanup_unsub is not None:
            self._cleanup_unsub()
            self._cleanup_unsub = None

    def _schedule_cleanup(self) -> None:
        if self._closed or self._cleanup_unsub is not None:
            return

        async def _cleanup(_: Any) -> None:
            self._cleanup_unsub = None
            if self._closed:
                return
            try:
                await self._async_cleanup()
            except OSError:
                _LOGGER.warning("Unable to prune the Herald audio cache")
            finally:
                self._schedule_cleanup()

        self._cleanup_unsub = async_call_later(self._hass, _CACHE_CLEANUP_INTERVAL, _cleanup)

    async def _async_cleanup(self) -> None:
        async with self._cache_lock:
            await self._hass.async_add_executor_job(self._prune_cache)

    def _validate_cache_root(self) -> None:
        """Reject redirected cache ancestors before any read, write or deletion."""
        try:
            relative = self._cache_root.relative_to(self._config_root)
        except ValueError as err:
            raise OSError("Herald audio cache must be inside the config directory") from err
        current = self._config_root
        for part in relative.parts:
            current /= part
            if part == ".." or current.is_symlink():
                raise OSError("Herald audio cache cannot use symlink directories")
        if not self._cache_root.resolve().is_relative_to(self._config_root.resolve()):
            raise OSError("Herald audio cache must be inside the config directory")

    def _prune_cache(self) -> None:
        """Bound regular audio files only; never traverse cache symlinks."""
        self._validate_cache_root()
        if not self._cache_root.exists():
            return
        cutoff = time.time() - _CACHE_MAX_AGE_SECONDS
        retained: list[tuple[float, Path, int]] = []
        for path in self._cache_root.glob("*.mp3"):
            if path.is_symlink() or not path.is_file():
                continue
            stat = path.stat()
            if stat.st_mtime <= cutoff:
                path.unlink(missing_ok=True)
            else:
                retained.append((stat.st_mtime, path, stat.st_size))
        retained.sort(key=lambda item: item[0], reverse=True)
        total_bytes = 0
        for index, (_, path, size) in enumerate(retained):
            total_bytes += size
            if index >= _CACHE_MAX_FILES or total_bytes > _CACHE_MAX_BYTES:
                path.unlink(missing_ok=True)

    async def async_deliver(
        self,
        *,
        channel: ChannelConfig,
        text: str,
        context: NotificationContext,
        before_play: Callable[[], Awaitable[str | None]] | None = None,
    ) -> dict[str, Any]:
        """Synthesize audio, then recheck an optional routing guard before playback."""
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
        if before_play is not None and (reason := await before_play()):
            return {"channel": channel.name, "status": "dropped", "reason": reason, "flow": context.flow}
        await self._hass.services.async_call(
            "media_player", "play_media", service_data, blocking=True
        )
        return {
            "service": "media_player.play_media",
            "provider": "hume",
            "target_entity_id": target_entity_id,
            "media_url": media_url,
        }

    async def _async_synthesize(self, *, channel: ChannelConfig, text: str) -> bytes:
        import httpx
        from hume import AsyncHumeClient
        from hume.tts import FormatMp3, PostedUtterance, PostedUtteranceVoiceWithName

        utterance_kwargs: dict[str, Any] = {"text": text}
        if description := str(channel.data.get("description", "")).strip():
            utterance_kwargs["description"] = description
        if voice_name := str(channel.data.get("voice_name", "")).strip():
            utterance_kwargs["voice"] = PostedUtteranceVoiceWithName(name=voice_name)
        # hume 0.13.10 accepts an injected httpx client but exposes no close method.
        # Owning that transport ensures closure on success, failure and cancellation.
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as transport:
            client = AsyncHumeClient(
                api_key=str(channel.data["api_key"]).strip(), httpx_client=transport
            )
            response = await client.tts.synthesize_json(
                utterances=[PostedUtterance(**utterance_kwargs)],
                format=FormatMp3(),
                num_generations=1,
            )
        if not response.generations:
            raise ValueError("HumeAI returned no audio generations")
        return base64.b64decode(response.generations[0].audio, validate=True)

    async def _async_store_audio(self, notification_id: str, audio_bytes: bytes) -> str:
        """Store an opaque cache name unrelated to caller-controlled notification IDs."""
        if len(audio_bytes) > _CACHE_MAX_BYTES:
            raise ValueError("HumeAI audio exceeds the cache size limit")
        filename = f"{uuid4().hex}.mp3"
        async with self._cache_lock:
            await self._hass.async_add_executor_job(self._store_audio, filename, audio_bytes)
        self._schedule_cleanup()
        return f"/local/herald/hume/{filename}"

    def _store_audio(self, filename: str, audio_bytes: bytes) -> None:
        """Run every filesystem operation in the executor."""
        self._validate_cache_root()
        self._cache_root.mkdir(parents=True, exist_ok=True)
        self._validate_cache_root()
        destination = self._cache_root / filename
        with destination.open("xb") as stream:
            stream.write(audio_bytes)
        self._prune_cache()
