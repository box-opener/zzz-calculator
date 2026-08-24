import assert from "node:assert/strict";
import test from "node:test";
import { evaluateCondition, evaluatePanelBuffRules } from "../src/domain/engine/evaluate-buff-rules.js";
import { validateBuffRule } from "../src/domain/engine/validate-buff-rule.js";
import { DRIVE_DISC_2PC_RULES } from "../data/rules/drive-disc-2pc.js";
import { NANOKA_REVIEWED_BATCH_001 } from "../data/rules/nanoka-reviewed-batch-001.js";
import { NANOKA_REVIEWED_BATCH_002 } from "../data/rules/nanoka-reviewed-batch-002.js";
import { NANOKA_REVIEWED_BATCH_003 } from "../data/rules/nanoka-reviewed-batch-003.js";
import { NANOKA_REVIEWED_BATCH_004 } from "../data/rules/nanoka-reviewed-batch-004.js";
import {
  REVIEWED_BUFF_RULES,
  REVIEWED_CHARACTER_BUFF_RULES,
  REVIEWED_DRIVE_DISC_BUFF_RULES,
  REVIEWED_WEAPON_BUFF_RULES,
} from "../data/rules/reviewed-buff-registry.js";
import {
  NANOKA_REVIEW_DECISIONS_BATCH_001,
  NANOKA_REVIEW_DECISIONS_BATCH_002,
  NANOKA_REVIEW_DECISIONS_BATCH_003,
} from "../data/rules/nanoka-review-decisions.js";
import { resolveTeamDamageBuffs, type TeamMemberDamageProfile } from "../src/domain/engine/resolve-team-damage-buffs.js";

const EMPTY_COMBAT_PANEL = {
  hp: 1000,
  atk: 100,
  def: 100,
  impact: 86,
  critRate: 5,
  critDmg: 50,
  anomalyMastery: 100,
  anomalyProficiency: 100,
  penRate: 0,
  penFlat: 0,
  energyRegen: 1.2,
  physicalDmgBonus: 0,
  fireDmgBonus: 0,
  iceDmgBonus: 0,
  electricDmgBonus: 0,
  etherDmgBonus: 0,
} as const;

test("声明式 2 件套规则通过校验并生成面板修正项", () => {
  const rule = DRIVE_DISC_2PC_RULES["31800"]?.[0];
  assert.ok(rule);
  assert.equal(validateBuffRule(rule).valid, true);

  const result = evaluatePanelBuffRules([rule]);
  assert.deepEqual(result.modifiers, [
    {
      sourceId: "set:31800:2pc",
      label: "混沌爵士 2 件套",
      stat: "anomalyProficiency",
      value: 30,
    },
  ]);
  assert.deepEqual(result.warnings, []);
});

test("队伍 Buff 引擎消费任意规则并保持局内面板修正独立", () => {
  const member: TeamMemberDamageProfile = {
    id: "test-character",
    name: "测试角色",
    role: "异常",
    element: "物理",
    level: 60,
    cinema: 0,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL },
  };
  const result = resolveTeamDamageBuffs({
    attackerId: member.id,
    team: [member],
    assumeFullBuffs: false,
    rules: [{
      schemaVersion: 1,
      id: "manual:test:combat-anomaly-mastery",
      source: {
        type: "character",
        id: member.id,
        label: "测试角色｜局内异常掌控",
        provider: "manual",
      },
      status: "verified",
      target: "self",
      phase: "combat",
      timing: "permanent",
      condition: { type: "always" },
      effects: [{
        kind: "stat",
        stat: "anomalyMastery",
        operation: "add-flat",
        value: 12,
      }],
      rawDescription: "测试用局内异常掌控+12。",
    }],
  });

  assert.deepEqual(result.combatPanelModifiers, [{
    sourceId: "manual:test:combat-anomaly-mastery",
    label: "测试角色｜局内异常掌控",
    stat: "anomalyMastery",
    value: 12,
  }]);
  assert.equal(member.panel.anomalyMastery, 100);
});

