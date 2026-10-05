import { describe, expect, it } from "vitest";
import {
  defaultRemielleSourceSlots,
  remielleOrdinarySourceOptions,
  serializeRemielleSourceSlots,
} from "./remielleSourceSlots";

const characters = [
  { character_id: "character:1581", display_name: "Remielle", element: "luminance" },
  { character_id: "character:1091", display_name: "Miyabi", element: "ice" },
  { character_id: "character:1371", display_name: "Yixuan", element: "ether" },
];

describe("Remielle virtual-void source slots", () => {
  it("uses reviewed AnomalyRecord elements when they differ from the base element", () => {
    const options = remielleOrdinarySourceOptions(
      ["character:1581", "character:1091", "character:1371"],
      characters,
      {
        "character:1091": { luminance_source_elements: ["ice:lieshuang"] },
        "character:1371": { luminance_source_elements: ["ether:xuanmo"] },
      },
    );

    expect(options.map((item) => item.key)).toEqual([
      "ordinary:character:1091|ice:lieshuang",
      "ordinary:character:1371|ether:xuanmo",
    ]);
    expect(defaultRemielleSourceSlots(
      ["character:1581", "character:1091", "character:1371"],
      options,
    )).toEqual([
      "ordinary:character:1091|ice:lieshuang",
      "ordinary:character:1371|ether:xuanmo",
      "",
    ]);
  });

  it("serializes repeated current sources as distinct stable slots and preserves an empty list", () => {
    const options = remielleOrdinarySourceOptions(
      ["character:1581", "character:1091"],
      characters,
      { "character:1091": { luminance_source_elements: ["ice:lieshuang"] } },
    );
    const selection = options[0].key;
    expect(serializeRemielleSourceSlots([selection, selection, ""], options)).toEqual([
      {
        slot_id: "slot-1",
        kind: "ordinary-anomaly",
        source_character_id: "character:1091",
        element: "ice:lieshuang",
      },
      {
        slot_id: "slot-2",
        kind: "ordinary-anomaly",
        source_character_id: "character:1091",
        element: "ice:lieshuang",
      },
    ]);
    expect(serializeRemielleSourceSlots(["", "", ""], options)).toEqual([]);
    expect(serializeRemielleSourceSlots(["special-basic4"], options)).toEqual([
      {
        slot_id: "slot-1",
        kind: "special-basic4",
        source_character_id: "character:1581",
      },
    ]);
  });
});
