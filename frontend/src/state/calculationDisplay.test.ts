import { describe, expect, it } from "vitest";
import { calculationNodeLabel, formatMultiplierPercent } from "./calculationDisplay";

describe("calculation display formatting", () => {
  it("preserves useful precision for multiplier percentages", () => {
    expect(formatMultiplierPercent(0.625)).toBe("62.5%");
    expect(formatMultiplierPercent(2.0172)).toBe("201.72%");
    expect(formatMultiplierPercent(1.2607499999999998)).toBe("126.075%");
  });

  it("explains Polar Disorder's separate AP coefficient in breakdowns", () => {
    expect(calculationNodeLabel("disorder.polar.ap-coefficient"))
      .toBe("极性紊乱异常精通系数");
    expect(calculationNodeLabel("disorder.polar.multiplier")).toBe("极性紊乱倍率");
    expect(calculationNodeLabel("unknown.node")).toBe("unknown.node");
  });
});
