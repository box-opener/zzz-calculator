import assert from "node:assert/strict";
import test from "node:test";
import {
  calculateAnomalyDamage,
  calculateAnomalyEffectStrength,
} from "../src/domain/engine/calculate-anomaly-damage.js";

const noMonsterModifier = {
  attackerLevel: 60,
  monsterLevel: 70,
  monsterDefenseAtLevel70: 0,
  baseResistancePercent: 0,
  vulnerability: { currentVulnerabilityPercent: 0 },
};

test("异常效果强度按等级系数、异常精通区、普通增伤区和攻击力计算", () => {
  const result = calculateAnomalyEffectStrength({
    characterLevel: 60,
    anomalyProficiency: 500,
    normalDamageBonusPercent: 0,
    attackPower: 1000,
  });

  assert.equal(result.attackLevelCoefficient, 2);
  assert.equal(result.anomalyProficiencyZone, 5);
  assert.equal(result.normalDamageZone, 1);
  assert.equal(result.value, 10000);
});

test("强击基础值等于异常效果强度乘技能倍率", () => {
  const result = calculateAnomalyDamage({
    kind: "assault",
    anomalyEffectStrength: 10000,
    anomalySkillMultiplierPercent: 713,
    anomalyDamageBonusPercent: 20,
    anomalyCritMultiplier: 1,
    monster: noMonsterModifier,
  });

  assert.equal(result.baseValue, 71300);
  assert.equal(result.independentMultiplier, 1.2);
  assert.equal(result.finalValue, 85560);
});

test("异放同时乘异放倍率并额外进入异放增伤区", () => {
  const result = calculateAnomalyDamage({
    kind: "yifang",
    anomalyEffectStrength: 10000,
    yifangMode: "multiply-original-anomaly",
    anomalySkillMultiplierPercent: 713,
    extraDamageMultiplierPercent: 200,
    anomalyDamageBonusPercent: 20,
    extraDamageBonusPercent: 20,
    anomalyCritMultiplier: 1,
    monster: noMonsterModifier,
  });

  assert.equal(result.baseValue, 142600);
  assert.equal(result.independentMultiplier, 1.44);
  assert.equal(result.finalValue, 205344);
});

test("异放可以使用独立的抗性区而保留原异常倍率", () => {
  const anomaly = calculateAnomalyDamage({
    kind: "assault",
    anomalyEffectStrength: 10000,
    anomalySkillMultiplierPercent: 713,
    anomalyDamageBonusPercent: 0,
    anomalyCritMultiplier: 1,
    monster: { ...noMonsterModifier, baseResistancePercent: -20 },
  });
  const yifang = calculateAnomalyDamage({
    kind: "yifang",
    anomalyEffectStrength: 10000,
    yifangMode: "multiply-original-anomaly",
    anomalySkillMultiplierPercent: 713,
    extraDamageMultiplierPercent: 200,
    anomalyDamageBonusPercent: 0,
    extraDamageBonusPercent: 0,
    anomalyCritMultiplier: 1,
    monster: { ...noMonsterModifier, baseResistancePercent: -40 },
  });

  assert.equal(anomaly.finalValue, 85560);
  assert.equal(yifang.finalValue, 199640);
});

test("直接属性异常型异放用自身倍率替换原异常倍率", () => {
  const result = calculateAnomalyDamage({
    kind: "yifang",
    anomalyEffectStrength: 10000,
    yifangMode: "replace-anomaly",
    anomalySkillMultiplierPercent: 500,
    anomalyDamageBonusPercent: 20,
    extraDamageBonusPercent: 20,
    anomalyCritMultiplier: 1,
    monster: noMonsterModifier,
  });

  assert.equal(result.anomalySkillMultiplier, 5);
  assert.equal(result.extraDamageMultiplier, 1);
  assert.equal(result.baseValue, 50000);
  assert.equal(result.independentMultiplier, 1.44);
  assert.equal(result.finalValue, 72000);
});

test("异放未声明两种倍率语义时拒绝计算", () => {
  assert.throws(() => calculateAnomalyDamage({
    kind: "yifang",
    anomalyEffectStrength: 10000,
    anomalySkillMultiplierPercent: 713,
    extraDamageMultiplierPercent: 200,
    anomalyDamageBonusPercent: 0,
    anomalyCritMultiplier: 1,
    monster: noMonsterModifier,
  }), /yifangMode/);
});
