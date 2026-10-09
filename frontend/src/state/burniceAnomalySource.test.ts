import { describe, expect, it } from "vitest";

import {
  burniceAnomalySourceOptions,
  defaultBurniceAnomalySource,
  selectedBurniceAnomalySource,
} from "./burniceAnomalySource";

describe("Burnice Discharge source selection", () => {
  it("uses Burnice Fire by default and exposes only reviewed active anomaly sources", () => {
    const options = burniceAnomalySourceOptions(
      ["character:1171", "character:1371", "character:1281", "character:1581"],
      {
        "character:1171": { character_id: "character:1171", reviewed_anomaly_source_elements: ["fire"] },
        "character:1371": { character_id: "character:1371", reviewed_anomaly_source_elements: ["ether:xuanmo"] },
        "character:1281": { character_id: "character:1281", reviewed_anomaly_source_elements: ["physical"] },
        "character:1581": { character_id: "character:1581", reviewed_anomaly_source_elements: [] },
        // Older projection fallback must not make an unreviewed base element selectable.
        "character:1431": { character_id: "character:1431", reviewed_anomaly_source_elements: [] },
      },
    );

    expect(options.map((option) => option.key)).toEqual([
      "character:1171|fire",
      "character:1371|ether:xuanmo",
      "character:1281|physical",
    ]);
    expect(defaultBurniceAnomalySource(options)).toEqual(options[0]);
  });

  it("preserves an explicit source while it remains active and falls back after removal", () => {
    const options = burniceAnomalySourceOptions(
      ["character:1171", "character:1371"],
      {
        "character:1171": { character_id: "character:1171", reviewed_anomaly_source_elements: ["fire"] },
        "character:1371": { character_id: "character:1371", reviewed_anomaly_source_elements: ["ether:xuanmo"] },
      },
    );
    expect(selectedBurniceAnomalySource(options, options[1].key)).toEqual(options[1]);
    expect(selectedBurniceAnomalySource(options.slice(0, 1), options[1].key)).toEqual(options[0]);
  });

  it("can default a reviewed-source picker to Grace without changing Burnice defaults", () => {
    const options = [
      { key: "character:1011|electric", characterId: "character:1011", element: "electric" },
      { key: "character:1181|electric", characterId: "character:1181", element: "electric" },
    ];
    expect(selectedBurniceAnomalySource(options, null, "character:1181")).toEqual(options[1]);
    expect(selectedBurniceAnomalySource(options, null)).toEqual(options[0]);
  });
});
