import assert from "node:assert/strict";
import test from "node:test";
import { calculateTurbulenceDamage } from "../src/domain/engine/calculate-turbulence-damage.js";

const noMonsterModifier = {
  attackerLevel: 60,
  monsterLevel: 70,
  monsterDefenseAtLevel70: 0,
  baseResistancePercent: 0,
  vulnerability: { currentVulnerabilityPercent: 0 },
};

test("没有风化时乱流不会触发", () => {
  const result = calculateTurbulenceDamage({
    windAnomalyPresent: false,
    sourceAnomaly: "physical",
    sourceAnomalyEffectStrength: 10000,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, false);
});

test("乱流继承非风异常来源者的异常效果强度", () => {
  const result = calculateTurbulenceDamage({
    windAnomalyPresent: true,
    sourceAnomaly: "physical",
    sourceAnomalyEffectStrength: 10000,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.remainingSeconds, 10);
  assert.equal(result.baseMultiplierPercent, 800);
  assert.equal(result.durationMultiplierPercent, 75);
  assert.equal(result.baseAndDurationMultiplierPercent, 875);
  assert.equal(result.baseValue, 87500);
  assert.equal(result.finalValue, 87500);
});

test("乱流各属性的默认总倍率不含附加倍率", () => {
  const cases = [
    ["physical", 875],
    ["frost", 1375],
    ["burn", 1900],
    ["electric", 1900],
    ["corrosion", 1900],
    ["frost-ice", 1500],
  ] as const;

  for (const [sourceAnomaly, expectedMultiplier] of cases) {
    const result = calculateTurbulenceDamage({
      windAnomalyPresent: true,
      sourceAnomaly,
      sourceAnomalyEffectStrength: 100,
      monster: noMonsterModifier,
    });

    assert.equal(result.supported, true);
    if (!result.supported) continue;
    assert.equal(result.baseAndDurationMultiplierPercent, expectedMultiplier);
    assert.equal(result.additionalTurbulenceMultiplierPercent, 0);
  }
});

test("乱流持续时间延长会直接进入持续时间倍率", () => {
  const result = calculateTurbulenceDamage({
    windAnomalyPresent: true,
    sourceAnomaly: "physical",
    sourceAnomalyEffectStrength: 100,
    remainingSeconds: 13,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.durationMultiplierPercent, 97.5);
  assert.equal(result.baseAndDurationMultiplierPercent, 897.5);
});

test("维琳娜附加倍率属于基础伤害，简的乱流暴击会连同附加倍率一起放大", () => {
  const result = calculateTurbulenceDamage({
    windAnomalyPresent: true,
    sourceAnomaly: "physical",
    sourceAnomalyEffectStrength: 10000,
    additionalTurbulenceMultiplierPercent: 150,
    turbulenceDamageBonusPercent: 20,
    turbulenceCritMultiplier: 2,
    monster: {
      ...noMonsterModifier,
      monsterDefenseAtLevel70: 198.5,
      baseResistancePercent: -20,
      vulnerability: { currentVulnerabilityPercent: 50 },
    },
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.baseAndDurationMultiplierPercent, 875);
  assert.equal(result.totalMultiplierPercent, 1025);
  assert.equal(result.baseValue, 102500);
  assert.equal(result.turbulenceIndependentMultiplier, 2.4);
  assert.equal(result.monsterMultiplier, 1.44);
  assert.equal(result.finalValue, 354240);
});
