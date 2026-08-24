import assert from "node:assert/strict";
import test from "node:test";
import { REVIEWED_BUFF_RULES } from "../data/rules/reviewed-buff-registry.js";
import {
  resolveDamageEventContext,
  resolveIndependentCrit,
} from "../src/domain/engine/resolve-damage-event-effects.js";
import { calculateDerivedAnomalyDamage } from "../src/domain/engine/calculate-derived-anomaly-damage.js";
import {
  calculateDirectDamage,
  calculateResolvedDamageInstance,
} from "../src/domain/engine/calculate-direct-damage.js";
import {
  resolveTeamDamageBuffs,
  type TeamMemberDamageProfile,
} from "../src/domain/engine/resolve-team-damage-buffs.js";
import type { FinalPanelStats } from "../src/domain/model/panel.js";

const panel: FinalPanelStats = {
  hp: 10000,
  atk: 3000,
  def: 800,
  impact: 100,
  critRate: 50,
  critDmg: 100,
  anomalyMastery: 200,
  anomalyProficiency: 500,
  penRate: 0,
  penFlat: 0,
  energyRegen: 1.2,
  physicalDmgBonus: 0,
  fireDmgBonus: 0,
  iceDmgBonus: 0,
  electricDmgBonus: 0,
  etherDmgBonus: 0,
  windDmgBonus: 0,
};

function member(id: string, cinema = 6): TeamMemberDamageProfile {
  return {
    id,
    name: id,
    role: "异常",
    element: id === "1501" ? "以太" : "物理",
    level: 60,
    cinema,
    coreLevel: 7,
    driveDiscSetCounts: {},
    panel: { ...panel },
  };
}

test("团队解析器保留伤害实例、派生伤害、独立暴击区和标签转换", () => {
  const rules = REVIEWED_BUFF_RULES.filter((rule) =>
    rule.id === "nanoka:character_1401_skill_basic_1_polar_assault" ||
    rule.id === "nanoka:character_1541_talent_6_yifang_damage" ||
    rule.id === "nanoka:character_1501_talent_1_yifang_crit_profile" ||
    rule.id === "nanoka:character_1051_core_ice_penetration_conversion");
  const result = resolveTeamDamageBuffs({
    attackerId: "1401",
    team: [member("1401"), member("1541"), member("1501")],
    enemyStates: {},
    assumeFullBuffs: true,
    rules,
  });

  assert.equal(result.damageInstances.length, 1);
  assert.equal(result.damageInstances[0]?.damageKind, "assault");
  assert.equal(result.damageInstances[0]?.baseValue, 21390);
  assert.equal(result.derivedDamageEffects.length, 1);
  assert.equal(result.derivedDamageEffects[0]?.multiplier, 2);
  // target=self 且当前攻击者不是爱芮/伊德海莉，因此不会错误借用队友的独立区或转换。
  assert.equal(result.critProfiles.length, 0);
  assert.equal(result.damageConversions.length, 0);
});

test("简的强击暴击读取异常精通、在100%封顶，并叠加2画暴伤", () => {
  const jane = member("1261", 2);
  const rules = REVIEWED_BUFF_RULES.filter((rule) => rule.source.id === "1261");
  const buffs = resolveTeamDamageBuffs({
    attackerId: jane.id,
    team: [jane],
    enemyStates: { "啮咬": true },
    assumeFullBuffs: true,
    rules,
  });
  const crit = resolveIndependentCrit({
    damageKind: "assault",
    element: "physical",
    sourceMemberId: jane.id,
  }, buffs.critProfiles, buffs.critDamageBonusEffects);

  assert.equal(crit.zones.length, 1);
  assert.equal(crit.zones[0]?.critRatePercent, 100);
  assert.equal(crit.zones[0]?.critDamagePercent, 50);
  assert.equal(crit.zones[0]?.critDamageBonusPercent, 50);
  assert.equal(crit.multiplier, 2);
});

test("爱芮异放暴击使用局外初始异常掌控，0.5%不会缩小100倍", () => {
  const ares = member("1501", 1);
  ares.panel.anomalyMastery = 200;
  const buffs = resolveTeamDamageBuffs({
    attackerId: ares.id,
    team: [ares],
    assumeFullBuffs: true,
    rules: REVIEWED_BUFF_RULES.filter((rule) =>
      rule.id === "nanoka:character_1501_talent_1_yifang_crit_profile"),
  });
  const crit = resolveIndependentCrit({
    damageKind: "yifang",
    element: "ether",
    skillCategory: "basic",
    sourceMemberId: ares.id,
  }, buffs.critProfiles, buffs.critDamageBonusEffects);

  assert.equal(crit.zones[0]?.critRatePercent, 75);
  assert.equal(crit.zones[0]?.critDamagePercent, 25);
  assert.equal(crit.multiplier, 1.1875);
});

