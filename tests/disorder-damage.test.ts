import assert from "node:assert/strict";
import test from "node:test";
import { calculateDisorderDamage } from "../src/domain/engine/calculate-disorder-damage.js";

const noMonsterModifier = {
  attackerLevel: 60,
  monsterLevel: 70,
  monsterDefenseAtLevel70: 0,
  baseResistancePercent: 0,
  vulnerability: { currentVulnerabilityPercent: 0 },
};

test("紊乱使用异常来源者的异常效果强度，并按剩余时间计算基础倍率", () => {
  const result = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "physical",
    variant: "normal",
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.remainingSeconds, 10);
  assert.equal(result.timeCompensationPercent, 75);
  assert.equal(result.baseMultiplierPercent, 525);
  assert.equal(result.baseValue, 52500);
  assert.equal(result.finalValue, 52500);
});

test("灼烧、感电、侵蚀、烈霜使用各自的剩余时间倍率，烈霜默认20秒", () => {
  const cases = [
    ["burn", 1450],
    ["electric", 1700],
    ["corrosion", 1700],
    ["frost-ice", 1950],
  ] as const;

  for (const [source, expectedMultiplier] of cases) {
    const result = calculateDisorderDamage({
      sourceAnomalyEffectStrength: 100,
      source,
      variant: "normal",
      monster: noMonsterModifier,
    });

    assert.equal(result.supported, true);
    if (!result.supported) continue;
    assert.equal(result.baseMultiplierPercent, expectedMultiplier);
  }
});

test("异常持续时间延长可以让剩余时间超过基础10秒", () => {
  const result = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 100,
    source: "physical",
    variant: "normal",
    remainingSeconds: 13,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.timeCompensationPercent, 97.5);
  assert.equal(result.baseMultiplierPercent, 547.5);
});

test("风化不结算普通紊乱，风极性紊乱不受剩余时间影响", () => {
  const normal = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "wind",
    variant: "normal",
    monster: noMonsterModifier,
  });
  assert.equal(normal.supported, false);

  const polar = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "wind",
    variant: "polar",
    remainingSeconds: 0,
    polarDisorderPercent: 100,
    monster: noMonsterModifier,
  });
  assert.equal(polar.supported, true);
  if (!polar.supported) return;
  assert.equal(polar.timeCompensationPercent, 0);
  assert.equal(polar.baseMultiplierPercent, 450);
  assert.equal(polar.finalValue, 45000);
});

test("造成与被结算的紊乱增伤属于同一个独立乘区，但归属分别保留", () => {
  const result = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "physical",
    variant: "normal",
    disorderDamageBonusFromSourcePercent: 10,
    disorderDamageBonusFromTriggererPercent: 20,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.sourceDisorderBonusZone, 1.1);
  assert.equal(result.triggererDisorderBonusZone, 1.2);
  assert.equal(result.disorderIndependentMultiplier, 1.3);
  assert.equal(result.finalValue, 68250);
});

test("极性紊乱先结算原紊乱比例，再叠加柳的异常精通附加伤害", () => {
  const result = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "physical",
    variant: "polar",
    polarDisorderPercent: 50,
    polarAnomalyMasterySkillMultiplierPercent: 3200,
    currentAnomalyMastery: 400,
    triggererAttackPower: 2000,
    monster: noMonsterModifier,
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.finalDisorderValue, 52500);
  assert.equal(result.polarOriginalValue, 26250);
  assert.equal(result.polarAdditionalBaseValue, 64000);
  assert.equal(result.polarAdditionalFinalValue, 64000);
  assert.equal(result.finalValue, 90250);
});

test("极性紊乱附加基础值也经过紊乱增伤区和怪物乘区", () => {
  const result = calculateDisorderDamage({
    sourceAnomalyEffectStrength: 10000,
    source: "physical",
    variant: "polar",
    polarDisorderPercent: 50,
    disorderDamageBonusFromSourcePercent: 10,
    disorderDamageBonusFromTriggererPercent: 20,
    polarAnomalyMasterySkillMultiplierPercent: 3200,
    currentAnomalyMastery: 400,
    triggererAttackPower: 2000,
    monster: {
      ...noMonsterModifier,
      monsterDefenseAtLevel70: 198.5,
      baseResistancePercent: -20,
      vulnerability: { currentVulnerabilityPercent: 50 },
    },
  });

  assert.equal(result.supported, true);
  if (!result.supported) return;
  assert.equal(result.disorderIndependentMultiplier, 1.3);
  assert.equal(result.monsterMultiplier, 1.44);
  assert.equal(result.polarAdditionalBaseValue, 64000);
  assert.equal(result.polarAdditionalFinalValue, 119808);
  assert.equal(result.finalValue, 168948);
});
