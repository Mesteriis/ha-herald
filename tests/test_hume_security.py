"""Isolated Hume transport and audio-cache regression coverage."""

from __future__ import annotations

import asyncio
import os
import re
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.herald import channel_tts_hume as hume_module
from custom_components.herald.channel_tts_hume import HeraldHumeTTSChannel
from custom_components.herald.models import ChannelConfig


def _channel(tmp_path):
    executor_threads = []
    async def execute(func, *args):
        def run():
            executor_threads.append(threading.get_ident())
            return func(*args)
        return await asyncio.get_running_loop().run_in_executor(None, run)
    hass = SimpleNamespace(config=SimpleNamespace(path=lambda path: str(tmp_path / path)), async_add_executor_job=execute)
    return HeraldHumeTTSChannel(hass), executor_threads


@pytest.mark.asyncio
async def test_audio_ids_cannot_escape_cache_and_all_io_uses_executor(tmp_path) -> None:
    channel, threads = _channel(tmp_path)
    urls = [await channel._async_store_audio(value, b"audio") for value in ("../escaped", "/tmp/escaped", "same", "same")]
    assert len(set(urls)) == 4
    assert all(re.fullmatch(r"/local/herald/hume/[a-f0-9]{32}\.mp3", url) for url in urls)
    assert len(list(tmp_path.rglob("*.mp3"))) == 4
    assert all(thread_id != threading.get_ident() for thread_id in threads)
    assert all((channel._cache_root / url.rsplit("/", 1)[1]).read_bytes() == b"audio" for url in urls)


@pytest.mark.asyncio
async def test_cache_expiry_count_and_byte_limits_preserve_external_symlinks(tmp_path, monkeypatch) -> None:
    channel, _ = _channel(tmp_path)
    channel._cache_root.mkdir(parents=True)
    old = channel._cache_root / "old.mp3"
    old.write_bytes(b"old")
    os.utime(old, (time.time() - 100, time.time() - 100))
    outside = tmp_path / "external.mp3"
    outside.write_bytes(b"untouched")
    (channel._cache_root / "link.mp3").symlink_to(outside)
    monkeypatch.setattr(hume_module, "_CACHE_MAX_AGE_SECONDS", 50)
    monkeypatch.setattr(hume_module, "_CACHE_MAX_FILES", 2)
    monkeypatch.setattr(hume_module, "_CACHE_MAX_BYTES", 6)
    for _ in range(4):
        await channel._async_store_audio("id", b"abcd")
    retained = [path for path in channel._cache_root.glob("*.mp3") if not path.is_symlink()]
    assert len(retained) == 1
    assert not old.exists()
    assert outside.read_bytes() == b"untouched"
    assert (channel._cache_root / "link.mp3").is_symlink()
    with pytest.raises(ValueError, match="cache size"):
        await channel._async_store_audio("id", b"1234567")


@pytest.mark.asyncio
async def test_periodic_cache_cleanup_is_cancelled_on_unload(tmp_path, monkeypatch) -> None:
    channel, _ = _channel(tmp_path)
    callbacks = []
    cancel = Mock()
    def schedule(hass, delay, callback):
        callbacks.append(callback)
        return cancel
    monkeypatch.setattr(hume_module, "async_call_later", schedule)
    await channel.async_setup()
    assert len(callbacks) == 1
    await channel.async_shutdown()
    cancel.assert_called_once()
    await callbacks[0](None)
    assert len(callbacks) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [None, RuntimeError("synthesis failed"), asyncio.CancelledError()])
async def test_owned_hume_transport_closes_on_success_failure_and_cancellation(monkeypatch, error) -> None:
    transport = SimpleNamespace(__aenter__=AsyncMock(), __aexit__=AsyncMock())
    class ClientContext:
        async def __aenter__(self):
            return transport
        async def __aexit__(self, *args):
            await transport.__aexit__(*args)
    httpx = ModuleType("httpx")
    httpx.AsyncClient = Mock(return_value=ClientContext())
    sdk = ModuleType("hume")
    sdk.AsyncHumeClient = Mock(return_value=SimpleNamespace(tts=SimpleNamespace(synthesize_json=AsyncMock(side_effect=error, return_value=SimpleNamespace(generations=[SimpleNamespace(audio="YXVkaW8=")])))))
    tts = ModuleType("hume.tts")
    tts.FormatMp3 = lambda: None
    tts.PostedUtterance = lambda **kwargs: kwargs
    tts.PostedUtteranceVoiceWithName = lambda **kwargs: kwargs
    for name, module in (("httpx", httpx), ("hume", sdk), ("hume.tts", tts)):
        monkeypatch.setitem(sys.modules, name, module)
    channel = HeraldHumeTTSChannel(SimpleNamespace())
    config = ChannelConfig(name="voice", channel_type="tts_hume", data={"api_key": "synthetic"})
    if error is None:
        assert await channel._async_synthesize(channel=config, text="text") == b"audio"
    else:
        with pytest.raises(type(error)):
            await channel._async_synthesize(channel=config, text="text")
    sdk.AsyncHumeClient.assert_called_once_with(api_key="synthetic", httpx_client=transport)
    transport.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("redirected", ["www", "www/herald", "www/herald/hume"])
async def test_cache_rejects_symlink_ancestors_for_writes_and_cleanup(tmp_path, redirected) -> None:
    channel, _ = _channel(tmp_path)
    external = tmp_path / "outside"
    external.mkdir()
    preserved = external / "private.mp3"
    preserved.write_bytes(b"private")
    os.utime(preserved, (0, 0))
    link = tmp_path / redirected
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external, target_is_directory=True)
    with pytest.raises(OSError, match="symlink"):
        await channel._async_store_audio("id", b"audio")
    with pytest.raises(OSError, match="symlink"):
        await channel._async_cleanup()
    assert preserved.read_bytes() == b"private"
    assert list(external.iterdir()) == [preserved]
