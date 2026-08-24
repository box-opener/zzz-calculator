import assert from "node:assert/strict";
import test from "node:test";
import { validateBuffRule } from "../src/domain/engine/validate-buff-rule.js";
import {
  parseNanokaBuffEntries,
  parseNanokaBuffEntry,
  renderNanokaActionableReviewQueue,
  renderNanokaEquipmentReviewQueue,
  renderNanokaEquipmentRemainingReviewQueue,
  selectNanokaActionableReviewBatch,
  selectNanokaEquipmentReviewEntries,
} from "../src/importers/nanoka/parse-buff.js";
import {
  buildNanokaTeamConditionValues,
  mapNanokaCharacterProfile,
} from "../src/importers/nanoka/profile.js";
import type { NanokaBuffReviewEntry } from "../src/importers/nanoka/detail-review.js";

function entry(
  key: string,
  text: string,
  section: NanokaBuffReviewEntry["section"] = "character-talent",
): NanokaBuffReviewEntry {
  return {
    key,
    kind: section === "equipment" ? "equipment" : section === "weapon-talent" ? "weapon" : "character",
    id: section === "equipment" ? "31000" : "1011",
    name: section === "equipment" ? "啄木鸟电音" : "安比",
    section,
    ...(section === "character-talent" || section === "weapon-talent" ? { level: 2 } : {}),
    title: "测试文本",
    rawText: text,
    displayText: text,
    sourceUrl: "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/character/1011.json",
  };
}

test("Nanoka 简单 2 件套静态属性可生成候选规则", () => {
  const parsed = parseNanokaBuffEntry(
    entry("equipment:31000:desc2", "暴击率+8%。", "equipment"),
  );
  assert.equal(parsed.status, "parsed");
  assert.equal(parsed.disposition, "auto-accepted");
  assert.ok(parsed.rule);
  assert.equal(parsed.rule.status, "verified");
  assert.deepEqual(parsed.rule.effects, [
    { kind: "stat", stat: "critRate", operation: "add-percent", value: 8 },
  ]);
  assert.equal(parsed.rule.equippedCountAtLeast, 2);
  assert.equal(validateBuffRule(parsed.rule).valid, true);
});

test("能量类文本自动归入当前范围外，不进入人工审查队列", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1011:passive:1011507:1",
      "队伍中存在同属性角色时，命中敌人额外回复7.2点能量，5秒内最多触发一次。",
    ),
  );
  assert.equal(parsed.disposition, "ignored");
  assert.equal(parsed.rule, null);
  assert.deepEqual(selectNanokaActionableReviewBatch([parsed], 10), []);
});

test("动态伤害公式进入人工队列，但同一被动不同等级只保留一条", () => {
  const entries = [
    entry(
      "character:1051:passive:1051501:0",
      "生命值低于50%后，攻击造成的伤害最多提升100%。",
    ),
    entry(
      "character:1051:passive:1051507:0",
      "生命值低于50%后，攻击造成的伤害最多提升100%。",
    ),
  ];
  const parsed = parseNanokaBuffEntries(entries);
  assert.ok(parsed.every((item) => item.disposition === "needs-review"));
  assert.equal(selectNanokaActionableReviewBatch(parsed, 10).length, 1);
});

test("核心被动等级数值不同但语义相同，审查队列合并为一组并记录覆盖项", () => {
  const parsed = parseNanokaBuffEntries([
    entry(
      "character:1261:passive:1261506:0",
      "生命值低于50%后，攻击造成的伤害最多提升100%。",
    ),
    entry(
      "character:1261:passive:1261507:0",
      "生命值低于50%后，攻击造成的伤害最多提升120%。",
    ),
  ]);
  assert.equal(selectNanokaActionableReviewBatch(parsed, 10).length, 1);
  const report = renderNanokaActionableReviewQueue(
    "3.2.1+17934514",
    parsed,
    selectNanokaActionableReviewBatch(parsed, 10),
  );
  assert.match(report, /覆盖条目：2 条/);
  assert.match(report, /character:1261:passive:1261506:0、character:1261:passive:1261507:0/);
});

test("不同条件的复合影画不会被合并成同一条可用规则", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1011:talent:2",
      "[普通攻击：落雷]命中处于失衡状态下的敌人时，招式造成的伤害提升30%；[强化特殊技]命中未处于失衡状态下的敌人时，招式造成的失衡值提升10%。",
    ),
  );
  assert.equal(parsed.status, "review");
  assert.equal(parsed.rule, null);
  assert.ok(parsed.issues.some((issue) => issue.includes("互斥")));
});

test("装备审查队列合并音擎精炼等级，但保留驱动盘 2/4 件套和全部原文", () => {
  const parsed = parseNanokaBuffEntries([
    entry("weapon:14140:talent:1", "造成的物理伤害提升20%。", "weapon-talent"),
    entry("weapon:14140:talent:5", "造成的物理伤害提升32%。", "weapon-talent"),
    entry("equipment:32600:desc2", "物理伤害加成10%。", "equipment"),
    entry("equipment:32600:desc4", "物理属性异常状态下的敌人受到的伤害提升35%。", "equipment"),
  ]);
  const selected = selectNanokaEquipmentReviewEntries(parsed);
  assert.equal(selected.length, 3);
  assert.ok(selected.some((item) => item.key === "weapon:14140:talent:5"));
  const report = renderNanokaEquipmentReviewQueue("3.2.1+17934514", parsed, selected);
  assert.match(report, /weapon:14140:talent:1/);
  assert.match(report, /weapon:14140:talent:5/);
  assert.match(report, /equipment:32600:desc2/);
  assert.match(report, /equipment:32600:desc4/);
});

