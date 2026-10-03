import { describe, expect, it } from "vitest";
import {
  canAddToTeamSlot,
  calculationTeamOrder,
  createTeamState,
  isCurrentCalculationResponse,
  teamReducer,
} from "./teamReducer";

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
  it("discards stale in-flight results after roster/editor generations change", () => {
    const request = { calculation: 4, editor: 7 };
    expect(isCurrentCalculationResponse(request, request)).toBe(true);
    expect(isCurrentCalculationResponse(request, { calculation: 5, editor: 7 })).toBe(false);
    expect(isCurrentCalculationResponse(request, { calculation: 4, editor: 8 })).toBe(false);
  });

  it("starts empty and assigns the first added character as operator", () => {
    const empty = createTeamState([]);
    expect(empty).toEqual({ teamCharacterIds: [], currentOperatorId: "" });
    const first = teamReducer(empty, { type: "add-character", characterId: "character:one" });
    expect(first).toEqual({ teamCharacterIds: ["character:one"], currentOperatorId: "character:one" });
  });

  it("allows filling only the next dense roster slot", () => {
    expect([0, 1, 2].map((slot) => canAddToTeamSlot(slot, 0))).toEqual([true, false, false]);
    expect([0, 1, 2].map((slot) => canAddToTeamSlot(slot, 1))).toEqual([false, true, false]);
    expect([0, 1, 2].map((slot) => canAddToTeamSlot(slot, 2))).toEqual([false, false, true]);
    expect([0, 1, 2].map((slot) => canAddToTeamSlot(slot, 3))).toEqual([false, false, false]);
  });

  it("adds up to three unique members and rejects duplicates/max overflow", () => {
    const first = teamReducer(createTeamState([]), { type: "add-character", characterId: "character:one" });
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

  it("keeps the lineup dense, selects the next slot operator, and allows removal to empty", () => {
    const state = createTeamState(["character:one", "character:two", "character:three"], "character:two");
    const removed = teamReducer(state, { type: "remove-character", characterId: "character:two" });
    expect(removed).toEqual({
      teamCharacterIds: ["character:one", "character:three"],
      currentOperatorId: "character:three",
    });
    const removedFirstOperator = teamReducer(
      createTeamState(["character:one", "character:two", "character:three"], "character:one"),
      { type: "remove-character", characterId: "character:one" },
    );
    expect(removedFirstOperator.currentOperatorId).toBe("character:two");
    const empty = teamReducer(
      createTeamState(["character:one"]),
      { type: "remove-character", characterId: "character:one" },
    );
    expect(empty).toEqual({ teamCharacterIds: [], currentOperatorId: "" });
  });

  it("swaps occupied slots while preserving the current operator character", () => {
    const state = createTeamState(
      ["character:one", "character:two", "character:three"],
      "character:one",
    );
    const swapped = teamReducer(state, { type: "swap-slots", firstSlot: 0, secondSlot: 2 });
    expect(swapped).toEqual({
      teamCharacterIds: ["character:three", "character:two", "character:one"],
      currentOperatorId: "character:one",
    });
    expect(teamReducer(swapped, { type: "swap-slots", firstSlot: 0, secondSlot: 3 })).toBe(swapped);
    expect(teamReducer(swapped, { type: "swap-slots", firstSlot: 1, secondSlot: 1 })).toBe(swapped);
    const twoMemberTeam = createTeamState(["character:one", "character:two"]);
    expect(teamReducer(twoMemberTeam, { type: "swap-slots", firstSlot: 0, secondSlot: 2 })).toBe(twoMemberTeam);
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
      formationCharacterIds: ["character:one", "character:two", "character:three"],
    });
  });

  it("composes an empty team without inventing a primary or formation", () => {
    expect(calculationTeamOrder([], "")).toEqual({
      primaryCharacterId: "",
      supportingCharacterIds: [],
      teamCharacterIds: [],
      formationCharacterIds: [],
    });
  });

  it("keeps swapped formation order separate from operator-first request order", () => {
    const swapped = teamReducer(
      createTeamState(["character:one", "character:two", "character:three"], "character:one"),
      { type: "swap-slots", firstSlot: 0, secondSlot: 2 },
    );
    expect(calculationTeamOrder(swapped.teamCharacterIds, swapped.currentOperatorId)).toEqual({
      primaryCharacterId: "character:one",
      supportingCharacterIds: ["character:three", "character:two"],
      teamCharacterIds: ["character:one", "character:three", "character:two"],
      formationCharacterIds: ["character:three", "character:two", "character:one"],
    });
  });
});
