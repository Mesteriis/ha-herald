Ты AI инженер-архитектор интеграций Home Assistant.

Твоя задача — проанализировать текущую реализацию проекта Herald и привести её к архитектуре AI Notification Center, описанной ниже.

Herald — это слой доставки и обогащения уведомлений, расположенный между автоматизациями Home Assistant и пользователями.

Архитектура системы

Automation / Script
↓
Herald
↓
User / Device / Voice

Automation сообщает событие и смысл, Herald решает:

кому доставить сообщение

когда доставить

какой канал использовать

использовать ли AI

какой персонаж

какой язык

агрегировать ли уведомления

Ограничения Herald

Herald не должен знать:

какие уведомления существуют в системе

бизнес-логику автоматизаций

правила автоматизаций

Automation передает только смысл события.

Структура запроса Herald

Automation вызывает сервис:

herald.notify

Модель запроса должна выглядеть так:

@dataclass
class HeraldAI:

character: str | None
context: dict | None

@dataclass
class HeraldRequest:

event: str
message: str

level: str = "info"

ai: HeraldAI | None = None

context: dict | None = None

entities: list[str] | None = None

suppress: int | None = None

group: str | None = None

immediately: bool = True

Automation не передает:

устройства

пользователей

каналы

комнату

язык

Эти данные Herald получает сам из Home Assistant.

Пользователи и присутствие

Herald должен автоматически использовать сущности:

person.*
device_tracker.*

Herald должен определять:

находится ли пользователь дома

в какой комнате находится пользователь

Датчики присутствия комнат

В каждой комнате должен быть датчик:

binary_sensor.room_<name>_presence

Если датчик отсутствует Herald должен автоматически создать helper:

input_boolean.herald_room_<name>_presence

Helpers которые должен создавать Herald

Если helper отсутствует — Herald должен создать его автоматически.

Каналы

input_boolean.herald_channel_voice
input_boolean.herald_channel_push
input_boolean.herald_channel_tv

AI

input_boolean.herald_ai_enabled

Уровни сообщений

input_boolean.herald_level_info
input_boolean.herald_level_warning
input_boolean.herald_level_critical

AI по уровням

input_boolean.herald_ai_info
input_boolean.herald_ai_warning
input_boolean.herald_ai_critical

Настройки пользователей

input_select.herald_user_<name>language
input_select.herald_user<name>character
input_boolean.herald_user<name>_silent

AI персонажи

Каждый AI персонаж должен храниться в:

/config/herald/

Структура:

/config/herald/<character>/

Пример:

/config/herald/domovoy/

Файлы персонажа:

character.yaml
system.jinja
notification.jinja
short.jinja
critical.jinja
vocabulary.yaml

Herald должен автоматически загружать персонажей.

Контекст Jinja шаблонов

Jinja шаблоны должны получать контекст:

message
event
level
person
room
entities
context
time

AI генерация текста

AI используется для:

переписывания уведомлений

стилизации персонажа

суммаризации

перевода

Поддерживаемый AI провайдер:

Ollama

TTS система

Herald должен поддерживать два типа TTS.

локальный

через media_player Home Assistant

внешний

через HumeAI

https://github.com/HumeAI/hume-python-sdk

Должен существовать модуль:

channel_tts_hume.py

Он должен:

отправлять текст в HumeAI

получать аудио

воспроизводить аудио через media_player

Каналы доставки

Herald должен поддерживать каналы:

voice
push
telegram
dashboard
persistent
tv

Router

Router должен выбирать канал на основе:

присутствия пользователя

комнаты пользователя

уровня сообщения

времени суток

активности пользователя

Router должен поддерживать стратегии:

presence_based
room_based
severity_based
time_based
activity_based

Очередь уведомлений

Herald должен иметь очередь уведомлений.

Функции очереди:

deduplication
aggregation
delay_delivery
summary_generation

Pipeline обработки

Pipeline должен выглядеть так:

event
↓
context builder
↓
flow resolver
↓
ai decision
↓
ai rewrite
↓
router
↓
queue
↓
delivery

Dashboard

Herald должен автоматически создавать dashboard:

Herald Control Center

Карточки dashboard:

notifications
queue
flows
users
channels
ai
diagnostics
analytics

Lovelace Card

Frontend должен поддерживать карточку:

herald-card

Функции карточки:

recent notifications
queue view
flow toggles
language selector
character selector
mute controls

Диагностика

Herald должен поддерживать:

routing logs
flow logs
ai logs
queue state
pipeline trace

Плагины

Herald должен поддерживать плагины:

custom channels
custom flows
custom ai prompts
custom dashboard cards

Задачи AI агента

AI агент должен:

проанализировать текущий код Herald

определить несоответствия архитектуре

рефакторить код

создать недостающие модули

реализовать helper management

реализовать AI characters

реализовать HumeAI TTS

реализовать router

реализовать queue

реализовать auto dashboard

создать документацию

обновить changelog

обновить TODO

создать тесты

Требования к коду

Код должен:

использовать Python 3.11

использовать typing

использовать dataclasses

быть полностью async

соответствовать Home Assistant integration guidelines

быть совместимым с HACS

Документация

AI агент должен поддерживать:

README.md
ARCHITECTURE.md
TODO.md
CHANGELOG.md

Цель

Создать production-ready интеграцию Home Assistant:

Herald AI Notification Center

которая обеспечивает:

интеллектуальные уведомления

AI персонажей

динамическую маршрутизацию

голосовые уведомления

внешние TTS сервисы

UI управления