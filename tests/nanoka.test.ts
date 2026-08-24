import assert from "node:assert/strict";
import test from "node:test";
import {
  buildNanokaDetailUrl,
  parseNanokaVersion,
  type NanokaDetailSnapshot,
} from "../src/importers/nanoka/client.js";
import {
  extractNanokaBuffReviewEntries,
  selectNanokaReviewBatch,
  stripNanokaMarkup,
} from "../src/importers/nanoka/detail-review.js";
import { diffManifest } from "../src/importers/nanoka/diff.js";

test("从 Nanoka 页面发现当前数据版本", () => {
  assert.equal(
    parseNanokaVersion(
      '<div data-url="https://static.nanoka.cc/zzz/3.2.1+17934514/character.json"></div>',
    ),
    "3.2.1+17934514",
  );
});

test("Nanoka manifest 差异区分新增、删除和变更", () => {
  assert.deepEqual(
    diffManifest(
      { "1": { name: "A" }, "2": { name: "B" } },
      { "1": { name: "A2" }, "3": { name: "C" } },
    ),
    {
      beforeCount: 2,
      afterCount: 2,
      added: ["3"],
      removed: ["2"],
      changed: ["1"],
    },
  );
});

test("Nanoka 详情 URL 使用版本化中文详情接口", () => {
  assert.equal(
    buildNanokaDetailUrl("3.2.1+17934514", "zh", "character", "1011"),
    "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/character/1011.json",
  );
});

test("原文清洗只移除 Nanoka 显示标记，不改写数值文本", () => {
  assert.equal(
    stripNanokaMarkup(
      "命中<color=#FFFFFF>[强化特殊技]</color>时，伤害提升<color=#2BAD00>30%</color>。",
    ),
    "命中[强化特殊技]时，伤害提升30%。",
  );
});

test("Buff 审查候选直接来自角色、音擎和驱动盘详情字段", () => {
  const snapshot: NanokaDetailSnapshot = {
    source: "nanoka.cc",
    version: "3.2.1+17934514",
    locale: "zh",
    fetchedAt: "2026-08-14T00:00:00.000Z",
    details: {
      character: {
        "1011": {
          id: 1011,
          name: "安比",
          passive: {
            level: {
              "1011507": {
                level: 7,
                name: ["核心被动：波动电压"],
                desc: ["招式造成的失衡值提升64%。"],
              },
            },
          },
          talent: {
            "2": {
              level: 2,
              name: "精准放电",
              desc: "招式造成的伤害提升30%。",
            },
          },
        },
      },
      weapon: {
        "13001": {
          id: 13001,
          name: "嵌合编译器",
          talents: {
            "5": { name: "编译", desc: "攻击力提升24%。" },
          },
        },
      },
      equipment: {
        "31000": {
          id: 31000,
          name: "啄木鸟电音",
          desc2: "暴击率+8%。",
          desc4: "触发暴击时，攻击力提升9%，持续6秒。",
        },
      },
    },
  };
  const entries = extractNanokaBuffReviewEntries(snapshot);
  assert.equal(entries.length, 5);
  assert.ok(entries.every((entry) => entry.sourceUrl.includes("static.nanoka.cc")));
  assert.ok(entries.some((entry) => entry.rawText.includes("64%")));
  assert.ok(entries.some((entry) => entry.section === "weapon-talent"));
  assert.ok(entries.some((entry) => entry.section === "equipment"));
  assert.equal(selectNanokaReviewBatch(entries, 20).length, 5);
});
