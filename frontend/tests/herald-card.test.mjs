import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import { gunzipSync } from "node:zlib";
import test from "node:test";
import { transformSync } from "esbuild";

const bundlePath = fileURLToPath(new URL("../../custom_components/herald/frontend/herald-card.js", import.meta.url));
const bundle = readFileSync(bundlePath, "utf8");
const script = transformSync(bundle, { format: "iife", target: "es2020" }).code;
const modes = {
  "herald-card": "full",
  "ha-herald-general": "general",
  "ha-herald-policies": "policies",
  "ha-herald-policy-guide": "policy-guide",
  "ha-herald-flows": "flows",
  "ha-herald-languages": "languages",
  "ha-herald-characters": "characters",
  "ha-herald-mute": "mute",
  "ha-herald-rooms": "rooms",
  "ha-herald-queue": "queue",
  "ha-herald-controls": "controls",
  "ha-herald-feed": "feed",
  "ha-herald-recent": "recent",
  "ha-herald-overview": "overview",
};

// Execute the distributed browser bundle. These shims provide module startup and
// custom-element registration only: template tests below do not claim DOM/layout QA.
function loadBundle() {
  const elements = new Map();
  const context = vm.createContext({
    console,
    setTimeout,
    clearTimeout,
    CustomEvent,
    window: { customCards: [] },
    HTMLElement: class {},
    CSSStyleSheet: class {},
    document: { createTreeWalker: () => ({}) },
    customElements: {
      get: (name) => elements.get(name),
      define(name, component) {
        assert.ok(!elements.has(name), `duplicate registration: ${name}`);
        void component.observedAttributes; // Browsers finalize Lit reactive properties here.
        elements.set(name, component);
      },
    },
  });
  vm.runInContext(script, context, { filename: bundlePath });
  return { context, elements };
}

function templateText(value) {
  if (value == null || typeof value === "symbol" || typeof value === "function") return "";
  if (Array.isArray(value)) return value.map(templateText).join("");
  if (value.strings && value.values) {
    return value.strings.map((part, index) => part + templateText(value.values[index])).join("");
  }
  return String(value);
}

function policy(overrides = {}) {
  return {
    notification_key: "fixture.washer",
    title: "Тестовая стирка",
    family: "laundry",
    active: true,
    effective: { enabled: true, delivery_mode: "inherit", channels: ["dashboard"] },
    policy: { delivery_mode: "inherit" },
    available_channels: ["dashboard", "mobile_test"],
    ...overrides,
  };
}

function makeCard(tag = "herald-card") {
  const { elements } = loadBundle();
  const card = new (elements.get(tag))();
  const calls = [];
  const wsCalls = [];
  let savedPolicy = { enabled: true, delivery_mode: "inherit", channels: [], level_override: "", cooldown_override: "", notes: "" };
  const state = (value, attributes = {}) => ({ state: value, attributes });
  card.setConfig({
    type: `custom:${tag}`,
    room_entities: [{ room: "test_room", sensor: "binary_sensor.test_room", fallback: "switch.test_room" }],
  });
  card.hass = {
    states: {
      sensor_today: state("1"),
      "sensor.herald_notification_center_status": state("ready", { notification_registry: { items: [policy()] } }),
      "sensor.herald_notification_center_notifications_today": state("1", {
        recent_notifications: [{ title: "Fixture", message: "Recent fixture", channels: ["dashboard"] }],
        dashboard_feed: [{ title: "Fixture", message: "Feed fixture" }],
      }),
      "sensor.herald_notification_center_last_notification": state("Fixture"),
      "sensor.herald_notification_center_queue_size": state("1", {
        queued_notifications: [{ title: "Fixture", message: "Queue fixture" }],
        flow_states: { device_alerts: true },
        control_entities: { users: ["select.test_language", "select.test_character", "switch.test_silent"] },
      }),
      "select.test_language": state("ru", { options: ["ru", "en"] }),
      "select.test_character": state("hestia", { options: ["hestia", "jarvis"] }),
      "switch.test_silent": state("off"),
      "binary_sensor.test_room": state("on"),
      "switch.test_room": state("on"),
    },
    async callService(domain, service, data) {
      calls.push({ domain, service, data: JSON.parse(JSON.stringify(data)) });
      const entity = card.hass.states[data.entity_id];
      if (entity && domain === "select") entity.state = data.option;
      if (entity && domain === "switch") entity.state = service === "turn_on" ? "on" : "off";
    },
    async callWS(request) {
      const plain = JSON.parse(JSON.stringify(request));
      wsCalls.push(plain);
      const { notification_key, ...data } = plain.service_data;
      if (plain.service === "preview_notification_policy") return { response: {
        scenario: data.scenario, draft: true,
        explanation: { status: "deliver", summary: "Будет отправлено на выбранный канал", channels: ["dashboard"], steps: [{ label: "Правило", detail: "Черновик применён" }], warnings: [] },
      } };
      calls.push({ domain: plain.domain, service: plain.service, data: plain.service_data });
      if (plain.service === "reset_notification_policy") savedPolicy = { enabled: true, delivery_mode: "inherit", channels: [], level_override: "", cooldown_override: "", notes: "" };
      else savedPolicy = { ...savedPolicy, ...data };
      return { response: { ...policy(), notification_key, policy: { ...savedPolicy }, effective: { enabled: savedPolicy.enabled && savedPolicy.delivery_mode !== "disabled", delivery_mode: savedPolicy.delivery_mode, channels: savedPolicy.channels } } };
    },
  };
  return { card, calls, wsCalls };
}

