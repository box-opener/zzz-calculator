import { describe, expect, it } from "vitest";
import { reconcileEditorState } from "./editorState";

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
});
