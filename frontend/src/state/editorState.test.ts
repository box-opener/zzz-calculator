import { describe, expect, it } from "vitest";
import { conditionValuesForViews, reconcileEditorState, resolveAuthoritativeConditionContext } from "./editorState";

const previous = {
  conditionValues: { active: true },
  parameterValues: { count: 5 },
  enabledRules: new Set<string>(),
  disabledRules: new Set(["hedao"]),
  triggerActors: { entry: "character:ye" },
  stacks: { c1: 2 },
};

describe("reconcileEditorState", () => {
  it("preserves user selections across definition refresh", () => {
    const next = reconcileEditorState(previous, {
      conditions: [{ condition_id: "active", value: false, editable: true }],
      parameters: [{ parameter_id: "count", value: null, minimum: 0, maximum: 8 }],
      rules: [{ rule_id: "hedao", availability: "available", enabled_by_default: true, toggleable: true, stack: { default: null, minimum: null, maximum: null } }],
      triggers: [{ input_id: "entry", actor_options: ["character:ye"], selected_actor: null }],
    }, ["character:ye"]);
    expect(next.conditionValues.active).toBe(true);
    expect(next.parameterValues.count).toBe(5);
    expect(next.enabledRules.has("hedao")).toBe(false);
    expect(next.disabledRules.has("hedao")).toBe(true);
    expect(next.triggerActors.entry).toBe("character:ye");
  });

  it("prunes stale actors, stacks, and rules", () => {
    const next = reconcileEditorState(previous, {
      conditions: [],
      parameters: [{ parameter_id: "count", value: null, minimum: 0, maximum: 1 }],
      rules: [{ rule_id: "c1", availability: "unavailable", enabled_by_default: false, toggleable: false, stack: { default: 0, minimum: 0, maximum: 3 } }],
      triggers: [{ input_id: "entry", actor_options: ["character:astra"], selected_actor: null }],
    }, ["character:astra"]);
    expect(next.parameterValues.count).toBe(null);
    expect(next.stacks).toEqual({});
    expect(next.triggerActors).toEqual({});
    expect(next.enabledRules).toEqual(new Set());
    expect(next.disabledRules).toEqual(new Set());
  });

  it("does not synthesize a trigger actor when the server leaves it unresolved", () => {
    const next = reconcileEditorState({ ...previous, triggerActors: {} }, {
      conditions: [],
      parameters: [],
      rules: [],
      triggers: [{ input_id: "entry", actor_options: ["character:ye"], selected_actor: null }],
    }, ["character:ye"]);
    expect(next.triggerActors).toEqual({});
  });

  it("keeps an explicitly disabled rule off when ARIA makes it temporarily unavailable", () => {
    const blocked = reconcileEditorState({
      ...previous,
      conditionValues: { "condition:astra:aria-active": false },
      enabledRules: new Set(),
      disabledRules: new Set(["rule:astra:1311:cinema2"]),
    }, {
      conditions: [{ condition_id: "condition:astra:aria-active", value: false, editable: true }],
      parameters: [],
      rules: [{ rule_id: "rule:astra:1311:cinema2", availability: "unavailable", enabled_by_default: false, toggleable: false, stack: { default: null, minimum: null, maximum: null } }],
      triggers: [],
    }, ["character:1311"]);
    const restored = reconcileEditorState(blocked, {
      conditions: [{ condition_id: "condition:astra:aria-active", value: true, editable: true }],
      parameters: [],
      rules: [{ rule_id: "rule:astra:1311:cinema2", availability: "available", enabled_by_default: true, toggleable: true, stack: { default: null, minimum: null, maximum: null } }],
      triggers: [],
    }, ["character:1311"]);

    expect(blocked.disabledRules.has("rule:astra:1311:cinema2")).toBe(true);
    expect(restored.enabledRules.has("rule:astra:1311:cinema2")).toBe(false);
    expect(restored.disabledRules.has("rule:astra:1311:cinema2")).toBe(true);
  });
});

describe("resolveAuthoritativeConditionContext", () => {
  it("uses the latest character value for static conditions", () => {
    expect(resolveAuthoritativeConditionContext(
      { mingxin: false, selected: true },
      [
        { condition_id: "mingxin", value: true, editable: false },
        { condition_id: "selected", value: false, editable: true },
      ],
    )).toEqual({ mingxin: true, selected: true });
  });

  it("preserves user values and leaves equipment-only values intact", () => {
    expect(resolveAuthoritativeConditionContext(
      { selected: true, "wengine:active": true },
      [{ condition_id: "selected", value: false, editable: true }],
    )).toEqual({ selected: true, "wengine:active": true });
  });

  it("keeps ARIA true through a refresh whose response still carries the old default", () => {
    const selected = resolveAuthoritativeConditionContext(
      { "condition:astra:aria-active": true },
      [{ condition_id: "condition:astra:aria-active", value: false, editable: true }],
    );
    expect(selected["condition:astra:aria-active"]).toBe(true);
  });
});

describe("conditionValuesForViews", () => {
  it("emits editable ARIA values and excludes static response-only conditions", () => {
    expect(conditionValuesForViews(
      { "condition:astra:aria-active": true, "condition:static": false },
      [
        { condition_id: "condition:astra:aria-active", value: false, editable: true },
        { condition_id: "condition:static", value: true, editable: false },
      ],
    )).toEqual({ "condition:astra:aria-active": true });
  });
});
