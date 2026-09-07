import { describe, expect, it } from "vitest";
import { calculationTeamOrder, createTeamState, teamReducer } from "./teamReducer";

describe("teamReducer", () => {
  it("swaps the old primary into support when selecting the current support", () => {
    expect(teamReducer(
      { primaryId: "character:ye", supportId: "character:astra" },
      { type: "select-primary", characterId: "character:astra" },
    )).toEqual({ primaryId: "character:astra", supportId: "character:ye" });
  });

  it("never accepts primary as support", () => {
    const state = { primaryId: "character:ye", supportId: "character:astra" };
    expect(teamReducer(state, { type: "select-support", characterId: "character:ye" })).toBe(state);
  });

  it("allows clearing support", () => {
    expect(teamReducer(
      { primaryId: "character:ye", supportId: "character:astra" },
      { type: "select-support", characterId: "" },
    )).toEqual({ primaryId: "character:ye", supportId: "" });
  });
});

describe("data-driven three-member team", () => {
  it("adds up to three unique members and rejects duplicates/max overflow", () => {
    const first = createTeamState(["character:one"]);
    const second = teamReducer(first, { type: "add-character", characterId: "character:two" });
    const third = teamReducer(second, { type: "add-character", characterId: "character:three" });
    expect(third.teamCharacterIds).toEqual(["character:one", "character:two", "character:three"]);
    expect(teamReducer(third, { type: "add-character", characterId: "character:two" })).toBe(third);
    expect(teamReducer(third, { type: "add-character", characterId: "character:four" })).toBe(third);
  });

  it("replaces a slot without duplicating and promotes an operator replacement", () => {
    const state = createTeamState(["character:one", "character:two", "character:three"], "character:two");
    const replaced = teamReducer(state, { type: "replace-character", slotIndex: 1, characterId: "character:four" });
    expect(replaced).toEqual({
      teamCharacterIds: ["character:one", "character:four", "character:three"],
      currentOperatorId: "character:four",
    });
    expect(teamReducer(replaced, { type: "replace-character", slotIndex: 0, characterId: "character:three" })).toBe(replaced);
  });

  it("keeps at least one member and selects the first remaining member after operator removal", () => {
    const state = createTeamState(["character:one", "character:two", "character:three"], "character:two");
    const removed = teamReducer(state, { type: "remove-character", characterId: "character:two" });
    expect(removed).toEqual({
      teamCharacterIds: ["character:one", "character:three"],
      currentOperatorId: "character:one",
    });
    const single = createTeamState(["character:one"]);
    expect(teamReducer(single, { type: "remove-character", characterId: "character:one" })).toBe(single);
  });

  it("changes only the operator and preserves the stable slot order", () => {
    const state = createTeamState(["character:one", "character:two", "character:three"]);
    expect(teamReducer(state, { type: "set-current-operator", characterId: "character:three" })).toEqual({
      teamCharacterIds: ["character:one", "character:two", "character:three"],
      currentOperatorId: "character:three",
    });
    expect(teamReducer(state, { type: "set-current-operator", characterId: "character:missing" })).toBe(state);
  });

  it("places the selected operator first while preserving support slot order in requests", () => {
    expect(calculationTeamOrder(
      ["character:one", "character:two", "character:three"],
      "character:three",
    )).toEqual({
      primaryCharacterId: "character:three",
      supportingCharacterIds: ["character:one", "character:two"],
      teamCharacterIds: ["character:three", "character:one", "character:two"],
    });
  });
});
