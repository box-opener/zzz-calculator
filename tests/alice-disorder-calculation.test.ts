import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { calculateAnomalyEffectStrength } from "../src/domain/engine/calculate-anomaly-damage.js";
import { calculateDisorderDamage } from "../src/domain/engine/calculate-disorder-damage.js";
import { calculatePanel } from "../src/domain/engine/calculate-panel.js";
import type { FinalPanelStats, PanelCalculationInput } from "../src/domain/model/panel.js";

interface AliceFixture {
  build: {
    character: {
      level: number;
    };
  };
  panelInput: PanelCalculationInput;
  expected: FinalPanelStats;
}

interface MonsterRecord {
  stats_lv70: {
    def: number;
  };
  resistances: {
    damage_res: {
      physical: number;
    };
  };
  stun_extra_damage_taken_pct: number;
}

async function loadJson<T>(fileName: string): Promise<T> {
  const filePath = path.join(process.cwd(), fileName);
  return JSON.parse(await readFile(filePath, "utf8")) as T;
}

test("引擎串联计算爱丽丝对卫士Ⅱ型的满时长强击紊乱", async () => {
  const fixture = await loadJson<AliceFixture>("tests/fixtures/alice-uid-16241824.json");
  const monsters = await loadJson<Record<string, MonsterRecord>>("dict/zzz_monsters.json");
  const guardianType2 = monsters["300021"];
  assert.ok(guardianType2);

  const panel = calculatePanel(fixture.panelInput);
  assert.deepEqual(panel.final, fixture.expected);

  // 这些是本次计算假设下已激活的规则效果，不重新修改面板 fixture：
  // 十方锻星两层物理伤害+40%，獠牙重金属4件套伤害+35%。
  const normalDamageBonusPercent = panel.final.physicalDmgBonus + 40 + 35;
  const anomalyEffectStrength = calculateAnomalyEffectStrength({
    characterLevel: fixture.build.character.level,
    anomalyProficiency: panel.final.anomalyProficiency,
    normalDamageBonusPercent,
    attackPower: panel.final.atk,
  });

  const disorder = calculateDisorderDamage({
    sourceAnomalyEffectStrength: anomalyEffectStrength.value,
    source: "physical",
    variant: "normal",
    remainingSeconds: 10,
    fixedDisorderMultiplierPercent: 180,
    disorderDamageBonusFromSourcePercent: 15,
    monster: {
      attackerLevel: 60,
      monsterLevel: 70,
      monsterDefenseAtLevel70: guardianType2.stats_lv70.def,
      baseResistancePercent: guardianType2.resistances.damage_res.physical,
      defenseEffects: [{ kind: "shred", percent: 20 }],
      penetrationFlat: panel.final.penFlat,
      damageScope: { damageKind: "disorder" },
      vulnerability: { currentVulnerabilityPercent: 0 },
    },
  });

  assert.equal(disorder.supported, true);
  if (!disorder.supported) return;
  assert.equal(anomalyEffectStrength.value, 54839.319);
  assert.equal(disorder.baseMultiplierPercent, 705);
  assert.ok(Math.abs(disorder.finalValue - 244471.0892131701) < 1e-6);
});
