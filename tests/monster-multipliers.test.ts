import assert from "node:assert/strict";
import test from "node:test";
import {
  calculateDefenseZone,
  calculateMonsterMultipliers,
  calculateResistanceZone,
  calculateVulnerabilityZone,
} from "../src/domain/engine/calculate-monster-multipliers.js";

const baseMonster = {
  attackerLevel: 60,
  monsterLevel: 70,
  monsterDefenseAtLevel70: 794,
  baseResistancePercent: 0,
  vulnerability: { currentVulnerabilityPercent: 0 },
};

test("防御区沿用旧版：Lv60角色对Lv70同防御目标为794/(794+794)", () => {
  const result = calculateDefenseZone(baseMonster);

  assert.equal(result.attackerDefenseConstant, 794);
  assert.equal(result.monsterDefense, 794);
  assert.equal(result.effectiveDefense, 794);
  assert.equal(result.zone, 0.5);
});

test("防御区按防御削减/无视、穿透率、固定穿透顺序计算", () => {
  const result = calculateDefenseZone({
    ...baseMonster,
    defenseShredPercent: 20,
    defenseIgnorePercent: 10,
    penetrationRatePercent: 25,
    penetrationFlat: 50,
  });

  assert.ok(Math.abs(result.effectiveDefense - 366.85) < 1e-12);
  assert.ok(Math.abs(result.zone - 794 / (366.85 + 794)) < 1e-12);
});

test("防御削减是全局 Debuff，防御无视按伤害标签过滤", () => {
  const effects = [
    { kind: "shred" as const, percent: 20 },
    { kind: "ignore" as const, percent: 15, scope: { damageKinds: ["assault"] as const } },
  ];
  const assault = calculateDefenseZone({
    ...baseMonster,
    defenseEffects: effects,
    damageScope: { damageKind: "assault" },
  });
  const disorder = calculateDefenseZone({
    ...baseMonster,
    defenseEffects: effects,
    damageScope: { damageKind: "disorder" },
  });

  assert.equal(assault.defenseShredPercent, 20);
  assert.equal(assault.defenseIgnorePercent, 15);
  assert.equal(disorder.defenseShredPercent, 20);
  assert.equal(disorder.defenseIgnorePercent, 0);
  assert.ok(assault.effectiveDefense < disorder.effectiveDefense);
});

test("抗性区按基础抗性减去减抗和抗性无视后线性计算", () => {
  const result = calculateResistanceZone({
    ...baseMonster,
    baseResistancePercent: 25,
    resistanceShredPercent: 10,
    resistanceIgnorePercent: 20,
  });

  assert.equal(result.effectiveResistancePercent, -5);
  assert.equal(result.zone, 1.05);
});

test("易伤区只接收当前有效易伤，并支持来源层计算后的上限", () => {
  const result = calculateVulnerabilityZone({
    currentVulnerabilityPercent: 30,
    maxMultiplier: 1.1,
  });

  assert.equal(result.uncappedPercent, 130);
  assert.equal(result.zone, 1.1);
});

test("三类怪物乘区最终相乘", () => {
  const result = calculateMonsterMultipliers({
    ...baseMonster,
    baseResistancePercent: -20,
    vulnerability: { currentVulnerabilityPercent: 50 },
  });

  assert.equal(result.defense.zone, 0.5);
  assert.equal(result.resistance.zone, 1.2);
  assert.equal(result.vulnerability.zone, 1.5);
  assert.ok(Math.abs(result.multiplier - 0.9) < 1e-12);
});
