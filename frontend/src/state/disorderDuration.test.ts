import { describe, expect, it } from "vitest";
import {
  disorderDurationControl,
  disorderDurationExtraRuleId,
  isDisorderDurationParameter,
  retainKnownParameterIds,
} from "./disorderDuration";

const ariaMove = {
  damage_type: "disorder",
  element: "ether",
  variants: [{ parameter_value_id: "parameter:aria:duration" }],
};
const ariaParameter = {
  parameter_id: "parameter:aria:duration",
  label: "以太异常当前剩余半秒数",
  original_text: "以太异常最多13秒；按当前静态剩余时间输入。",
};
const promeiaMove = {
  damage_type: "disorder",
  element: "ice",
  variants: [{ parameter_value_id: "parameter:promeia:duration" }],
};
const promeiaParameter = {
  parameter_id: "parameter:promeia:duration",
  label: "霜寒紊乱时目标剩余持续时间（秒）",
  original_text: "按当前霜寒记录选择0–13秒；未手动设置时默认13秒。",
};

describe("disorder duration controls", () => {
  it("follows the active Extra default and maximum in half-second units", () => {
    expect(isDisorderDurationParameter(ariaMove, ariaParameter)).toBe(true);
    expect(disorderDurationControl(ariaParameter, false, false, 26)).toEqual({ value: 20, maximum: 20 });
    expect(disorderDurationControl(ariaParameter, true, false, 20)).toEqual({ value: 26, maximum: 26 });
  });

  it("preserves a manually selected valid duration when the Extra changes", () => {
    expect(disorderDurationControl(ariaParameter, false, true, 16)).toEqual({ value: 16, maximum: 20 });
    expect(disorderDurationControl(ariaParameter, true, true, 16)).toEqual({ value: 16, maximum: 26 });
  });

  it("only adapts the selected, authored Ether or Xuanmo disorder parameter", () => {
    expect(isDisorderDurationParameter({ ...ariaMove, damage_type: "direct" }, ariaParameter)).toBe(false);
    expect(isDisorderDurationParameter({ ...ariaMove, element: "fire" }, ariaParameter)).toBe(false);
    expect(isDisorderDurationParameter({ ...ariaMove, variants: [] }, ariaParameter)).toBe(false);
    expect(isDisorderDurationParameter({ ...ariaMove, element: "ether:xuanmo" }, ariaParameter)).toBe(true);
  });

  it("follows Promeia's Frost Chill duration in whole-second units", () => {
    expect(isDisorderDurationParameter(promeiaMove, promeiaParameter)).toBe(true);
    expect(disorderDurationControl(promeiaParameter, false, false, 13)).toEqual({ value: 10, maximum: 10 });
    expect(disorderDurationControl(promeiaParameter, true, false, 10)).toEqual({ value: 13, maximum: 13 });
    expect(disorderDurationControl(promeiaParameter, false, true, 8)).toEqual({ value: 8, maximum: 10 });
  });

  it("extends the Lieshuang Frost Chill family from twenty to twenty-three seconds", () => {
    const lieshuangMove = { ...promeiaMove, element: "ice:lieshuang" };
    expect(isDisorderDurationParameter(lieshuangMove, promeiaParameter)).toBe(true);
    expect(disorderDurationControl(promeiaParameter, false, false, 23, 20)).toEqual({ value: 20, maximum: 20 });
    expect(disorderDurationControl(promeiaParameter, true, false, 20, 20)).toEqual({ value: 23, maximum: 23 });
  });

  it("chooses the duration rule for the selected anomaly family", () => {
    expect(disorderDurationExtraRuleId("ice")).toBe("rule:character:1541:extra-ability:frost-chill-duration");
    expect(disorderDurationExtraRuleId("ice:lieshuang")).toBe("rule:character:1541:extra-ability:frost-chill-duration");
    expect(disorderDurationExtraRuleId("ether")).toBe("rule:character:1501:extra-ability:ether-corrosion-duration");
    expect(disorderDurationExtraRuleId("ether:xuanmo")).toBe("rule:character:1501:extra-ability:ether-corrosion-duration");
  });

  it("drops explicit state for parameters removed from the active team", () => {
    expect(retainKnownParameterIds(
      new Set(["parameter:aria:duration", "parameter:other"]),
      new Set(["parameter:other"]),
    )).toEqual(new Set(["parameter:other"]));
  });
});
