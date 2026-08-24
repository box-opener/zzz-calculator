import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { calculateAnomalyDamage, calculateAnomalyEffectStrength } from "../src/domain/engine/calculate-anomaly-damage.js";
import { calculateDisorderDamage } from "../src/domain/engine/calculate-disorder-damage.js";
import { calculatePanel } from "../src/domain/engine/calculate-panel.js";
import { resolveTeamDamageBuffs, type TeamMemberDamageProfile } from "../src/domain/engine/resolve-team-damage-buffs.js";
import type { FinalPanelStats, PanelCalculationInput } from "../src/domain/model/panel.js";
import { TEAM_DAMAGE_REVIEWED_RULES } from "../data/rules/team-damage-reviewed-001.js";

interface AliceFixture {
  build: { character: { level: number; cinema: number; coreLevel: number } };
  panelInput: PanelCalculationInput;
}

interface YuzuhaFixture {
  build: {
    character: {
      id: string;
      level: number;
      cinema: number;
      coreLevel: number;
      role: string;
      element: string;
    };
    weapon: { id: string; level: number; refinement: number };
    driveDiscSetCounts: Record<string, number>;
  };
  panelInput: PanelCalculationInput;
  expected: FinalPanelStats;
}

interface MonsterRecord {
  stats_lv70: { def: number };
  resistances: { damage_res: { physical: number } };
}

async function loadJson<T>(fileName: string): Promise<T> {
  const filePath = path.join(process.cwd(), fileName);
  return JSON.parse(await readFile(filePath, "utf8")) as T;
}

