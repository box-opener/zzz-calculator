import { describe, expect, it } from "vitest";
import { filterCharacterCatalog, isCharacterSelectable } from "./characterLibrary";

const catalog = [
  { character_id: "character:one", display_name: "一号", specialty: "support", element: "ether" },
  { character_id: "character:two", display_name: "二号", specialty: "attack", element: "physical" },
  { character_id: "character:three", display_name: "三号", specialty: "anomaly", element: "electric" },
];

describe("character library", () => {
  it("filters catalog entries by readable query, specialty, and element", () => {
    expect(filterCharacterCatalog(catalog, { specialty: "support" }).map((item) => item.character_id)).toEqual(["character:one"]);
    expect(filterCharacterCatalog(catalog, { element: "electric" }).map((item) => item.character_id)).toEqual(["character:three"]);
    expect(filterCharacterCatalog(catalog, { query: "二号" }).map((item) => item.character_id)).toEqual(["character:two"]);
  });

  it("marks active members disabled while allowing replacement candidates", () => {
    expect(isCharacterSelectable("character:one", ["character:one", "character:two"])).toBe(false);
    expect(isCharacterSelectable("character:three", ["character:one", "character:two", "character:four"])).toBe(true);
  });
});
