import { describe, expect, it } from "vitest";
import { filterCharacterCatalog, isCharacterSelectable, sortCharactersById } from "./characterLibrary";

const catalog = [
  { character_id: "character:one", display_name: "一号", specialty: "support", element: "ether" },
  { character_id: "character:two", display_name: "二号", specialty: "attack", element: "physical" },
  { character_id: "character:three", display_name: "三号", specialty: "anomaly", element: "electric" },
];

describe("character library", () => {
  it("sorts numeric IDs descending without changing saved roster or catalog order", () => {
    const entries = [{ character_id: "character:101" }, { character_id: "character:1591" }, { character_id: "character:1001" }];
    expect(sortCharactersById(entries).map((c) => c.character_id)).toEqual(["character:1591", "character:1001", "character:101"]);
    expect(entries[0].character_id).toBe("character:101");
  });
  it("combines faction with other filters and includes factions in search", () => {
    const entries = catalog.map((c, i) => ({ ...c, faction: i < 2 ? "狡兔屋" : "白祇重工" }));
    expect(filterCharacterCatalog(entries, { faction: "狡兔屋", element: "physical" }).map((c) => c.display_name)).toEqual(["二号"]);
    expect(filterCharacterCatalog(entries, { query: "白祇" }).map((c) => c.display_name)).toEqual(["三号"]);
    expect(filterCharacterCatalog(entries, { faction: "狡兔屋", specialty: "anomaly" })).toEqual([]);
  });
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