test("音擎规则记录精炼档位，剩余无法表达的装备效果单独列出", () => {
  const weapon = parseNanokaBuffEntry(
    entry("weapon:12001:talent:3", "造成的伤害提升14%。", "weapon-talent"),
  );
  assert.ok(weapon.rule);
  assert.equal(weapon.rule.weaponRefinement, 2);
  const unresolved = parseNanokaBuffEntry(
    entry("weapon:12014:talent:1", "受到敌方攻击时，攻击者造成的伤害降低6%，持续12秒。", "weapon-talent"),
  );
  assert.equal(unresolved.rule, null);
  const report = renderNanokaEquipmentRemainingReviewQueue(
    "3.2.1+17934514",
    [unresolved],
    [unresolved],
  );
  assert.match(report, /weapon:12014:talent:1/);
});

test("以太伤害额外提升保留元素作用范围，不误判为以太面板属性", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1031:talent:6",
      "所有单位对目标造成的以太伤害额外提升25%，持续3.5秒。",
    ),
  );
  assert.ok(parsed.rule);
  assert.deepEqual(parsed.rule.effects, [
    {
      kind: "damage-bonus",
      operation: "add-percent",
      value: 25,
      scope: { elements: ["ether"] },
    },
  ]);
  assert.equal(parsed.rule.target, "all-allies");
});

test("冲刺攻击使用独立技能类别", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1041:talent:2",
      "[普通攻击]或[冲刺攻击]中触发效果时，招式造成的伤害提升70%。",
    ),
  );
  assert.ok(parsed.rule);
  assert.deepEqual(parsed.rule.effects[0], {
    kind: "damage-bonus",
    operation: "add-percent",
    value: 70,
    scope: { skillCategories: ["basic", "dash"] },
  });
});

test("额外能力候选保留同属性、同职业、同阵营队伍条件", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1031:passive:1031507:1",
      "队伍中存在与自身属性或阵营相同的角色时触发：所有单位对目标造成的以太伤害额外提升25%。",
    ),
  );
  assert.ok(parsed.rule);
  assert.deepEqual(parsed.rule.condition, {
    type: "any",
    conditions: [
      { type: "team-match", relation: "element" },
      { type: "team-match", relation: "role" },
      { type: "team-match", relation: "camp" },
    ],
  });
});

test("Nanoka 角色详情字段可以提供职业、元素和阵营", () => {
  assert.deepEqual(
    mapNanokaCharacterProfile("1071", {
      name: "凯撒",
      weapon_type: { "5": "防护" },
      element_type: { "200": "物理" },
      camp: { "4": "卡吕冬之子" },
    }),
    {
      id: "1071",
      name: "凯撒",
      role: "防护",
      element: "物理",
      camp: "卡吕冬之子",
    },
  );
});

test("直接伤害与抗性无视使用独立效果，不降级为普通伤害加成", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1091:passive:1091507:0",
      "对目标造成星见雅1500%攻击力的烈霜伤害。",
    ),
  );
  assert.ok(parsed.rule);
  assert.deepEqual(parsed.rule.effects, [{
    kind: "damage-instance",
    operation: "add",
    damageKind: "direct",
    value: { type: "source-stat", path: "self.atk", scale: 15 },
    element: "ice",
  }]);
});

test("凯撒额外能力候选同时识别阵营和防护职业", () => {
  const parsed = parseNanokaBuffEntry(
    entry(
      "character:1071:passive:1071507:1",
      "队伍中存在其他可发动[招架支援]的角色或与自身阵营相同的角色时触发：全队角色造成的伤害提升25%。",
    ),
  );
  assert.ok(parsed.rule);
  assert.deepEqual(parsed.rule.condition, {
    type: "any",
    conditions: [
      { type: "team-match", relation: "camp" },
      { type: "team-role", role: "防护" },
    ],
  });
});

test("Nanoka 角色标签可以构造队伍条件上下文", () => {
  const values = buildNanokaTeamConditionValues("1071", [
    mapNanokaCharacterProfile("1071", {
      name: "凯撒",
      weapon_type: { "5": "防护" },
      element_type: { "200": "物理" },
      camp: { "4": "卡吕冬之子" },
    }),
    mapNanokaCharacterProfile("1011", {
      name: "安比",
      weapon_type: { "2": "击破" },
      element_type: { "203": "电属性" },
      camp: { "1": "狡兔屋" },
    }),
  ]);
  assert.deepEqual(values, {
    team: {
      members: [
        {
          id: "1071",
          name: "凯撒",
          role: "防护",
          element: "物理",
          camp: "卡吕冬之子",
        },
        {
          id: "1011",
          name: "安比",
          role: "击破",
          element: "电属性",
          camp: "狡兔屋",
        },
      ],
      self: {
        id: "1071",
        name: "凯撒",
        role: "防护",
        element: "物理",
        camp: "卡吕冬之子",
      },
    },
  });
});