test("伤害转换先改写标签，后续乘区读取贯穿伤害上下文", () => {
  const converted = resolveDamageEventContext({
    damageKind: "direct",
    element: "ice",
    sourceMemberId: "1051",
  }, [{
    id: "conversion",
    label: "冰伤贯穿化",
    sourceMemberId: "1051",
    from: "ice",
    to: "penetration",
  }]);
  assert.equal(converted.originalDamageKind, "direct");
  assert.equal(converted.damageKind, "penetration");
  assert.equal(converted.appliedConversions.length, 1);
});

test("派生异常伤害严格区分乘原异常倍率和替换异常倍率", () => {
  const monster = {
    attackerLevel: 60,
    monsterLevel: 70,
    monsterDefenseAtLevel70: 0,
    baseResistancePercent: 0,
    vulnerability: { currentVulnerabilityPercent: 0 },
    damageScope: { damageKind: "yifang" as const, element: "physical" as const },
  };
  const common = {
    anomalyEffectStrength: 10000,
    sourceAnomalySkillMultiplierPercent: 713,
    anomalyDamageBonusPercent: 20,
    anomalyCritMultiplier: 1,
    derivedDamageBonusPercent: 20,
    monster,
  };
  const multiplied = calculateDerivedAnomalyDamage({
    ...common,
    effect: {
      id: "multiply",
      label: "原属性异常异放",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "multiply-original-anomaly",
      multiplier: 2,
      inheritElement: true,
    },
  });
  const replaced = calculateDerivedAnomalyDamage({
    ...common,
    effect: {
      id: "replace",
      label: "替换倍率异放",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "replace-anomaly",
      multiplier: 5,
      inheritElement: true,
    },
  });

  assert.equal(multiplied.damage.baseValue, 142600);
  assert.equal(multiplied.damage.finalValue, 205344);
  assert.equal(replaced.damage.baseValue, 50000);
  assert.equal(replaced.damage.finalValue, 72000);
});

test("直伤实例计算暴击期望，贯穿伤害只绕过防御区", () => {
  const monster = {
    attackerLevel: 60,
    monsterLevel: 70,
    monsterDefenseAtLevel70: 794,
    baseResistancePercent: 20,
    vulnerability: { currentVulnerabilityPercent: 50 },
  };
  const direct = calculateDirectDamage({
    baseValue: 1000,
    damageKind: "direct",
    damageBonusPercent: 100,
    critRatePercent: 50,
    critDamagePercent: 100,
    monster,
  });
  const penetration = calculateDirectDamage({
    baseValue: 1000,
    damageKind: "penetration",
    damageBonusPercent: 100,
    critRatePercent: 50,
    critDamagePercent: 100,
    monster,
  });

  assert.equal(direct.defenseZone, 0.5);
  assert.ok(Math.abs(direct.expectedValue - 1800) < 1e-9);
  assert.equal(penetration.defenseZone, 1);
  assert.ok(Math.abs(penetration.expectedValue - 3600) < 1e-9);
});

test("附加伤害实例按触发作用域过滤，并统一消费队伍乘区", () => {
  const result = calculateResolvedDamageInstance({
    instance: {
      id: "instance",
      label: "强化特殊技附加伤害",
      sourceMemberId: "9001",
      damageKind: "direct",
      baseValue: 1000,
      element: "fire",
      scope: { skillCategories: ["special"] },
    },
    triggerContext: { damageKind: "direct", element: "fire", skillCategory: "special" },
    fallbackElement: "fire",
    baseDamageBonusPercent: 20,
    baseCritRatePercent: 100,
    baseCritDamagePercent: 50,
    buffs: {
      normalDamageBonusPercent: 10,
      scopedDamageBonusEffects: [{
        id: "fire",
        label: "火伤",
        percent: 20,
        scope: { elements: ["fire"] },
      }],
      critDamageBonusEffects: [{ id: "crit", label: "暴伤", percent: 50 }],
      damageConversions: [],
      defenseEffects: [],
      resistanceEffects: [],
      vulnerabilityEffects: [],
    },
    monster: {
      attackerLevel: 60,
      monsterLevel: 70,
      monsterDefenseAtLevel70: 0,
      baseResistancePercent: 0,
      vulnerability: { currentVulnerabilityPercent: 0 },
    },
  });
  if ("supported" in result) throw new Error(result.reason);
  assert.equal(result.damageBonusZone, 1.5);
  assert.equal(result.critDamageZone, 2);
  assert.equal(result.expectedValue, 3000);
});