test("home event feed omits channel and AI metadata, including expanded entries", () => {
  const { card } = makeCard("ha-herald-recent");
  card.setConfig({ compact: true, max_items: 3 });
  const text = templateText(card._renderNotification({
    title: "Fixture", message: "Original event text", timestamp: "2026-10-01T12:00:00Z",
    results: [
      { channel: "voice_auto", status: "sent", _herald_ai_status: "rewritten" },
      { channel: "push_default", status: "error", _herald_ai_status: "fallback" },
      { channel: "dashboard_default", status: "dropped", _herald_ai_status: "passthrough" },
    ],
  }));
  assert.match(text, /Original event text/);
  assert.doesNotMatch(text, /AI:|Отправлено|Ошибка отправки|перефразировано|voice_auto|push_default/);
});

test("home event feed tolerates legacy records and invalid timestamps without guessing status", () => {
  const { card } = makeCard("ha-herald-recent");
  for (const results of [undefined, null, {}, [], [null, false]]) {
    const text = templateText(card._renderNotification({ message: "Old record", results }));
    assert.match(text, /Old record/);
    assert.doesNotMatch(text, /AI:|Отправка:|перефразировано|Отправлено/);
    assert.match(text, /Время неизвестно/);
  }
  assert.equal(card._notificationTime("invalid date"), "Время неизвестно");
  card.hass.config = { time_zone: "Europe/Madrid" };
  assert.match(card._notificationTime("2026-10-01T12:00:00Z"), /14:00/);
});

test("compact home event feed keeps full descriptions and older events accessible", () => {
  const { card } = makeCard("ha-herald-recent");
  card.setConfig({ type: "custom:ha-herald-recent", compact: true, max_items: 3, title: "Журнал" });
  const message = "A".repeat(500);
  const text = templateText(card._renderNotification({ title: "Fixture", message }));
  assert.match(text, /<details class="event-entry">/);
  assert.ok(text.includes(message));
  assert.ok(text.includes("A".repeat(110) + "…"));
  const summary = text.slice(text.indexOf("<summary>"), text.indexOf("</summary>"));
  assert.match(summary, /Fixture/);
  assert.doesNotMatch(summary, /AI:|Отправка:|Текст события:/);
  assert.doesNotMatch(text, /<details[^>]*\bopen\b/);
  assert.equal(card._recentLimit(), 3);
  const items = Array.from({ length: 6 }, (_, i) => ({ title: `Unique ${i}`, message: "Test" }));
  card.hass.states["sensor.herald_notification_center_notifications_today"].attributes.recent_notifications = items;
  const rendered = templateText(card.render());
  assert.match(rendered, /Журнал/);
  assert.match(rendered, /Unique 2/);
  assert.match(rendered, /<details class="older-events">/);
  assert.match(rendered, /Ещё события \(3\)/);
  assert.match(rendered, /Unique 5/);
  assert.doesNotMatch(rendered, /Последние доставки и сводки/);
  card.setConfig({ max_items: 100 });
  assert.equal(card._recentLimit(), 8);
});

test("distributed bundle registers every supported card and picker entry once", () => {
  const { context, elements } = loadBundle();
  assert.deepEqual([...elements.keys()].sort(), [...Object.keys(modes), "ha-herald-dashboard", "herald-dashboard-section"].sort());
  assert.deepEqual(Array.from(context.window.customCards, (item) => item.type).sort(), [...Object.keys(modes), "ha-herald-dashboard"].sort());
  vm.runInContext(script, context);
  assert.equal(elements.size, 16);
  assert.equal(context.window.customCards.length, 15);
});

test("dashboard uses exact registry identities and disables controls when Herald disconnects", () => {
  const { card, calls } = makeCard("ha-herald-dashboard");
  const status = card.hass.states["sensor.herald_notification_center_status"];
  status.attributes.control_entity_ids = { mute_all: "switch.test_silent" };
  assert.equal(card._controlId("mute_all"), "switch.test_silent");
  assert.equal(card._controlId("ai_enabled"), null);
  assert.match(templateText(card.render()), /Последние события/);
  status.state = "unavailable";
  assert.equal(card._controlId("mute_all"), null);
  card._switchTab("rules");
  assert.match(templateText(card.render()), /после подключения/);
  assert.equal(calls.length, 0);
});

test("dashboard number edits validate range and accept numeric HA acknowledgement", async () => {
  const { card, calls } = makeCard("ha-herald-dashboard");
  card.hass.states["number.renamed_interval"] = { state: "5.0", attributes: { min: 0, max: 60 } };
  await card._setNumber("number.renamed_interval", { target: { value: "61" } });
  assert.equal(calls.length, 0);
  const field = { value: "30" };
  await card._setNumber("number.renamed_interval", { target: field });
  assert.equal(calls[0].domain, "number");
  assert.equal(calls[0].data.entity_id, "number.renamed_interval");
  assert.equal(field.value, "5.0");
  assert.equal(card._controlActions["number.renamed_interval"].phase, "awaiting");
  card.hass.states["number.renamed_interval"].state = "30.0";
  card._reconcileControlActions();
  assert.equal(card._controlActions["number.renamed_interval"].phase, "success");
});

test("nested editor receives configuration once and retains pending draft on state updates", () => {
  const { elements } = loadBundle();
  const section = new (elements.get("herald-dashboard-section"))();
  section.settings = { view_mode: "policies", initial_policy_key: "fixture.washer" };
  section._setPolicyDraft("fixture.washer", "notes", "Unsaved fixture");
  section._controlActions = { "switch.fixture": { phase: "awaiting", expected: "on" } };
  section.settings = { view_mode: "policies", initial_policy_key: "fixture.washer" };
  assert.equal(section._policyDrafts["fixture.washer"].notes, "Unsaved fixture");
  assert.equal(section._controlActions["switch.fixture"].phase, "awaiting");
  assert.equal(section._policyExpanded, "fixture.washer");
});

