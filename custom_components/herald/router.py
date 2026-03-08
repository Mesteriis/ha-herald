"""Channel routing for Herald notifications."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from homeassistant.core import HomeAssistant

from .actions import build_ack_action, build_snooze_action
from .ai import HeraldAIClient
from .const import (
    DEFAULT_PERSONALITY,
    DEFAULT_SNOOZE_MINUTES,
    QUIET_HOURS_POLICY_ALLOW,
    QUIET_HOURS_POLICY_BLOCK,
    QUIET_HOURS_POLICY_DEFAULT,
    SEVERITY_RANK,
)
from .flows import severity_allowed
from .models import ChannelConfig, FlowConfig, HeraldConfig, NotificationContext, PresenceSnapshot, UserConfig
from .presence import PresenceResolver
from .translations import normalize_language

_LOGGER = logging.getLogger(__name__)

ACTION_LABELS: dict[str, dict[str, str]] = {
    "ru": {"ack": "Принято", "snooze": "Отложить на 30 минут"},
    "en": {"ack": "Acknowledge", "snooze": "Snooze 30 min"},
    "es": {"ack": "Confirmado", "snooze": "Posponer 30 min"},
    "fr": {"ack": "Pris en compte", "snooze": "Reporter 30 min"},
}


class HeraldRouter:
    """Route notifications to channels based on flow, presence, and language."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: HeraldConfig,
        ai_client: HeraldAIClient,
        presence: PresenceResolver,
    ) -> None:
        self._hass = hass
        self._config = config
        self._ai_client = ai_client
        self._presence = presence

    async def async_route(
        self,
        context: NotificationContext,
        flow: FlowConfig,
    ) -> list[dict[str, Any]]:
        """Route a notification to one or more output channels."""
        presence = await self._presence.async_resolve(context)
        channel_names = self._resolve_channel_names(context, flow, presence)
        channels = [
            self._config.channels[name]
            for name in channel_names
            if name in self._config.channels and self._config.channels[name].enabled
        ]

        rendered_cache: dict[tuple[str, str], dict[str, str]] = {}
        results: list[dict[str, Any]] = []
        channels_by_user: dict[str | None, list[ChannelConfig]] = defaultdict(list)
        for channel in channels:
            channels_by_user[channel.user].append(channel)

        for user_key, bucket in channels_by_user.items():
            language = self._resolve_language(user_key)
            personality = context.personality or flow.personality or DEFAULT_PERSONALITY
            cache_key = (language, personality)
            if cache_key not in rendered_cache:
                rendered_cache[cache_key] = await self._ai_client.async_rewrite_payload(
                    title=context.title,
                    message=context.message,
                    level=context.level,
                    language=language,
                    personality=personality,
                    rewrite=context.rewrite,
                )
            payload = rendered_cache[cache_key]
            for channel in bucket:
                result = await self._async_send_channel(
                    channel=channel,
                    title=payload["title"],
                    message=payload["message"],
                    language=language,
                    context=context,
                    flow=flow,
                    presence=presence,
                )
                results.append(result)
        return results

    def _resolve_channel_names(
        self,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
    ) -> list[str]:
        explicit = list(context.channels)
        candidate_names = explicit or list(flow.channels)
        if not candidate_names:
            candidate_names = list(self._config.channels)

        if presence.nobody_home:
            away_channels = self._presence.away_channels()
            if away_channels:
                candidate_names = away_channels
            else:
                candidate_names = [
                    name
                    for name in candidate_names
                    if self._config.channels.get(name)
                    and self._config.channels[name].channel_type != "tts"
                ]

        bypass_quiet_hours = severity_allowed(context.level, "critical")
        filtered: list[str] = []
        for name in candidate_names:
            channel = self._config.channels.get(name)
            if channel is None:
                continue
            if channel.user and context.users and channel.user not in context.users:
                continue
            if (
                presence.quiet_hours
                and not bypass_quiet_hours
                and not self._channel_allowed_in_quiet_hours(channel)
            ):
                continue
            filtered.append(name)

        room_filtered = self._prefer_room_channels(filtered, presence)
        return room_filtered or filtered

    def _prefer_room_channels(self, channel_names: list[str], presence: PresenceSnapshot) -> list[str]:
        room = presence.primary_room
        if room is None:
            return channel_names

        tts_channels = [
            name
            for name in channel_names
            if self._config.channels.get(name)
            and self._config.channels[name].channel_type == "tts"
        ]
        room_tts = [
            name
            for name in tts_channels
            if self._config.channels[name].room == room
        ]
        if not room_tts:
            return channel_names

        non_tts = [
            name
            for name in channel_names
            if self._config.channels.get(name)
            and self._config.channels[name].channel_type != "tts"
        ]
        return room_tts + non_tts

    def _resolve_language(self, user_key: str | None) -> str:
        if user_key is None:
            return "ru"

        user_config: UserConfig | None = self._config.users.get(user_key)
        if user_config is None or not user_config.language_helper:
            return "ru"

        state = self._hass.states.get(user_config.language_helper)
        if state is None:
            return "ru"
        return normalize_language(state.state)

    def _channel_allowed_in_quiet_hours(self, channel: ChannelConfig) -> bool:
        """Evaluate the effective quiet-hours behavior for a channel."""
        if channel.quiet_hours_policy == QUIET_HOURS_POLICY_ALLOW:
            return True
        if channel.quiet_hours_policy == QUIET_HOURS_POLICY_BLOCK:
            return False
        if channel.quiet_hours_policy != QUIET_HOURS_POLICY_DEFAULT:
            return channel.channel_type != "tts"
        return channel.channel_type != "tts"

    async def _async_send_channel(
        self,
        *,
        channel: ChannelConfig,
        title: str,
        message: str,
        language: str,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
    ) -> dict[str, Any]:
        """Send one notification to a concrete channel."""
        title_to_send = f"{channel.title_prefix} {title}".strip() if channel.title_prefix else title
        try:
            if channel.channel_type == "tts":
                await self._async_send_tts(channel, title_to_send, message)
            elif channel.channel_type == "mobile_app":
                await self._async_send_notify_service(channel, title_to_send, message, context, language)
            elif channel.channel_type == "telegram":
                await self._async_send_telegram(channel, title_to_send, message, context, presence, language)
            elif channel.channel_type == "persistent_notification":
                await self._hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": title_to_send,
                        "message": message,
                        "notification_id": context.notification_id,
                    },
                    blocking=True,
                )
            elif channel.channel_type == "logbook":
                await self._hass.services.async_call(
                    "logbook",
                    "log",
                    {
                        "name": title_to_send,
                        "message": message,
                        "domain": "herald",
                    },
                    blocking=True,
                )
            else:
                await self._hass.services.async_call(
                    "system_log",
                    "write",
                    {
                        "level": "warning" if SEVERITY_RANK.get(context.level, 0) >= 20 else "info",
                        "message": f"[{context.flow}] {title_to_send}: {message}",
                    },
                    blocking=True,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Herald channel %s failed: %s", channel.name, err)
            return {
                "channel": channel.name,
                "status": "error",
                "error": str(err),
                "flow": flow.name,
            }

        return {
            "channel": channel.name,
            "status": "sent",
            "flow": flow.name,
            "room": presence.primary_room,
            "user": channel.user,
            "type": channel.channel_type,
            "language": language,
        }

    async def _async_send_tts(self, channel: ChannelConfig, title: str, message: str) -> None:
        service = channel.service or "tts.yandex_station_say"
        data = {**channel.data, "message": message}
        if channel.entity_id is not None:
            data["entity_id"] = channel.entity_id
        if title:
            data.setdefault("cache", False)
        await self._async_call_service(service, data)

    async def _async_send_notify_service(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        language: str,
    ) -> None:
        if not channel.service:
            raise ValueError(f"Channel {channel.name} requires a notify service")
        data = {**channel.data, "title": title, "message": message}
        payload_data = dict(data.get("data", {}))
        payload_data.setdefault("tag", context.notification_id)
        payload_data.setdefault("group", f"herald_{context.flow}")
        if context.include_actions:
            payload_data["actions"] = self._build_mobile_actions(context, language)
            payload_data["herald_notification_id"] = context.notification_id
            payload_data["herald_flow"] = context.flow
        data["data"] = payload_data
        await self._async_call_service(channel.service, data)

    async def _async_send_telegram(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        presence: PresenceSnapshot,
        language: str,
    ) -> None:
        service = channel.service or "telegram_bot.send_message"
        payload = {
            **channel.data,
            "title": title,
            "message": message,
            "disable_notification": not presence.nobody_home,
        }
        if context.include_actions:
            payload["inline_keyboard"] = self._build_telegram_inline_keyboard(context, language)
        if channel.chat_id is not None:
            payload["chat_id"] = [channel.chat_id] if not isinstance(channel.chat_id, list) else channel.chat_id
        if channel.thread_id is not None:
            payload["message_thread_id"] = channel.thread_id
        await self._async_call_service(service, payload)

    def _build_mobile_actions(self, context: NotificationContext, language: str) -> list[dict[str, str]]:
        labels = ACTION_LABELS.get(language, ACTION_LABELS["en"])
        return [
            {
                "action": build_ack_action(context.notification_id),
                "title": labels["ack"],
            },
            {
                "action": build_snooze_action(
                    context.flow,
                    minutes=DEFAULT_SNOOZE_MINUTES,
                    notification_id=context.notification_id,
                ),
                "title": labels["snooze"],
            },
        ]

    def _build_telegram_inline_keyboard(
        self,
        context: NotificationContext,
        language: str,
    ) -> list[str]:
        labels = ACTION_LABELS.get(language, ACTION_LABELS["en"])
        ack = build_ack_action(context.notification_id)
        snooze = build_snooze_action(
            context.flow,
            minutes=DEFAULT_SNOOZE_MINUTES,
            notification_id=context.notification_id,
        )
        return [f"{labels['ack']}:/{ack}, {labels['snooze']}:/{snooze}"]

    async def _async_call_service(self, service_name: str, data: dict[str, Any]) -> None:
        if "." not in service_name:
            raise ValueError(f"Invalid service name: {service_name}")
        domain, service = service_name.split(".", maxsplit=1)
        await self._hass.services.async_call(domain, service, data, blocking=True)
