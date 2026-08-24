import assert from "node:assert/strict";
import test from "node:test";
import compiledDatabase from "../data/compiled/nanoka-buffs-3.2.1+17934514.json" with { type: "json" };
import { REVIEWED_CHARACTER_BUFF_RULES } from "../data/rules/reviewed-buff-registry.js";
import {
  auditCharacterRules,
  findMissingAutoAcceptedCharacterRules,
  renderCharacterRuleAuditMarkdown,
} from "../src/domain/audit/character-rule-audit.js";
import type { BuffRule } from "../src/domain/model/buff.js";
import type { NanokaParsedBuff } from "../src/importers/nanoka/parse-buff.js";

const source = {
  type: "character" as const,
  id: "9001",
  label: "测试角色｜额外能力",
  provider: "reference" as const,
  key: "character:9001:passive:9001507:1",
};

const testedRule: BuffRule = {
  schemaVersion: 1,
  id: "audit:test:team-condition",
  source,
  status: "verified",
  target: "all-allies",
  phase: "combat",
  timing: "on-trigger",
  trigger: "skill-used",
  cinemaAtLeast: 1,
  condition: { type: "team-role", role: "支援" },
  effects: [{ kind: "damage-bonus", operation: "add-percent", value: 20 }],
  rawDescription: "队伍中存在支援角色时，造成的伤害提升20%。",
};

const unsupportedRule: BuffRule = {
  ...testedRule,
  id: "audit:test:crit-profile",
  source: { ...source, key: "character:9001:talent:2" },
  cinemaAtLeast: 2,
  condition: { type: "always" },
  effects: [{
    kind: "crit-profile",
    operation: "add",
    zone: "测试独立暴击区",
    critRate: 50,
    critDamage: 100,
  }],
};

test("角色审计器用虚拟队伍验证正向激活、影画边界和已接入独立暴击区", () => {
  const entries = [
    parsed("character:9001:passive:9001507:1", "auto-accepted", "造成的伤害提升20%。"),
    parsed("character:9001:talent:2", "needs-review", "暴击率提升50%。"),
    parsed("character:9001:skill:special:0", "needs-review", "招式发动期间拥有无敌效果。"),
  ];
  const report = auditCharacterRules({
    sourceVersion: "test",
    generatedAt: "2026-08-15T00:00:00.000Z",
    profiles: [
      { id: "9001", name: "测试角色", role: "异常", element: "物理", camp: "测试阵营" },
      { id: "9002", name: "测试支援", role: "支援", element: "电", camp: "另一阵营" },
    ],
    entries,
    rules: [testedRule, unsupportedRule],
  });

  assert.equal(report.summary.errors, 0);
  assert.equal(report.summary.reviewedRules, 2);
  assert.equal(report.summary.activatedRules, 2);
  assert.equal(report.summary.pendingReviewGroups, 0);
  assert.equal(report.summary.deferredOutOfScopeGroups, 1);
  assert.equal(report.summary.integrationGaps, 0);
  assert.deepEqual(report.unsupportedEffectKinds, {});
  const testedCheck = report.characters.find((item) => item.id === "9001")?.ruleChecks
    .find((item) => item.ruleId === testedRule.id);
  assert.equal(testedCheck?.activated, true);
  assert.equal(testedCheck?.cinemaBoundaryPassed, true);
  assert.equal(testedCheck?.conditionBoundaryPassed, true);
  assert.deepEqual(testedCheck?.positiveTeamIds, ["9001", "9002"]);
  assert.match(renderCharacterRuleAuditMarkdown(report), /测试角色/);
});

test("当前 Nanoka 自动接收的角色规则没有从统一注册表静默丢失", () => {
  const database = compiledDatabase as { entries: NanokaParsedBuff[] };
  assert.deepEqual(
    findMissingAutoAcceptedCharacterRules(database.entries, REVIEWED_CHARACTER_BUFF_RULES),
    [],
  );
});

test("自动接收条目缺少统一规则时会成为阻断错误", () => {
  const missing = parsed(
    "character:9001:talent:4",
    "auto-accepted",
    "攻击力提升20%。",
  );
  const report = auditCharacterRules({
    sourceVersion: "test",
    profiles: [{ id: "9001", name: "测试角色", role: "异常", element: "物理" }],
    entries: [missing],
    rules: [],
  });
  assert.equal(report.summary.errors, 1);
  assert.equal(report.characters[0]?.issues.some((issue) => issue.code === "missing-auto-rule"), true);
});

function parsed(
  key: string,
  disposition: NanokaParsedBuff["disposition"],
  displayText: string,
): NanokaParsedBuff {
  return {
    key,
    sourceUrl: "https://example.invalid/test.json",
    rawText: displayText,
    displayText,
    status: disposition === "auto-accepted" ? "parsed" : "review",
    rule: null,
    recognized: [],
    issues: [],
    disposition,
    reviewReasons: disposition === "needs-review" ? ["测试待审"] : [],
  };
}