test("all 14 card types use their view mode and render a populated Lit template", () => {
  for (const [tag, mode] of Object.entries(modes)) {
    const { card } = makeCard(tag);
    assert.equal(card._config.view_mode, mode, tag);
    const text = templateText(card.render());
    assert.match(text, /<ha-card/, tag);
    assert.doesNotMatch(text, /Loading…|сейчас недоступны/, tag);
    assert.ok(card.getCardSize() > 0);
    assert.equal(card.constructor.elementProperties.get("hass").attribute, false);
    assert.equal(card.constructor.elementProperties.get("_policyDrafts").state, true);
  }
  const { card } = makeCard("ha-herald-policies");
  const text = templateText(card.render());
  assert.match(text, /Правила уведомлений/);
  assert.match(text, /Тестовая стирка/);
  assert.doesNotMatch(text, /Queue fixture|Recent fixture/);
  card._togglePolicyExpanded("fixture.washer");
  assert.match(templateText(card.render()), /Дополнительно: важность и интервал/);
});

test("card tolerates missing Home Assistant data and honors explicit view mode", () => {
  const { card } = makeCard("ha-herald-policies");
  card.setConfig({ view_mode: "queue" });
  assert.match(templateText(card.render()), /Queue fixture/);
  card.hass = { states: {} };
  assert.match(templateText(card.render()), /Сущности Herald сейчас недоступны/);
  card.hass = undefined;
  assert.match(templateText(card.render()), /Loading…/);
});

test("policy search, family, scope, and paging operate on live registry values", () => {
  const { card } = makeCard();
  const items = Array.from({ length: 25 }, (_, index) => policy({
    notification_key: `fixture.${index}`,
    title: `Fixture ${String(index).padStart(2, "0")}`,
    family: index % 2 ? "energy" : "laundry",
    active_attention: index === 24,
  }));
  assert.equal(card._filterPolicies(items)[0].notification_key, "fixture.24");
  card._setPolicyPage(3);
  assert.equal(card._paginatePolicies(items).items.length, 1);
  card._setPolicyPage(100);
  assert.equal(card._paginatePolicies(items).page, 3);
  card._togglePolicyExpanded("fixture.24");
  card._setPolicySearch("Fixture 24");
  assert.equal(card._policyPage, 1);
  assert.equal(card._policyExpanded, "");
  assert.equal(card._filterPolicies(items).length, 1);
  card._setPolicySearch("");
  card._setPolicyFamily("energy");
  assert.equal(card._filterPolicies(items).length, 12);
  card._setPolicyFamily("all");
  card._setPolicyScope("attention");
  assert.equal(card._filterPolicies(items).length, 1);
  assert.equal(card._paginatePolicies([]).totalPages, 0);
});

test("policy draft save, toggle, reset, and refresh call the expected HA services", async () => {
  const { card, calls } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "delivery_mode", "custom");
  card._setPolicyDraft(item.notification_key, "channels", "mobile_test, dashboard");
  card._setPolicyDraft(item.notification_key, "cooldown_override", "30");
  await card._savePolicy(item);
  assert.deepEqual(calls[0], {
    domain: "herald", service: "set_notification_policy", data: {
      notification_key: "fixture.washer", enabled: true, delivery_mode: "custom", channels: ["mobile_test", "dashboard"],
      users: null, target_room: null, presence: "any", quiet_hours: "inherit",
      cooldown_override: 30, level_override: "", notes: "",
    },
  });
  await card._togglePolicyEnabled(item);
  assert.equal(calls[1].data.enabled, false);
  await card._resetPolicy(item);
  assert.equal(calls[2].service, "reset_notification_policy");
  assert.equal(card._policyDrafts[item.notification_key], undefined);
  await card._refreshPolicies();
  assert.deepEqual(calls[3], { domain: "herald", service: "refresh_notification_registry", data: { force: true } });
  assert.equal(card._busyPolicy, "");
});

test("custom policy can deliberately save an empty channel selection", async () => {
  const { card, calls } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "delivery_mode", "custom");
  card._setPolicyDraft(item.notification_key, "channels", []);
  await card._savePolicy(item);
  assert.deepEqual(calls[0].data.channels, []);
});

test("flow, language, character, and mute controls preserve service contracts", async () => {
  const { card, calls } = makeCard();
  await card._toggleFlow("device_alerts", true);
  await card._setLanguage("select.test_language", { target: { value: "en" } });
  await card._setSelectOption("select.test_character", { target: { value: "jarvis" } });
  await card._toggleSwitch("switch.test_silent", false);
  assert.deepEqual(calls, [
    { domain: "herald", service: "set_flow_state", data: { flow: "device_alerts", enabled: false } },
    { domain: "select", service: "select_option", data: { entity_id: "select.test_language", option: "en" } },
    { domain: "select", service: "select_option", data: { entity_id: "select.test_character", option: "jarvis" } },
    { domain: "switch", service: "turn_on", data: { entity_id: "switch.test_silent" } },
  ]);
});

