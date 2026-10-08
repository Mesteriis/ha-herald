import { css, html, nothing } from "lit";
import { HeraldCard } from "./herald-card.js";
import { DASHBOARD_TABS, eventIcon, eventIdentity, eventOutcome, knownCounter, ruleForEvent } from "./dashboard-model.js";

// Existing editors retain their own drafts and pending HA acknowledgements.
// A state update must not run setConfig again and discard those interactions.
class HeraldDashboardSection extends HeraldCard {
  set settings(value) {
    const signature = JSON.stringify(value);
    if (signature === this._settingsSignature) return;
    this._settingsSignature = signature;
    this.setConfig(value);
  }
  static styles = [HeraldCard.styles, css`
    :host { --ha-card-background: #092a36; --primary-text-color: #d9edf4; --secondary-text-color: #93b7c6; --primary-color: #43c4e9; }
    ha-card.panel, ha-card { background: transparent; border: 0; box-shadow: none; }
    .panel-shell { padding: 0; }
    .panel-header h3 { font-size: 22px; }
    input, select { color-scheme: dark; }
  `];
}

export class HeraldDashboard extends HeraldCard {
  static properties = {
    _tab: { state: true }, _selectedEvent: { state: true }, _detailOpen: { state: true },
    _subview: { state: true }, _ruleKey: { state: true }, _now: { state: true },
    _numberErrors: { state: true }, _eventFeedback: { state: true }, _eventBusy: { state: true },
  };
  constructor() {
    super();
    this._tab = "overview";
    this._subview = "channels";
    this._selectedEvent = "";
    this._detailOpen = false;
    this._ruleKey = "";
    this._now = new Date();
    this._numberErrors = {};
    this._eventFeedback = "";
    this._eventBusy = false;
  }
  connectedCallback() {
    super.connectedCallback();
    this._clockTimer = setInterval(() => { this._now = new Date(); }, 60000);
  }
  disconnectedCallback() {
    clearInterval(this._clockTimer);
    super.disconnectedCallback();
  }
  getCardSize() { return 12; }
  _data() { return this._statusEntity()?.attributes ?? {}; }
  _events() {
    const items = this.hass?.states[this._config?.today_entity]?.attributes?.recent_notifications;
    return Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
  }
  _selected() {
    const items = this._events();
    return items.find((item, index) => eventIdentity(item, index) === this._selectedEvent) ?? items[0] ?? null;
  }
  _switchTab(tab) {
    if (!DASHBOARD_TABS.some(([key]) => key === tab)) return;
    this._tab = tab;
    this._detailOpen = false;
    this._subview = tab === "delivery" ? "channels" : "general";
  }
  async _tabKey(event, index) {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % DASHBOARD_TABS.length;
    if (event.key === "ArrowLeft") next = (index + DASHBOARD_TABS.length - 1) % DASHBOARD_TABS.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = DASHBOARD_TABS.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    this._switchTab(DASHBOARD_TABS[next][0]);
    await this.updateComplete;
    this.shadowRoot.querySelectorAll('.dashboard-tabs [role="tab"]')[next]?.focus();
  }
  _icon(icon, tone = "") { return html`<ha-icon class=${tone} .icon=${icon}></ha-icon>`; }
  _section(mode, extra = {}) {
    return html`<herald-dashboard-section .hass=${this.hass} .settings=${{
      ...this._config, type: "custom:herald-card", view_mode: mode, compact: true, ...extra,
    }}></herald-dashboard-section>`;
  }
  _controlId(key) { return this._entityUsable(this._statusEntity()) ? this._data().control_entity_ids?.[key] ?? null : null; }
  _quickControl(key, label, icon, tone, description = "") {
    const id = this._controlId(key);
    const entity = this.hass?.states[id];
    const known = this._binaryEntityKnown(entity);
    return html`<div class="quick-control">
      ${this._icon(icon, tone)}<div><span>${label}</span>${description ? html`<small>${description}</small>` : nothing}
      ${!known ? html`<small>Управление недоступно</small>` : nothing}${this._renderControlFeedback(id)}</div>
      <ha-switch aria-label=${label} .checked=${known && entity.state === "on"}
        .disabled=${!known || this._controlPending(id)} @change=${() => this._toggleSwitch(id, entity?.state === "on")}></ha-switch>
    </div>`;
  }
  render() {
    if (!this.hass || !this._config) return html`<div class="loading" role="status">Загружаем Herald…</div>`;
    const status = this._statusEntity();
    const ready = this._entityUsable(status);
    const data = this._data();
    const date = this._now.toLocaleDateString("ru", { weekday: "short", day: "numeric", month: "long" });
    const clock = this._now.toLocaleTimeString("ru", { hour: "2-digit", minute: "2-digit" });
    const homePath = /^\/(?!\/)[^\s]*$/.test(this._config.home_path ?? "") ? this._config.home_path : "/";
    return html`<main class="dashboard" style=${this._config.fullscreen === true ? "--header-height: 0px" : ""}>
      <header class="dashboard-header"><div class="brand">${this._icon("mdi:bell-badge-outline")}<strong>Herald</strong></div>
        <a class="home-link" href=${homePath}>Главная дома</a><div class="date">${this._icon("mdi:calendar-blank-outline")}<span>${date}</span>${this._icon("mdi:clock-outline")}<time>${clock}</time></div>
      </header>
      ${this._metrics(status, data)}
      <nav class="dashboard-tabs" role="tablist" aria-label="Разделы Herald">${DASHBOARD_TABS.map(([tab, label, icon], index) => html`
        <button id=${`tab-${tab}`} role="tab" aria-selected=${this._tab === tab} aria-controls="dashboard-content"
          tabindex=${this._tab === tab ? 0 : -1} @click=${() => this._switchTab(tab)} @keydown=${(event) => this._tabKey(event, index)}>
          ${this._icon(icon)}${label}</button>`)}</nav>
      ${!ready ? html`<p class="availability" role="status">Herald недоступен. Показаны последние данные; управление появится после подключения.</p>` : nothing}
      <section id="dashboard-content" class=${`workspace ${this._tab === "overview" ? "overview-workspace" : ""}`} role="tabpanel" aria-labelledby=${`tab-${this._tab}`}>
        ${this._tab === "overview" ? this._overview(ready) : !ready ? html`<p class="empty">Этот раздел появится после подключения Herald.</p>` : this._tab === "rules" ? this._section("policies", { initial_policy_key: this._ruleKey }) : this._tab === "delivery" ? this._delivery() : this._tab === "analytics" ? this._analytics() : this._tab === "controls" ? this._controls() : this._diagnostics()}
      </section>
      <footer>${this._icon("mdi:home-outline")}<span>Тихие часы: ${data.quiet_hours === true ? "включены" : data.quiet_hours === false ? "выключены" : "нет данных"}</span>
        <span>Основная комната: ${this._roomLabel(data.topology?.primary_room)}</span></footer>
      ${this._detailOpen ? this._eventDialog() : nothing}
    </main>`;
  }
  _metrics(status, data) {
    const ready = this._entityUsable(status);
    const statusLabels = { ready: "Готов", idle: "Готов", maintenance: "Обслуживание", muted: "Тишина", degraded: "Требует внимания", error: "Ошибка" };
    const statusLabel = ready ? statusLabels[status.state] ?? this._humanizeCode(status.state) : "Недоступен";
    const today = this.hass.states[this._config.today_entity];
    const queue = this.hass.states[this._config.queue_entity];
    const analytics = data.analytics ?? {};
    return html`<div class="metrics">
      <article class="metric metric-status"><div><h2>Herald</h2><strong class=${`status-value ${ready && ["ready", "idle"].includes(status.state) ? "success" : "warning"}`}>${this._icon("mdi:circle", ready && ["ready", "idle"].includes(status.state) ? "success" : "warning")}${statusLabel}</strong><p>Слушает. Обрабатывает.<br>Заботится о важном.</p></div></article>
      <article class="metric metric-events"><h2>События сегодня</h2><strong>${this._icon("mdi:text-box-outline")}${this._entityUsable(today) ? knownCounter(today.state) : "—"}</strong><p>Важное не пропустим</p></article>
      <article class="metric metric-delivery"><h2>Отправки</h2><strong>${this._icon("mdi:send")}${ready ? knownCounter(analytics.deliveries_today) : "—"}</strong><p>Передано сервисам доставки</p></article>
      <article class="metric metric-queue"><h2>Очередь</h2><strong>${this._icon("mdi:timer-sand")}${this._entityUsable(queue) ? knownCounter(queue.state) : "—"}</strong><p>Ошибки: <span class=${Number(analytics.errors_today) > 0 ? "error" : ""}>${ready ? knownCounter(analytics.errors_today) : "—"}</span></p></article>
    </div>`;
  }
  _overview(ready) {
    const item = this._selected();
    const outcome = eventOutcome(item);
    const registry = this._data().notification_registry?.items ?? [];
    const rule = ruleForEvent(item, registry);
    return html`<div class="overview-grid">
      <article class="hero"><div class="hero-copy">
        <p class="eyebrow">${item ? (item === this._events()[0] ? "Последнее событие" : "Выбранное событие") : "События дома"}</p>
        <div class="hero-title">${this._icon(item ? eventIcon(item) : "mdi:bell-outline")}<div><h1>${item ? this._friendlyDeliveryItemTitle(item) : "Дом пока молчит"}</h1>
          ${item ? html`<p class="muted">${this._notificationTime(item.timestamp, true)} · ${this._friendlyFlowName(item.flow ?? "general")} · ${this._friendlyLevelLabel(item.level ?? "info")}</p>` : nothing}</div></div>
        <p class="hero-message">${item?.message ?? "Новые уведомления появятся здесь автоматически."}</p>
        <div class="hero-actions"><span class=${outcome.tone}>${this._icon("mdi:send-outline")}${item ? outcome.label : "Ожидаем первое событие"}</span>
          <button class="primary" ?disabled=${!item} @click=${() => this._openEvent()}>Открыть событие ${this._icon("mdi:chevron-right")}</button>
          <button class="secondary" ?disabled=${!rule || !ready} @click=${() => this._openRule(rule)}>Правило доставки</button></div>
      </div></article>
      <aside class="overview-side"><section class="surface events-surface"><div class="surface-heading"><h2>Последние события</h2><button class="icon-button" aria-label="Все события" @click=${() => { this._switchTab("diagnostics"); this._subview = "events"; }}>${this._icon("mdi:chevron-right")}</button></div>
        <div class="events-list">${this._events().length ? this._events().slice(0, 4).map((event, index) => html`<button class=${`event-row ${this._selected() === event ? "selected" : ""}`}
          aria-pressed=${this._selected() === event} @click=${() => { this._selectedEvent = eventIdentity(event, index); }}>
          ${this._icon(eventIcon(event), ["warning", "critical", "security"].includes(event.level) ? "warning" : event.flow === "ai_events" ? "purple" : event.flow === "timer_notifications" ? "timer" : "")}
          <span><strong>${this._friendlyDeliveryItemTitle(event)}</strong><small>${event.message ?? "Описание не указано"}</small></span><time>${this._notificationTime(event.timestamp, true)}</time></button>`) : html`<p class="empty">Пока нет событий</p>`}</div>
      </section><section class="surface modes-surface"><h2>Быстрые режимы</h2>
        ${this._quickControl("ai_enabled", "ИИ-перефразирование", "mdi:auto-fix", "purple", "Более естественные уведомления")}
        ${this._quickControl("mute_all", "Глобальная тишина", "mdi:bell-off-outline", "", "Обычные события отключены; критические могут проходить")}
        ${this._quickControl("maintenance_mode", "Обслуживание", "mdi:wrench", "warning", "Уведомления HA и системный журнал")}
      </section></aside>
    </div>`;
  }
  _roomLabel(room) {
    if (!room) return "не определена";
    return this._data().topology?.rooms?.find((item) => item.room === room)?.label ?? this._friendlyRoomLabel(room);
  }
  _openRule(rule) {
    if (!rule?.notification_key) return;
    this._ruleKey = rule.notification_key;
    this._switchTab("rules");
  }
  async _openEvent() {
    if (!this._selected()) return;
    this._eventFeedback = "";
    this._detailOpen = true;
    await this.updateComplete;
    this.shadowRoot.querySelector("dialog")?.showModal();
  }
  _eventDialog() {
    const item = this._selected();
    const rule = ruleForEvent(item, this._data().notification_registry?.items ?? []);
    return html`<dialog aria-labelledby="event-title" @close=${() => { this._detailOpen = false; }}>
      <div class="surface-heading"><h2 id="event-title">${this._friendlyDeliveryItemTitle(item)}</h2><button class="icon-button" aria-label="Закрыть событие" @click=${() => this.shadowRoot.querySelector("dialog").close()}>${this._icon("mdi:close")}</button></div>
      <p class="muted">${this._notificationTime(item.timestamp)} · ${this._friendlyLevelLabel(item.level ?? "info")}</p><p class="full-message">${item.message ?? "Описание не указано"}</p>
      ${item.explanation ? this._renderPolicyExplanation({ explanation: item.explanation }) : html`<p class="muted">Для этого события подробное объяснение не сохранено.</p>`}
      <h3>Результаты отправки</h3>${item.results?.length ? html`<ul class="plain-list">${item.results.map((result) => html`<li>${this._friendlyChannelName(result.channel)}<strong class=${result.status === "error" ? "error" : result.status === "sent" ? "success" : "muted"}>${({ sent: "Отправлено", error: "Ошибка", dropped: "Пропущено" })[result.status] ?? "Нет результата"}</strong></li>`)}</ul>` : html`<p class="muted">Нет сохранённых результатов</p>`}
      <p class="muted">Отправка в сервис не подтверждает получение или прочтение на устройстве.</p>
      <div class="dialog-actions"><button class="primary" ?disabled=${!rule} @click=${() => this._openRule(rule)}>Открыть правило</button>
        <button class="secondary" ?disabled=${!item.notification_id || item.acknowledged || this._eventBusy} @click=${() => this._acknowledge(item)}>${item.acknowledged ? "Отмечено прочитанным" : this._eventBusy ? "Сохраняем…" : "Отметить прочитанным"}</button></div>
      ${this._eventFeedback ? html`<p role="status">${this._eventFeedback}</p>` : nothing}
    </dialog>`;
  }
  async _acknowledge(item) {
    if (!item?.notification_id || this._eventBusy) return;
    this._eventBusy = true;
    try {
      await this.hass.callService("herald", "acknowledge", { notification_id: item.notification_id, ...this._entryScope() });
      this._eventFeedback = "Команда принята. Ожидаем подтверждение в событии.";
    } catch (error) { this._eventFeedback = this._policyError(error); }
    finally { this._eventBusy = false; }
  }
  _entryScope() { return this._config.entry_id ? { entry_id: this._config.entry_id } : {}; }
  _subnav(items) {
    return html`<nav class="subnav" aria-label="Подраздел">${items.map(([key, label]) => html`<button class=${this._subview === key ? "active" : ""} aria-pressed=${this._subview === key} @click=${() => { this._subview = key; }}>${label}</button>`)}</nav>`;
  }
  _delivery() {
    return html`${this._subnav([["channels", "Каналы"], ["rooms", "Комнаты"], ["users", "Получатели"]])}
      ${this._subview === "rooms" ? html`<h2>Доставка по комнатам</h2><div class="room-grid">${(this._data().topology?.rooms ?? []).map((room) => html`<section class="surface"><div class="surface-heading"><h3>${room.label ?? this._roomLabel(room.room)}</h3>${this._icon("mdi:home-account")}</div>
        <p class="muted">${room.primary ? "Основная комната · " : ""}${this._friendlyBinaryState(this.hass.states[room.presence_entity]?.state)}</p>
        ${this._controlRow(this._controlId(`room_presence:${room.room}`), "Ручное присутствие", "mdi:account-outline")}
        ${this._controlId(`room_audio_target:${room.room}`) ? this._controlRow(this._controlId(`room_audio_target:${room.room}`), "Устройство доставки", "mdi:speaker") : nothing}
        <ul class="plain-list">${[...(room.voice_targets ?? []), ...(room.tv_targets ?? [])].map((target) => html`<li>${this.hass.states[target.entity_id]?.attributes.friendly_name ?? this._friendlyChannelName(target.channel)}<small>${target.available ? "Есть в HA" : "Недоступно"}</small></li>`)}</ul>
        ${!room.voice_targets?.length && !room.tv_targets?.length ? html`<p class="muted">Цели доставки не найдены</p>` : nothing}</section>`)}</div>` : this._subview === "users" ? this._users() : html`${this._renderConfigurationOverview()}${this._renderChannels()}`}`;
  }
  _analytics() {
    const data = this._data().analytics ?? {};
    return html`<h2>Аналитика Herald</h2><div class="counter-row">${[["Отправки", data.deliveries_today], ["Пропуски", data.dropped_today], ["Ошибки", data.errors_today], ["ИИ-запросы", data.ai_requests_today]].map(([label, value]) => html`<div><span>${label} сегодня</span><strong>${knownCounter(value)}</strong></div>`)}</div>
      <div class="analytics-grid">${this._distribution("Отправки по каналам", data.channel_delivery_counts, (name) => this._friendlyChannelName(name))}${this._distribution("Ошибки по каналам", data.channel_error_counts, (name) => this._friendlyChannelName(name))}
      ${this._distribution("Причины пропусков", data.drop_reasons, (name) => this._humanizeCode(name))}${this._distribution("ИИ-персонажи", data.ai_character_counts, (name) => this._friendlyCharacterName(name))}</div>
      <p class="muted">Распределение по сохранённым счётчикам Herald. История по часам пока не собирается.</p>`;
  }
  _distribution(title, values, label) {
    const entries = Object.entries(values ?? {}).filter(([, value]) => Number.isFinite(Number(value)) && Number(value) >= 0).sort((a, b) => b[1] - a[1]);
    const max = Math.max(1, ...entries.map(([, value]) => Number(value)));
    return html`<section class="surface"><h3>${title}</h3>${entries.length ? html`<ul class="distribution">${entries.map(([name, value]) => html`<li><span>${label(name)}</span><meter min="0" max=${max} value=${value} aria-label=${label(name)}></meter><strong>${value}</strong></li>`)}</ul>` : html`<p class="empty">Данных пока нет</p>`}</section>`;
  }
  _users() {
    const users = this._data().topology?.users ?? [];
    return html`<h2>Получатели</h2><div class="room-grid">${users.map((user) => html`<section class="surface"><h3>${user.name}</h3><p class="muted">${user.home ? "Дома" : "Не дома"}</p>
      ${this._controlRow(this._controlId(`user_language:${user.slug}`), "Язык", "mdi:translate")}
      ${this._controlRow(this._controlId(`user_character:${user.slug}`), "Персонаж", "mdi:account-star-outline")}
      ${this._controlRow(this._controlId(`user_silent:${user.slug}`), "Без звука", "mdi:bell-off-outline")}</section>`)}</div>`;
  }
  _controls() {
    const data = this._data();
    return html`${this._subnav([["general", "Общее"], ["flows", "Потоки"], ["users", "Пользователи"], ["ai", "ИИ и персонажи"]])}
      ${this._subview === "users" ? this._users() : this._subview === "flows" ? html`<h2>Потоки уведомлений</h2><div class="room-grid">${Object.entries(data.flow_policies ?? {}).map(([flow]) => html`<section class="surface"><h3>${this._friendlyFlowName(flow)}</h3>
        ${[["flow_enabled", "Включён", "mdi:source-branch"], ["flow_summary_window", "Окно сводки, с", "mdi:timer-outline"], ["flow_dedup_window", "Защита от повторов, с", "mdi:content-copy"], ["flow_cooldown", "Пауза доставки, с", "mdi:pause"]].map(([key, label, icon]) => this._controlRow(this._controlId(`${key}:${flow}`), label, icon))}
        ${this._renderFlow(flow, data.flow_states?.[flow], data.snoozed_flows?.[flow])}</section>`)}</div>${this._section("queue")}` : this._subview === "ai" ? html`<h2>ИИ и персонажи</h2><div class="surface">${this._quickControl("ai_enabled", "ИИ-перефразирование", "mdi:auto-fix", "purple")}
          ${["info", "warning", "critical"].map((level) => this._controlRow(this._controlId(`ai_level:${level}`), this._friendlyLevelLabel(level), "mdi:brain"))}
          <p class="muted">Сервер, модель и голос настраиваются в параметрах интеграции.</p><a class="secondary settings-link" href="/config/integrations/integration/herald">Параметры Herald</a></div>${this._section("characters")}` : html`<h2>Общие настройки</h2><div class="analytics-grid"><section class="surface"><h3>Режимы</h3>
          ${this._quickControl("mute_all", "Глобальная тишина", "mdi:bell-off-outline", "")}${this._quickControl("maintenance_mode", "Обслуживание", "mdi:wrench", "warning")}
          ${this._controlRow(this._controlId("maintenance_min_level"), "Важность в обслуживании", "mdi:alert-outline")}${this._quickControl("dashboard_sidebar", "Показывать в меню", "mdi:view-dashboard", "")}</section>
          <section class="surface"><h3>Важность и способы доставки</h3>${["info", "warning", "critical"].map((level) => this._controlRow(this._controlId(`level_enabled:${level}`), this._friendlyLevelLabel(level), "mdi:bell-outline"))}
          ${["voice", "push", "tv"].map((family) => this._controlRow(this._controlId(`channel_family:${family}`), this._friendlyChannelFamilyLabel(family), "mdi:send-outline"))}</section></div>`}`;
  }
  _controlRow(id, label, icon) {
    const entity = this.hass.states[id];
    const known = this._entityUsable(entity);
    const domain = String(id ?? "").split(".")[0];
    return html`<div class="control-row">${this._icon(entity?.attributes.icon ?? icon)}<label for=${id ?? label}>${label}</label>
      ${domain === "switch" ? html`<ha-switch aria-label=${label} .checked=${known && entity.state === "on"} .disabled=${!this._binaryEntityKnown(entity) || this._controlPending(id)} @change=${() => this._toggleSwitch(id, entity.state === "on")}></ha-switch>` : domain === "select" ? html`<select id=${id} aria-label=${label} .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(id)} @change=${(event) => this._setSelectOption(id, event)}>
      ${known ? (entity.attributes.options ?? []).map((value) => html`<option value=${value} .selected=${entity.state === value}>${value}</option>`) : html`<option value="">Недоступно</option>`}</select>` : domain === "number" ? html`<input id=${id} type="number" aria-label=${label} .value=${known ? entity.state : ""} min=${entity?.attributes.min ?? 0} max=${entity?.attributes.max ?? 86400} step=${entity?.attributes.step ?? 1} ?disabled=${!known || this._controlPending(id)} @change=${(event) => this._setNumber(id, event)}>` : html`<span class="muted">Недоступно</span>`}
      <div class="control-feedback">${this._numberErrors[id] ? html`<p class="error" role="alert">${this._numberErrors[id]}</p>` : this._renderControlFeedback(id)}</div></div>`;
  }
  async _setNumber(id, event) {
    const entity = this.hass.states[id];
    const input = event.target;
    const value = Number(input.value);
    if (!id?.startsWith("number.") || !this._entityUsable(entity) || input.value === "" || !Number.isFinite(value) || value < Number(entity.attributes.min ?? 0) || value > Number(entity.attributes.max ?? 86400) || input.validity?.valid === false) {
      this._numberErrors = { ...this._numberErrors, [id]: "Значение вне допустимого диапазона" };
      input.value = entity?.state ?? "";
      return;
    }
    this._numberErrors = { ...this._numberErrors, [id]: undefined };
    input.value = entity.state;
    await this._runControlAction(id, String(value), "number", "set_value", { entity_id: id, value });
  }
  _diagnostics() {
    const data = this._data();
    return html`${this._subnav([["general", "Настройки и состояние"], ["events", "Все события"], ["trace", "Этапы обработки"]])}
      ${this._subview === "events" ? html`<h2>История событий</h2><div class="history-list">${this._events().map((item, index) => html`<button class="event-row" @click=${() => { this._selectedEvent = eventIdentity(item, index); this._openEvent(); }}>${this._icon(eventIcon(item))}<span><strong>${this._friendlyDeliveryItemTitle(item)}</strong><small>${item.message}</small></span><time>${this._notificationTime(item.timestamp)}</time></button>`)}</div>` : this._subview === "trace" ? html`<h2>Последние этапы обработки</h2><ul class="trace-list">${(data.pipeline_trace ?? []).map((stage) => html`<li><time>${this._notificationTime(stage.timestamp, true)}</time><strong>${this._humanizeCode(stage.stage)}</strong><span>${stage.status ? this._humanizeCode(stage.status) : stage.event ?? ""}</span></li>`)}</ul><h3>Последняя проверка маршрута</h3>${data.last_route_preview?.explanation ? this._renderPolicyExplanation(data.last_route_preview) : html`<p class="muted">Предпросмотр ещё не выполнялся</p>`}` : html`<h2>Диагностика</h2>${this._renderConfigurationOverview()}${this._section("queue")}
        <section class="surface"><h3>Проверка доставки</h3><p class="muted">Откройте тестовую сущность в Home Assistant. Её кнопка отправляет реальное уведомление.</p>
        <div class="test-actions">${(data.control_entities?.tests ?? []).filter((id) => this.hass.states[id]).map((id) => html`<button class="secondary" @click=${() => this._openSetting(id)}>${this.hass.states[id].attributes.friendly_name ?? "Проверка канала"} ${this._icon("mdi:open-in-new")}</button>`)}</div></section>`}`;
  }
  static styles = [HeraldCard.styles, css`
    :host { display: block; --primary-text-color: #d9edf4; --secondary-text-color: #93b7c6; --primary-color: #43c4e9; --ha-card-background: #082631; color: #d9edf4; font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
    * { box-sizing: border-box; }
    .dashboard { background: #082631; height: calc(100dvh - var(--header-height, 56px)); min-height: 0; padding: 16px 22px 12px; display: flex; flex-direction: column; gap: 14px; }
    .dashboard-header { display: flex; align-items: center; gap: 26px; min-height: 44px; }
    .brand { display: flex; align-items: center; gap: 12px; font-size: 28px; }
    .brand ha-icon { --mdc-icon-size: 38px; }
    .home-link { border-left: 1px solid #245060; padding-left: 26px; }
    a { color: #d9edf4; text-decoration: none; }
    a:hover { color: #43c4e9; }
    .date { margin-left: auto; display: flex; align-items: center; gap: 12px; font-size: 15px; }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
    .metric { background-size: cover; background-position: center; height: clamp(140px, 18dvh, 216px); border: 1px solid #376272; border-radius: 10px; padding: 22px 30px; display: flex; flex-direction: column; justify-content: center; }
    .metric h2 { font-size: 20px; max-width: 180px; margin: 0 0 12px; }
    .metric strong { font-size: 42px; display: flex; align-items: center; gap: 12px; }
    .metric strong ha-icon { --mdc-icon-size: 36px; }
    .metric p { font-size: 13px; line-height: 1.5; margin: 8px 0 0; color: #b0cbd7; }
    .metric-status { background-image: url('/herald/assets/herald-status.webp'); padding-left: 42%; }
    .metric-status h2 { font-size: 22px; }
    .metric .status-value { font-size: 24px; gap: 10px; }
    .metric .status-value ha-icon { --mdc-icon-size: 20px; }
    .metric-events { background-image: url('/herald/assets/herald-events.webp'); }
    .metric-delivery { background-image: url('/herald/assets/herald-delivery.webp'); }
    .metric-queue { background-image: url('/herald/assets/herald-queue.webp'); }
    ha-icon { color: #43c4e9; flex-shrink: 0; --mdc-icon-size: 24px; }
    .success, ha-icon.success { color: #43dca0; } .warning, ha-icon.warning { color: #ffc65b; } .error { color: #ff7979; } .purple, ha-icon.purple { color: #b17aff; } .timer, ha-icon.timer { color: #eaa385; } .muted { color: #93b7c6; }
    .dashboard-tabs { display: flex; border-bottom: 1px solid #245060; gap: 10px; flex-shrink: 0; overflow-x: auto; }
    .dashboard-tabs button { flex: 1; display: flex; align-items: center; justify-content: center; gap: 13px; padding: 12px 8px 15px; border: 0; border-bottom: 3px solid transparent; border-radius: 0; background: none; color: #93b7c6; white-space: nowrap; font-size: 16px; }
    .dashboard-tabs button[aria-selected='true'] { border-bottom-color: #43c4e9; color: #edfaff; font-weight: 600; }
    button { font: inherit; cursor: pointer; color: inherit; }
    button:hover:not(:disabled) { filter: brightness(1.14); }
    button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid #cceffa; outline-offset: 3px; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .workspace { background: #082631; flex: 1; min-height: 0; }
    .workspace:not(.overview-workspace) { max-height: calc(100dvh - 350px); overflow: auto; padding: 12px 6px; scrollbar-color: #346174 #082631; }
    .overview-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(340px, 1fr); gap: 14px; min-height: 0; height: 100%; }
    .hero { background-image: url('/herald/assets/herald-hero.webp'); background-size: cover; background-position: center; position: relative; border-radius: 10px; border: 1px solid #245060; overflow: hidden; display: flex; align-items: flex-end; }
    .hero-copy { padding: 25px 32px; width: 100%; background: rgba(3, 25, 34, .85); }
    .eyebrow { text-transform: none; letter-spacing: 0; font-size: 16px; color: #a1c7d7; margin: 0 0 16px; }
    .hero-title { display: flex; gap: 20px; align-items: center; }
    .hero-title > ha-icon { --mdc-icon-size: 42px; }
    h1 { font-size: 27px; line-height: 1.18; margin: 0 0 8px; }
    h2 { font-size: 20px; margin: 0 0 18px; } h3 { font-size: 18px; margin: 0 0 15px; }
    .hero-title p { font-size: 14px; margin: 0; }
    .hero-message { font-size: 16px; line-height: 1.5; max-height: 100px; overflow: auto; margin: 18px 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    .hero-actions { border-top: 1px solid #245060; padding-top: 15px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .hero-actions > span { display: flex; align-items: center; gap: 10px; font-size: 13px; margin-right: auto; }
    .primary, .secondary { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 13px 18px; border-radius: 10px; font-size: 14px; min-height: 44px; }
    .primary { background: #43c4e9; color: #002430; border: 1px solid #43c4e9; font-weight: 600; }
    .primary ha-icon { color: #002430; }
    .secondary { background: #072732; color: #d9edf4; border: 1px solid #3e758c; }
    .overview-side { display: grid; grid-template-rows: minmax(0, 1.15fr) minmax(220px, .85fr); gap: 14px; min-height: 0; }
    .surface { background: #092a36; border: 1px solid #245060; border-radius: 12px; padding: 22px 24px; }
    .surface-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    .surface-heading h2, .surface-heading h3 { margin: 0; }
    .icon-button { border: 0; background: transparent; padding: 8px; display: inline-flex; }
    .events-surface { padding: 14px 10px; display: flex; flex-direction: column; min-height: 0; }
    .events-surface .surface-heading { padding: 0 12px 12px; }
    .events-list { min-height: 0; overflow: auto; }
    .event-row { display: flex; align-items: center; gap: 16px; width: 100%; text-align: left; background: transparent; padding: 17px 14px; border: 0; border-bottom: 1px solid #245060; border-radius: 0; }
    .event-row:last-child { border-bottom: 0; }
    .event-row.selected { background: #10394a; border-radius: 9px; }
    .event-row > ha-icon { --mdc-icon-size: 32px; }
    .event-row > span { flex: 1; min-width: 0; }
    .event-row strong { font-size: 14px; font-weight: 500; line-height: 1.4; display: block; }
    .event-row small { font-size: 12px; color: #93b7c6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-top: 6px; line-height: 1.4; overflow-wrap: anywhere; }
    .event-row time { font-size: 12px; align-self: flex-start; padding-top: 4px; color: #afceda; }
    .quick-control { display: flex; align-items: center; gap: 16px; padding: 17px 0; border-bottom: 1px solid #245060; }
    .quick-control:last-child { border-bottom: 0; padding-bottom: 0; }
    .quick-control > ha-icon { --mdc-icon-size: 29px; }
    .quick-control > div { flex: 1; min-width: 0; font-size: 14px; }
    .quick-control small { display: block; color: #93b7c6; font-size: 11px; line-height: 1.45; margin-top: 6px; }
    ha-switch { --switch-checked-button-color: #e8f8ff; --switch-checked-track-color: #43c4e9; --switch-unchecked-button-color: #d9edf4; --switch-unchecked-track-color: #547484; }
    .modes-surface { padding: 20px 24px; overflow: auto; }
    footer { display: flex; justify-content: flex-start; align-items: center; gap: 16px; color: #93b7c6; font-size: 12px; min-height: 25px; flex-wrap: wrap; }
    .subnav { display: flex; gap: 8px; margin-bottom: 22px; overflow: auto; }
    .subnav button { border: 0; border-radius: 8px; background: transparent; padding: 10px 18px; white-space: nowrap; color: #93b7c6; }
    .subnav button.active { background: #164455; color: #edfaff; }
    .analytics-grid, .room-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin: 18px 0; }
    .counter-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 25px; padding: 20px 0 35px; }
    .counter-row span { display: block; color: #93b7c6; } .counter-row strong { display: block; font-size: 32px; margin-top: 12px; }
    .plain-list, .distribution, .trace-list { list-style: none; padding: 0; margin: 20px 0; }
    .plain-list li { display: flex; justify-content: space-between; padding: 12px 0; gap: 20px; border-bottom: 1px solid #245060; }
    .distribution li { display: grid; grid-template-columns: minmax(0, 1fr) 110px 35px; align-items: center; gap: 14px; padding: 13px 0; }
    meter { width: 100%; accent-color: #43c4e9; }
    .control-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; align-items: center; gap: 12px; border-bottom: 1px solid #245060; padding: 14px 0; }
    .control-feedback { grid-column: 2 / 4; }
    .control-feedback:empty { display: none; }
    input, select { color-scheme: dark; background: #0c3342; color: #d9edf4; border: 1px solid #346174; border-radius: 8px; padding: 10px; font: inherit; max-width: 190px; }
    input[type=number] { width: 100px; }
    .trace-list li { display: grid; grid-template-columns: 80px minmax(150px, 1fr) 2fr; gap: 20px; padding: 15px 0; border-bottom: 1px solid #245060; }
    .test-actions { display: flex; flex-wrap: wrap; gap: 12px; }
    .availability { color: #ffc65b; margin: 0; }
    .history-list .event-row small { -webkit-line-clamp: 3; }
    dialog { color: #d9edf4; background: #082631; border: 1px solid #43c4e9; border-radius: 18px; padding: 25px; width: min(850px, calc(100vw - 32px)); max-height: 85dvh; overflow: auto; }
    dialog::backdrop { background: rgba(1, 15, 22, .8); backdrop-filter: blur(7px); }
    .full-message { white-space: pre-wrap; line-height: 1.6; overflow-wrap: anywhere; }
    .dialog-actions { display: flex; gap: 12px; flex-wrap: wrap; }
    @media (min-width: 1100px) and (max-height: 850px) { .dashboard { gap: 10px; } .metric { height: 138px; padding-top: 14px; padding-bottom: 14px; } .metric h2 { font-size: 16px; margin-bottom: 8px; } .metric strong { font-size: 30px; } .metric p { font-size: 11px; } .overview-grid { height: 100%; min-height: 0; } .hero-copy { padding: 18px 22px; } .hero-title h1 { font-size: 22px; } .overview-side { grid-template-rows: 1.1fr .9fr; } .event-row { padding: 10px; } .quick-control { padding: 10px 0; } .modes-surface { padding: 15px 20px; } .quick-control small { font-size: 10px; } .workspace:not(.overview-workspace) { max-height: calc(100dvh - 300px); } }
    @media (max-width: 1050px) { .dashboard { padding: 14px; } .metric { padding: 18px; } .metric-status { padding-left: 36%; } .metric h2 { font-size: 17px; } .metric .status-value { font-size: 20px; } .overview-grid { grid-template-columns: minmax(0, 1.4fr) minmax(290px, 1fr); } .hero-actions { gap: 10px; } .hero-actions > span { width: 100%; } .hero-copy { padding: 22px; } .hero-title { gap: 12px; } h1 { font-size: 22px; } .dashboard-tabs { gap: 0; } .dashboard-tabs button { gap: 7px; font-size: 14px; } .date { font-size: 13px; } }
    @media (min-width: 761px) and (max-width: 1100px) { .overview-grid { grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr); } .surface-heading h2 { font-size: 17px; } .event-row { padding: 10px; gap: 10px; } .event-row strong { font-size: 12px; } .event-row small { font-size: 10px; margin-top: 4px; } .event-row time { font-size: 10px; } .event-row > ha-icon { --mdc-icon-size: 26px; } .quick-control { padding: 10px 0; gap: 10px; } .quick-control > div { font-size: 12px; } .quick-control small { font-size: 10px; margin-top: 4px; } .modes-surface { padding: 15px 18px; } .events-surface .surface-heading { padding-bottom: 8px; } }
    @media (min-width: 761px) and (max-height: 1000px) { .dashboard { gap: 10px; } .dashboard-header { min-height: 38px; } .overview-side { grid-template-rows: minmax(0, 1fr) auto; } .event-row { padding-top: 8px; padding-bottom: 8px; } .quick-control { padding-top: 8px; padding-bottom: 8px; } .modes-surface { padding-top: 12px; padding-bottom: 12px; } .metric { height: clamp(138px, 17dvh, 170px); } footer { min-height: 20px; } }
    @media (max-width: 760px) { .dashboard { gap: 12px; height: auto; min-height: auto; } .dashboard-header { flex-wrap: wrap; gap: 15px; } .brand { font-size: 24px; } .home-link { padding-left: 15px; font-size: 14px; } .date { width: 100%; margin: 0; justify-content: flex-end; } .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .metric { height: 150px; } .metric-status { padding-left: 42%; } .dashboard-tabs button { min-width: 110px; } .overview-grid { display: flex; flex-direction: column; height: auto; min-height: 0; } .hero { min-height: 570px; } .hero-copy { margin-top: 280px; } .hero-actions > span { width: 100%; } .overview-side { display: flex; flex-direction: column; } .events-list { max-height: 390px; } .workspace:not(.overview-workspace) { max-height: none; overflow: visible; } .analytics-grid, .room-grid { grid-template-columns: 1fr; } .counter-row { grid-template-columns: repeat(2, 1fr); } footer { font-size: 11px; } .control-row { grid-template-columns: 24px minmax(0, 1fr); } .control-row > select, .control-row > input, .control-row > ha-switch { grid-column: 2; justify-self: start; } .control-feedback { grid-column: 2; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
  `];
}

if (!customElements.get("herald-dashboard-section")) customElements.define("herald-dashboard-section", HeraldDashboardSection);
if (!customElements.get("ha-herald-dashboard")) customElements.define("ha-herald-dashboard", HeraldDashboard);
if (!window.customCards.some((item) => item.type === "ha-herald-dashboard")) window.customCards.push({ type: "ha-herald-dashboard", name: "Herald: Дашборд", description: "Обзор и управление Herald", preview: true, documentationURL: "https://github.com/Mesteriis/ha-herald" });
