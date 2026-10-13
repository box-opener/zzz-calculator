import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import PanelStatBreakdown from "./PanelStatBreakdown";

describe("live panel white and additional values", () => {
  it("labels both components and marks the addition separately for green display", () => {
    const html = renderToStaticMarkup(<PanelStatBreakdown value={{ white_value: 1681.2102, additional_value: 316 }} />);
    expect(html).toContain("白值 1,681.21");
    expect(html).toContain('class="live-panel-additional"');
    expect(html).toContain("附加 +316");
  });

  it("preserves small energy values and distinguishes missing additions from zero", () => {
    const energy = renderToStaticMarkup(<PanelStatBreakdown value={{ white_value: 1.2, additional_value: 0.72 }} />);
    expect(energy).toContain("附加 +0.72");
    expect(renderToStaticMarkup(<PanelStatBreakdown value={{ white_value: null, additional_value: null }} />)).toContain("附加 —");
    expect(renderToStaticMarkup(<PanelStatBreakdown value={{ white_value: 1.2, additional_value: 0 }} />)).toContain("附加 +0");
  });
});