test("丽娜核心按局内穿透率动态提升其他队友且不作用于自己", () => {
  const rina: TeamMemberDamageProfile = {
    id: "1211",
    name: "丽娜",
    role: "支援",
    element: "电",
    level: 60,
    cinema: 0,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL, penRate: 20 },
  };
  const attacker: TeamMemberDamageProfile = {
    id: "test-attacker",
    name: "测试队友",
    role: "强攻",
    element: "电",
    level: 60,
    cinema: 0,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL },
  };

  const allyResult = resolveTeamDamageBuffs({
    attackerId: attacker.id,
    team: [rina, attacker],
    assumeFullBuffs: true,
    rules: REVIEWED_CHARACTER_BUFF_RULES,
  });
  assert.equal(
    allyResult.combatPanelModifiers.find((modifier) =>
      modifier.sourceId === "nanoka:character_1211_passive_pen_rate_core_7")?.value,
    17,
  );

  const selfResult = resolveTeamDamageBuffs({
    attackerId: rina.id,
    team: [rina, attacker],
    assumeFullBuffs: true,
    rules: REVIEWED_CHARACTER_BUFF_RULES,
  });
  assert.equal(selfResult.combatPanelModifiers.some((modifier) =>
    modifier.sourceId === "nanoka:character_1211_passive_pen_rate_core_7"), false);
});

test("薇薇安单人不会激活额外能力，专武满6层后同时进入异放倍率与异常效果强度", () => {
  const vivian: TeamMemberDamageProfile = {
    id: "1331",
    name: "薇薇安",
    role: "异常",
    element: "以太",
    level: 60,
    cinema: 1,
    coreLevel: 7,
    weaponId: "14133",
    weaponRefinement: 1,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL, atk: 1593, anomalyProficiency: 208, anomalyMastery: 144 },
  };
  const solo = resolveTeamDamageBuffs({
    attackerId: vivian.id,
    team: [vivian],
    assumeFullBuffs: true,
    rules: REVIEWED_BUFF_RULES,
  });

  assert.equal(solo.normalDamageBonusPercent, 0);
  assert.equal(solo.anomalyDamageBonusPercent, 16);
  assert.equal(solo.yifangDamageBonusPercent, 0);
  assert.equal(solo.disorderDamageBonusFromSourcePercent, 16);
  assert.equal(solo.combatPanelModifiers.find((modifier) =>
    modifier.sourceId === "nanoka:weapon_14133_talent_1_proficiency_stacks")?.value, 120);
  const etherYifang = solo.derivedDamageEffects.find((effect) => effect.element === "ether");
  assert.ok(etherYifang);
  assert.ok(Math.abs(etherYifang.multiplier - 2.0172) < 1e-9);
  assert.equal(solo.activatedBuffs.some((buff) =>
    buff.id === "nanoka:character_1331_extra_ability_corrosion_bonus"), false);

  const anomalyAlly: TeamMemberDamageProfile = {
    id: "test-anomaly-ally",
    name: "测试异常队友",
    role: "异常",
    element: "火属性",
    level: 60,
    cinema: 0,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL },
  };
  const team = resolveTeamDamageBuffs({
    attackerId: vivian.id,
    team: [vivian, anomalyAlly],
    assumeFullBuffs: true,
    rules: REVIEWED_BUFF_RULES,
  });
  assert.equal(team.anomalyDamageBonusPercent, 28);
  assert.equal(team.yifangDamageBonusPercent, 0);
  assert.equal(team.disorderDamageBonusFromSourcePercent, 28);
});

test("条件树明确区分 all 和 any，未满足条件时不应用 Buff", () => {
  const context = {
    values: {
      attack: { skillCategory: "basic" },
      enemy: { isStunned: true },
    },
  };
  assert.equal(
    evaluateCondition(
      {
        type: "all",
        conditions: [
          { type: "compare", path: "attack.skillCategory", operator: "equals", value: "basic" },
          { type: "compare", path: "enemy.isStunned", operator: "equals", value: true },
        ],
      },
      context,
    ),
    true,
  );
  assert.equal(
    evaluateCondition(
      {
        type: "all",
        conditions: [
          { type: "compare", path: "attack.skillCategory", operator: "equals", value: "special" },
          { type: "compare", path: "enemy.isStunned", operator: "equals", value: true },
        ],
      },
      context,
    ),
    false,
  );
});

