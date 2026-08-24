import assert from "node:assert/strict";
import test from "node:test";
import { calculateResistanceZone } from "../src/domain/engine/calculate-monster-multipliers.js";

const baseInput = {
  attackerLevel: 60,
  monsterLevel: 70,
  monsterDefenseAtLevel70: 0,
  baseResistancePercent: 0,
  vulnerability: { currentVulnerabilityPercent: 0 },
  resistanceEffects: [
    { kind: "shred" as const, percent: 18 },
    {
      kind: "ignore" as const,
      percent: 15,
      scope: { damageKinds: ["direct", "penetration"] as const },
    },
  ],
};

test("全局减抗对直伤和异放都生效，但直伤才额外吃照的抗性无视", () => {
  const direct = calculateResistanceZone({
    ...baseInput,
    damageScope: { damageKind: "direct" },
  });
  const yifang = calculateResistanceZone({
    ...baseInput,
    damageScope: { damageKind: "yifang" },
  });

  assert.equal(direct.effectiveResistancePercent, -33);
  assert.equal(direct.zone, 1.33);
  assert.equal(yifang.effectiveResistancePercent, -18);
  assert.equal(yifang.zone, 1.18);
});

test("没有攻击上下文时不应用带作用域的抗性无视", () => {
  const result = calculateResistanceZone(baseInput);

  assert.equal(result.effectiveResistancePercent, -18);
  assert.equal(result.zone, 1.18);
});
