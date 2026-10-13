import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import MiyoushePanel from "./MiyoushePanel";

describe("Miyoushe import entry", () => {
  it("provides labelled UID and temporary credentials with a local-data clear action", () => {
    const html = renderToStaticMarkup(<MiyoushePanel ready catalog={{ wengines: [], driveDiscSets: [] }} supportedCharacterIds={[]} onLoad={() => undefined} />);
    expect(html).toContain('aria-label="米游社游戏 UID"');
    expect(html).toContain('type="password"');
    expect(html).toContain('autoComplete="off"');
    expect(html).toContain("获取并保存角色");
    expect(html).toContain("清除本地资料");
    expect(html).toContain("生成登录二维码");
    expect(html).toContain("手动 Cookie");
  });
});