test("校验器拒绝缺少效果和越界叠层的规则", () => {
  const result = validateBuffRule({
    schemaVersion: 1,
    id: "invalid",
    source: {
      type: "drive-disc-set",
      id: "x",
      label: "无效规则",
      provider: "manual",
    },
    status: "verified",
    target: "self",
    phase: "panel",
    timing: "permanent",
    condition: { type: "always" },
    effects: [],
    rawDescription: "测试",
    stacks: { mode: "manual", min: 2, max: 1, initial: 3 },
  });

  assert.equal(result.valid, false);
  assert.ok(result.issues.some((issue) => issue.path === "effects"));
  assert.ok(result.issues.some((issue) => issue.path === "stacks"));
  assert.ok(result.issues.some((issue) => issue.path === "stacks.initial"));
});

test("Nanoka 首批人工确认规则全部通过校验", () => {
  assert.equal(NANOKA_REVIEWED_BATCH_001.length, 19);
  for (const rule of NANOKA_REVIEWED_BATCH_001) {
    const result = validateBuffRule(rule);
    assert.equal(result.valid, true, `${rule.id}: ${JSON.stringify(result.issues)}`);
    assert.equal(rule.status, "verified");
    assert.equal(rule.source.provider, "nanoka");
  }
});

test("Nanoka 第二批人工确认规则和审查决定通过校验", () => {
  assert.equal(NANOKA_REVIEWED_BATCH_002.length, 8);
  for (const rule of NANOKA_REVIEWED_BATCH_002) {
    const result = validateBuffRule(rule);
    assert.equal(result.valid, true, `${rule.id}: ${JSON.stringify(result.issues)}`);
    assert.equal(rule.status, "verified");
  }
  assert.equal(Object.keys(NANOKA_REVIEW_DECISIONS_BATCH_001).length, 22);
  assert.equal(
    NANOKA_REVIEW_DECISIONS_BATCH_001["character:1111:passive:1111507:1"]?.action,
    "ignore",
  );
  assert.equal(
    NANOKA_REVIEW_DECISIONS_BATCH_001["character:1141:passive:1141514:0"]?.action,
    "promote",
  );
  assert.equal(
    NANOKA_REVIEW_DECISIONS_BATCH_001["character:1111:passive:1111506:1"]?.action,
    "ignore",
  );
  assert.equal(
    NANOKA_REVIEW_DECISIONS_BATCH_001["character:1141:passive:1141513:0"]?.action,
    "promote",
  );
  const qingyiDecision = NANOKA_REVIEW_DECISIONS_BATCH_001["character:1251:talent:6"];
  assert.equal(qingyiDecision?.action, "promote");
  if (qingyiDecision?.action === "promote") {
    assert.equal(qingyiDecision.rules?.length, 2);
  }
  const jianDecision = NANOKA_REVIEW_DECISIONS_BATCH_001["character:1261:talent:2"];
  assert.equal(jianDecision?.action, "promote");
  if (jianDecision?.action === "promote") {
    assert.equal(jianDecision.rules?.length, 2);
  }
  const jianDefIgnore = NANOKA_REVIEWED_BATCH_002.find((rule) => rule.id === "nanoka:character_1261_talent_2_assault_def_ignore");
  assert.ok(jianDefIgnore);
  const jianDefIgnoreEffect = jianDefIgnore.effects.find((effect) => effect.kind === "def-ignore");
  assert.ok(jianDefIgnoreEffect && jianDefIgnoreEffect.kind === "def-ignore");
  assert.deepEqual(jianDefIgnoreEffect.scope?.damageKinds, ["assault"]);
});