test("rejected service calls release busy state without hiding the failure", async () => {
  const { card } = makeCard();
  card.hass.callService = async () => { throw new Error("synthetic service failure"); };
  card.hass.callWS = async () => { throw new Error("synthetic service failure"); };
  card._setPolicyDraft("fixture.washer", "notes", "keep draft");
  await card._savePolicy(policy());
  assert.match(card._policyFeedback["fixture.washer"].message, /synthetic service failure/);
  assert.equal(card._policyDrafts["fixture.washer"].notes, "keep draft");
  assert.equal(card._policyDirty(policy()), true);
  assert.equal(card._busyPolicy, "");
  await assert.rejects(card._toggleFlow("device_alerts", true), /synthetic service failure/);
  assert.equal(card._busyFlow, "");
});

test("gzip asset decompresses to the exact shipped JavaScript", () => {
  assert.equal(gunzipSync(readFileSync(`${bundlePath}.gz`)).toString("utf8"), bundle);
});


test("inherit, disabled and deliberately empty custom have distinct visible meanings", () => {
  const { card } = makeCard();
  assert.match(card._policyRouteSummary({ delivery_mode: "inherit" }), /По общему правилу/);
  assert.match(card._policyRouteSummary({ delivery_mode: "disabled" }), /отключена/);
  assert.match(card._policyRouteSummary({ delivery_mode: "custom", channels: [] }), /доставки не будет/);
  assert.match(card._policyRouteSummary({ enabled: false, delivery_mode: "inherit" }), /отключена/);
  assert.doesNotMatch(templateText(card._renderPolicyTableRow(policy({ policy: { delivery_mode: "custom", channels: [] }, effective: { enabled: true, delivery_mode: "custom", channels: [] } }))), /наследовать/);
});

test("legacy disabled mode renders unchecked and enabling restores inherit atomically", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy({ policy: { enabled: true, delivery_mode: "disabled", notes: "keep this" }, effective: { enabled: false, delivery_mode: "disabled", channels: [] } });
  const checkbox = () => {
    const template = card._renderPolicyEditor(item);
    const index = template.strings.findIndex((part) => part.includes('class="policy-enabled"'));
    assert.notEqual(index, -1);
    return { checked: template.values[index], change: template.values[index + 1] };
  };
  assert.equal(checkbox().checked, false);
  assert.equal(card._policyDirty(item), false, "rendering preserves the saved legacy policy");
  await card._previewPolicy(item);
  assert.equal(wsCalls[0].service_data.policy.delivery_mode, "disabled");
  checkbox().change({ target: { checked: true } });
  assert.equal(checkbox().checked, true);
  assert.equal(card._policyPayload(item).enabled, true);
  assert.equal(card._policyPayload(item).delivery_mode, "inherit");
  assert.equal(card._policyPayload(item).notes, "keep this");
  assert.equal(card._policyRevisions[item.notification_key], 1, "one atomic draft change");
  assert.equal(card._policyPreviews[item.notification_key], undefined);
  card._setPolicyDraft(item.notification_key, "delivery_mode", "disabled");
  assert.equal(checkbox().checked, false, "selecting disabled also unchecks delivery");
  checkbox().change({ target: { checked: true } });
  checkbox().change({ target: { checked: false } });
  assert.equal(checkbox().checked, false);
  assert.equal(card._policyPayload(item).delivery_mode, "inherit");
  assert.equal(card._policyPayload(item).enabled, false);
});

test("filtered draft modes never infer channel availability from saved disabled or empty routes", () => {
  for (const savedMode of ["disabled", "custom"]) {
    const { card } = makeCard();
    const item = policy({ policy: { enabled: true, delivery_mode: savedMode, channels: [] }, effective: { enabled: savedMode !== "disabled", delivery_mode: savedMode, channels: [] } });
    for (const mode of ["text_only", "voice_only", "push_only"]) {
      card._setPolicyDraft(item.notification_key, "delivery_mode", mode);
      const text = templateText(card._renderPolicyEditor(item));
      assert.match(text, /итог определяется проверкой/);
      assert.doesNotMatch(text, /подходящих каналов пока нет/);
      assert.equal(card._policyRouteSummary(card._policyPayload(item)), `${card._friendlyDeliveryMode(mode)}; итог определяется проверкой`);
    }
  }
});

test("save uses actual server response, clears submitted draft, and discard never calls a service", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "notes", "saved note");
  assert.equal(card._policyDirty(item), true);
  await card._savePolicy(item);
  assert.equal(wsCalls[0].return_response, true);
  assert.equal(card._policyDirty(item), false);
  assert.equal(card._policyPayload(item).notes, "saved note");
  assert.match(card._policyFeedback[item.notification_key].message, /сохранено/);
  card._setPolicyDraft(item.notification_key, "notes", "discard this");
  card._discardPolicyDraft(item.notification_key);
  assert.equal(card._policyPayload(item).notes, "saved note");
  assert.equal(wsCalls.length, 1);
});

test("preview sends the unsaved full policy through response-only service with scenario and entry scope", async () => {
  const { card, wsCalls, calls } = makeCard();
  const item = policy();
  card.setConfig({ entry_id: "fixture-entry" });
  card._setPolicyDraft(item.notification_key, "delivery_mode", "custom");
  card._setPolicyDraft(item.notification_key, "channels", []);
  card._setPolicyDraft(item.notification_key, "notes", "unsaved");
  card._setPolicyScenario(item.notification_key, "quiet_hours");
  await card._previewPolicy(item);
  assert.deepEqual(wsCalls[0], {
    type: "call_service", domain: "herald", service: "preview_notification_policy", return_response: true,
    service_data: { notification_key: "fixture.washer", entry_id: "fixture-entry", scenario: "quiet_hours", policy: {
      enabled: true, delivery_mode: "custom", channels: [], level_override: "", cooldown_override: "", notes: "unsaved",
      users: null, target_room: null, presence: "any", quiet_hours: "inherit",
    } },
  });
  assert.equal(calls.length, 0);
  assert.equal(card._policyDirty(item), true);
  assert.match(templateText(card._renderPolicyEditor(item)), /Уведомления и команды устройствам не отправляются/);
  assert.match(templateText(card._renderPolicyEditor(item)), /время и условия автоматизаций остаются текущими/);
});

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
const previewResponse = { response: { explanation: { status: "deliver", summary: "Old response", channels: [] } } };

