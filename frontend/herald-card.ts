import { LitElement, css, html, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

interface HassState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

interface HomeAssistant {
  states: Record<string, HassState>;
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<void>;
}

interface HeraldCardConfig {
  title?: string;
  today_entity?: string;
  last_entity?: string;
  queue_entity?: string;
  language_entities?: string[];
}

declare global {
  interface Window {
    customCards?: Array<Record<string, string>>;
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'herald-card',
  name: 'Herald Card',
  description: 'Notification Center card for Herald',
});

const DEFAULT_LANGUAGES = ['ru', 'en', 'es', 'fr'];

@customElement('herald-card')
export class HeraldCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: HeraldCardConfig;
  @state() private _busyFlow = '';

  public setConfig(config: HeraldCardConfig): void {
    if (!config.today_entity || !config.last_entity || !config.queue_entity) {
      throw new Error('today_entity, last_entity, and queue_entity are required');
    }
    this._config = config;
  }

  public getCardSize(): number {
    return 6;
  }

  protected render() {
    if (!this.hass || !this._config) {
      return html`<ha-card>Loading…</ha-card>`;
    }

    const today = this.hass.states[this._config.today_entity ?? ''];
    const last = this.hass.states[this._config.last_entity ?? ''];
    const queue = this.hass.states[this._config.queue_entity ?? ''];

    if (!today || !last || !queue) {
      return html`<ha-card><div class="shell">Herald entities are not available.</div></ha-card>`;
    }

    const recent = (today.attributes.recent_notifications as Array<Record<string, unknown>> | undefined) ?? [];
    const flowStates = (queue.attributes.flow_states as Record<string, boolean> | undefined) ?? {};
    const snoozedFlows = (queue.attributes.snoozed_flows as Record<string, string> | undefined) ?? {};
    const languageEntities = this._config.language_entities ?? [];

    return html`
      <ha-card>
        <div class="shell">
          <div class="hero">
            <div>
              <p class="eyebrow">Smart Home Dispatch</p>
              <h2>${this._config.title ?? 'Herald Notification Center'}</h2>
              <p class="subhead">Очередь, статусы flow, последние события и выбор языка пользователей.</p>
            </div>
            <div class="stats">
              ${this._renderStat('Сегодня', today.state)}
              ${this._renderStat('Очередь', queue.state)}
              ${this._renderStat('Последнее', last.state)}
            </div>
          </div>

          <section class="panel">
            <div class="panel-header">
              <h3>Flow Control</h3>
              <span>Runtime mute / unmute</span>
            </div>
            <div class="flow-grid">
              ${Object.entries(flowStates).map(([flow, enabled]) => this._renderFlow(flow, enabled, snoozedFlows[flow]))}
            </div>
          </section>

          ${languageEntities.length
            ? html`
                <section class="panel">
                  <div class="panel-header">
                    <h3>Languages</h3>
                    <span>User-level notification language</span>
                  </div>
                  <div class="language-grid">
                    ${languageEntities.map((entityId) => this._renderLanguage(entityId))}
                  </div>
                </section>
              `
            : nothing}

          <section class="panel">
            <div class="panel-header">
              <h3>Recent Notifications</h3>
              <span>Latest deliveries and summaries</span>
            </div>
            <div class="list">
              ${recent.length
                ? recent.slice(0, 8).map((item) => this._renderNotification(item))
                : html`<div class="empty">Уведомлений пока нет.</div>`}
            </div>
          </section>
        </div>
      </ha-card>
    `;
  }

  private _renderStat(label: string, value: unknown) {
    return html`
      <div class="stat">
        <span>${label}</span>
        <strong>${value ?? 'n/a'}</strong>
      </div>
    `;
  }

  private _renderFlow(flow: string, enabled: boolean, snoozedUntil?: string) {
    const snoozed = Boolean(snoozedUntil && !enabled);
    return html`
      <button class="flow ${enabled ? 'enabled' : 'disabled'}" @click=${() => this._toggleFlow(flow, enabled)}>
        <span class="flow-name">${flow}</span>
        <span class="flow-state">${enabled ? 'enabled' : snoozed ? `snoozed until ${snoozedUntil}` : 'disabled'}</span>
      </button>
    `;
  }

  private _renderLanguage(entityId: string) {
    const entity = this.hass?.states[entityId];
    if (!entity) {
      return nothing;
    }
    const options = (entity.attributes.options as string[] | undefined) ?? DEFAULT_LANGUAGES;
    return html`
      <label class="language-card">
        <span>${entity.attributes.friendly_name ?? entityId}</span>
        <select .value=${entity.state} @change=${(event: Event) => this._setLanguage(entityId, event)}>
          ${options.map((option) => html`<option value=${option}>${option}</option>`)}
        </select>
      </label>
    `;
  }

  private _renderNotification(item: Record<string, unknown>) {
    const channels = Array.isArray(item.channels) ? item.channels.join(', ') : 'n/a';
    return html`
      <article class="notification">
        <div class="notification-head">
          <strong>${String(item.title ?? 'Herald')}</strong>
          <span class="pill">${String(item.level ?? 'info')}</span>
        </div>
        <p>${String(item.message ?? '')}</p>
        <footer>
          <span>${channels}</span>
          <span>${String(item.timestamp ?? '')}</span>
        </footer>
      </article>
    `;
  }

  private async _toggleFlow(flow: string, enabled: boolean): Promise<void> {
    if (!this.hass || this._busyFlow === flow) {
      return;
    }
    this._busyFlow = flow;
    try {
      await this.hass.callService('herald', 'set_flow_state', {
        flow,
        enabled: !enabled,
      });
    } finally {
      this._busyFlow = '';
    }
  }

  private async _setLanguage(entityId: string, event: Event): Promise<void> {
    if (!this.hass) {
      return;
    }
    const target = event.target as HTMLSelectElement;
    await this.hass.callService('input_select', 'select_option', {
      entity_id: entityId,
      option: target.value,
    });
  }

  static styles = css`
    :host {
      --herald-ink: #1c2220;
      --herald-muted: #5c665f;
      --herald-warm: #f2ece1;
      --herald-accent: #af3a2b;
      --herald-accent-soft: #f4cdb4;
      --herald-surface: linear-gradient(180deg, #fff8ee 0%, #f6efe4 100%);
      display: block;
    }

    ha-card {
      border-radius: 26px;
      overflow: hidden;
      background: var(--herald-surface);
      color: var(--herald-ink);
      box-shadow: 0 24px 60px rgba(65, 37, 17, 0.14);
    }

    .shell {
      padding: 24px;
      display: grid;
      gap: 18px;
      background:
        radial-gradient(circle at top right, rgba(175, 58, 43, 0.14), transparent 26%),
        radial-gradient(circle at bottom left, rgba(209, 135, 65, 0.16), transparent 28%);
    }

    .hero {
      display: grid;
      gap: 18px;
    }

    .eyebrow {
      margin: 0;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 0.72rem;
      color: var(--herald-muted);
    }

    h2,
    h3,
    p {
      margin: 0;
    }

    h2 {
      font-size: 1.7rem;
      line-height: 1.1;
      margin-top: 4px;
    }

    .subhead {
      color: var(--herald-muted);
      margin-top: 8px;
    }

    .stats,
    .flow-grid,
    .language-grid {
      display: grid;
      gap: 12px;
    }

    .stats {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }

    .stat,
    .panel,
    .language-card,
    .notification,
    .flow {
      border-radius: 18px;
      border: 1px solid rgba(28, 34, 32, 0.08);
      background: rgba(255, 255, 255, 0.68);
      backdrop-filter: blur(8px);
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
      color: var(--herald-muted);
      font-size: 0.85rem;
    }

    .panel {
      padding: 18px;
      display: grid;
      gap: 14px;
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
      padding: 14px;
      cursor: pointer;
      display: grid;
      gap: 6px;
      transition: transform 160ms ease, border-color 160ms ease;
    }

    .flow:hover {
      transform: translateY(-1px);
      border-color: rgba(175, 58, 43, 0.35);
    }

    .flow-name {
      font-weight: 700;
    }

    .flow.enabled {
      background: rgba(255, 255, 255, 0.72);
    }

    .flow.disabled {
      background: rgba(239, 225, 219, 0.72);
    }

    .language-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .language-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    select {
      border: 1px solid rgba(28, 34, 32, 0.14);
      border-radius: 12px;
      padding: 10px 12px;
      background: white;
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
      background: var(--herald-accent-soft);
      color: var(--herald-accent);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .empty {
      padding: 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.6);
      color: var(--herald-muted);
      text-align: center;
    }

    @media (max-width: 640px) {
      .shell {
        padding: 18px;
      }

      h2 {
        font-size: 1.35rem;
      }
    }
  `;
}