test("Nanoka 合并语义组的第三批规则全部通过校验", () => {
  assert.equal(NANOKA_REVIEWED_BATCH_003.length, 22);
  for (const rule of NANOKA_REVIEWED_BATCH_003) {
    const result = validateBuffRule(rule);
    assert.equal(result.valid, true, `${rule.id}: ${JSON.stringify(result.issues)}`);
    assert.equal(rule.status, "verified");
  }
  assert.equal(Object.keys(NANOKA_REVIEW_DECISIONS_BATCH_002).length, 27);
  const jianProfile = NANOKA_REVIEWED_BATCH_003.find((rule) => rule.id.endsWith("1261506_assault_crit_profile"));
  assert.ok(jianProfile);
  const jianCrit = jianProfile.effects.find((effect) => effect.kind === "crit-profile");
  assert.ok(jianCrit && jianCrit.kind === "crit-profile");
  assert.equal(typeof jianCrit.critRate, "object");
  if (typeof jianCrit.critRate === "object") {
    assert.equal(jianCrit.critRate.type, "source-stat");
    assert.equal(jianCrit.critRate.path, "self.anomalyProficiency");
    assert.equal(jianCrit.critRate.scale, 0.15);
    assert.equal(jianCrit.critRate.cap, 100);
  }
  assert.ok(NANOKA_REVIEWED_BATCH_003.some((rule) =>
    rule.effects.some((effect) => effect.kind === "derived-damage" && effect.damageKind === "yifang"),
  ));
  const vivianProfile = NANOKA_REVIEWED_BATCH_003.find((rule) => rule.id.endsWith("1331507_yifang_damage"));
  assert.ok(vivianProfile);
  const etherYifang = vivianProfile.effects.find((effect) => effect.kind === "derived-damage" && effect.element === "ether");
  assert.ok(etherYifang && etherYifang.kind === "derived-damage");
  assert.equal(etherYifang.mode, "multiply-original-anomaly");
  assert.equal(
    typeof etherYifang.multiplier === "object" && etherYifang.multiplier.type === "source-stat"
      ? etherYifang.multiplier.scale
      : undefined,
    0.00615,
  );
  const promiaYifang = NANOKA_REVIEWED_BATCH_003.find((rule) => rule.id.endsWith("1541_talent_6_yifang_damage"));
  assert.ok(promiaYifang);
  const promiaEffect = promiaYifang.effects.find((effect) => effect.kind === "derived-damage");
  assert.ok(promiaEffect && promiaEffect.kind === "derived-damage");
  assert.equal(promiaEffect.mode, "replace-anomaly");
  assert.equal(NANOKA_REVIEW_DECISIONS_BATCH_002["character:1521:passive:1521055:0"]?.action, "ignore");
});

test("Nanoka 第四批异常伤害复审规则全部通过校验", () => {
  assert.equal(NANOKA_REVIEWED_BATCH_004.length, 25);
  for (const rule of NANOKA_REVIEWED_BATCH_004) {
    const result = validateBuffRule(rule);
    assert.equal(result.valid, true, `${rule.id}: ${JSON.stringify(result.issues)}`);
    assert.equal(rule.status, "verified");
  }
  assert.equal(Object.keys(NANOKA_REVIEW_DECISIONS_BATCH_003).length, 17);
  assert.equal(NANOKA_REVIEW_DECISIONS_BATCH_003["character:1071:passive:1071507:0"]?.action, "ignore");
  const anomalyCoefficient = NANOKA_REVIEWED_BATCH_004.find((rule) => rule.id.endsWith("1581_passive_1581507_0_anomaly_team_bonus"));
  assert.ok(anomalyCoefficient);
  assert.deepEqual(anomalyCoefficient.condition, {
    type: "team-role-count",
    role: "异常",
    operator: "equals",
    value: 3,
  });
  const polarDisorder = NANOKA_REVIEWED_BATCH_004.find((rule) => rule.id.endsWith("1511_talent_2_polar_disorder_count"));
  assert.ok(polarDisorder);
  const polarEffect = polarDisorder.effects.find((effect) => effect.kind === "polar-disorder");
  assert.ok(polarEffect && polarEffect.kind === "polar-disorder");
  assert.equal(polarEffect.maxTriggers, 3);
});

