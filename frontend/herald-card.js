import { LitElement, css, html, nothing } from "lit";

window.customCards = window.customCards || [];
[
  {
    type: "herald-card",
    name: "Herald Card",
    description: "Полная карточка Herald",
    preview: true
  },
  {
    type: "ha-herald-general",
    name: "Herald: Общее",
    description: "Краткий статус и сводка Herald",
    preview: true
  },
  {
    type: "ha-herald-policies",
    name: "Herald: Политики",
    description: "Политики уведомлений Herald",
    preview: true
  },
  {
    type: "ha-herald-policy-guide",
    name: "Herald: Памятка",
    description: "Краткая памятка по policy-объектам Herald",
    preview: true
  },
  {
    type: "ha-herald-flows",
    name: "Herald: Потоки",
    description: "Потоки и заглушение Herald",
    preview: true
  },
  {
    type: "ha-herald-languages",
    name: "Herald: Языки",
    description: "Языки пользователей Herald",
    preview: true
  },
  {
    type: "ha-herald-characters",
    name: "Herald: Персонажи",
    description: "Персонажи пользователей Herald",
    preview: true
  },
  {
    type: "ha-herald-mute",
    name: "Herald: Тишина",
    description: "Точечное заглушение Herald",
    preview: true
  },
  {
    type: "ha-herald-rooms",
    name: "Herald: Комнаты",
    description: "Комнаты и fallback-переключатели Herald",
    preview: true
  },
  {
    type: "ha-herald-queue",
    name: "Herald: Очередь",
    description: "Очередь событий Herald",
    preview: true
  },
  {
    type: "ha-herald-feed",
    name: "Herald: Лента",
    description: "Лента доставки Herald",
    preview: true
  },
  {
    type: "ha-herald-recent",
    name: "Herald: Последние",
    description: "Последние уведомления Herald",
    preview: true
  },
  {
    type: "ha-herald-controls",
    name: "Herald: Управление",
    description: "Составная карточка управления Herald",
    preview: true
  },
  {
    type: "ha-herald-overview",
    name: "Herald: Обзор",
    description: "Составная обзорная карточка Herald",
    preview: true
  }
].forEach((card) => {
  if (!window.customCards.some((item) => item.type === card.type)) {
    window.customCards.push({
      ...card,
      documentationURL: "https://github.com/Mesteriis/ha-herald"
    });
  }
});
const DEFAULT_LANGUAGES = ["ru", "en", "es", "fr"];
const DEFAULT_STATUS_ENTITY = "sensor.herald_notification_center_status";
const DEFAULT_TODAY_ENTITY = "sensor.herald_notification_center_notifications_today";
const DEFAULT_LAST_ENTITY = "sensor.herald_notification_center_last_notification";
const DEFAULT_QUEUE_ENTITY = "sensor.herald_notification_center_queue_size";
const POLICY_PAGE_SIZE = 12;
export class HeraldCard extends LitElement {
  static properties = {
    hass: { attribute: false },
    _config: { state: true },
    _busyFlow: { state: true },
    _busyPolicy: { state: true },
    _policyDrafts: { state: true },
    _policySearch: { state: true },
    _policyFamily: { state: true },
    _policyScope: { state: true },
    _policyPage: { state: true },
    _policyExpanded: { state: true },
    _policySaved: { state: true },
    _policyFeedback: { state: true },
    _policyPreviews: { state: true },
    _policyScenarios: { state: true },
    _controlActions: { state: true },
    _configurationResponse: { state: true },
    _configurationBusy: { state: true },
    _configurationFeedback: { state: true },
  };

