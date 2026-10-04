import { describe, expect, it } from "vitest";
import { formatMultiplierPercent } from "./calculationDisplay";

describe("calculation display formatting", () => {
  it("preserves useful precision for multiplier percentages", () => {
    expect(formatMultiplierPercent(0.625)).toBe("62.5%");
    expect(formatMultiplierPercent(2.0172)).toBe("201.72%");
    expect(formatMultiplierPercent(1.2607499999999998)).toBe("126.075%");
  });
});