test("第四批规则会按队伍职业和敌人失衡状态解析异化与极性紊乱", () => {
  const member = (id: string, role: string): TeamMemberDamageProfile => ({
    id,
    name: id,
    role,
    element: "物理",
    level: 60,
    cinema: 0,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_COMBAT_PANEL },
  });
  const rules = NANOKA_REVIEWED_BATCH_004.filter((rule) => [
    "nanoka:character_1581_passive_1581507_0_anomaly_coefficient",
    "nanoka:character_1581_passive_1581507_0_anomaly_team_bonus",
    "nanoka:character_1511_passive_1511055_1_polar_disorder",
  ].includes(rule.id));
  const result = resolveTeamDamageBuffs({
    attackerId: "1581",
    team: [member("1581", "异常"), member("1511", "异常"), member("1401", "异常")],
    enemyStates: { stunned: true },
    assumeFullBuffs: true,
    rules,
  });

  assert.equal(result.anomalyEffectStrengthMultiplierPercent, 12);
  assert.equal(result.polarDisorderPercent, 25);
  assert.equal(result.polarDisorderMaxTriggers, 2);
  assert.deepEqual(
    result.vulnerabilityEffects.map((effect) => effect.percent),
    [30],
  );
});

test("统一注册表包含全部已审查的角色、音擎和驱动盘规则", () => {
  // 旧版人工规则仍然保留；Nanoka 无语义歧义的自动候选也由统一注册表
  // 接收，因此数量应至少覆盖旧基线，而不是被固定在旧版本的 586 条。
  assert.ok(REVIEWED_CHARACTER_BUFF_RULES.length >= 86);
  assert.ok(REVIEWED_WEAPON_BUFF_RULES.length >= 443);
  assert.ok(REVIEWED_DRIVE_DISC_BUFF_RULES.length >= 57);
  assert.equal(
    REVIEWED_BUFF_RULES.length,
    REVIEWED_CHARACTER_BUFF_RULES.length +
      REVIEWED_WEAPON_BUFF_RULES.length +
      REVIEWED_DRIVE_DISC_BUFF_RULES.length,
  );

  const ids = new Set<string>();
  for (const rule of REVIEWED_BUFF_RULES) {
    assert.equal(ids.has(rule.id), false, `重复规则：${rule.id}`);
    ids.add(rule.id);
    assert.equal(rule.status, "verified");
    assert.equal(validateBuffRule(rule).valid, true, `${rule.id}: ${JSON.stringify(validateBuffRule(rule).issues)}`);
  }

  assert.ok(REVIEWED_WEAPON_BUFF_RULES.some((rule) => rule.source.id === "14140"));
  assert.ok(REVIEWED_WEAPON_BUFF_RULES.some((rule) => rule.source.id === "14121"));
  assert.ok(REVIEWED_DRIVE_DISC_BUFF_RULES.some((rule) => rule.id === "set:31800:2pc"));
  assert.ok(REVIEWED_DRIVE_DISC_BUFF_RULES.some((rule) => rule.id === "nanoka:set_32600_4pc_damage"));
});

test("额外能力条件支持同属性、同职业、同阵营和凯撒防护特例", () => {
  const context = {
    values: {
      team: {
        members: [
          { id: "1071", role: "防护", element: "物理", camp: "卡吕冬之子" },
          { id: "1011", role: "防护", element: "电属性", camp: "狡兔屋" },
        ],
        self: { id: "1071", role: "防护", element: "物理", camp: "卡吕冬之子" },
      },
    },
  };
  const caesarRule = NANOKA_REVIEWED_BATCH_001.find((rule) => rule.id.includes("1071_extra"));
  assert.ok(caesarRule);
  assert.equal(evaluateCondition(caesarRule.condition, context), true);
  assert.equal(
    evaluateCondition({ type: "team-role", role: "支援" }, context),
    false,
  );
  assert.equal(
    evaluateCondition({ type: "team-match", relation: "camp" }, context),
    false,
  );
  assert.equal(
    evaluateCondition(
      { type: "team-match", relation: "camp" },
      { values: { team: { members: [{ id: "1071", camp: "卡吕冬之子" }, { id: "1011", camp: "卡吕冬之子" }], self: { id: "1071", camp: "卡吕冬之子" } } } },
    ),
    true,
  );
});