test("draft, scenario, and selection changes discard stale preview responses", async () => {
  for (const change of [
    (card) => card._setPolicyDraft("fixture.washer", "notes", "new draft"),
    (card) => card._setPolicyScenario("fixture.washer", "away"),
    (card) => card._togglePolicyExpanded("fixture.other"),
    (card) => card._setPolicySearch("other"),
  ]) {
    const { card } = makeCard();
    const pending = deferred();
    card.hass.callWS = () => pending.promise;
    const request = card._previewPolicy(policy());
    change(card);
    pending.resolve(previewResponse);
    await request;
    assert.equal(card._policyPreviews["fixture.washer"], undefined);
  }
});

test("late preview response cannot replace a newer request", async () => {
  const { card } = makeCard();
  const first = deferred();
  const second = deferred();
  let calls = 0;
  card.hass.callWS = () => ++calls === 1 ? first.promise : second.promise;
  const request1 = card._previewPolicy(policy());
  const request2 = card._previewPolicy(policy());
  second.resolve({ response: { explanation: { summary: "New response", channels: [] } } });
  await request2;
  first.resolve(previewResponse);
  await request1;
  assert.equal(card._policyPreviews["fixture.washer"].result.explanation.summary, "New response");
});

test("changes made during save stay in draft and server-normalized saved values are retained", async () => {
  const { card } = makeCard();
  const item = policy();
  const pending = deferred();
  card.hass.callWS = () => pending.promise;
  card._setPolicyDraft(item.notification_key, "notes", "first");
  const save = card._savePolicy(item);
  card._setPolicyDraft(item.notification_key, "notes", "newer");
  pending.resolve({ response: { ...item, policy: { enabled: true, delivery_mode: "inherit", channels: [], notes: "server normalized" } } });
  await save;
  assert.equal(card._policyPayload(item).notes, "newer");
  assert.equal(card._policyDirty(item), true);
  assert.match(card._policyFeedback[item.notification_key].message, /Более новые изменения/);
  card._discardPolicyDraft(item.notification_key);
  assert.equal(card._policyPayload(item).notes, "server normalized");
});

test("invalid interval and incomplete response do not report a successful save", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "cooldown_override", "-1");
  await card._savePolicy(item);
  assert.equal(wsCalls.length, 0);
  assert.equal(card._policyFeedback[item.notification_key].type, "error");
  card._setPolicyDraft(item.notification_key, "cooldown_override", "");
  card.hass.callWS = async () => ({});
  await card._savePolicy(item);
  assert.equal(card._policyFeedback[item.notification_key].type, "error");
});


test("preview explains setting provenance and later live decisions remain visible after save", async () => {
  const { card } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "notes", "saved");
  await card._savePolicy(item);
  const live = { ...item, last_decision: { summary: "Новое решение", at: "сейчас" } };
  assert.match(templateText(card._renderPolicyEditor(live)), /Новое решение/);
  const result = {
    explanation: { summary: "Проверено", channels: [], steps: [], warnings: [] },
    effective_settings: { "flow_cooldown:device_alerts": { value: 60, source: "runtime", inherited: 120, inherited_source: "options" } },
  };
  const text = templateText(card._renderPolicyExplanation(result));
  assert.match(text, /Откуда настройки/);
  assert.match(text, /Ручное изменение/);
  assert.match(text, /Базовое значение: 120 · Настройки интеграции/);
});

const targetDefaults = { users: null, target_room: null, presence: "any", quiet_hours: "inherit" };
const targetOverrides = { users: ["person.test_person"], target_room: "test_room", presence: "someone_home", quiet_hours: "text_only" };
function targets(value) {
  return JSON.parse(JSON.stringify(Object.fromEntries(Object.keys(targetDefaults).map((key) => [key, value[key]]))));
}

test("legacy policies normalize to inherited recipients and room with unchanged conditions", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy();
  assert.deepEqual(targets(card._policyPayload(item)), targetDefaults);
  assert.equal(card._policyDirty(item), false);
  assert.match(card._policyTargetSummary(item.policy, item), /Получатели по общему правилу.*Комната автоматически.*При любом присутствии.*Тихие часы по общему правилу/);
  await card._previewPolicy(item);
  assert.deepEqual(targets(wsCalls[0].service_data.policy), targetDefaults);
});

test("recipient, room and when overrides participate in every scenario preview, save and reset", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy();
  for (const [key, value] of Object.entries(targetOverrides)) card._setPolicyDraft(item.notification_key, key, value);
  assert.equal(card._policyDirty(item), true);
  for (const scenario of ["current", "quiet_hours", "away"]) {
    card._setPolicyScenario(item.notification_key, scenario);
    await card._previewPolicy(item);
    assert.deepEqual(targets(wsCalls.at(-1).service_data.policy), targetOverrides);
    assert.equal(wsCalls.at(-1).service_data.scenario, scenario);
  }
  await card._savePolicy(item);
  assert.deepEqual(targets(wsCalls.at(-1).service_data), targetOverrides);
  assert.equal(card._policyDirty(item), false);
  assert.deepEqual(targets(card._policyPayload(item)), targetOverrides);
  await card._resetPolicy(item);
  assert.equal(wsCalls.at(-1).service, "reset_notification_policy");
  assert.deepEqual(targets(card._policyPayload(item)), targetDefaults);
  assert.equal(card._policyDirty(item), false);
  assert.ok(wsCalls.every((request) => request.service !== "notify"));
});

