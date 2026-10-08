// Pure presentation helpers. Never infer successful delivery from a channel list.
export const DASHBOARD_TABS = [
  ["overview", "Обзор", "mdi:view-dashboard"],
  ["rules", "Правила", "mdi:cog"],
  ["delivery", "Доставка", "mdi:send"],
  ["analytics", "Аналитика", "mdi:chart-bar"],
  ["controls", "Управление", "mdi:wrench"],
  ["diagnostics", "Диагностика", "mdi:pulse"],
];

export function eventIdentity(item, index = 0) {
  return String(item?.notification_id || `${item?.timestamp ?? ""}|${item?.event ?? item?.title ?? ""}|${index}`);
}

export function eventOutcome(item) {
  const results = Array.isArray(item?.results) ? item.results : [];
  const sent = results.filter((result) => result.status === "sent").length;
  const errors = results.filter((result) => result.status === "error").length;
  if (errors) return { label: sent ? `Отправки: ${sent} · Ошибки: ${errors}` : `Ошибки: ${errors}`, tone: "error" };
  if (sent) return { label: `Отправлено в ${sent} ${sent === 1 ? "канал" : sent < 5 ? "канала" : "каналов"}`, tone: "success" };
  if (results.some((result) => result.status === "dropped")) return { label: "Доставка пропущена", tone: "warning" };
  return { label: "Результат отправки не указан", tone: "muted" };
}

export function eventIcon(item) {
  const code = `${item?.event ?? ""} ${item?.flow ?? ""} ${item?.title ?? ""}`.toLowerCase();
  if (/washer|laundry|стир/.test(code)) return "mdi:washing-machine";
  if (/battery|батар|заряд/.test(code)) return "mdi:battery-alert-variant-outline";
  if (/timer|таймер/.test(code)) return "mdi:timer-sand";
  if (/report|brief|отч|бриф/.test(code)) return "mdi:text-box-outline";
  if (/security|alarm|охран/.test(code)) return "mdi:shield-home-outline";
  return "mdi:bell-outline";
}

export function ruleForEvent(item, registry) {
  if (!item) return null;
  const key = item.notification_key ?? item.explanation?.notification_key;
  if (key) return registry.find((rule) => rule.notification_key === key) ?? null;
  // Older records did not retain the registry key. Only a unique exact match is safe.
  const matches = registry.filter((rule) => rule.notification_key === item.event || rule.event === item.event);
  return matches.length === 1 ? matches[0] : null;
}

export function knownCounter(value) {
  return value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? value : "—";
}
