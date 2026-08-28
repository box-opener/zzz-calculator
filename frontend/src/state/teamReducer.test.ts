import { describe, expect, it } from "vitest";
import { teamReducer } from "./teamReducer";

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
