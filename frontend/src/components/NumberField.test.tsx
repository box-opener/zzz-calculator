import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import NumberField from "./NumberField";

describe("NumberField", () => {
  it("renders a labelled value surface with unit, helper, and read-only state", () => {
    const markup = renderToStaticMarkup(
      <NumberField
        label="暴击率"
        value={0.5}
        displayValue="50%"
        displayAsPercent
        readOnly
        unit="%"
        helper="装备解析结果"
      />,
    );

    expect(markup).toContain("number-field");
    expect(markup).toContain("number-field-readonly");
    expect(markup).toContain("暴击率");
    expect(markup).toContain("50%");
    expect(markup).toContain("装备解析结果");
    expect(markup).toContain("number-field-unit");
  });

  it("keeps an editable control backed by DraftNumberInput", () => {
    const markup = renderToStaticMarkup(
      <NumberField
        label="层数"
        value={2}
        integer
        min={1}
        max={6}
        unit="层"
        helper="范围 1–6"
        onCommit={() => undefined}
      />,
    );

    expect(markup).toContain('inputMode="numeric"');
    expect(markup).toContain('value="2"');
    expect(markup).toContain("范围 1–6");
  });
});
