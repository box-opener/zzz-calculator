import { describe, expect, it } from "vitest";
import {
  conditionValuesForViews,
  matchingMoveVariantIndexes,
  projectMoveOptions,
  reconcileEditorState,
  resolveAuthoritativeConditionContext,
  selectMoveVariantConditions,
  stackValueForDisplay,
} from "./editorState";

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

  it("uses a new rule's maximum by default while preserving manual layers through a v2-shaped refresh", () => {
    const previousWithSelections = {
      ...previous,
      stacks: { zero: 0, middle: 3 },
    };
    const rules = ["zero", "middle", "new"].map((rule_id) => ({
      rule_id,
      availability: "available",
      enabled_by_default: true,
      toggleable: true,
      stack: { default: 6, minimum: 0, maximum: 6 },
    }));
    // A v2 equipment/build import refreshes editor definitions but contains no
    // scenario stack fields, so the current explicit scenario choices survive.
    const refreshed = reconcileEditorState(
      previousWithSelections,
      { conditions: [], parameters: [], rules, triggers: [] },
      ["character:ye"],
    );

    expect(stackValueForDisplay(undefined, rules[2].stack.default, rules[2].stack.minimum)).toBe(6);
    expect(refreshed.stacks).toEqual({ zero: 0, middle: 3 });
    expect(stackValueForDisplay(refreshed.stacks.zero, rules[0].stack.default, rules[0].stack.minimum)).toBe(0);
    expect(stackValueForDisplay(refreshed.stacks.middle, rules[1].stack.default, rules[1].stack.minimum)).toBe(3);
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

  it("prunes the third member's active controls when a three-person team is reduced", () => {
    const threeMemberState = reconcileEditorState({
      conditionValues: { "condition:three": true },
      parameterValues: { "parameter:three": 2 },
      enabledRules: new Set(["rule:three"]),
      disabledRules: new Set(),
      triggerActors: { "trigger:three": "character:three" },
      stacks: { "rule:three": 2 },
    }, {
      conditions: [{ condition_id: "condition:three", value: false, editable: true }],
      parameters: [{ parameter_id: "parameter:three", value: 1, minimum: 0, maximum: 4 }],
      rules: [{ rule_id: "rule:three", availability: "available", enabled_by_default: true, toggleable: true, stack: { default: 1, minimum: 0, maximum: 4 } }],
      triggers: [{ input_id: "trigger:three", actor_options: ["character:three"], selected_actor: "character:three" }],
    }, ["character:one", "character:two", "character:three"]);
    const reduced = reconcileEditorState(threeMemberState, {
      conditions: [],
      parameters: [],
      rules: [],
      triggers: [],
    }, ["character:one", "character:two"]);

    expect(reduced.conditionValues).toEqual({});
    expect(reduced.parameterValues).toEqual({});
    expect(reduced.enabledRules).toEqual(new Set());
    expect(reduced.disabledRules).toEqual(new Set());
    expect(reduced.triggerActors).toEqual({});
    expect(reduced.stacks).toEqual({});
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

describe("move variant projection", () => {
  const moves = [
    {
      entry_id: "move:plain",
      label: "普通攻击：一击",
      multiplier_relation: "complete",
      variants: [{ variant_id: "variant:plain", label: "伤害倍率", condition_ids: [] }],
    },
    {
      entry_id: "move:charge",
      label: "普通攻击：星芒圆舞曲",
      multiplier_relation: "mutually-exclusive-variant",
      variants: [
        { variant_id: "variant:charge-1", label: "一段蓄力伤害倍率", condition_ids: ["charge-1"] },
        { variant_id: "variant:charge-2", label: "二段蓄力伤害倍率", condition_ids: ["charge-2"] },
      ],
    },
  ] as const;

  it("projects every mutually-exclusive variant into the existing move selector", () => {
    expect(projectMoveOptions(moves)).toEqual([
      expect.objectContaining({ optionKey: "move:plain", entryId: "move:plain", label: "普通攻击：一击" }),
      expect.objectContaining({
        optionKey: "move:charge::variant:charge-1",
        entryId: "move:charge",
        label: "普通攻击：星芒圆舞曲（一段蓄力）",
        variantIndex: 0,
      }),
      expect.objectContaining({
        optionKey: "move:charge::variant:charge-2",
        entryId: "move:charge",
        label: "普通攻击：星芒圆舞曲（二段蓄力）",
        variantIndex: 1,
      }),
    ]);
  });

  it("atomically switches variant conditions and preserves static/shared values", () => {
    const sharedMove = {
      entry_id: "move:shared",
      label: "共享条件招式",
      multiplier_relation: "mutually-exclusive-variant",
      variants: [
        { variant_id: "variant:a", label: "A", condition_ids: ["shared", "a"] },
        { variant_id: "variant:b", label: "B", condition_ids: ["shared", "b"] },
      ],
    } as const;
    expect(selectMoveVariantConditions(
      { shared: true, a: true, b: false, static: true },
      sharedMove,
      1,
      [
        { condition_id: "shared", editable: false },
        { condition_id: "static", editable: false },
      ],
    )).toEqual({ shared: true, a: false, b: true, static: true });
    expect(matchingMoveVariantIndexes(sharedMove, { shared: true, a: false, b: true })).toEqual([1]);
  });
});
