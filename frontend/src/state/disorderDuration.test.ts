import { describe, expect, it } from "vitest";
import {
  disorderDurationControl,
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

  it("drops explicit state for parameters removed from the active team", () => {
    expect(retainKnownParameterIds(
      new Set(["parameter:aria:duration", "parameter:other"]),
      new Set(["parameter:other"]),
    )).toEqual(new Set(["parameter:other"]));
  });
});