  constructor() {
    super(...arguments);
    this._busyFlow = "";
    this._busyPolicy = "";
    this._policyDrafts = {};
    this._policySearch = "";
    this._policyFamily = "all";
    this._policyScope = "all";
    this._policyPage = 1;
    this._policyExpanded = "";
    this._policySaved = {};
    this._policyFeedback = {};
    this._policyPreviews = {};
    this._policyScenarios = {};
    this._policyRevisions = {};
    this._previewSequence = 0;
    this._controlActions = {};
    this._controlTimers = new Map();
    this._controlSequence = 0;
    this._configurationSequence = 0;
    this._configurationBusy = false;
    this._configurationResponse = null;
    this._configurationFeedback = null;
  }
  setConfig(config) {
    this._clearControlActions();
    this._invalidateConfiguration();
    this._config = {
      ...config,
      view_mode: config.view_mode || this.constructor.viewMode || "full",
      status_entity: config.status_entity || DEFAULT_STATUS_ENTITY,
      today_entity: config.today_entity || DEFAULT_TODAY_ENTITY,
      last_entity: config.last_entity || DEFAULT_LAST_ENTITY,
      queue_entity: config.queue_entity || DEFAULT_QUEUE_ENTITY
    };
    if (config.initial_policy_key) {
      this._policyExpanded = config.initial_policy_key;
      this._policySearch = config.initial_policy_key;
      this._policyPage = 1;
    }
  }
  willUpdate(changed) {
    if (changed.has("hass")) this._reconcileControlActions();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._clearControlActions();
    this._invalidateConfiguration();
  }
  getCardSize() {
    const mode = this._config?.view_mode || this.constructor.viewMode || "full";
    if (["general", "flows", "languages", "characters", "mute", "rooms", "queue", "feed", "recent", "policy-guide"].includes(mode)) {
      return 3;
    }
    if (mode === "policies") {
      return 8;
    }
    return 6;
  }
  render() {
    if (!this.hass || !this._config) {
      return html`<ha-card>Loading…</ha-card>`;
    }
    const today = this.hass.states[this._config.today_entity ?? ""];
    const last = this.hass.states[this._config.last_entity ?? ""];
    const queue = this.hass.states[this._config.queue_entity ?? ""];
    const status = this.hass.states[this._config.status_entity ?? DEFAULT_STATUS_ENTITY];
    if (!today || !last || !queue || !status) {
      return html`<ha-card><div class="shell">Сущности Herald сейчас недоступны.</div></ha-card>`;
    }
    const recent = today.attributes.recent_notifications ?? [];
    const dashboardFeed = today.attributes.dashboard_feed ?? queue.attributes.dashboard_feed ?? [];
    const queuedNotifications = queue.attributes.queued_notifications ?? [];
    const flowStates = queue.attributes.flow_states ?? {};
    const snoozedFlows = queue.attributes.snoozed_flows ?? {};
    const userControlEntities = queue.attributes.control_entities?.users ?? [];
    const dedupe = (items) => [...new Set(items)];
    const languageEntities = dedupe([
      ...(this._config.language_entities ?? []),
      ...userControlEntities.filter((entityId) => entityId.endsWith("_language"))
    ]);
    const characterEntities = dedupe(
      userControlEntities.filter((entityId) => entityId.endsWith("_character"))
    );
    const muteEntities = dedupe(
      userControlEntities.filter((entityId) => entityId.endsWith("_silent"))
    );
    const notificationRegistry = status.attributes.notification_registry?.items ?? [];
    const notificationSummary = status.attributes.notification_registry_summary ?? {};
    const policyFamilies = [...new Set(notificationRegistry.map((item) => item.family).filter(Boolean))].sort();
    const filteredRegistry = this._filterPolicies(notificationRegistry);
    const policyPage = this._paginatePolicies(filteredRegistry);
    const roomEntities = this._config.room_entities ?? [];
    const renderEmptySection = (title, subtitle, message, panelClass) => this._renderPanelCard(
      title,
      subtitle,
      html`<div class="empty">${message}</div>`,
      nothing,
      panelClass
    );
    const heroCard = html`
      <ha-card class="panel hero-panel">
        <div class="panel-shell">
          <div class="hero">
            <div>
              <p class="eyebrow">Herald</p>
              <h2>${this._config.title ?? "Центр уведомлений Herald"}</h2>
              <p class="subhead">Нативная карточка управления уведомлениями: статус, очередь, пользователи, комнаты и последние события.</p>
            </div>
            <div class="stats">
              ${this._renderStat("Сегодня", today.state)}
              ${this._renderStat("Очередь", queue.state)}
              ${this._renderStat("Последнее", last.state)}
            </div>
          </div>
          ${this._renderConfigurationOverview()}
        </div>
      </ha-card>
    `;
    const channelsSection = this._renderChannels();
    const policySection = notificationRegistry.length ? this._renderPanelCard(
      "Правила уведомлений",
      "Выберите уведомление, настройте доставку и проверьте результат.",
      html`
        <div class="stats compact">
          ${this._renderStat("Всего", notificationSummary.count ?? notificationRegistry.length)}
          ${this._renderStat("Включено", notificationSummary.enabled_count ?? "нет")}
          ${this._renderStat("Выключено", notificationSummary.disabled_count ?? "нет")}
          ${this._renderStat("Кастом", notificationSummary.customized_count ?? "нет")}
          ${this._renderStat("Фильтр", filteredRegistry.length)}
          ${this._renderStat("Страница", policyPage.totalPages ? `${policyPage.page}/${policyPage.totalPages}` : "0/0")}
        </div>
        <div class="policy-toolbar">
          <label class="language-card policy-filter">
            <span>Поиск</span>
            <input
              .value=${this._policySearch}
              placeholder="стиралка, тариф, гости, камеры..."
              @input=${(event) => this._setPolicySearch(event.target.value)}
            />
          </label>
          <label class="language-card policy-filter">
            <span>Семейство</span>
            <select .value=${this._policyFamily} @change=${(event) => this._setPolicyFamily(event.target.value)}>
              <option value="all">Все</option>
              ${policyFamilies.map((family) => html`<option value=${family}>${this._friendlyFamilyLabel(family)}</option>`)}
            </select>
          </label>
          <label class="language-card policy-filter">
            <span>Срез</span>
            <select .value=${this._policyScope} @change=${(event) => this._setPolicyScope(event.target.value)}>
              <option value="all">Все</option>
              <option value="active">Активные</option>
              <option value="attention">Требуют внимания</option>
              <option value="customized">Переопределенные</option>
              <option value="disabled">Отключенные</option>
            </select>
          </label>
        </div>
        ${policyPage.items.length ? this._renderPolicyTable(policyPage, filteredRegistry.length) : html`<div class="empty">По текущему фильтру уведомлений нет.</div>`}
      `,
      html`
        <button class="secondary-action" @click=${() => this._refreshPolicies()}>
          Обновить реестр
        </button>
      `,
      "policy-panel"
    ) : nothing;
    const policyGuideSection = notificationRegistry.length ? this._renderPanelCard(
      "Как настроить уведомление",
      "Общее правило, личное исключение и проверка результата",
      html`
        <div class="notification">
          <p>Открой уведомление и выбери способ доставки. «По общему правилу» учитывает поток, присутствие и общие настройки. «Выбрать каналы» задаёт свой список; пустой список означает отсутствие доставки. Проверь черновик без отправки, затем сохрани. Дополнительные параметры нужны для отдельных исключений.</p>
        </div>
      `,
      nothing,
      "policy-guide-panel"
    ) : nothing;
    const flowsSection = this._renderPanelCard(
      "Потоки",
      "Временное включение и заглушение потоков",
      html`
        <div class="flow-grid">
          ${Object.entries(flowStates).map(([flow, enabled]) => this._renderFlow(flow, enabled, snoozedFlows[flow]))}
        </div>
      `,
      nothing,
      "flows-panel"
    );
    const languagesSection = languageEntities.length ? this._renderPanelCard(
      "Языки",
      "Язык уведомлений по пользователям",
      html`
        <div class="language-grid">
          ${languageEntities.map((entityId) => this._renderLanguage(entityId))}
        </div>
      `,
      nothing,
      "languages-panel"
    ) : renderEmptySection("Языки", "Язык уведомлений по пользователям", "Пользовательские языковые контролы пока не найдены.", "languages-panel");
    const charactersSection = characterEntities.length ? this._renderPanelCard(
      "Персонажи",
      "ИИ-персонаж по пользователям",
      html`
        <div class="character-grid">
          ${characterEntities.map((entityId) => this._renderCharacter(entityId))}
        </div>
      `,
      nothing,
      "characters-panel"
    ) : renderEmptySection("Персонажи", "ИИ-персонаж по пользователям", "Пользовательские персонажи пока не найдены.", "characters-panel");
    const muteSection = muteEntities.length ? this._renderPanelCard(
      "Заглушение",
      "Точечное отключение звука по пользователям",
      html`
        <div class="mute-grid">
          ${muteEntities.map((entityId) => this._renderMute(entityId))}
        </div>
      `,
      nothing,
      "mute-panel"
    ) : renderEmptySection("Заглушение", "Точечное отключение звука по пользователям", "Персональные переключатели тишины пока не найдены.", "mute-panel");
    const roomsSection = roomEntities.length ? this._renderPanelCard(
      "Комнаты",
      "Комнаты, присутствие и fallback-переключатели Herald",
      html`
        <div class="room-grid">
          ${roomEntities.map((item) => this._renderRoom(item))}
        </div>
      `,
      nothing,
      "rooms-panel"
    ) : renderEmptySection("Комнаты", "Комнаты, присутствие и fallback-переключатели Herald", "Комнатные контролы пока не настроены.", "rooms-panel");
    const queueSection = this._renderPanelCard(
      "Очередь",
      "События, которые ждут отправки или сводки",
      html`
        <div class="list">
          ${queuedNotifications.length ? queuedNotifications.slice(0, 8).map((item) => this._renderQueuedItem(item)) : html`<div class="empty">Очередь сейчас пуста.</div>`}
        </div>
      `,
      nothing,
      "queue-panel"
    );
    const dashboardFeedSection = this._renderPanelCard(
      "Лента панели",
      "Уведомления, доставленные в канал Herald dashboard",
      html`
        <div class="list">
          ${dashboardFeed.length ? dashboardFeed.slice(0, 8).map((item) => this._renderFeedItem(item)) : html`<div class="empty">Лента панели пока пуста.</div>`}
        </div>
      `,
      nothing,
      "feed-panel"
    );
    const recentSection = this._renderPanelCard(
      this._config.view_mode === "recent" ? this._config.title ?? "Последние уведомления" : "Последние уведомления",
      this._config.compact ? "" : "Последние доставки и сводки",
      html`
        <div class="list">
          ${recent.length ? recent.slice(0, this._recentLimit()).map((item) => this._renderNotification(item)) : html`<div class="empty">Уведомлений пока нет.</div>`}
          ${this._config.compact && recent.length > this._recentLimit() ? html`
            <details class="older-events">
              <summary>Ещё события (${recent.length - this._recentLimit()})</summary>
              <div class="list">${recent.slice(this._recentLimit()).map((item) => this._renderNotification(item))}</div>
            </details>
          ` : nothing}
        </div>
      `,
      nothing,
      "recent-panel"
    );
    if (this._config.view_mode === "general") {
      return heroCard;
    }
    if (this._config.view_mode === "policies") {
      return policySection;
    }
    if (this._config.view_mode === "policy-guide") {
      return policyGuideSection;
    }
    if (this._config.view_mode === "flows") {
      return flowsSection;
    }
    if (this._config.view_mode === "languages") {
      return languagesSection;
    }
    if (this._config.view_mode === "characters") {
      return charactersSection;
    }
    if (this._config.view_mode === "mute") {
      return muteSection;
    }
    if (this._config.view_mode === "rooms") {
      return roomsSection;
    }
    if (this._config.view_mode === "queue") {
      return queueSection;
    }
    if (this._config.view_mode === "feed") {
      return dashboardFeedSection;
    }
    if (this._config.view_mode === "recent") {
      return recentSection;
    }
    if (this._config.view_mode === "controls") {
      return html`
        <ha-card>
          <div class="shell shell-controls">
            ${this._renderPanelCard("Общая доставка", "Ограничения и последняя проверка настройки", this._renderConfigurationOverview())}
            ${channelsSection}
            ${flowsSection}
            ${languagesSection}
            ${charactersSection}
            ${muteSection}
            ${roomsSection}
          </div>
        </ha-card>
      `;
    }
    if (this._config.view_mode === "overview") {
      return html`
        <ha-card>
          <div class="shell shell-overview">
            ${heroCard}
            ${channelsSection}
            ${flowsSection}
            ${queueSection}
            ${dashboardFeedSection}
            ${recentSection}
          </div>
        </ha-card>
      `;
    }
    return html`
      <ha-card>
        <div class="shell">
          ${heroCard}
          ${channelsSection}
          ${policySection}
          ${policyGuideSection}
          ${flowsSection}
          ${languagesSection}
          ${charactersSection}
          ${muteSection}
          ${roomsSection}
          ${queueSection}
          ${dashboardFeedSection}
          ${recentSection}
        </div>
      </ha-card>
    `;
  }
  _renderPanelCard(title, subtitle, body, actions = nothing, panelClass = "") {
    return html`
      <ha-card class="panel ${panelClass} ${this._config?.compact ? "compact-panel" : ""}">
        <div class="panel-shell">
          <div class="panel-header">
            <div>
              <h3>${title}</h3>
              ${subtitle ? html`<span>${subtitle}</span>` : nothing}
            </div>
            ${actions}
          </div>
          ${body}
        </div>
      </ha-card>
    `;
  }
  _renderStat(label, value) {
    return html`
      <div class="stat">
        <span>${label}</span>
        <strong>${value ?? "нет"}</strong>
      </div>
    `;
  }
  _renderFlow(flow, enabled, snoozedUntil) {
    const snoozed = Boolean(snoozedUntil && !enabled);
    return html`
      <button class="flow ${enabled ? "enabled" : "disabled"}" @click=${() => this._toggleFlow(flow, enabled)}>
        <span class="flow-name">${this._friendlyFlowName(flow)}</span>
        <span class="flow-state">${enabled ? "включено" : snoozed ? `до ${snoozedUntil}` : "выключено"}</span>
      </button>
    `;
  }
  _configurationReport() {
    const current = this._statusEntity()?.attributes?.configuration_check;
    const response = this._configurationResponse;
    const report = response && response.sourceVersion === JSON.stringify(current)
      ? response.report : current;
    return report?.schema_version === 1 && Array.isArray(report.channels) && Array.isArray(report.restrictions) ? report : null;
  }
  _configurationRestrictions(report) {
    if (report) return report.restrictions;
    const attributes = this._statusEntity()?.attributes ?? {};
    return [
      attributes.mute_all === true && { code: "mute_all", title: "Общее заглушение включено", detail: "Обычная доставка ограничена общим выключателем." },
      attributes.maintenance_mode === true && { code: "maintenance", title: "Режим обслуживания", detail: "Действуют ограничения режима обслуживания." },
      attributes.quiet_hours === true && { code: "quiet_hours", title: "Сейчас тихие часы", detail: "Доставка зависит от настроек каналов и правил уведомлений." },
    ].filter(Boolean);
  }
  _renderConfigurationOverview() {
    const report = this._configurationReport();
    const restrictions = this._configurationRestrictions(report);
    return html`<section class="configuration-overview" aria-label="Состояние общей доставки">
      <div class="configuration-heading"><strong>Общая доставка</strong>${this._renderConfigurationRefresh()}</div>
      ${restrictions.length ? html`<ul class="configuration-restrictions">${restrictions.map((item) => html`<li><strong>${item.title}</strong><p>${item.detail}</p>${item.entity_id && this.hass?.states[item.entity_id] ? html`<button class="secondary-action restriction-action" @click=${() => this._openSetting(item.entity_id)}>Открыть настройку</button>` : nothing}</li>`)}</ul>` : html`<p class="policy-hint">${report ? "Активные общие ограничения не обнаружены. Отдельные правила и состояние устройств по-прежнему влияют на доставку." : "Подробный отчёт пока недоступен. Общая готовность доставки не проверена."}</p>`}
      ${report ? html`<div class="configuration-counts"><span>Каналов: ${report.summary?.total ?? report.channels.length}</span><span>Включено: ${report.summary?.enabled ?? "неизвестно"}</span><span>Требуют внимания: ${report.summary?.attention ?? "неизвестно"}</span><span>Проверены не полностью: ${report.summary?.not_checked ?? "неизвестно"}</span></div><p class="policy-hint">Проверено: ${this._formatCheckedAt(report.checked_at)}. Это снимок настроек, а не подтверждение доставки.</p>` : nothing}
      ${this._configurationFeedback ? html`<p class="policy-feedback ${this._configurationFeedback.type}" role=${this._configurationFeedback.type === "error" ? "alert" : "status"}>${this._configurationFeedback.message}</p>` : nothing}
    </section>`;
  }
  _openSetting(entityId) {
    if (typeof entityId !== "string" || !this.hass?.states[entityId]) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId }, bubbles: true, composed: true,
    }));
  }
  _formatCheckedAt(value) {
    if (!value) return "время не указано";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "время не указано" : date.toLocaleString("ru", {
      day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", timeZoneName: "short",
    });
  }
  _renderConfigurationRefresh() {
    return html`<button class="secondary-action" ?disabled=${this._configurationBusy || Object.keys(this._controlActions).some((id) => this._controlPending(id))} @click=${() => this._refreshConfiguration()}>${this._configurationBusy ? "Проверяем настройки…" : "Проверить настройки"}</button>`;
  }
  _renderChannels() {
    const report = this._configurationReport();
    const channels = report?.channels ?? (this._statusEntity()?.attributes?.topology?.channels ?? []).map((channel) => ({ ...channel, status: "not_checked", controls: {}, settings: {}, checks: [] }));
    return this._renderPanelCard("Каналы доставки", "Куда направляются уведомления и какие настройки действуют", html`
      ${!report ? html`<p class="policy-hint">Отчёт проверки ещё недоступен. Показана только объявленная конфигурация; управление появится, когда Herald сообщит точные сущности каналов.</p>` : nothing}
      <div class="channel-controls-grid">${channels.length ? channels.map((channel) => this._renderChannelControl(channel)) : html`<p class="empty">Каналы не представлены в отчёте. Запросите проверку настроек.</p>`}</div>
      ${report?.truncated ? html`<p class="policy-hint">Отчёт ограничен по размеру: часть каналов или проверок не показана.</p>` : nothing}
      ${(report?.limitations ?? ["Доставка уведомлений не выполнялась и не подтверждена."]).map((message) => html`<p class="policy-hint">${message}</p>`)}
    `, nothing, "channel-controls-panel");
  }
  _channelControlId(channel, field) {
    const id = channel.controls?.[field];
    const domain = field === "enabled" ? "switch" : "select";
    return typeof id === "string" && id.startsWith(`${domain}.`) ? id : null;
  }
  _renderChannelControl(channel) {
    const enabledId = this._channelControlId(channel, "enabled");
    const levelId = this._channelControlId(channel, "min_level");
    const enabledEntity = this.hass?.states[enabledId];
    const levelEntity = this.hass?.states[levelId];
    const enabledKnown = this._binaryEntityKnown(enabledEntity);
    const levelKnown = this._entityUsable(levelEntity);
    const declared = channel.enabled === true ? "включён" : channel.enabled === false ? "выключен" : "неизвестно";
    const state = enabledKnown ? (enabledEntity.state === "on" ? "Включён" : "Выключен") : `По отчёту: ${declared}`;
    const statusLabel = ({ configured: "Локально настроен", attention: "Требует внимания", not_checked: "Проверен не полностью" })[channel.status] ?? "Не проверен";
    const type = ({ tts: "Голос", tts_hume: "Голос Hume", tv: "TV", mobile_app: "Телефон", telegram: "Telegram", dashboard: "Панель Herald", persistent_notification: "Уведомления Home Assistant", system_log: "Журнал" })[channel.type] ?? String(channel.type ?? "Тип не указан");
    const quiet = ({ default: "По общему правилу", allow: "Разрешён", block: "Запрещён" })[channel.quiet_hours_policy] ?? String(channel.quiet_hours_policy ?? "Не указано");
    return html`<article class="channel-control-card" aria-label=${`Канал ${this._friendlyChannelName(channel.name)}`}>
      <div class="configuration-heading"><h4>${this._friendlyChannelName(channel.name)}</h4><span class="pill ${channel.status === "attention" ? "danger" : ""}">${statusLabel}</span></div>
      <p class="policy-hint">${type} · ${channel.user ? `Получатель: ${channel.user}` : ["mobile_app", "telegram"].includes(channel.type) ? "Владелец не указан" : "Общий канал"}${channel.rooms?.length ? ` · Комнаты: ${channel.rooms.map((room) => this._friendlyRoomLabel(room)).join(", ")}` : ""}</p>
      <div class="configuration-heading"><strong>${state}</strong><button class="secondary-action" ?disabled=${!enabledKnown || this._controlPending(enabledId)} @click=${() => this._toggleSwitch(enabledId, enabledEntity?.state === "on")}>${this._controlPending(enabledId) ? "Ожидаем…" : enabledKnown && enabledEntity.state === "on" ? "Выключить канал" : "Включить канал"}</button></div>
      ${!enabledKnown ? html`<p class="policy-hint">${enabledId ? "Переключатель канала недоступен в Home Assistant." : "Сущность управления каналом не указана."}</p>` : nothing}
      ${this._renderControlFeedback(enabledId)}
      <label class="language-card channel-level"><span>Минимальная важность</span><select aria-label=${`Минимальная важность: ${this._friendlyChannelName(channel.name)}`} .value=${levelKnown ? levelEntity.state : ""} ?disabled=${!levelKnown || this._controlPending(levelId)} @change=${(event) => this._setSelectOption(levelId, event)}>
        ${!levelKnown ? html`<option value="">Управление недоступно</option>` : (levelEntity.attributes.options ?? []).map((level) => html`<option value=${level} .selected=${levelEntity.state === level}>${this._friendlyLevelLabel(level)}</option>`)}
      </select></label>
      ${!levelKnown ? html`<p class="policy-hint">По отчёту: ${this._friendlyLevelLabel(channel.min_level ?? "unknown")}. ${levelId ? "Сущность порога недоступна." : "Сущность порога не указана."}</p>` : nothing}
      ${this._renderControlFeedback(levelId)}
      <p class="policy-hint">В тихие часы: ${quiet}</p>
      <ul class="channel-checks">${(channel.checks ?? []).map((check) => html`<li class=${check.status === "error" || check.status === "warning" ? "attention" : ""}>${check.message}</li>`)}</ul>
      ${Object.keys(channel.settings ?? {}).length ? html`<details class="policy-provenance"><summary>Откуда настройки на момент проверки</summary><dl>${Object.entries(channel.settings).filter(([, setting]) => setting).map(([field, setting]) => html`<div><dt>${field === "enabled" ? "Включение" : "Минимальная важность"}</dt><dd>${field === "min_level" ? this._friendlyLevelLabel(setting.value) : this._settingValue(setting.value)} · ${this._settingSource(setting.source)}${setting.inherited !== undefined && JSON.stringify(setting.inherited) !== JSON.stringify(setting.value) ? html`<small>Базовое значение: ${field === "min_level" ? this._friendlyLevelLabel(setting.inherited) : this._settingValue(setting.inherited)} · ${this._settingSource(setting.inherited_source)}</small>` : nothing}</dd></div>`)}</dl></details>` : nothing}
    </article>`;
  }
  _invalidateConfiguration() {
    ++this._configurationSequence;
    this._configurationResponse = null;
    this._configurationBusy = false;
    this._configurationFeedback = null;
  }
  async _refreshConfiguration() {
    if (this._configurationBusy || Object.keys(this._controlActions).some((id) => this._controlPending(id))) return;
    const token = ++this._configurationSequence;
    const sourceVersion = JSON.stringify(this._statusEntity()?.attributes?.configuration_check);
    this._configurationBusy = true;
    this._configurationFeedback = null;
    try {
      const report = await this._policyService("configuration_check", {});
      if (token !== this._configurationSequence) return;
      if (sourceVersion !== JSON.stringify(this._statusEntity()?.attributes?.configuration_check)) {
        this._configurationFeedback = { type: "success", message: "Получен более свежий снимок Home Assistant." };
        return;
      }
      if (report.schema_version !== 1 || !Array.isArray(report.channels) || !Array.isArray(report.restrictions)) throw new Error("Herald не вернул поддерживаемый отчёт проверки. Обновите интеграцию и повторите попытку.");
      this._configurationResponse = { report, sourceVersion };
      this._configurationFeedback = { type: "success", message: "Настройки проверены без отправки уведомлений. Фактическая доставка не проверялась." };
    } catch (error) {
      if (token === this._configurationSequence) this._configurationFeedback = { type: "error", message: this._policyError(error) };
    } finally {
      if (token === this._configurationSequence) this._configurationBusy = false;
    }
  }
  _renderLanguage(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._entityUsable(entity);
    const options = entity?.attributes.options ?? DEFAULT_LANGUAGES;
    const label = this._friendlyEntityLabel(entityId, entity);
    return html`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(entityId)} @change=${(event) => this._setLanguage(entityId, event)}>
          ${!known ? html`<option value="">Управление недоступно</option>` : options.map((option) => html`<option value=${option} .selected=${entity.state === option}>${this._friendlyLanguageName(option)}</option>`)}
        </select>
        ${this._renderControlFeedback(entityId)}
      </label>
    `;
  }
  _renderCharacter(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._entityUsable(entity);
    const options = entity?.attributes.options ?? [];
    const label = this._friendlyEntityLabel(entityId, entity);
    return html`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(entityId)} @change=${(event) => this._setSelectOption(entityId, event)}>
          ${!known ? html`<option value="">Управление недоступно</option>` : options.map((option) => html`<option value=${option} .selected=${entity.state === option}>${this._friendlyCharacterName(option)}</option>`)}
        </select>
        ${this._renderControlFeedback(entityId)}
      </label>
    `;
  }
  _renderMute(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._binaryEntityKnown(entity);
    const muted = entity?.state === "on";
    const label = this._friendlyEntityLabel(entityId, entity);
    return html`
      <article class="room-card ${known ? muted ? "disabled" : "enabled" : ""}">
        <div class="room-head">
          <strong>${label}</strong>
          <span class="pill">${!known ? "недоступно" : muted ? "тихо" : "активно"}</span>
        </div>
        <div class="room-meta">
          <span>${!known ? "Состояние заглушения неизвестно. Проверьте сущность в Home Assistant." : muted ? "Уведомления заглушены" : "Уведомления активны"}</span>
        </div>
        <button class="room-toggle" ?disabled=${!known || this._controlPending(entityId)} @click=${() => this._toggleSwitch(entityId, muted)}>
          ${this._controlPending(entityId) ? "Ожидаем…" : muted ? "Включить звук" : "Заглушить"}
        </button>
        ${this._renderControlFeedback(entityId)}
      </article>
    `;
  }
  _renderRoom(item) {
    const sensorEntityId = item?.sensor ?? "";
    const fallbackEntityId = item?.fallback ?? "";
    const sensor = this.hass?.states[sensorEntityId];
    const fallback = this.hass?.states[fallbackEntityId];
    const roomName = item?.room ?? sensor?.attributes?.room ?? fallback?.attributes?.room ?? sensorEntityId ?? fallbackEntityId;
    const sensorOn = sensor?.state === "on";
    const sensorKnown = this._binaryEntityKnown(sensor);
    const fallbackKnown = this._binaryEntityKnown(fallback);
    const fallbackOn = fallback?.state === "on";
    const resolvedFrom = sensor?.attributes?.resolved_from;
    const resolvedFromLabel = resolvedFrom ? this._friendlyResolvedFrom(resolvedFrom) : "не определён";
    return html`
      <article class="room-card ${sensorKnown ? sensorOn ? "occupied" : "idle" : ""}">
        <div class="room-head">
          <strong>${this._friendlyRoomLabel(roomName)}</strong>
          <span class="pill">${!sensorKnown ? "присутствие неизвестно" : sensorOn ? "занято" : "свободно"}</span>
        </div>
        <div class="room-meta">
          <span>Сенсор: ${this._friendlyBinaryState(sensor?.state)}</span>
          <span>Fallback: ${this._friendlyBinaryState(fallback?.state)}</span>
          <span>Источник: ${resolvedFromLabel}</span>
        </div>
        ${fallbackEntityId ? html`
              <button class="room-toggle" ?disabled=${!fallbackKnown || this._controlPending(fallbackEntityId)} @click=${() => this._toggleSwitch(fallbackEntityId, fallbackOn)}>
                ${!fallbackKnown ? "Fallback недоступен" : this._controlPending(fallbackEntityId) ? "Ожидаем…" : fallbackOn ? "Выключить fallback" : "Включить fallback"}
              </button>
            ` : nothing}
        ${this._renderControlFeedback(fallbackEntityId)}
      </article>
    `;
  }
  _renderNotification(item) {
    const message = String(item.message ?? "");
    const compact = this._config?.compact === true;
    if (compact) {
      const preview = message.replace(/\s+/g, " ").trim();
      return html`
        <details class="event-entry">
          <summary>
            <ha-icon icon="mdi:bell-outline"></ha-icon>
            <span class="event-preview">
              <strong>${this._friendlyDeliveryItemTitle(item, "Событие дома")}</strong>
              ${preview ? html`<span class="event-description">${preview.length > 110 ? `${preview.slice(0, 110)}…` : preview}</span>` : nothing}
            </span>
            <time datetime=${String(item.timestamp ?? "")} title=${this._notificationTime(item.timestamp)}>${this._notificationTime(item.timestamp, true)}</time>
            <ha-icon class="event-chevron" icon="mdi:chevron-down"></ha-icon>
          </summary>
          <div class="event-content">
            <span class="event-date">${this._notificationTime(item.timestamp)}</span>
            <p class="event-text">${message}</p>
          </div>
        </details>
      `;
    }
    return html`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._notificationTime(item.timestamp)} · ${this._friendlyDeliveryItemTitle(item, "Herald")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p class="event-text">${message}</p>
      </article>
    `;
  }
  _recentLimit() {
    const limit = this._config?.max_items;
    return Number.isInteger(limit) && limit > 0 ? Math.min(limit, 8) : 8;
  }
  _notificationTime(timestamp, timeOnly = false) {
    if (!timestamp) return "Время неизвестно";
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return "Время неизвестно";
    return new Intl.DateTimeFormat(this.hass?.language || "ru", {
      ...(timeOnly ? {} : { day: "2-digit", month: "2-digit" }),
      hour: "2-digit", minute: "2-digit",
      timeZone: this.hass?.config?.time_zone,
    }).format(date);
  }
  _renderQueuedItem(item) {
    const channels = Array.isArray(item.channels) && item.channels.length ? item.channels.join(", ") : "авто";
    return html`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "Уведомление в очереди")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${this._formatChannels(Array.isArray(item.channels) ? item.channels : []) || channels}</span>
          <span>${String(item.enqueued_at ?? item.timestamp ?? "")}</span>
          <span>окно ${item.summary_window_seconds ?? 0} c</span>
        </footer>
      </article>
    `;
  }
  _renderFeedItem(item) {
    const channel = item.channel ?? "dashboard";
    const room = item.room ?? "n/a";
    return html`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "Лента панели")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${this._friendlyChannelName(channel)}</span>
          <span>${room === "n/a" ? "без комнаты" : this._friendlyRoomLabel(room)}</span>
          <span>${String(item.timestamp ?? "")}</span>
        </footer>
      </article>
    `;
  }
  _renderPolicyTable(pageData, totalItems) {
    const selected = pageData.items.find((item) => item.notification_key === this._policyExpanded);
    return html`
      ${selected ? html`<div class="policy-editor-container">${this._renderPolicyEditor(selected)}</div>` : nothing}
      <div class="policy-table-wrap">
        <table class="policy-table">
          <thead>
            <tr>
              <th>Уведомление</th>
              <th>Семейство</th>
              <th>Состояние</th>
              <th>Доставка</th>
              <th>Каналы</th>
              <th>Последнее событие</th>
              <th>Источники</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            ${pageData.items.map((item) => this._renderPolicyTableRow(item))}
          </tbody>
        </table>
      </div>
      <div class="policy-pager">
        <div class="policy-meta">
          <span>Показано ${(pageData.items ?? []).length} из ${totalItems}</span>
          <span>Страница ${pageData.page} из ${pageData.totalPages || 1}</span>
        </div>
        <div class="policy-actions">
          <button class="secondary-action" ?disabled=${pageData.page <= 1} @click=${() => this._setPolicyPage(pageData.page - 1)}>
            Назад
          </button>
          <button class="secondary-action" ?disabled=${pageData.page >= pageData.totalPages} @click=${() => this._setPolicyPage(pageData.page + 1)}>
            Дальше
          </button>
        </div>
      </div>
    `;
  }
  _renderPolicyTableRow(item) {
    item = this._policyItem(item);
    const key = String(item.notification_key ?? "");
    const effective = item.effective ?? {};
    const policy = item.policy ?? {};
    const lastEventAt = item.last_seen_at ?? item.family_last_event_at ?? "нет";
    const titleLabel = this._friendlyNotificationTitle(item);
    const routeLabel = this._friendlyRouteLabel(item);
    const eventLabel = this._friendlyEventLabel(item.family_last_event_code ?? "n/a");
    const isCustomized = this._policyCustomized(item);
    const expanded = this._policyExpanded === key;
    return html`
      <tr class="policy-row ${item.active ? "is-active" : ""} ${item.active_attention ? "is-attention" : ""}">
        <td>
          <div class="policy-row-main">
            <strong>${titleLabel}</strong>
            ${item.selected_title_ru && item.selected_title_ru !== titleLabel ? html`<div class="policy-table-subline">${item.selected_title_ru}</div>` : nothing}
          </div>
        </td>
        <td>
          <span class="pill">${this._friendlyFamilyLabel(item.family ?? "general")}</span>
        </td>
        <td>
          <div class="policy-status-stack">
            <span class="policy-status ${effective.enabled ? "enabled" : "disabled"}">${effective.enabled ? "вкл" : "выкл"}</span>
            ${item.active ? html`<span class="pill active">активно</span>` : nothing}
            ${item.active_attention ? html`<span class="pill danger">внимание</span>` : nothing}
            ${isCustomized ? html`<span class="pill custom">кастом</span>` : nothing}
            ${item.selected_state_ru ? html`<span class="policy-table-subline">${item.selected_state_ru}</span>` : nothing}
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${this._friendlyDeliveryMode(effective.delivery_mode ?? "inherit")}</strong>
            <div class="policy-table-subline">${routeLabel}</div>
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${this._policyRouteSummary(item.policy ?? {}, item.default_flow)}</strong>
            ${isCustomized ? html`<div class="policy-table-subline">${this._policyTargetSummary(item.policy, item)}</div>` : nothing}
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${eventLabel}</strong>
            <div class="policy-table-subline">${lastEventAt}</div>
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${item.source_count ?? (item.source_files?.length ?? 0)}</strong>
            <div class="policy-table-subline">${this._friendlySourceCount(item.source_count ?? (item.source_files?.length ?? 0))}</div>
          </div>
        </td>
        <td>
          <div class="policy-inline-actions">
            <button class="secondary-action" @click=${() => this._togglePolicyExpanded(key)}>
              ${expanded ? "Скрыть" : "Редактировать"}
            </button>
            <button class="secondary-action" ?disabled=${this._busyPolicy === key} @click=${() => this._togglePolicyEnabled(item)}>
              ${effective.enabled ? "Выключить" : "Включить по общему правилу"}
            </button>
          </div>
        </td>
      </tr>
    `;
  }
  _renderPolicyEditor(item) {
    item = this._policyItem(item);
    const key = String(item.notification_key ?? "");
    const saved = this._normalizedPolicy(item.policy);
    const draft = this._policyPayload(item);
    const dirty = this._policyDirty(item);
    const busy = Boolean(this._busyPolicy);
    const feedback = this._policyFeedback[key];
    const preview = this._policyPreviews[key];
    const scenario = this._policyScenarios[key] ?? "current";
    const availableChannels = item.available_channels ?? [];
    const userOptions = this._policyTargetOptions(item, "users", draft.users ?? []);
    const roomOptions = this._policyTargetOptions(item, "rooms", draft.target_room ? [draft.target_room] : []);
    const last = item.last_decision;
    return html`
      <article class="policy-card policy-card-editor">
        <div class="policy-editor-heading">
          <div>
            <h4 tabindex="-1">${this._friendlyNotificationTitle(item)}</h4>
            <p class="policy-hint">Сохранено: ${this._policyRouteSummary(saved, item.default_flow)}</p>
            <p class="policy-hint policy-saved-targets">${this._policyTargetSummary(saved, item)}</p>
          </div>
          <span class="pill ${dirty ? "custom" : "active"}">${dirty ? "Есть изменения" : "Сохранённое правило"}</span>
        </div>
        ${last ? html`<div class="policy-last-decision"><strong>Последнее решение</strong><p>${last.summary ?? last.reason ?? "Нет объяснения"}</p>${last.at ? html`<small>${last.at}</small>` : nothing}</div>` : nothing}
        <label class="policy-enabled"><input type="checkbox" .checked=${draft.enabled && draft.delivery_mode !== "disabled"} @change=${(event) => this._setPolicyDraft(key, "enabled", event.target.checked, event.target.checked && draft.delivery_mode === "disabled" ? { delivery_mode: "inherit" } : {})} /> Доставлять это уведомление</label>
        <label class="language-card policy-field">
          <span>Как доставлять</span>
          <select aria-label="Как доставлять" .value=${draft.delivery_mode} @change=${(event) => this._setPolicyDraft(key, "delivery_mode", event.target.value)}>
            ${["inherit", "disabled", "text_only", "voice_only", "push_only", "custom"].map((mode) => html`<option value=${mode} .selected=${draft.delivery_mode === mode}>${this._friendlyDeliveryMode(mode)}</option>`)}
          </select>
        </label>
        <p class="policy-rule-summary">${this._policyRouteSummary(draft, item.default_flow)}</p>
        ${draft.delivery_mode === "inherit" ? html`<p class="policy-hint">Маршрут определится общими настройками, потоком и присутствием. Проверка ниже покажет результат для выбранной ситуации.</p>` : nothing}
        ${draft.delivery_mode === "custom" ? html`
          <fieldset class="policy-channel-fieldset"><legend>Выбранные каналы</legend>
            <div class="policy-channel-grid">
              ${availableChannels.map((channel) => html`<button type="button" class="policy-channel ${draft.channels.includes(channel) ? "selected" : ""}" aria-pressed=${draft.channels.includes(channel)} @click=${() => this._togglePolicyDraftChannel(key, channel, item)}>${this._friendlyChannelName(channel)}</button>`)}
            </div>
            ${!availableChannels.length ? html`<p class="policy-hint">Каналы не найдены. Проверьте настройки устройств.</p>` : nothing}
          </fieldset>` : nothing}
        <div class="policy-target-grid">
          <section class="policy-rule-section" aria-label="Кому доставлять">
            <h5>Кому</h5>
            <label class="language-card policy-field"><span>Получатели личных сообщений</span>
              <select aria-label="Получатели личных сообщений" .value=${draft.users === null ? "inherit" : "selected"} @change=${(event) => this._setPolicyDraft(key, "users", event.target.value === "inherit" ? null : [])}>
                <option value="inherit">По общему правилу</option><option value="selected">Выбрать получателей</option>
              </select>
            </label>
            ${draft.users !== null ? html`<div class="policy-channel-grid policy-user-options" role="group" aria-label="Выбранные получатели">
              ${userOptions.map((option) => html`<button type="button" class="policy-channel ${draft.users.includes(option.value) ? "selected" : ""}" aria-pressed=${draft.users.includes(option.value)} @click=${() => this._togglePolicyDraftUser(key, option.value, item)}>${option.label}</button>`)}
            </div>${!draft.users.length ? html`<p class="policy-hint policy-empty-recipients">Получатели не выбраны — доставки не будет.</p>` : nothing}` : nothing}
            <p class="policy-hint">Выбор ограничивает личные каналы. При доставке общие каналы панели и журнала остаются общими. Локальный голос доступен только для подходящих получателей дома; его могут услышать и другие люди.</p>
          </section>
          <section class="policy-rule-section" aria-label="Где доставлять">
            <h5>Где</h5>
            <label class="language-card policy-field"><span>Комната для голоса и TV</span>
              <select aria-label="Комната для голоса и TV" .value=${draft.target_room ?? ""} @change=${(event) => this._setPolicyDraft(key, "target_room", event.target.value || null)}>
                <option value="" .selected=${draft.target_room === null}>Автоматически по общему правилу</option>
                ${roomOptions.map((option) => html`<option value=${option.value} .selected=${draft.target_room === option.value}>${option.label}</option>`)}
              </select>
            </label>
            <p class="policy-hint">Выбранная комната используется строго для голоса и TV, без перехода в другую комнату. Личные каналы получателей не меняются.</p>
          </section>
        </div>
        <section class="policy-rule-section" aria-label="Когда доставлять">
          <h5>Когда</h5>
          <div class="policy-target-grid">
            <label class="language-card policy-field"><span>Присутствие дома</span>
              <select aria-label="Присутствие дома" .value=${draft.presence} @change=${(event) => this._setPolicyDraft(key, "presence", event.target.value)}>
                <option value="any">При любом присутствии</option><option value="someone_home">Только когда кто-то дома</option><option value="nobody_home">Только когда никого дома</option>
              </select>
            </label>
            <label class="language-card policy-field"><span>В тихие часы</span>
              <select aria-label="В тихие часы" .value=${draft.quiet_hours} @change=${(event) => this._setPolicyDraft(key, "quiet_hours", event.target.value)}>
                <option value="inherit">По общему правилу</option><option value="text_only">Только текст</option><option value="mute">Не доставлять</option>
              </select>
            </label>
          </div>
          <p class="policy-hint">Условия проверяются в момент события. Отложенная отправка и расписание здесь не задаются.</p>
        </section>
        <p class="policy-draft-targets"><strong>${dirty ? "Черновик" : "Правило"}:</strong> ${this._policyTargetSummary(draft, item)}</p>
        <details class="policy-advanced">
          <summary>Дополнительно: важность и интервал</summary>
          <div class="policy-grid policy-grid-advanced">
            <label class="language-card policy-field"><span>Важность вместо уровня события</span>
              <select .value=${draft.level_override} @change=${(event) => this._setPolicyDraft(key, "level_override", event.target.value)}>
                ${["", "debug", "info", "notice", "warning", "critical", "security", "ai", "system"].map((level) => html`<option value=${level}>${level ? this._friendlyLevelLabel(level) : "Уровень самого события"}</option>`)}
              </select>
            </label>
            <label class="language-card policy-field"><span>Минимальный интервал, секунд</span>
              <input type="number" min="0" max="86400" step="1" .value=${String(draft.cooldown_override ?? "")} placeholder="По общему правилу" @input=${(event) => this._setPolicyDraft(key, "cooldown_override", event.target.value)} />
            </label>
          </div>
          <p class="policy-hint">Пустой интервал использует настройку потока; 0 отключает это ограничение для уведомления.</p>
        </details>
        <label class="language-card policy-field"><span>Заметка к правилу</span><input .value=${draft.notes} placeholder="Почему выбрана эта настройка" @input=${(event) => this._setPolicyDraft(key, "notes", event.target.value)} /></label>
        <section class="policy-preview" aria-label="Проверка доставки">
          <div class="policy-preview-heading"><strong>Проверка без отправки</strong><span class="policy-hint">${dirty ? "Используется несохранённый черновик" : "Используется сохранённое правило"}</span></div>
          <div class="policy-preview-controls">
            <label>Ситуация<select aria-label="Ситуация" .value=${scenario} @change=${(event) => this._setPolicyScenario(key, event.target.value)}>
              <option value="current">Сейчас</option><option value="quiet_hours">Тихие часы</option><option value="away">Никого дома</option>
            </select></label>
            <button class="secondary-action" ?disabled=${preview?.loading} @click=${() => this._previewPolicy(item)}>${preview?.loading ? "Проверяем…" : "Проверить без отправки"}</button>
          </div>
          <p class="policy-hint">Уведомления и команды устройствам не отправляются. ${scenario === "quiet_hours" ? "Моделируется правило тихих часов; время и условия автоматизаций остаются текущими." : scenario === "away" ? "Моделируется отсутствие людей дома; состояния устройств и время остаются текущими." : "Используются текущие состояния устройств и время."}</p>
          ${preview?.error ? html`<p class="policy-feedback error" role="alert">${preview.error}</p>` : nothing}
          ${preview?.result ? this._renderPolicyExplanation(preview.result) : nothing}
        </section>
        ${feedback ? html`<p class="policy-feedback ${feedback.type}" role=${feedback.type === "error" ? "alert" : "status"}>${feedback.message}</p>` : nothing}
        <div class="policy-actions">
          <button class="secondary-action primary-action" ?disabled=${busy || !dirty} @click=${() => this._savePolicy(item)}>${this._busyPolicy === key ? "Сохраняем…" : "Сохранить изменения"}</button>
          <button class="secondary-action" ?disabled=${busy || !dirty} @click=${() => this._discardPolicyDraft(key)}>Отменить изменения</button>
          <button class="secondary-action" ?disabled=${busy} @click=${() => this._resetPolicy(item)}>Вернуть общее правило</button>
        </div>
      </article>
    `;
  }
  _renderPolicyExplanation(result) {
    const explanation = result.explanation;
    return html`<div class="policy-explanation" aria-live="polite">
      <strong>${explanation.summary}</strong>
      <p>${explanation.channels?.length ? `Каналы: ${this._formatChannels(explanation.channels)}` : "Доставка не запланирована"}</p>
      ${explanation.steps?.length ? html`<ol>${explanation.steps.map((step) => html`<li><strong>${step.label}</strong> ${step.detail}</li>`)}</ol>` : nothing}
      ${[...new Set([...(explanation.warnings ?? []), ...(result.warnings ?? [])])].map((warning) => html`<p class="policy-hint">${warning}</p>`)}
      ${Object.keys(result.effective_settings ?? {}).length ? html`<details class="policy-provenance"><summary>Откуда настройки</summary><dl>${Object.entries(result.effective_settings).map(([key, setting]) => html`<div><dt>${this._settingLabel(key)}</dt><dd>${this._settingValue(setting.value)} · ${this._settingSource(setting.source)}${setting.inherited !== undefined && JSON.stringify(setting.inherited) !== JSON.stringify(setting.value) ? html`<small>Базовое значение: ${this._settingValue(setting.inherited)} · ${this._settingSource(setting.inherited_source)}</small>` : nothing}</dd></div>`)}</dl></details>` : nothing}
      <small>Это проверка черновика без отправки. Реальный результат может измениться вместе с состоянием дома.</small>
    </div>`;
  }
  _settingSource(source) {
    return ({ options: "Настройки интеграции", runtime: "Ручное изменение", restored: "Сохранённое переопределение", default: "По умолчанию", yaml: "YAML", entry: "Начальная настройка", legacy: "Прежняя настройка" })[source] ?? "Источник не указан";
  }
  _settingValue(value) {
    if (value === true) return "Включено";
    if (value === false) return "Выключено";
    return value == null ? "Не задано" : String(value);
  }
  _settingLabel(key) {
    const [kind, name] = key.split(":", 2);
    const label = ({ flow_enabled: "Поток", flow_cooldown: "Интервал потока, с", flow_dedup_window: "Повторы потока, с", channel_enabled: "Канал", channel_min_level: "Порог важности канала", maintenance_min_level: "Порог режима обслуживания" })[kind] ?? kind;
    return name ? `${label}: ${kind.startsWith("flow_") ? this._friendlyFlowName(name) : this._friendlyChannelName(name)}` : label;
  }
  async _toggleFlow(flow, enabled) {
    if (!this.hass || this._busyFlow === flow) {
      return;
    }
    this._busyFlow = flow;
    try {
      await this.hass.callService("herald", "set_flow_state", {
        flow,
        enabled: !enabled
      });
    } finally {
      this._busyFlow = "";
    }
  }
  async _setLanguage(entityId, event) {
    if (!this.hass) {
      return;
    }
    await this._setSelectOption(entityId, event);
  }
  async _setSelectOption(entityId, event) {
    const entity = this.hass?.states[entityId];
    const option = event.target.value;
    // A native select changes before @change; restore the last HA state until acknowledged.
    event.target.value = this._entityUsable(entity) ? entity.state : "";
    if (!entityId?.startsWith("select.") || !this._entityUsable(entity) || !(entity.attributes.options ?? []).includes(option)) {
      this._controlActions = { ...this._controlActions, [entityId]: { phase: "error", message: "Сущность или выбранное значение недоступны в Home Assistant." } };
      return;
    }
    await this._runControlAction(entityId, option, "select", "select_option", { entity_id: entityId, option });
  }
  async _toggleSwitch(entityId, enabled) {
    const entity = this.hass?.states[entityId];
    if (!entityId?.startsWith("switch.") || !this._binaryEntityKnown(entity)) {
      this._controlActions = { ...this._controlActions, [entityId]: { phase: "error", message: "Переключатель недоступен в Home Assistant." } };
      return;
    }
    const next = entity.state === "on" ? "off" : "on";
    await this._runControlAction(entityId, next, "switch", next === "on" ? "turn_on" : "turn_off", { entity_id: entityId });
  }
  _entityUsable(entity) {
    return Boolean(entity && entity.state != null && !["", "unknown", "unavailable"].includes(entity.state));
  }
  _binaryEntityKnown(entity) {
    return entity?.state === "on" || entity?.state === "off";
  }
  _controlPending(entityId) {
    return ["sending", "awaiting"].includes(this._controlActions[entityId]?.phase);
  }
  _renderControlFeedback(entityId) {
    const action = this._controlActions[entityId];
    if (!action) return nothing;
    const message = action.message ?? ({ sending: "Сохраняем…", awaiting: "Команда принята. Ожидаем новое состояние Home Assistant.", success: "Изменение подтверждено Home Assistant." })[action.phase];
    return html`<p class="policy-feedback ${action.phase === "error" ? "error" : "success"}" role=${action.phase === "error" ? "alert" : "status"}>${message}</p>`;
  }
  _clearControlActions() {
    for (const timer of this._controlTimers.values()) clearTimeout(timer);
    this._controlTimers.clear();
    this._controlActions = {};
  }
  _finishControlAction(entityId, token, phase, message) {
    if (this._controlActions[entityId]?.token !== token) return;
    clearTimeout(this._controlTimers.get(entityId));
    this._controlTimers.delete(entityId);
    this._controlActions = { ...this._controlActions, [entityId]: { ...this._controlActions[entityId], phase, message } };
  }
  _reconcileControlActions() {
    for (const [entityId, action] of Object.entries(this._controlActions)) {
      const state = this.hass?.states[entityId]?.state;
      const matches = state === action.expected || (entityId.startsWith("number.") && this._entityUsable(this.hass?.states[entityId]) && Number(state) === Number(action.expected));
      if (action.phase === "awaiting" && matches) this._finishControlAction(entityId, action.token, "success");
    }
  }
  _expireControlAction(entityId, token) {
    if (!this._controlPending(entityId)) return;
    this._finishControlAction(entityId, token, "error", "Подтверждение от Home Assistant не получено. Показано последнее известное состояние; проверьте его перед повтором.");
  }
  async _runControlAction(entityId, expected, domain, service, data) {
    if (!this.hass || this._controlPending(entityId) || this.hass.states[entityId]?.state === expected) return;
    const token = ++this._controlSequence;
    this._invalidateConfiguration();
    this._configurationFeedback = { type: "success", message: "Настройки меняются. После подтверждения обновите проверку." };
    this._controlActions = { ...this._controlActions, [entityId]: { token, phase: "sending", expected } };
    const timer = setTimeout(() => this._expireControlAction(entityId, token), 10000);
    timer?.unref?.();
    this._controlTimers.set(entityId, timer);
    try {
      await this.hass.callService(domain, service, data);
      if (this._controlActions[entityId]?.token !== token || !this._controlPending(entityId)) return;
      this._controlActions = { ...this._controlActions, [entityId]: { token, phase: "awaiting", expected } };
      this._reconcileControlActions();
    } catch (error) {
      if (this._controlPending(entityId)) this._finishControlAction(entityId, token, "error", this._policyError(error));
    }
  }
  _policyDraftValue(notificationKey, field, fallback) {
    return this._policyDrafts?.[notificationKey]?.[field] ?? fallback;
  }
  _policyDraftChannels(notificationKey, item) {
    return this._policyPayload(item).channels;
  }
  _setPolicyDraft(notificationKey, field, value, relatedFields = {}) {
    this._policyDrafts = { ...this._policyDrafts, [notificationKey]: { ...(this._policyDrafts[notificationKey] ?? {}), ...relatedFields, [field]: value } };
    this._policyRevisions[notificationKey] = (this._policyRevisions[notificationKey] ?? 0) + 1;
    this._clearPolicyPreview(notificationKey);
    this._policyFeedback = { ...this._policyFeedback, [notificationKey]: undefined };
  }
  _togglePolicyDraftChannel(notificationKey, channel, item) {
    const current = this._policyDraftChannels(notificationKey, item);
    const next = current.includes(channel) ? current.filter((entry) => entry !== channel) : [...current, channel];
    this._setPolicyDraft(notificationKey, "channels", next);
  }
  _togglePolicyDraftUser(notificationKey, user, item) {
    const current = this._policyPayload(item).users ?? [];
    this._setPolicyDraft(notificationKey, "users", current.includes(user) ? current.filter((value) => value !== user) : [...current, user]);
  }
  _policyTargetOptions(item, kind, selected = []) {
    const registry = this._statusEntity()?.attributes?.notification_registry ?? {};
    const options = item[`available_${kind}`] ?? registry[kind === "users" ? "user_options" : "room_options"] ?? [];
    const known = new Map(options.filter((option) => typeof option?.value === "string" && option.value).map((option) => [option.value, { value: option.value, label: String(option.label ?? (kind === "rooms" ? this._friendlyRoomLabel(option.value) : option.value)) }]));
    for (const value of selected) if (!known.has(value)) known.set(value, { value, label: `${value} (недоступно)` });
    return [...known.values()];
  }
  _policyTargetSummary(policy, item) {
    const normalized = this._normalizedPolicy(policy);
    const users = normalized.users === null ? "Получатели по общему правилу" : normalized.users.length
      ? `Получатели: ${this._policyTargetOptions(item, "users", normalized.users).filter((option) => normalized.users.includes(option.value)).map((option) => option.label).join(", ")}`
      : "Получатели не выбраны — доставки не будет";
    const room = normalized.target_room ? `Голос и TV: ${this._policyTargetOptions(item, "rooms", [normalized.target_room]).find((option) => option.value === normalized.target_room).label}` : "Комната автоматически";
    const presence = ({ any: "При любом присутствии", someone_home: "Только когда кто-то дома", nobody_home: "Только когда никого дома" })[normalized.presence] ?? normalized.presence;
    const quiet = ({ inherit: "Тихие часы по общему правилу", text_only: "В тихие часы только текст", mute: "В тихие часы без доставки" })[normalized.quiet_hours] ?? normalized.quiet_hours;
    return [users, room, presence, quiet].join(" · ");
  }
  _policyCustomized(item) {
    const policy = this._normalizedPolicy(item.policy);
    return !policy.enabled || policy.delivery_mode !== "inherit" || Boolean(policy.level_override) || policy.cooldown_override !== "" || Boolean(policy.notes) || policy.users !== null || policy.target_room !== null || policy.presence !== "any" || policy.quiet_hours !== "inherit";
  }
  _friendlyFlowName(flow) {
    const labels = {
      security_alerts: "Безопасность",
      system_events: "Системные события",
      device_alerts: "Устройства",
      ai_events: "ИИ-события",
      energy_events: "Энергия",
      camera_alerts: "Камеры",
      timer_notifications: "Таймеры"
    };
    return labels[flow] ?? this._humanizeCode(flow);
  }
  _friendlyLevelLabel(level) {
    const labels = {
      debug: "отладка",
      info: "инфо",
      notice: "обычное",
      warning: "важное",
      critical: "критичное",
      security: "безопасность",
      ai: "ИИ",
      system: "система"
    };
    return labels[level] ?? this._humanizeCode(level);
  }
  _friendlyChannelName(channel) {
    const labels = {
      system_log_default: "Системный лог",
      persistent_default: "Постоянные уведомления",
      telegram_default: "Telegram",
      voice_auto: "Голос: авто",
      dashboard_default: "Лента Herald",
      push_default: "Push",
      tv_default: "TV"
    };
    return labels[channel] ?? this._humanizeCode(channel);
  }
  _friendlyChannelFamilyLabel(value) {
    const labels = {
      voice: "Голос",
      push: "Push",
      tv: "TV",
      dashboard: "Панель",
      persistent: "Постоянные",
      system_log: "Системный лог",
      mobile_app: "Мобильные"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyFamilyLabel(value) {
    const labels = {
      general: "Общее",
      ai: "ИИ",
      ai_foundation: "Базовый ИИ",
      energy: "Энергия",
      energy_policy: "Тарифы и бюджет",
      energy_runtime: "Энергосигналы",
      reports: "Брифинги и отчеты",
      system: "Система",
      security: "Безопасность",
      recovery: "Восстановление",
      recovery_ops: "Восстановление",
      timer: "Таймер",
      guests: "Гости",
      adult_content: "18+",
      environment: "Экология",
      geo: "Гео",
      washer: "Стиралка",
      copilot: "Copilot",
      home_mode: "Режим дома",
      device_ops: "Операции устройств",
      manual_lights: "Ручной свет",
      household_power: "Фоновая нагрузка",
      tts: "Озвучка",
      alarm_clock: "Будильник",
      ev_dispatcher: "EV-диспетчер",
      camera: "Камеры"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyDeliveryMode(value) {
    const labels = {
      inherit: "По общему правилу",
      disabled: "Отключить",
      text_only: "Только текст",
      voice_only: "Только голос",
      push_only: "Только push",
      custom: "Выбрать каналы"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyEntityLabel(entityId, entity) {
    const rawName = String(entity?.attributes?.friendly_name ?? "").trim();
    if (rawName && rawName !== entityId && !this._looksSystemLabel(rawName)) {
      return rawName;
    }
    const objectId = String(entityId).split(".").slice(1).join(".");
    const flowMatch = objectId.match(/^herald_flow_(.+)$/);
    if (flowMatch) {
      return `Поток · ${this._friendlyFlowName(flowMatch[1])}`;
    }
    const channelFamilyMatch = objectId.match(/^herald_channel_family_(.+)$/);
    if (channelFamilyMatch) {
      return `Семейство каналов · ${this._friendlyChannelFamilyLabel(channelFamilyMatch[1])}`;
    }
    const match = objectId.match(/^herald_user_(.+)_(language|character|silent)$/);
    if (match) {
      const user = this._friendlyUserSlug(match[1]);
      const suffixLabels = {
        language: "Язык",
        character: "Персонаж",
        silent: "Звук"
      };
      return `${user} · ${suffixLabels[match[2]]}`;
    }
    return this._humanizeCode(objectId || entityId);
  }
  _statusEntity() {
    return this.hass?.states?.[this._config?.status_entity ?? DEFAULT_STATUS_ENTITY];
  }
  _containsCyrillic(value) {
    return /[А-Яа-яЁё]/.test(String(value ?? ""));
  }
  _looksSystemLabel(value) {
    const raw = String(value ?? "").trim().toLowerCase();
    if (!raw) {
      return true;
    }
    return raw.startsWith("select.herald_") || raw.startsWith("switch.herald_") || raw.startsWith("sensor.") || raw.startsWith("binary_sensor.") || raw.startsWith("herald ") || raw.includes("_");
  }
  _friendlyUserSlug(slug) {
    const normalized = String(slug ?? "").trim().toLowerCase();
    const exact = {
      abrikos: "Абрикос",
      aleksandr_meshcheriakov: "Александр",
      victoria_meshchryakovf: "Виктория"
    };
    if (exact[normalized]) {
      return exact[normalized];
    }
    const topologyUsers = this._statusEntity()?.attributes?.topology?.users ?? [];
    const matchedUser = topologyUsers.find((item) => String(item?.slug ?? "").trim().toLowerCase() === normalized);
    const matchedName = String(matchedUser?.name ?? "").trim();
    if (matchedName && this._containsCyrillic(matchedName)) {
      return matchedName;
    }
    return this._humanizeCode(normalized);
  }
  _friendlyLanguageName(value) {
    const labels = {
      ru: "Русский",
      en: "Английский",
      es: "Испанский",
      fr: "Французский",
      de: "Немецкий",
      ca: "Каталанский"
    };
    return labels[String(value ?? "").trim().toLowerCase()] ?? String(value ?? "");
  }
  _friendlyCharacterName(value) {
    const labels = {
      domovoy: "Домовой",
      hestia: "Hestia",
      plugins: "Плагины",
      jarvis: "Jarvis"
    };
    return labels[String(value ?? "").trim().toLowerCase()] ?? this._humanizeCode(value);
  }
  _friendlyNotificationTitle(item) {
    const selectedTitle = String(item?.selected_title_ru ?? "").trim();
    if (selectedTitle && this._containsCyrillic(selectedTitle)) {
      return selectedTitle;
    }
    const rawTitle = String(item?.title ?? "").trim();
    if (rawTitle && this._containsCyrillic(rawTitle) && !this._looksSystemLabel(rawTitle)) {
      return rawTitle;
    }
    const codeTitle = this._friendlyEventLabel(item?.notification_key ?? "");
    if (codeTitle && codeTitle !== "Нет события") {
      return codeTitle;
    }
    return rawTitle || String(item?.notification_key ?? "Уведомление");
  }
  _friendlyDeliveryItemTitle(item, fallbackTitle = "Уведомление") {
    const rawTitle = String(item?.title ?? "").trim();
    if (rawTitle && this._containsCyrillic(rawTitle) && !this._looksSystemLabel(rawTitle)) {
      return rawTitle;
    }
    const eventLabel = this._friendlyEventLabel(item?.event ?? rawTitle);
    if (eventLabel && eventLabel !== "Нет события") {
      return eventLabel;
    }
    return rawTitle || fallbackTitle;
  }
  _friendlyRoomLabel(value) {
    const raw = String(value ?? "").trim();
    if (!raw || raw === "n/a") {
      return "без комнаты";
    }
    return this._humanizeCode(raw);
  }
  _friendlyRouteLabel(item) {
    const entityId = String(item?.selected_entity ?? "").trim();
    if (!entityId || entityId === "n/a") {
      return "Маршрут уточняется при проверке";
    }
    const entity = this.hass?.states?.[entityId];
    const friendlyName = String(entity?.attributes?.friendly_name ?? "").trim();
    if (friendlyName && !this._looksSystemLabel(friendlyName)) {
      return friendlyName;
    }
    const objectId = entityId.split(".").slice(1).join(".");
    const familyGuess = String(item?.family ?? "").trim();
    const familyLabel = familyGuess ? this._friendlyFamilyLabel(familyGuess) : "";
    if (objectId.endsWith("_alert_selected") || objectId.endsWith("_selected")) {
      return familyLabel ? `Маршрут · ${familyLabel}` : `Маршрут · ${this._humanizeCode(objectId.replace(/_alert_selected$/, "").replace(/_selected$/, ""))}`;
    }
    if (objectId.endsWith("_attention_required")) {
      return familyLabel ? `Внимание · ${familyLabel}` : `Внимание · ${this._humanizeCode(objectId.replace(/_attention_required$/, ""))}`;
    }
    return this._humanizeCode(objectId || entityId);
  }
  _friendlyEventLabel(code) {
    if (!code || code === "n/a" || code === "idle" || code === "none") {
      return "Нет события";
    }
    const normalized = String(code ?? "").trim().toLowerCase();
    const exact = {
      washer_started_expensive_tariff: "Стиралка запущена на дорогом тарифе",
      washer_finished: "Стирка завершена",
      wifi_guest_detected: "Обнаружен гостевой Wi-Fi",
      adult_content_enabled: "Режим 18+ включен",
      adult_content_disabled: "Режим 18+ выключен",
      morning_briefing: "Утренний брифинг",
      evening_briefing: "Вечерний брифинг",
      daily_report: "Ежедневный отчет",
      weekly_report: "Недельный отчет",
      geomagnetic_storm: "Геомагнитная буря",
      critical_co2: "Критический CO2",
      ollama_unavailable: "Ollama недоступен",
      power_overload: "Перегрузка мощности",
      grid_quality_problem: "Проблема качества сети",
      grid_quality_recovered: "Качество сети восстановлено",
      jump_expensive: "Скачок нагрузки на дорогом тарифе",
      punta_started: "Начался пиковый тариф",
      valle_started: "Начался ночной тариф",
      report_ready: "Отчет готов",
      report_skipped: "Отчет пропущен",
      timer_status: "Статус таймера",
      timer_finished: "Таймер завершен",
      timer_cancelled: "Таймер отменен"
    };
    if (exact[normalized]) {
      return exact[normalized];
    }
    const tokenLabels = {
      ai: "ИИ",
      co2: "CO2",
      pm10: "PM10",
      pm25: "PM2.5",
      ev: "EV",
      tts: "TTS",
      wifi: "Wi-Fi",
      herald: "Herald",
      washer: "стиралка",
      guest: "гость",
      guests: "гости",
      adult: "18+",
      content: "контент",
      mode: "режим",
      started: "запущено",
      finished: "завершено",
      enabled: "включено",
      disabled: "отключено",
      detected: "обнаружено",
      recommendation: "рекомендация",
      critical: "критический",
      warning: "предупреждение",
      alert: "сигнал",
      reminder: "напоминание",
      report: "отчет",
      power: "мощность",
      overload: "перегрузка",
      grid: "сеть",
      quality: "качество",
      problem: "проблема",
      recovered: "восстановлено",
      expensive: "дорогой",
      tariff: "тариф",
      morning: "утренний",
      evening: "вечерний",
      timer: "таймер",
      status: "статус",
      cancelled: "отменено",
      beach: "пляж",
      walk: "прогулка",
      window: "окна",
      unavailable: "недоступно",
      security: "безопасность",
      camera: "камеры",
      suspicious: "подозрительно",
      silence: "тишина",
      anomaly: "аномалия",
      manual: "ручной",
      lights: "свет",
      home: "дом",
      selected: "выбрано"
    };
    const human = normalized.split("_").map((part) => tokenLabels[part] ?? part).join(" ").replace(/\s+/g, " ").trim();
    if (!human) {
      return "Нет события";
    }
    return human.charAt(0).toUpperCase() + human.slice(1);
  }
  _friendlySourceCount(count) {
    const number = Number(count ?? 0) || 0;
    if (number === 1) {
      return "1 источник";
    }
    if (number >= 2 && number <= 4) {
      return `${number} источника`;
    }
    return `${number} источников`;
  }
  _friendlyBinaryState(value) {
    if (value === "on") return "вкл";
    if (value === "off") return "выкл";
    if (["unknown", "unavailable"].includes(value)) return "недоступно";
    if (value === "n/a" || value == null || value === "") return "нет данных";
    return this._humanizeCode(value);
  }
  _friendlyResolvedFrom(value) {
    const labels = {
      herald_fallback_switch: "Fallback-переключатель",
      room_presence_sensor: "Сенсор комнаты",
      room_presence_binary_sensor: "Бинарный сенсор комнаты",
      real_room_sensor: "Реальный сенсор комнаты"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _humanizeCode(value) {
    return String(value ?? "").replace(/^select\./, "").replace(/^switch\./, "").replace(/^sensor\./, "").replace(/^binary_sensor\./, "").replaceAll("_", " ").trim();
  }
  _formatChannels(channels) {
    return (channels ?? []).map((channel) => this._friendlyChannelName(channel)).join(", ");
  }
  _setPolicySearch(value) {
    this._policyPreviews = {};
    this._policySearch = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyFamily(value) {
    this._policyPreviews = {};
    this._policyFamily = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyScope(value) {
    this._policyPreviews = {};
    this._policyScope = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _filterPolicies(items) {
    const query = String(this._policySearch ?? "").trim().toLowerCase();
    const family = this._policyFamily ?? "all";
    const scope = this._policyScope ?? "all";
    return [...items].filter((item) => {
      const effective = item.effective ?? {};
      const policy = item.policy ?? {};
      const haystack = [
        item.notification_key,
        item.title,
        this._friendlyNotificationTitle(item),
        item.family,
        this._friendlyFamilyLabel(item.family),
        item.selected_entity,
        this._friendlyRouteLabel(item),
        item.selected_title_ru,
        item.family_last_event_code,
        this._friendlyEventLabel(item.family_last_event_code),
        item.selected_state_ru,
        item.selected_state,
        item.last_seen_at,
        ...(item.source_files ?? []),
        ...(item.effective?.channels ?? []),
        item.effective?.delivery_mode,
        item.policy?.notes
      ].join(" ").toLowerCase();
      if (query && !haystack.includes(query)) {
        return false;
      }
      if (family !== "all" && item.family !== family) {
        return false;
      }
      if (scope === "active" && !item.active) {
        return false;
      }
      if (scope === "attention" && !item.active_attention) {
        return false;
      }
      if (scope === "disabled" && effective.enabled !== false) {
        return false;
      }
      if (scope === "customized") {
        const customized = this._policyCustomized(item);
        if (!customized) {
          return false;
        }
      }
      return true;
    }).sort((left, right) => {
      const score = (item) => (item.active_attention ? 4 : 0) + (item.active ? 2 : 0) + (item.effective?.enabled === false ? 0 : 1);
      return score(right) - score(left) || String(left.title ?? left.notification_key).localeCompare(String(right.title ?? right.notification_key));
    });
  }
  _paginatePolicies(items) {
    const total = items.length;
    const totalPages = total ? Math.ceil(total / POLICY_PAGE_SIZE) : 0;
    const page = totalPages ? Math.min(Math.max(this._policyPage, 1), totalPages) : 1;
    const start = (page - 1) * POLICY_PAGE_SIZE;
    return {
      items: items.slice(start, start + POLICY_PAGE_SIZE),
      page,
      totalPages
    };
  }
  _humanizeFamily(value) {
    return String(value ?? "general").replaceAll("_", " ");
  }
  _togglePolicyExpanded(notificationKey) {
    this._policyPreviews = {};
    this._policyExpanded = this._policyExpanded === notificationKey ? "" : notificationKey;
    if (this._policyExpanded) {
      void this.updateComplete.then(() => {
        const heading = this.renderRoot?.querySelector(".policy-editor-heading h4");
        heading?.focus({ preventScroll: true });
        heading?.scrollIntoView({ block: "start", behavior: "auto" });
      });
    }
  }
  _setPolicyPage(page) {
    this._policyPreviews = {};
    this._policyPage = Math.max(1, page);
  }
  async _refreshPolicies() {
    if (!this.hass) {
      return;
    }
    await this.hass.callService("herald", "refresh_notification_registry", {
      force: true
    });
  }
  _normalizedPolicy(policy = {}) {
    const rawCooldown = policy.cooldown_override;
    return {
      enabled: policy.enabled !== false,
      delivery_mode: policy.delivery_mode ?? "inherit",
      channels: Array.isArray(policy.channels) ? [...policy.channels] : String(policy.channels ?? "").split(",").map((part) => part.trim()).filter(Boolean),
      users: Array.isArray(policy.users) ? [...policy.users] : null,
      target_room: policy.target_room || null,
      presence: policy.presence ?? "any",
      quiet_hours: policy.quiet_hours ?? "inherit",
      level_override: policy.level_override ?? "",
      cooldown_override: rawCooldown == null || rawCooldown === "" ? "" : Number(rawCooldown),
      notes: policy.notes ?? "",
    };
  }
  _policyItem(item) {
    const saved = this._policySaved[item.notification_key];
    return saved && saved.sourceVersion === JSON.stringify(item.policy ?? {})
      ? { ...item, policy: saved.response.policy, effective: saved.response.effective ?? item.effective }
      : item;
  }
  _policyPayload(item) {
    const saved = this._policyItem(item);
    return this._normalizedPolicy({ ...saved.policy, ...this._policyDrafts[item.notification_key] });
  }
  _policyDirty(item) {
    return JSON.stringify(this._policyPayload(item)) !== JSON.stringify(this._normalizedPolicy(this._policyItem(item).policy));
  }
  _policyRouteSummary(policy, flow) {
    if (policy.enabled === false || policy.delivery_mode === "disabled") return "Доставка отключена";
    const mode = policy.delivery_mode ?? "inherit";
    if (mode === "inherit") return flow ? `По общему правилу потока «${this._friendlyFlowName(flow)}»` : "По общему правилу потока и дома";
    if (mode === "custom") return policy.channels?.length ? `Только выбранные каналы: ${this._formatChannels(policy.channels)}` : "Каналы не выбраны — доставки не будет";
    return `${this._friendlyDeliveryMode(mode)}; итог определяется проверкой`;
  }
  _clearPolicyPreview(key) {
    const next = { ...this._policyPreviews };
    delete next[key];
    this._policyPreviews = next;
  }
  _discardPolicyDraft(key) {
    const drafts = { ...this._policyDrafts };
    delete drafts[key];
    this._policyDrafts = drafts;
    this._policyRevisions[key] = (this._policyRevisions[key] ?? 0) + 1;
    this._clearPolicyPreview(key);
    this._policyFeedback = { ...this._policyFeedback, [key]: { type: "success", message: "Изменения отменены. Показано сохранённое правило." } };
  }
  _setPolicyScenario(key, scenario) {
    this._policyScenarios = { ...this._policyScenarios, [key]: scenario };
    this._clearPolicyPreview(key);
  }
  async _policyService(service, data) {
    if (!this.hass?.callWS) throw new Error("Соединение с Home Assistant недоступно. Обновите страницу.");
    const serviceData = { ...data };
    if (this._config?.entry_id) serviceData.entry_id = this._config.entry_id;
    const result = await this.hass.callWS({ type: "call_service", domain: "herald", service, service_data: serviceData, return_response: true });
    if (!result?.response || typeof result.response !== "object") throw new Error("Home Assistant не вернул результат. Обновите реестр и проверьте состояние правила.");
    return result.response;
  }
  _policyError(error) {
    return error?.message ? String(error.message) : "Не удалось выполнить действие. Проверьте подключение и журнал Home Assistant.";
  }
  _validatePolicy(policy) {
    if (policy.cooldown_override !== "" && (!Number.isInteger(policy.cooldown_override) || policy.cooldown_override < 0 || policy.cooldown_override > 86400)) {
      throw new Error("Интервал должен быть целым числом от 0 до 86400 секунд или пустым.");
    }
  }
  async _previewPolicy(item) {
    const key = String(item.notification_key ?? "");
    const token = ++this._previewSequence;
    const scenario = this._policyScenarios[key] ?? "current";
    const policy = this._policyPayload(item);
    this._policyPreviews = { ...this._policyPreviews, [key]: { loading: true, token } };
    try {
      this._validatePolicy(policy);
      const result = await this._policyService("preview_notification_policy", { notification_key: key, policy, scenario });
      if (this._policyPreviews[key]?.token !== token) return;
      if (!result.explanation?.summary) throw new Error("Сервер не вернул объяснение маршрута.");
      this._policyPreviews = { ...this._policyPreviews, [key]: { loading: false, token, result } };
    } catch (error) {
      if (this._policyPreviews[key]?.token !== token) return;
      this._policyPreviews = { ...this._policyPreviews, [key]: { loading: false, token, error: this._policyError(error) } };
    }
  }
  async _mutatePolicy(item, service, payload, message, { clearDraft = false } = {}) {
    if (this._busyPolicy) return;
    const key = String(item.notification_key ?? "");
    const revision = this._policyRevisions[key] ?? 0;
    this._busyPolicy = key;
    this._clearPolicyPreview(key);
    this._policyFeedback = { ...this._policyFeedback, [key]: undefined };
    try {
      const response = await this._policyService(service, { notification_key: key, ...payload });
      if (!response.policy || response.notification_key !== key) throw new Error("Ответ сервера не содержит сохранённое правило. Обновите реестр.");
      const source = this._statusEntity()?.attributes?.notification_registry?.items?.find((entry) => entry.notification_key === key) ?? item;
      this._policySaved = {
        ...this._policySaved,
        [key]: JSON.stringify(source.policy ?? {}) === JSON.stringify(response.policy)
          ? undefined
          : { sourceVersion: JSON.stringify(source.policy ?? {}), response },
      };
      if (clearDraft && (this._policyRevisions[key] ?? 0) === revision) {
        const drafts = { ...this._policyDrafts };
        delete drafts[key];
        this._policyDrafts = drafts;
      }
      const suffix = (this._policyRevisions[key] ?? 0) !== revision ? " Более новые изменения остаются в черновике." : "";
      this._policyFeedback = { ...this._policyFeedback, [key]: { type: "success", message: message + suffix } };
    } catch (error) {
      this._policyFeedback = { ...this._policyFeedback, [key]: { type: "error", message: this._policyError(error) } };
    } finally {
      this._busyPolicy = "";
    }
  }
  async _togglePolicyEnabled(item) {
    item = this._policyItem(item);
    const enable = !(item.effective?.enabled ?? true);
    const payload = { enabled: enable };
    if (enable && item.policy?.delivery_mode === "disabled") payload.delivery_mode = "inherit";
    await this._mutatePolicy(item, "set_notification_policy", payload, enable ? "Уведомление включено." : "Уведомление отключено.");
  }
  async _savePolicy(item) {
    const policy = this._policyPayload(item);
    try {
      this._validatePolicy(policy);
    } catch (error) {
      this._policyFeedback = { ...this._policyFeedback, [item.notification_key]: { type: "error", message: this._policyError(error) } };
      return;
    }
    await this._mutatePolicy(item, "set_notification_policy", policy, "Правило сохранено.", { clearDraft: true });
  }
  async _resetPolicy(item) {
    await this._mutatePolicy(item, "reset_notification_policy", {}, "Восстановлено общее правило.", { clearDraft: true });
  }

}

HeraldCard.styles = css`
    :host {
      display: block;
    }

    ha-card {
      color: var(--primary-text-color);
      background: var(--ha-card-background, var(--card-background-color));
    }

    .shell {
      padding: 16px;
      display: grid;
      gap: 16px;
    }

    .hero {
      display: grid;
      gap: 14px;
    }

    .hero-panel .panel-shell {
      gap: 16px;
    }

    .eyebrow {
      margin: 0;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
      color: var(--secondary-text-color);
    }

    h2,
    h3,
    p {
      margin: 0;
    }

    h2 {
      font-size: 1.4rem;
      line-height: 1.2;
      margin-top: 2px;
    }

    .subhead {
      color: var(--secondary-text-color);
      margin-top: 8px;
    }

    .stats,
    .flow-grid,
    .language-grid,
    .room-grid,
    .character-grid,
    .mute-grid {
      display: grid;
      gap: 12px;
    }

    .stats {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }

    .stats.compact {
      grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
    }

    .stat,
    .panel,
    .language-card,
    .policy-card,
    .room-card,
    .notification,
    .flow {
      border-radius: 14px;
      border: 1px solid var(--divider-color);
      background: var(--secondary-background-color);
    }

    .stat {
      padding: 14px;
      display: grid;
      gap: 6px;
    }

    .stat span,
    .panel-header span,
    footer,
    .flow-state {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .panel {
      overflow: hidden;
      background: var(--ha-card-background, var(--card-background-color));
    }

    .panel-shell {
      padding: 14px;
      display: grid;
      gap: 12px;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      flex-wrap: wrap;
    }

    .flow-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .flow {
      appearance: none;
      text-align: left;
      padding: 12px;
      cursor: pointer;
      display: grid;
      gap: 6px;
      transition: border-color 160ms ease, background 160ms ease;
      color: inherit;
    }

    .flow:hover {
      border-color: var(--primary-color);
    }

    .flow-name {
      font-weight: 700;
    }

    .flow.enabled {
      background: var(--ha-card-background, var(--card-background-color));
    }

    .flow.disabled {
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 12%, var(--secondary-background-color));
    }

    .language-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .character-grid,
    .mute-grid {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }

    .policy-grid-advanced {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .language-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .room-grid {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }

    .room-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .room-head,
    .room-meta {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .room-meta {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .room-toggle {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
      text-align: left;
    }

    .room-toggle:hover {
      border-color: var(--primary-color);
    }

    .secondary-action {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
    }

    .secondary-action:hover {
      border-color: var(--primary-color);
    }

    .secondary-action:disabled,
    .room-toggle:disabled {
      opacity: 0.6;
      cursor: default;
    }

    .policy-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .policy-toolbar {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .policy-card.disabled {
      opacity: 0.8;
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 10%, var(--secondary-background-color));
    }

    .policy-head,
    .policy-meta,
    .policy-actions {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }

    .policy-meta {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .policy-actions {
      justify-content: flex-end;
    }

    .policy-table-wrap {
      overflow-x: auto;
      border: 1px solid var(--divider-color);
      border-radius: 14px;
      background: var(--ha-card-background, var(--card-background-color));
    }

    .policy-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
    }

    .policy-table th,
    .policy-table td {
      padding: 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: top;
      text-align: left;
    }

    .policy-table th {
      color: var(--secondary-text-color);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      background: color-mix(in srgb, var(--secondary-background-color) 85%, transparent);
    }

    .policy-table tbody tr:last-child td {
      border-bottom: none;
    }

    .policy-row.is-active {
      background: color-mix(in srgb, var(--success-color, #43a047) 7%, transparent);
    }

    .policy-row.is-attention {
      background: color-mix(in srgb, var(--error-color, #e53935) 8%, transparent);
    }

    .policy-row-main {
      display: grid;
      gap: 4px;
    }

    .policy-table-subline {
      color: var(--secondary-text-color);
      font-size: 0.82rem;
      line-height: 1.35;
    }

    .policy-status-stack,
    .policy-inline-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .policy-status {
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      background: color-mix(in srgb, var(--divider-color) 45%, transparent);
    }

    .policy-status.enabled {
      background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent);
      color: var(--success-color, #43a047);
    }

    .policy-status.disabled {
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 18%, transparent);
      color: var(--state-unavailable-color, #9e9e9e);
    }

    .policy-editor-row td {
      background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
    }

    .policy-editor-container { padding: 18px; border: 1px solid var(--divider-color); border-radius: 14px; margin-bottom: 16px; min-width: 0; }
    .policy-provenance { margin: 12px 0; }
    .policy-provenance summary { cursor: pointer; }
    .policy-provenance dl { display: grid; gap: 10px; }
    .policy-provenance dt { font-weight: 600; }
    .policy-provenance dd { margin: 4px 0 0; }
    .policy-provenance small { display: block; color: var(--secondary-text-color); }
    .policy-card-editor {
      border: none;
      padding: 0;
      background: transparent;
    }

    .policy-editor-heading, .policy-preview-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
    .policy-editor-heading h4 { margin: 0 0 6px; font-size: 1.05rem; }
    .policy-hint { color: var(--secondary-text-color); font-size: 0.85rem; line-height: 1.5; margin: 6px 0; }
    .policy-rule-summary { margin: 0; font-weight: 600; }
    .policy-target-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .policy-rule-section { min-width: 0; }
    .policy-rule-section h5 { font-size: 1rem; margin: 0 0 10px; }
    .policy-user-options { margin-top: 10px; }
    .policy-user-options .policy-channel { max-width: 100%; overflow-wrap: anywhere; }
    .policy-saved-targets { overflow-wrap: anywhere; }
    .policy-draft-targets { margin: 0; line-height: 1.5; overflow-wrap: anywhere; }
    .policy-enabled { display: flex; align-items: center; gap: 8px; }
    .policy-channel-fieldset { border: 1px solid var(--divider-color); border-radius: 10px; padding: 12px; min-width: 0; }
    .policy-advanced { border-top: 1px solid var(--divider-color); padding-top: 12px; }
    .policy-advanced summary { cursor: pointer; padding: 6px 0; }
    .policy-advanced .policy-grid { margin-top: 12px; }
    .policy-preview, .policy-last-decision { padding: 14px; border-radius: 12px; background: var(--secondary-background-color); }
    .policy-preview-controls { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; margin-top: 12px; }
    .policy-preview-controls label { display: grid; gap: 6px; flex: 1; min-width: 150px; }
    .policy-preview-controls select { padding: 9px; border-radius: 8px; background: var(--card-background-color); color: var(--primary-text-color); border: 1px solid var(--divider-color); }
    .policy-feedback { padding: 12px; border-radius: 10px; margin: 0; line-height: 1.5; }
    .policy-feedback.success { background: color-mix(in srgb, var(--success-color, #43a047) 12%, transparent); }
    .policy-feedback.error { background: color-mix(in srgb, var(--error-color, #e53935) 12%, transparent); color: var(--error-color, #e53935); }
    .policy-explanation { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--divider-color); line-height: 1.5; }
    .policy-explanation ol { padding-left: 20px; }
    .policy-explanation li { margin-bottom: 6px; }
    .policy-last-decision p { margin: 6px 0; }
    .primary-action { font-weight: 700; }
    .policy-pager {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }

    .policy-field {
      background: var(--ha-card-background, var(--card-background-color));
      border: 1px solid var(--divider-color);
    }
    .policy-field select { min-width: 0; max-width: 100%; width: 100%; box-sizing: border-box; }
    .configuration-overview { display: grid; gap: 12px; margin-top: 16px; }
    .configuration-heading { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
    .configuration-heading h4 { margin: 0; font-size: 1rem; overflow-wrap: anywhere; }
    .configuration-restrictions { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }
    .configuration-restrictions li { padding: 12px; border-left: 3px solid var(--warning-color, #e5a100); border-radius: 8px; background: var(--secondary-background-color); }
    .configuration-restrictions p { margin: 4px 0 0; line-height: 1.5; }
    .restriction-action { margin-top: 8px; }
    .configuration-counts { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--secondary-text-color); }
    .channel-controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 14px; }
    .channel-control-card { padding: 16px; border: 1px solid var(--divider-color); border-radius: 14px; display: grid; align-content: start; gap: 12px; min-width: 0; overflow-wrap: anywhere; }
    .channel-control-card .channel-level { padding: 0; background: transparent; border: 0; }
    .channel-level select, .language-card select { min-width: 0; max-width: 100%; width: 100%; box-sizing: border-box; }
    .channel-checks { margin: 0; padding-left: 20px; line-height: 1.5; }
    .channel-checks li + li { margin-top: 6px; }
    .channel-checks .attention { color: var(--error-color, #b72f37); }
    button:disabled, select:disabled { cursor: not-allowed; opacity: 0.6; }

    .policy-filter {
      background: var(--ha-card-background, var(--card-background-color));
      border: 1px solid var(--divider-color);
    }

    .policy-channel-summary {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .policy-channel-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .policy-channel {
      border: 1px solid var(--divider-color);
      border-radius: 999px;
      padding: 8px 10px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
    }

    .policy-channel.selected {
      border-color: var(--primary-color);
      background: color-mix(in srgb, var(--primary-color) 14%, transparent);
      color: var(--primary-color);
    }

    .policy-channel:disabled {
      opacity: 0.6;
      cursor: default;
    }

    select,
    input {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      font: inherit;
      color: inherit;
    }

    .list {
      display: grid;
      gap: 10px;
    }

    .notification {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .event-text {
      color: var(--secondary-text-color);
      line-height: 1.5;
      overflow-wrap: anywhere;
    }

    .event-entry + .event-entry {
      border-top: 1px solid var(--divider-color);
    }

    .older-events {
      border-top: 1px solid var(--divider-color);
    }

    .older-events > summary {
      padding: 12px 0;
      cursor: pointer;
      color: var(--primary-color);
    }

    .event-entry summary {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 16px 0;
      cursor: pointer;
      list-style: none;
    }

    .event-entry summary::-webkit-details-marker {
      display: none;
    }

    .event-entry summary:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 4px;
    }

    .event-entry summary ha-icon {
      flex: 0 0 24px;
      color: var(--secondary-text-color);
    }

    .event-entry summary .event-chevron {
      flex-basis: 18px;
      --mdc-icon-size: 18px;
    }

    .event-entry[open] .event-chevron {
      transform: rotate(180deg);
    }

    .event-preview {
      min-width: 0;
      flex: 1;
      display: grid;
      gap: 6px;
      line-height: 1.4;
    }

    .event-preview strong {
      font-size: 1rem;
      font-weight: 500;
      overflow-wrap: anywhere;
    }

    .event-description {
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
      overflow: hidden;
      overflow-wrap: anywhere;
    }

    .event-entry time {
      flex: 0 0 auto;
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      line-height: 1.6;
    }

    .event-content {
      display: grid;
      gap: 12px;
      padding: 0 0 16px 36px;
    }

    .event-content .event-text {
      white-space: pre-wrap;
    }

    .event-date {
      color: var(--secondary-text-color);
      font-size: 0.875rem;
    }

    .compact-panel {
      border-radius: var(--ha-card-border-radius, 12px);
      border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
    }

    .compact-panel .panel-shell {
      padding: 16px;
    }

    .compact-panel h3 {
      font-size: var(--ha-card-header-font-size, 24px);
      font-weight: normal;
      line-height: 1.4;
    }

    .compact-panel .policy-table {
      min-width: 0;
    }

    .compact-panel .policy-table th:nth-child(2),
    .compact-panel .policy-table td:nth-child(2),
    .compact-panel .policy-table th:nth-child(6),
    .compact-panel .policy-table td:nth-child(6),
    .compact-panel .policy-table th:nth-child(7),
    .compact-panel .policy-table td:nth-child(7) {
      display: none;
    }

    .compact-panel .list {
      gap: 0;
    }

    .compact-panel .notification {
      padding: 16px 0;
      border: 0;
      border-radius: 0;
      background: transparent;
    }

    .compact-panel .notification + .notification {
      border-top: 1px solid var(--divider-color);
    }

    .compact-panel .notification-head .pill {
      padding: 0;
      background: transparent;
      text-transform: none;
      font-weight: normal;
    }

    .notification-head,
    footer {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--primary-color) 12%, transparent);
      color: var(--primary-color);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .pill.active {
      background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent);
      color: var(--success-color, #43a047);
    }

    .pill.danger {
      background: color-mix(in srgb, var(--error-color, #e53935) 14%, transparent);
      color: var(--error-color, #e53935);
    }

    .pill.custom {
      background: color-mix(in srgb, var(--warning-color, #fb8c00) 14%, transparent);
      color: var(--warning-color, #fb8c00);
    }

    .empty {
      padding: 18px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      color: var(--secondary-text-color);
      text-align: center;
    }

    @media (max-width: 640px) {
      .policy-target-grid { grid-template-columns: 1fr; }
      .policy-table { min-width: 0; }
      .policy-table thead { display: none; }
      .policy-table tbody, .policy-table tr { display: block; }
      .policy-table tr { padding: 8px 0; border-bottom: 1px solid var(--divider-color); }
      .policy-table td { display: none; }
      .policy-table td:nth-child(1), .policy-table td:nth-child(3), .policy-table td:nth-child(5), .policy-table td:nth-child(8) { display: block; border: 0; padding: 7px 12px; }
      .policy-inline-actions { justify-content: flex-start; }
      .shell {
        padding: 18px;
      }

      h2 {
        font-size: 1.35rem;
      }

      .policy-pager {
        align-items: stretch;
      }
    }
  `;
if (!customElements.get("herald-card")) {
  customElements.define("herald-card", HeraldCard);
}

const registerHeraldVariant = (tagName, defaultViewMode) => {
  if (customElements.get(tagName)) {
    return;
  }
  class HeraldVariantCard extends HeraldCard {
  }
  HeraldVariantCard.viewMode = defaultViewMode;
  customElements.define(tagName, HeraldVariantCard);
};
registerHeraldVariant("ha-herald-general", "general");
registerHeraldVariant("ha-herald-policies", "policies");
registerHeraldVariant("ha-herald-policy-guide", "policy-guide");
registerHeraldVariant("ha-herald-flows", "flows");
registerHeraldVariant("ha-herald-languages", "languages");
registerHeraldVariant("ha-herald-characters", "characters");
registerHeraldVariant("ha-herald-mute", "mute");
registerHeraldVariant("ha-herald-rooms", "rooms");
registerHeraldVariant("ha-herald-queue", "queue");
registerHeraldVariant("ha-herald-controls", "controls");
registerHeraldVariant("ha-herald-feed", "feed");
registerHeraldVariant("ha-herald-recent", "recent");
registerHeraldVariant("ha-herald-overview", "overview");
