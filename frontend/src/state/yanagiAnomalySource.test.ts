import { describe, expect, it } from "vitest";
import {
  defaultYanagiAnomalySource,
  selectedYanagiAnomalySource,
  yanagiAnomalySourceOptions,
} from "./yanagiAnomalySource";

describe("Yanagi Polar Disorder source selection", () => {
  it("uses stable actor IDs and reviewed anomaly aliases, defaulting to Yanagi", () => {
    const options = yanagiAnomalySourceOptions(
      ["character:1221", "character:1091", "character:1371", "character:1581"],
      {
        "character:1221": { character_id: "character:1221", anomaly_source_elements: ["electric"] },
        "character:1091": { character_id: "character:1091", anomaly_source_elements: ["ice:lieshuang"] },
        "character:1371": { character_id: "character:1371", anomaly_source_elements: ["ether:xuanmo"] },
        "character:1581": { character_id: "character:1581", anomaly_source_elements: ["luminance"] },
      },
    );
    expect(options.map((option) => option.key)).toEqual([
      "character:1221|electric",
      "character:1091|ice:lieshuang",
      "character:1371|ether:xuanmo",
    ]);
    expect(defaultYanagiAnomalySource(options)?.key).toBe("character:1221|electric");
  });

  it("preserves a valid actor choice and falls back when that actor leaves", () => {
    const options = yanagiAnomalySourceOptions(
      ["character:1221", "character:1091"],
      {
        "character:1221": { character_id: "character:1221", anomaly_source_elements: ["electric"] },
        "character:1091": { character_id: "character:1091", anomaly_source_elements: ["ice:lieshuang"] },
      },
    );
    expect(selectedYanagiAnomalySource(options, "character:1091|ice:lieshuang")?.characterId)
      .toBe("character:1091");
    expect(selectedYanagiAnomalySource(options.slice(0, 1), "character:1091|ice:lieshuang")?.key)
      .toBe("character:1221|electric");
  });
});