test("null recipients and intentionally empty recipients remain different through draft, save and discard", async () => {
  const { card, wsCalls } = makeCard();
  const item = policy();
  card._setPolicyDraft(item.notification_key, "users", []);
  assert.match(templateText(card._renderPolicyEditor(item)), /Получатели не выбраны — доставки не будет/);
  assert.equal(card._policyDirty(item), true);
  await card._savePolicy(item);
  assert.deepEqual(wsCalls.at(-1).service_data.users, []);
  assert.deepEqual(targets(card._policyPayload(item)).users, []);
  card._setPolicyDraft(item.notification_key, "users", null);
  assert.equal(card._policyPayload(item).users, null);
  assert.equal(card._policyDirty(item), true);
  card._discardPolicyDraft(item.notification_key);
  assert.deepEqual(targets(card._policyPayload(item)).users, []);
  card._togglePolicyDraftUser(item.notification_key, "person.test_person", item);
  assert.deepEqual(targets(card._policyPayload(item)).users, ["person.test_person"]);
  card._togglePolicyDraftUser(item.notification_key, "person.test_person", item);
  assert.deepEqual(targets(card._policyPayload(item)).users, []);
});

test("unavailable saved users and rooms remain visible and intact with per-item or registry options", async () => {
  const { card, wsCalls } = makeCard();
  const registry = card.hass.states["sensor.herald_notification_center_status"].attributes.notification_registry;
  registry.user_options = [{ value: "person.test_person", label: "Тестовый получатель" }];
  registry.room_options = [{ value: "test_room", label: "Тестовая комната" }];
  const item = policy({ policy: { ...targetOverrides, users: ["person.unavailable"], target_room: "missing_room" } });
  const text = templateText(card._renderPolicyEditor(item));
  assert.match(text, /Тестовый получатель/);
  assert.match(text, /Тестовая комната/);
  assert.match(text, /person\.unavailable \(недоступно\)/);
  assert.match(text, /missing_room \(недоступно\)/);
  assert.match(text, /его могут услышать и другие люди/);
  assert.match(text, /без перехода в другую комнату/);
  assert.match(text, /Отложенная отправка и расписание здесь не задаются/);
  card._setPolicyDraft(item.notification_key, "notes", "Only note changed");
  await card._savePolicy(item);
  assert.deepEqual(wsCalls.at(-1).service_data.users, ["person.unavailable"]);
  assert.equal(wsCalls.at(-1).service_data.target_room, "missing_room");
  const unavailable = card._policyTargetOptions({ ...item, available_users: [] }, "users", ["person.test_person"]);
  assert.equal(unavailable[0].label, "person.test_person (недоступно)", "empty per-item options are authoritative");
  assert.equal(card._policyTargetOptions({ ...item, available_rooms: [{ value: "test_room", label: "Своя комната" }] }, "rooms")[0].label, "Своя комната");
});

test("every new rule field invalidates a pending preview", async () => {
  for (const [field, value] of Object.entries(targetOverrides)) {
    const { card } = makeCard();
    const pending = deferred();
    card.hass.callWS = () => pending.promise;
    const preview = card._previewPolicy(policy());
    card._setPolicyDraft("fixture.washer", field, value);
    pending.resolve(previewResponse);
    await preview;
    assert.equal(card._policyPreviews["fixture.washer"], undefined, field);
  }
});

test("partial draft edits during save retain new target fields and nullable recipients", async () => {
  const { card } = makeCard();
  const item = policy({ policy: { ...targetOverrides } });
  card.hass.states["sensor.herald_notification_center_status"].attributes.notification_registry.items = [item];
  const pending = deferred();
  card.hass.callWS = () => pending.promise;
  card._setPolicyDraft(item.notification_key, "notes", "submitted note");
  const save = card._savePolicy(item);
  card._setPolicyDraft(item.notification_key, "users", null);
  card._setPolicyDraft(item.notification_key, "presence", "nobody_home");
  pending.resolve({ response: { ...item, policy: { ...item.policy, notes: "submitted note" } } });
  await save;
  assert.deepEqual(targets(card._policyPayload(item)), { ...targetOverrides, users: null, presence: "nobody_home" });
  assert.equal(card._policyDirty(item), true);
  card._discardPolicyDraft(item.notification_key);
  assert.deepEqual(targets(card._policyPayload(item)), targetOverrides);
  assert.equal(card._policyPayload(item).notes, "submitted note");
});

test("new target-only overrides appear as customized while legacy defaults do not", () => {
  const { card } = makeCard();
  assert.equal(card._policyCustomized(policy()), false);
  for (const [key, value] of Object.entries({ ...targetOverrides, users: [] })) {
    const item = policy({ policy: { [key]: value } });
    assert.equal(card._policyCustomized(item), true, key);
    card._setPolicyScope("customized");
    assert.equal(card._filterPolicies([policy(), item]).length, 1, key);
  }
});

