import { describe, expect, it } from "vitest";

import {
  burniceAnomalySourceOptions,
  defaultBurniceAnomalySource,
  selectedBurniceAnomalySource,
} from "./burniceAnomalySource";

describe("Burnice Discharge source selection", () => {
  it("uses Burnice Fire by default and exposes only reviewed active anomaly sources", () => {
    const options = burniceAnomalySourceOptions(
      ["character:1171", "character:1371", "character:1581"],
      {
        "character:1171": { character_id: "character:1171", reviewed_anomaly_source_elements: ["fire"] },
        "character:1371": { character_id: "character:1371", reviewed_anomaly_source_elements: ["ether:xuanmo"] },
        "character:1581": { character_id: "character:1581", reviewed_anomaly_source_elements: [] },
        // Older projection fallback must not make an unreviewed base element selectable.
        "character:1431": { character_id: "character:1431", reviewed_anomaly_source_elements: [] },
      },
    );

    expect(options.map((option) => option.key)).toEqual([
      "character:1171|fire",
      "character:1371|ether:xuanmo",
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
});
