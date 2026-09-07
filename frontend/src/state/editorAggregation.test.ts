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
  rule_items: [{ id: `${source}-rule:${id}` }],
  scenario_conditions: [{ id: `${source}-condition:${id}` }],
  scenario_parameters: [{ id: `${source}-parameter:${id}` }],
  scenario_trigger_inputs: [{ id: `${source}-trigger:${id}` }],
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
});