function configurationReport(overrides = {}) {
  return {
    schema_version: 1, checked_at: "2026-09-30T12:00:00+00:00",
    restrictions: [{ code: "quiet_hours", title: "Сейчас тихие часы", detail: "Правила ограничивают голос." }],
    summary: { total: 1, enabled: 1, attention: 0, not_checked: 0 },
    limitations: ["Доставка уведомлений не выполнялась и не подтверждена."], truncated: false,
    channels: [{ name: "synthetic_phone", type: "mobile_app", enabled: true, min_level: "info", quiet_hours_policy: "default", user: "Тестовый получатель", rooms: [],
      controls: { enabled: "switch.renamed_fixture", min_level: "select.renamed_fixture" },
      settings: { enabled: { value: true, source: "runtime", inherited: false, inherited_source: "options" }, min_level: { value: "info", source: "options" } },
      status: "configured", checks: [{ code: "service", status: "ok", message: "Сервис зарегистрирован." }],
    }], ...overrides,
  };
}
function installConfiguration(card, report = configurationReport()) {
  card.hass.states["sensor.herald_notification_center_status"].attributes.configuration_check = report;
  card.hass.states["switch.renamed_fixture"] = { state: "on", attributes: {} };
  card.hass.states["select.renamed_fixture"] = { state: "info", attributes: { options: ["info", "warning", "critical"] } };
  return report;
}

test("general, overview, controls and full show restrictions with channels in control surfaces", () => {
  for (const tag of ["ha-herald-general", "ha-herald-overview", "ha-herald-controls", "herald-card"]) {
    const { card } = makeCard(tag);
    installConfiguration(card);
    const text = templateText(card.render());
    assert.match(text, /Сейчас тихие часы/);
    assert.match(text, /не подтверждение доставки/);
    if (tag !== "ha-herald-general") {
      assert.match(text, /Каналы доставки/);
      assert.match(text, /Локально настроен/);
      assert.match(text, /Откуда настройки на момент проверки/);
      assert.match(text, /Ручное изменение/);
      assert.match(text, /Базовое значение: Выключено/);
    }
  }
});

test("legacy report fallback remains read-only and never guesses control IDs", () => {
  const { card } = makeCard();
  const attributes = card.hass.states["sensor.herald_notification_center_status"].attributes;
  attributes.mute_all = true;
  attributes.topology = { channels: [{ name: "renamed_fixture", type: "mobile_app", enabled: true }] };
  card.hass.states["switch.herald_channel_renamed_fixture_enabled"] = { state: "on", attributes: {} };
  assert.match(templateText(card._renderConfigurationOverview()), /Общее заглушение включено/);
  assert.match(templateText(card._renderChannels()), /Показана только объявленная конфигурация/);
  assert.match(templateText(card._renderChannels()), /Сущность управления каналом не указана/);
  assert.equal(card._channelControlId(attributes.topology.channels[0], "enabled"), null);
  attributes.configuration_check = configurationReport({ schema_version: 2 });
  assert.equal(card._configurationReport(), null);
});

test("missing and unavailable controls are visible without claiming active mute or free room", () => {
  const { card } = makeCard();
  for (const state of [undefined, "unknown", "unavailable"]) {
    if (state === undefined) delete card.hass.states["switch.test_silent"];
    else card.hass.states["switch.test_silent"] = { state, attributes: {} };
    const mute = templateText(card._renderMute("switch.test_silent"));
    assert.match(mute, /Состояние заглушения неизвестно/);
    assert.doesNotMatch(mute, /Уведомления активны/);
    card.hass.states["binary_sensor.test_room"] = state ? { state, attributes: {} } : undefined;
    const room = templateText(card._renderRoom({ room: "fixture", sensor: "binary_sensor.test_room", fallback: "switch.missing" }));
    assert.match(room, /присутствие неизвестно/);
    assert.doesNotMatch(room, /свободно/);
  }
  assert.match(templateText(card._renderLanguage("select.missing")), /Управление недоступно/);
  assert.match(templateText(card._renderCharacter("select.missing")), /Управление недоступно/);
});

test("channel edits use supplied renamed entity IDs and require HA state acknowledgement", async () => {
  const { card } = makeCard();
  const report = installConfiguration(card);
  const pending = deferred();
  const calls = [];
  card.hass.callService = (...args) => { calls.push(JSON.parse(JSON.stringify(args))); return pending.promise; };
  const entityId = card._channelControlId(report.channels[0], "enabled");
  const operation = card._toggleSwitch(entityId, true);
  await card._toggleSwitch(entityId, true);
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], ["switch", "turn_off", { entity_id: "switch.renamed_fixture" }]);
  pending.resolve();
  await operation;
  assert.equal(card._controlActions[entityId].phase, "awaiting");
  assert.match(templateText(card._renderChannelControl(report.channels[0])), /<strong>Включён<\/strong>/);
  assert.match(templateText(card._renderControlFeedback(entityId)), /Ожидаем новое состояние/);
  card.hass.states[entityId].state = "off";
  card._reconcileControlActions();
  assert.equal(card._controlActions[entityId].phase, "success");
  assert.match(templateText(card._renderChannelControl(report.channels[0])), /<strong>Выключен<\/strong>/);
});

test("select change keeps server value while pending and displays rejection without changing it", async () => {
  const { card } = makeCard();
  installConfiguration(card);
  const pending = deferred();
  card.hass.callService = () => pending.promise;
  const target = { value: "warning" };
  const request = card._setSelectOption("select.renamed_fixture", { target });
  assert.equal(target.value, "info");
  pending.resolve();
  await request;
  assert.equal(card._controlActions["select.renamed_fixture"].phase, "awaiting");
  card._expireControlAction("select.renamed_fixture", card._controlActions["select.renamed_fixture"].token);
  assert.match(templateText(card._renderControlFeedback("select.renamed_fixture")), /Подтверждение.*не получено/);
  card.hass.callService = async () => { throw new Error("Synthetic HA denial"); };
  await card._setSelectOption("select.renamed_fixture", { target: { value: "critical" } });
  assert.equal(card.hass.states["select.renamed_fixture"].state, "info");
  assert.match(templateText(card._renderControlFeedback("select.renamed_fixture")), /Synthetic HA denial/);
});

