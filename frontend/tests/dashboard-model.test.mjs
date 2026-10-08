import assert from "node:assert/strict";
import test from "node:test";
import { eventOutcome, ruleForEvent, knownCounter } from "../dashboard-model.js";

test("only recorded sent results count as transport sends; failures remain visible", () => {
  assert.match(eventOutcome({ channels: ["voice", "push"] }).label, /не указан/);
  assert.deepEqual(eventOutcome({ results: [{ status: "sent" }, { status: "error" }] }), { label: "Отправки: 1 · Ошибки: 1", tone: "error" });
  assert.equal(eventOutcome({ results: [{ status: "dropped" }] }).tone, "warning");
  assert.equal(eventOutcome({ results: [{ status: "planned" }] }).tone, "muted");
  assert.equal(eventOutcome({ results: [{ status: "sent" }] }).label, "Отправлено в 1 канал");
});

test("legacy event rule link is disabled when identity is ambiguous", () => {
  const a = { notification_key: "a", event: "washer" };
  const b = { notification_key: "b", event: "washer" };
  assert.equal(ruleForEvent({ event: "washer" }, [a, b]), null);
  assert.equal(ruleForEvent({ notification_key: "b", event: "washer" }, [a, b]), b);
  assert.equal(ruleForEvent({ event: "washer" }, [a]), a);
  assert.equal(ruleForEvent(null, [a]), null);
  assert.equal(ruleForEvent({ notification_key: "removed", event: "washer" }, [a]), null);
});

test("missing counters are explicit unknowns instead of fabricated zeroes", () => {
  for (const value of [null, undefined, "", "unknown", "unavailable"]) assert.equal(knownCounter(value), "—");
  assert.equal(knownCounter(0), 0);
});