test("引擎自动激活爱丽丝+柚叶满拐并计算卫士Ⅱ型强击与紊乱", async () => {
  const alice = await loadJson<AliceFixture>("tests/fixtures/alice-uid-16241824.json");
  const yuzuha = await loadJson<YuzuhaFixture>("tests/fixtures/yuzuha-uid-16241824.json");
  const monsters = await loadJson<Record<string, MonsterRecord>>("dict/zzz_monsters.json");
  const guardianType2 = monsters["300021"];
  assert.ok(guardianType2);

  const alicePanel = calculatePanel(alice.panelInput);
  const yuzuhaPanel = calculatePanel(yuzuha.panelInput);
  assert.deepEqual(yuzuhaPanel.final, yuzuha.expected);

  const team: TeamMemberDamageProfile[] = [
    {
      id: "1401",
      name: "爱丽丝",
      role: "异常",
      element: "物理",
      level: alice.build.character.level,
      cinema: alice.build.character.cinema,
      coreLevel: alice.build.character.coreLevel,
      weaponId: "14140",
      weaponRefinement: 1,
      driveDiscSetCounts: { "31800": 2, "32600": 4 },
      panel: alicePanel.final,
    },
    {
      id: yuzuha.build.character.id,
      name: "柚叶",
      role: yuzuha.build.character.role,
      element: yuzuha.build.character.element,
      level: yuzuha.build.character.level,
      cinema: yuzuha.build.character.cinema,
      coreLevel: yuzuha.build.character.coreLevel,
    weaponId: yuzuha.build.weapon.id,
      weaponRefinement: yuzuha.build.weapon.refinement,
      driveDiscSetCounts: yuzuha.build.driveDiscSetCounts,
      panel: yuzuhaPanel.final,
    },
  ];

  const buffs = resolveTeamDamageBuffs({
    attackerId: "1401",
    team,
      // 满拐验证：狸之愿、啜泣摇篮满层、甜蜜惊吓和各类持续效果均已建立。
    enemyStates: { "sweet-frightened": true, stunned: false },
    assumeFullBuffs: true,
  });

  const activatedIds = buffs.activatedBuffs.map((buff) => buff.id);
  for (const id of [
    "nanoka:character_1401_passive_extra_anomaly_proficiency",
    "nanoka:weapon_14140_anomaly_mastery",
    "nanoka:character_1401_talent_1_defense_shred",
    "nanoka:character_1401_talent_2_damage_bonus",
    "nanoka:character_1411_core_team_attack",
    "nanoka:character_1411_extra_anomaly_damage",
    "nanoka:character_1411_talent_1_resistance_shred",
    "nanoka:character_1411_talent_2_team_damage",
    "nanoka:set_33400_4pc_team_damage",
    "nanoka:weapon_14121_team_damage",
  ]) {
    assert.ok(activatedIds.includes(id), `未自动激活 ${id}`);
  }

  const combatPanel = calculatePanel({
    ...alice.panelInput,
    modifiers: [...alice.panelInput.modifiers, ...buffs.combatPanelModifiers],
  });
  assert.equal(alicePanel.final.atk, 3103);
  assert.equal(alicePanel.final.anomalyMastery, 184);
  assert.equal(alicePanel.final.anomalyProficiency, 411);
  assert.equal(combatPanel.final.atk, 4303);
  assert.equal(combatPanel.final.anomalyMastery, 244);
  assert.equal(combatPanel.final.anomalyProficiency, 577.4);

  const reversedBuffs = resolveTeamDamageBuffs({
    attackerId: "1401",
    team,
    enemyStates: { "sweet-frightened": true, stunned: false },
    assumeFullBuffs: true,
    rules: [...TEAM_DAMAGE_REVIEWED_RULES].reverse(),
  });
  const reversedCombatPanel = calculatePanel({
    ...alice.panelInput,
    modifiers: [...alice.panelInput.modifiers, ...reversedBuffs.combatPanelModifiers],
  });
  assert.equal(reversedCombatPanel.final.anomalyProficiency, 577.4);

  // 面板40%物理伤害 + 十方锻星40% + 獠牙35% + 柚叶15% + 柚叶2画15% + 月光18% + 啜泣摇篮精炼5满层39.8%。
  const normalDamageBonusPercent = combatPanel.final.physicalDmgBonus + buffs.normalDamageBonusPercent;
  assert.equal(buffs.normalDamageBonusPercent, 162.8);
  const anomalyEffectStrength = calculateAnomalyEffectStrength({
    characterLevel: alice.build.character.level,
    anomalyProficiency: combatPanel.final.anomalyProficiency,
    normalDamageBonusPercent,
    attackPower: combatPanel.final.atk,
  });

  const monsterBase = {
    attackerLevel: 60,
    monsterLevel: 70,
    monsterDefenseAtLevel70: guardianType2.stats_lv70.def,
    baseResistancePercent: guardianType2.resistances.damage_res.physical,
    defenseEffects: buffs.defenseEffects,
    resistanceEffects: buffs.resistanceEffects,
    penetrationFlat: combatPanel.final.penFlat,
    vulnerability: { currentVulnerabilityPercent: 0 },
  } as const;

  const assault = calculateAnomalyDamage({
    kind: "assault",
    anomalyEffectStrength: anomalyEffectStrength.value,
    anomalySkillMultiplierPercent: 713,
    anomalyDamageBonusPercent: buffs.anomalyDamageBonusPercent,
    anomalyCritMultiplier: 1,
    monster: {
      ...monsterBase,
      damageScope: { damageKind: "assault", element: "physical" },
    },
  });

  const disorder = calculateDisorderDamage({
    sourceAnomalyEffectStrength: anomalyEffectStrength.value,
    source: "physical",
    variant: "normal",
    remainingSeconds: 10,
    fixedDisorderMultiplierPercent: buffs.fixedDisorderMultiplierPercent,
    disorderDamageBonusFromSourcePercent: buffs.disorderDamageBonusFromSourcePercent,
    disorderDamageBonusFromTriggererPercent: buffs.disorderDamageBonusFromTriggererPercent,
    monster: {
      ...monsterBase,
      damageScope: { damageKind: "disorder", element: "physical" },
    },
  });

  assert.equal(assault.anomalyEffectStrength, anomalyEffectStrength.value);
  assert.equal(assault.monsterZones.resistance.effectiveResistancePercent, -10);
  assert.equal(buffs.fixedDisorderMultiplierPercent, 180);
  assert.equal(buffs.anomalyDamageBonusPercent, 33.46);
  assert.equal(buffs.disorderDamageBonusFromSourcePercent, 33.46);
  assert.equal(disorder.supported, true);
  if (!disorder.supported) return;

  // 固定回归值来自当前新引擎，不是手算或旧 app.js 的输出。
  assert.ok(Math.abs(assault.finalValue - 865995.8777728736) < 1e-6);
  assert.ok(Math.abs(disorder.finalValue - 856279.2339829956) < 1e-6);
});
