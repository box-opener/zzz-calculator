import { describe, expect, it } from "vitest";
import { aggregateEditorViews } from "./editorAggregation";

const characterView = (id: string) => ({
  rule_items: [{ id: `character-rule:${id}` }],
  scenario_conditions: [{ id: `character-condition:${id}` }],
  scenario_parameters: [{ id: `character-parameter:${id}` }],
  scenario_trigger_inputs: [{ id: `character-trigger:${id}` }],
  compile_config_fields: [{ id: `config:${id}` }],
});

const equipmentView = (id: string, source: string) => ({
  rule_items: [{
    id: `${source}-rule:${id}`,
    rule_id: `${source}-rule:${id}`,
    eligibility: "eligible",
    condition_ids: [`${source}-condition:${id}`],
    condition_not_ids: [],
  }],
  scenario_conditions: [{ id: `${source}-condition:${id}`, condition_id: `${source}-condition:${id}` }],
  scenario_parameters: [{ id: `${source}-parameter:${id}` }],
  scenario_trigger_inputs: [{ id: `${source}-trigger:${id}`, rule_item_id: `${source}-rule:${id}` }],
});

describe("aggregateEditorViews", () => {
  it("aggregates all three active members and their equipment in stable order", () => {
    const team = ["character:one", "character:two", "character:three"];
    const result = aggregateEditorViews(
      team,
      Object.fromEntries(team.map((id) => [id, characterView(id)])),
      {
        "character:one": equipmentView("character:one", "wengine"),
        "character:three": equipmentView("character:three", "wengine"),
      },
      { "character:two": equipmentView("character:two", "drive") },
    );

    expect(result.ruleItems.map((item) => item.id)).toEqual([
      "character-rule:character:one",
      "wengine-rule:character:one",
      "character-rule:character:two",
      "drive-rule:character:two",
      "character-rule:character:three",
      "wengine-rule:character:three",
    ]);
    expect(result.configFields.map((item) => item.owner)).toEqual(team);
    expect(result.conditions).toHaveLength(6);
    expect(result.parameters).toHaveLength(6);
    expect(result.triggers).toHaveLength(6);
  });

  it("prunes a removed member by projecting only the active team ids", () => {
    const views = {
      "character:one": characterView("character:one"),
      "character:two": characterView("character:two"),
      "character:three": characterView("character:three"),
    };
    const result = aggregateEditorViews(["character:one", "character:two"], views);
    expect(result.ruleItems.map((item) => item.id)).toEqual([
      "character-rule:character:one",
      "character-rule:character:two",
    ]);
    expect(result.conditions.every((item) => !item.id.includes("three"))).toBe(true);
  });

  it("hides equipment conditions referenced only by ineligible rules but keeps eligible false states", () => {
    const ye = "character:1431";
    const astra = "character:1311";
    const assaultCondition = "condition:drive-disc:32600:owner:character_1431:assault-target-active";
    const mismatchedWeaponCondition = "condition:wengine:14131:owner:1431:damage-buff-active";
    const matchedWeaponCondition = "condition:wengine:14131:owner:1311:damage-buff-active";
    const sharedCondition = "condition:shared-equipment-state";
    type Rule = {
      rule_id: string;
      eligibility: string;
      availability: string;
      condition_ids: readonly string[];
      condition_not_ids: readonly string[];
      stack: { default: number | null; minimum: number | null; maximum: number | null };
    };
    type Condition = { condition_id: string; value: boolean; editable: boolean };
    type Trigger = { input_id: string; rule_item_id: string };
    const driveRules: Rule[] = [
      {
        rule_id: "rule:drive-disc:31000:owner:character_1431:4pc:attack-stacks",
        eligibility: "eligible",
        availability: "available",
        condition_ids: [],
        condition_not_ids: [],
        stack: { default: 3, minimum: 0, maximum: 3 },
      },
      {
        rule_id: "rule:drive-disc:32600:owner:character_1431:4pc:assault-target-damage",
        eligibility: "ineligible",
        availability: "unavailable",
        condition_ids: [assaultCondition],
        condition_not_ids: [],
        stack: { default: null, minimum: null, maximum: null },
      },
    ];
    const wrongWeaponRule: Rule = {
      rule_id: "rule:wengine:14131:owner:1431:team-damage",
      eligibility: "ineligible",
      availability: "unavailable",
      condition_ids: [mismatchedWeaponCondition, sharedCondition],
      condition_not_ids: [],
      stack: { default: 2, minimum: 0, maximum: 2 },
    };
    const rightWeaponRule: Rule = {
      rule_id: "rule:wengine:14131:owner:1311:team-damage",
      eligibility: "eligible",
      availability: "unavailable",
      condition_ids: [matchedWeaponCondition, sharedCondition],
      condition_not_ids: [],
      stack: { default: 2, minimum: 0, maximum: 2 },
    };
    const result = aggregateEditorViews<Rule, Condition, unknown, Trigger, unknown>(
      [ye, astra],
      {},
      {
        [ye]: {
          rule_items: [wrongWeaponRule],
          scenario_conditions: [
            { condition_id: mismatchedWeaponCondition, value: false, editable: true },
            { condition_id: sharedCondition, value: false, editable: true },
          ],
          scenario_trigger_inputs: [
            { input_id: "trigger:wrong", rule_item_id: wrongWeaponRule.rule_id },
          ],
        },
        [astra]: {
          rule_items: [rightWeaponRule],
          scenario_conditions: [
            { condition_id: matchedWeaponCondition, value: false, editable: true },
            { condition_id: sharedCondition, value: false, editable: true },
          ],
          scenario_trigger_inputs: [
            { input_id: "trigger:right", rule_item_id: rightWeaponRule.rule_id },
          ],
        },
      },
      {
        [ye]: {
          rule_items: driveRules,
          scenario_conditions: [
            { condition_id: assaultCondition, value: false, editable: true },
          ],
          scenario_trigger_inputs: [],
        },
      },
    );

    expect(result.ruleItems.map((rule) => rule.rule_id)).toEqual([
      wrongWeaponRule.rule_id,
      driveRules[0].rule_id,
      driveRules[1].rule_id,
      rightWeaponRule.rule_id,
    ]);
    expect(result.ruleItems.find((rule) => rule.rule_id === driveRules[0].rule_id)?.stack.default).toBe(3);
    expect(result.conditions.map((condition) => condition.condition_id)).toEqual([
      matchedWeaponCondition,
      sharedCondition,
    ]);
    expect(result.conditions.every((condition) => condition.value === false)).toBe(true);
    expect(result.triggers.map((trigger) => trigger.input_id)).toEqual(["trigger:right"]);
  });
});