test("invalid or missing controls never call services; timed-out late responses cannot claim success", async () => {
  const { card, calls } = makeCard();
  await card._toggleSwitch("switch.missing", false);
  await card._toggleSwitch("script.fixture", false);
  await card._setSelectOption("select.test_language", { target: { value: "not_an_option" } });
  assert.equal(calls.length, 0);
  const pending = deferred();
  card.hass.callService = () => pending.promise;
  const operation = card._toggleSwitch("switch.test_silent", false);
  const token = card._controlActions["switch.test_silent"].token;
  card._expireControlAction("switch.test_silent", token);
  pending.resolve();
  await operation;
  assert.equal(card._controlActions["switch.test_silent"].phase, "error");
  assert.equal(card._controlTimers.size, 0);
});

test("configuration refresh is response-only, scoped and rejects malformed or failing responses", async () => {
  const { card, calls } = makeCard();
  card.setConfig({ entry_id: "synthetic-entry" });
  const report = installConfiguration(card);
  const requests = [];
  card.hass.callWS = async (request) => { requests.push(JSON.parse(JSON.stringify(request))); return { response: { ...report, checked_at: "new" } }; };
  await card._refreshConfiguration();
  assert.deepEqual(requests, [{ type: "call_service", domain: "herald", service: "configuration_check", service_data: { entry_id: "synthetic-entry" }, return_response: true }]);
  assert.equal(card._configurationReport().checked_at, "new");
  assert.match(card._configurationFeedback.message, /без отправки/);
  card.hass.callWS = async () => ({ response: {} });
  await card._refreshConfiguration();
  assert.equal(card._configurationFeedback.type, "error");
  assert.equal(card._configurationReport().checked_at, "new");
  card.hass.callWS = async () => { throw new Error("Synthetic report failure"); };
  await card._refreshConfiguration();
  assert.equal(card._configurationBusy, false);
  assert.match(card._configurationFeedback.message, /Synthetic report failure/);
  assert.equal(calls.length, 0);
});

test("fresh sensor report, setting edits and card scope changes isolate stale check responses", async () => {
  for (const change of [
    (card) => { card.hass.states["sensor.herald_notification_center_status"].attributes.configuration_check = configurationReport({ checked_at: "fresh sensor" }); },
    (card) => card._toggleSwitch("switch.renamed_fixture", true),
    (card) => card.setConfig({ entry_id: "another-entry" }),
  ]) {
    const { card } = makeCard();
    installConfiguration(card);
    const pending = deferred();
    let requests = 0;
    card.hass.callWS = () => { requests++; return pending.promise; };
    const refresh = card._refreshConfiguration();
    await card._refreshConfiguration();
    assert.equal(requests, 1);
    await change(card);
    pending.resolve({ response: configurationReport({ checked_at: "stale response" }) });
    await refresh;
    assert.notEqual(card._configurationReport()?.checked_at, "stale response");
    assert.equal(card._configurationBusy, false);
  }
});


test("restriction opens only an existing exact entity without issuing a service", () => {
  const { card, calls, wsCalls } = makeCard("ha-herald-controls");
  const report = installConfiguration(card);
  report.restrictions[0].entity_id = "switch.renamed_fixture";
  assert.match(templateText(card._renderConfigurationOverview()), /Открыть настройку/);
  const events = [];
  card.dispatchEvent = (event) => events.push(event);
  card._openSetting("switch.renamed_fixture");
  card._openSetting("switch.missing");
  card._openSetting(null);
  assert.equal(events.length, 1);
  assert.equal(events[0].type, "hass-more-info");
  assert.equal(events[0].detail.entityId, "switch.renamed_fixture");
  assert.equal(events[0].bubbles, true);
  assert.equal(events[0].composed, true);
  assert.equal(calls.length + wsCalls.length, 0);
  report.restrictions[0].entity_id = "switch.missing";
  assert.doesNotMatch(templateText(card._renderConfigurationOverview()), /Открыть настройку/);
  assert.equal(card._formatCheckedAt("not a date"), "время не указано");
  assert.match(card._formatCheckedAt(report.checked_at), /30 сентября/);
});


test("ownerless personal channels are not described as shared channels", () => {
  const { card } = makeCard();
  const report = installConfiguration(card);
  for (const type of ["mobile_app", "telegram"]) {
    const text = templateText(card._renderChannelControl({ ...report.channels[0], type, user: null }));
    assert.match(text, /Владелец не указан/);
    assert.doesNotMatch(text, /Общий канал/);
  }
  assert.match(templateText(card._renderChannelControl({ ...report.channels[0], type: "dashboard", user: null })), /Общий канал/);
});


test("compact panels use native theme styling without dropping policy actions", () => {
  const { card } = makeCard("ha-herald-policies");
  card.setConfig({ type: "custom:ha-herald-policies", compact: true });
  const text = templateText(card.render());
  assert.match(text, /panel policy-panel compact-panel/);
  assert.match(text, /Проверить черновик|Редактировать|Открыть/);
  assert.match(text, /Тестовая стирка/);
  card.setConfig({ type: "custom:ha-herald-policies" });
  assert.doesNotMatch(templateText(card.render()), /compact-panel/);
});
