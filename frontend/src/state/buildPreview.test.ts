import { describe, expect, it } from "vitest";
import {
  formatBuildContributionValue,
  formatDriveStatValue,
  formatPreviewRatio,
} from "./buildPreview";

describe("Build Preview display helpers", () => {
  it("keeps percentage values in human-readable units", () => {
    expect(formatDriveStatValue("attack-percent", 0.3)).toBe("30%");
    expect(formatDriveStatValue("crit-rate", 0.024)).toBe("2.4%");
    expect(formatPreviewRatio(0.194)).toBe("19.4%");
  });

  it("keeps flat values as flat values", () => {
    expect(formatDriveStatValue("attack-flat", 19)).toBe("19");
    expect(formatDriveStatValue("hp-flat", 112)).toBe("112");
  });

  it("formats percent-layer provenance as percentages", () => {
    expect(formatBuildContributionValue({
      value: 0.3,
      stat: "attack",
      layer: "out-of-combat-percent",
    })).toBe("+30%");
    expect(formatBuildContributionValue({
      value: 0.3,
      stat: "element_damage_bonus",
      layer: "direct-ratio",
    })).toBe("+30%");
    expect(formatBuildContributionValue({
      value: 19,
      stat: "attack",
      layer: "out-of-combat-flat",
    })).toBe("+19");
  });
});
