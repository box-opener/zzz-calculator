import assert from "node:assert/strict";
import test from "node:test";
import {
  calculateWebDamage,
  getWebEngineStatus,
  resolveWebTeamState,
  type WebDamageInput,
} from "../src/web/engine-entry.js";
import { calculateResistanceZone } from "../src/domain/engine/calculate-monster-multipliers.js";

const baseInput: WebDamageInput = {
  characterLevel: 60,
  attackPower: 1000,
  anomalyProficiency: 500,
  normalDamageBonusPercent: 0,
  anomalyEffectStrengthMultiplierPercent: 0,
  damageKind: "assault",
  anomalySkillMultiplierPercent: 713,
  anomalyDamageBonusPercent: 20,
  anomalyCritMultiplier: 1,
  extraDamageMultiplierPercent: 200,
  extraDamageBonusPercent: 20,
  disorderSource: "physical",
  disorderVariant: "normal",
  remainingSeconds: 10,
  fixedDisorderMultiplierPercent: 0,
  disorderDamageBonusFromSourcePercent: 0,
  disorderDamageBonusFromTriggererPercent: 0,
  polarDisorderPercent: 50,
  polarAnomalyMasterySkillMultiplierPercent: 0,
  currentAnomalyMastery: 400,
  triggererAttackPower: 2000,
  turbulenceSource: "physical",
  windAnomalyPresent: true,
  additionalTurbulenceMultiplierPercent: 0,
  turbulenceDamageBonusPercent: 0,
  turbulenceCritMultiplier: 1,
  monster: {
    attackerLevel: 60,
    monsterLevel: 70,
    monsterDefenseAtLevel70: 0,
    baseResistancePercent: 0,
    defenseShredPercent: 0,
    defenseIgnorePercent: 0,
    penetrationRatePercent: 0,
    penetrationFlat: 0,
    resistanceShredPercent: 0,
    resistanceIgnorePercent: 0,
    vulnerabilityPercent: 0,
    damageKind: "assault",
    element: "physical",
  },
};

test("浏览器适配层调用新版引擎且不会把异放倍率带入强击", () => {
  const result = calculateWebDamage(baseInput);
  assert.equal(result.effectStrength.value, 10000);
  if (!("finalValue" in result.trace)) throw new Error("强击不应返回不支持结果");
  assert.equal(result.trace.finalValue, 85560);
});

test("浏览器适配层可以明确计算两种异放语义", () => {
  const result = calculateWebDamage({
    ...baseInput,
    damageKind: "yifang",
    anomalySkillMultiplierPercent: 500,
    yifangMode: "replace-anomaly",
    monster: { ...baseInput.monster, damageKind: "yifang" },
  });
  if (!("finalValue" in result.trace)) throw new Error("异放不应返回不支持结果");
  assert.equal(result.trace.finalValue, 72000);
});

test("浏览器适配层暴露版本化规则状态并保留旧版路径", () => {
  const status = getWebEngineStatus();
  assert.equal(status.engine, "new");
  assert.ok(status.reviewedRuleCount >= 586);
  assert.equal(status.legacyPath, "../index.html");
});

test("浏览器队伍桥接先应用音擎面板再计算爱丽丝额外能力", () => {
  const result = resolveWebTeamState({
    attackerId: "1401",
    team: [
      {
        id: "1401",
        name: "爱丽丝",
        role: "异常",
        element: "物理",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        weaponId: "14140",
        weaponRefinement: 1,
        driveDiscSetCounts: { "31800": 2, "32600": 4 },
        panel: {
          hp: 10906,
          atk: 3103,
          def: 921,
          impact: 86,
          critRate: 7.4,
          critDmg: 54.8,
          anomalyMastery: 184,
          anomalyProficiency: 411,
          penRate: 0,
          penFlat: 36,
          energyRegen: 1.2,
          physicalDmgBonus: 40,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
      {
        id: "1411",
        name: "柚叶",
        role: "支援",
        element: "物理",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        weaponId: "14121",
        weaponRefinement: 5,
        driveDiscSetCounts: { "33000": 2, "33400": 4 },
        panel: {
          hp: 12272,
          atk: 3026,
          def: 826,
          impact: 86,
          critRate: 9.8,
          critDmg: 74,
          anomalyMastery: 171,
          anomalyProficiency: 248,
          penRate: 24,
          penFlat: 54,
          energyRegen: 1.44,
          physicalDmgBonus: 0,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
    ],
    enemyStates: { "sweet-frightened": true, stunned: false },
    assumeFullBuffs: true,
  });

  assert.equal(result.activePanel.atk, 4303);
  assert.equal(result.activePanel.anomalyMastery, 244);
  assert.equal(result.activePanel.anomalyProficiency, 577.4);
  assert.equal(result.buffs.normalDamageBonusPercent, 162.8);
  assert.equal(result.buffs.anomalyDamageBonusPercent, 33.46);
  assert.equal(result.buffs.disorderDamageBonusFromSourcePercent, 33.46);
  assert.ok(result.buffs.activatedBuffs.some((buff) => buff.id === "nanoka:weapon_14121_team_damage"));
  assert.equal(result.buffs.resistanceEffects[0]?.percent, 10);
});

test("爱丽丝、柚叶、扳机实装配置只结算一次扳机常态易伤", () => {
  const result = resolveWebTeamState({
    attackerId: "1401",
    team: [
      {
        id: "1401",
        name: "爱丽丝",
        role: "异常",
        element: "物理",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        weaponId: "14140",
        weaponRefinement: 1,
        driveDiscSetCounts: { "31800": 2, "32600": 4 },
        panel: {
          hp: 10906,
          atk: 3103,
          def: 921,
          impact: 86,
          critRate: 7.4,
          critDmg: 54.8,
          anomalyMastery: 184,
          anomalyProficiency: 411,
          penRate: 0,
          penFlat: 36,
          energyRegen: 1.2,
          physicalDmgBonus: 40,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
      {
        id: "1411",
        name: "柚叶",
        role: "支援",
        element: "物理",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        weaponId: "14121",
        weaponRefinement: 5,
        driveDiscSetCounts: { "33000": 2, "33400": 4 },
        panel: {
          hp: 12272,
          atk: 3026,
          def: 826,
          impact: 86,
          critRate: 9.8,
          critDmg: 74,
          anomalyMastery: 171,
          anomalyProficiency: 248,
          penRate: 24,
          penFlat: 54,
          energyRegen: 1.44,
          physicalDmgBonus: 0,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
      {
        id: "1361",
        name: "「扳机」",
        role: "击破",
        element: "电",
        level: 60,
        cinema: 1,
        coreLevel: 7,
        weaponId: "14136",
        weaponRefinement: 2,
        driveDiscSetCounts: {},
        panel: {
          hp: 10123,
          atk: 2219,
          def: 785,
          impact: 131,
          critRate: 53,
          critDmg: 50,
          anomalyMastery: 96,
          anomalyProficiency: 95,
          penRate: 0,
          penFlat: 0,
          energyRegen: 1.2,
          physicalDmgBonus: 0,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 30,
          etherDmgBonus: 0,
        },
      },
    ],
    enemyStates: { "sweet-frightened": true, stunned: false },
    assumeFullBuffs: true,
  });

  assert.ok(result.buffs.activatedBuffs.some((buff) => buff.id === "nanoka:weapon_14136_talent_2"));
  assert.deepEqual(
    result.buffs.defenseEffects.map((effect) => ({ kind: effect.kind, percent: effect.percent })),
    [
      { kind: "shred", percent: 20 },
      { kind: "shred", percent: 28.75 },
    ],
  );
  assert.deepEqual(
    result.buffs.vulnerabilityEffects.map((effect) => ({
      percent: effect.percent,
      label: effect.label,
    })),
    [
      { percent: 20, label: "「扳机」｜影画1：核心被动易伤提升" },
      { percent: 35, label: "「扳机」｜核心被动：破隙幽瞳" },
    ],
  );

  const damage = calculateWebDamage({
    ...baseInput,
    attackPower: 4303,
    anomalyProficiency: 577.4,
    normalDamageBonusPercent: 202.8,
    anomalyDamageBonusPercent: 33.46,
    monster: {
      ...baseInput.monster,
      monsterDefenseAtLevel70: 857.52,
      defenseShredPercent: 0,
      defenseIgnorePercent: 0,
      penetrationFlat: 36,
      resistanceShredPercent: 0,
      resistanceIgnorePercent: 0,
      // 非失衡卫士Ⅱ型没有怪物自带易伤；扳机的55%全部来自统一规则。
      vulnerabilityPercent: 0,
      defenseEffects: result.buffs.defenseEffects,
      resistanceEffects: result.buffs.resistanceEffects,
      vulnerabilityEffects: result.buffs.vulnerabilityEffects,
    },
  });
  if (!("monsterZones" in damage.trace)) throw new Error("强击应返回怪物乘区追踪");
  assert.equal(damage.trace.monsterZones.defense.defenseShredPercent, 48.75);
  assert.equal(damage.trace.monsterZones.defense.defenseIgnorePercent, 0);
  assert.equal(damage.trace.monsterZones.vulnerability.currentVulnerabilityPercent, 0);
  assert.equal(damage.trace.monsterZones.vulnerability.uncappedPercent, 155);
  assert.equal(damage.trace.monsterZones.vulnerability.zone, 1.55);
  assert.ok(Math.abs(damage.trace.finalValue - 1618645.045407072) < 1e-6);

  const disorder = calculateWebDamage({
    ...baseInput,
    attackPower: 4303,
    anomalyProficiency: 577.4,
    normalDamageBonusPercent: 202.8,
    anomalyDamageBonusPercent: 33.46,
    damageKind: "disorder",
    fixedDisorderMultiplierPercent: result.buffs.fixedDisorderMultiplierPercent,
    disorderDamageBonusFromSourcePercent: result.buffs.disorderDamageBonusFromSourcePercent,
    disorderDamageBonusFromTriggererPercent: result.buffs.disorderDamageBonusFromTriggererPercent,
    monster: {
      ...baseInput.monster,
      monsterDefenseAtLevel70: 857.52,
      defenseShredPercent: 0,
      defenseIgnorePercent: 0,
      penetrationFlat: 36,
      resistanceShredPercent: 0,
      resistanceIgnorePercent: 0,
      vulnerabilityPercent: 0,
      defenseEffects: result.buffs.defenseEffects,
      resistanceEffects: result.buffs.resistanceEffects,
      vulnerabilityEffects: result.buffs.vulnerabilityEffects,
      damageKind: "disorder",
      element: "physical",
    },
  });
  if (!("finalValue" in disorder.trace)) throw new Error("紊乱应返回伤害追踪");
  assert.ok(Math.abs(disorder.trace.finalValue - 1600483.5301710877) < 1e-6);
});

test("叶瞬光三人队的增伤来源按规则作用域和满层数值汇总", () => {
  const result = resolveWebTeamState({
    attackerId: "1431",
    team: [
      {
        id: "1431",
        name: "叶瞬光",
        role: "异常",
        element: "物理",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        initialAtk: 3482,
        weaponId: "14143",
        weaponRefinement: 1,
        driveDiscSetCounts: { "33500": 4, "31400": 2 },
        panel: {
          hp: 10564,
          atk: 3482,
          def: 877,
          impact: 83,
          critRate: 50.6,
          critDmg: 174.8,
          anomalyMastery: 94,
          anomalyProficiency: 102,
          penRate: 0,
          penFlat: 63,
          energyRegen: 1.2,
          physicalDmgBonus: 40,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
      {
        id: "1491",
        name: "千夏",
        role: "支援",
        element: "物理",
        level: 60,
        cinema: 1,
        coreLevel: 7,
        initialAtk: 3516,
        weaponId: "14149",
        weaponRefinement: 1,
        driveDiscSetCounts: { "33400": 4, "31600": 2 },
        panel: {
          hp: 11440,
          atk: 3516,
          def: 899,
          impact: 98,
          critRate: 29,
          critDmg: 93.2,
          anomalyMastery: 96,
          anomalyProficiency: 122,
          penRate: 0,
          penFlat: 36,
          energyRegen: 2.6,
          physicalDmgBonus: 0,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
      {
        id: "1311",
        name: "耀嘉音",
        role: "支援",
        element: "以太",
        level: 60,
        cinema: 2,
        coreLevel: 7,
        initialAtk: 3033,
        skillLevels: { special: 12 },
        weaponId: "14131",
        weaponRefinement: 1,
        driveDiscSetCounts: { "32800": 4, "31600": 2 },
        panel: {
          hp: 12291,
          atk: 3033,
          def: 856,
          impact: 83,
          critRate: 55.4,
          critDmg: 102.8,
          anomalyMastery: 93,
          anomalyProficiency: 137,
          penRate: 0,
          penFlat: 18,
          energyRegen: 2.8,
          physicalDmgBonus: 0,
          fireDmgBonus: 0,
          iceDmgBonus: 0,
          electricDmgBonus: 0,
          etherDmgBonus: 0,
        },
      },
    ],
    enemyStates: { "sweet-frightened": true, stunned: true },
    assumeFullBuffs: true,
  });

  assert.equal(result.activePanel.atk, 6828);
  assert.equal(result.activePanel.critRate, 100.6);
  assert.equal(result.activePanel.critDmg, 224.8);
  assert.equal(result.activePanel.physicalDmgBonus, 40);
  assert.equal(result.buffs.normalDamageBonusPercent, 167);
  assert.deepEqual(result.buffs.stunVulnerabilityCaptures, [{
    id: "nanoka:character_1431_passive_veil_vulnerability",
    label: "叶瞬光｜核心被动：以太帷幕·决裁",
    maxBonusPercent: 110,
  }]);
  const critRateSources = result.buffs.combatPanelModifiers
    .filter((modifier) => modifier.stat === "critRate")
    .reduce<Record<string, number>>((sources, modifier) => {
      sources[modifier.label] = (sources[modifier.label] ?? 0) + modifier.value;
      return sources;
    }, {});
  assert.deepEqual(critRateSources, {
    "叶瞬光｜核心被动：照破无明·合道": 30,
    "沧浪行歌｜4件套": 20,
  });
  assert.deepEqual(
    result.buffs.normalDamageBonusSources
      .filter((source) => [
        "nanoka:weapon_14143_talent_1",
        "nanoka:weapon_14131_talent_1",
        "nanoka:weapon_14149_talent_1",
        "nanoka:set_33400_4pc_team_damage",
        "nanoka:equipment_32800_desc4",
        "nanoka:character_1311_skill_special_1",
      ].includes(source.id))
      .map((source) => [source.id, source.value]),
    [
      ["nanoka:character_1311_skill_special_1", 20],
      ["nanoka:set_33400_4pc_team_damage", 18],
      ["nanoka:equipment_32800_desc4", 24],
      ["nanoka:weapon_14131_talent_1", 20],
      ["nanoka:weapon_14143_talent_1", 25],
      ["nanoka:weapon_14149_talent_1", 25],
    ],
  );
  const weaponResistanceIgnore = result.buffs.resistanceEffects.find((effect) =>
    effect.kind === "ignore" && effect.sourceId === "nanoka:weapon_14143_talent_1"
  );
  assert.deepEqual(weaponResistanceIgnore, {
    kind: "ignore",
    percent: 20,
    sourceId: "nanoka:weapon_14143_talent_1",
    label: "云霓孤光｜玉魄冰心",
    scope: { elements: ["physical"] },
  });
  const resistance = calculateResistanceZone({
    attackerLevel: 60,
    monsterLevel: 70,
    monsterDefenseAtLevel70: 858,
    baseResistancePercent: 0,
    resistanceEffects: result.buffs.resistanceEffects,
    damageScope: { damageKind: "direct", skillCategory: "ultimate", element: "physical" },
    vulnerability: { currentVulnerabilityPercent: 0 },
  });
  assert.equal(resistance.resistanceShredPercent, 18);
  assert.equal(resistance.resistanceIgnorePercent, 20);
  assert.equal(resistance.effectiveResistancePercent, -38);
  assert.equal(resistance.zone, 1.38);
});

test("叶瞬光帷幕易伤快照只在叶瞬光是伤害来源时生效", () => {
  const panel = {
    hp: 10000,
    atk: 3000,
    def: 800,
    impact: 83,
    critRate: 50,
    critDmg: 100,
    anomalyMastery: 90,
    anomalyProficiency: 100,
    penRate: 0,
    penFlat: 0,
    energyRegen: 1.2,
    physicalDmgBonus: 0,
    fireDmgBonus: 0,
    iceDmgBonus: 0,
    electricDmgBonus: 0,
    etherDmgBonus: 0,
  };
  const team = [
    {
      id: "1431",
      name: "叶瞬光",
      role: "强攻",
      element: "物理",
      level: 60,
      cinema: 2,
      coreLevel: 7,
      driveDiscSetCounts: {},
      panel,
    },
    {
      id: "1311",
      name: "耀嘉音",
      role: "支援",
      element: "以太",
      level: 60,
      cinema: 0,
      coreLevel: 7,
      driveDiscSetCounts: {},
      panel,
    },
  ];

  const shunguang = resolveWebTeamState({
    attackerId: "1431",
    team,
    assumeFullBuffs: true,
  });
  const astra = resolveWebTeamState({
    attackerId: "1311",
    team,
    assumeFullBuffs: true,
  });

  assert.equal(shunguang.buffs.stunVulnerabilityCaptures[0]?.maxBonusPercent, 110);
  assert.deepEqual(astra.buffs.stunVulnerabilityCaptures, []);
});

test("网页桥接会结算 panel 阶段的招式增伤但不会重复应用局外面板属性", () => {
  const result = resolveWebTeamState({
    attackerId: "1431",
    team: [{
      id: "1431",
      name: "叶瞬光",
      role: "强攻",
      element: "物理",
      level: 60,
      cinema: 0,
      coreLevel: 0,
      driveDiscSetCounts: { "33300": 2 },
      panel: {
        hp: 10000,
        atk: 3000,
        def: 800,
        impact: 83,
        critRate: 50,
        critDmg: 100,
        anomalyMastery: 90,
        anomalyProficiency: 100,
        penRate: 0,
        penFlat: 0,
        energyRegen: 1.2,
        physicalDmgBonus: 30,
        fireDmgBonus: 0,
        iceDmgBonus: 0,
        electricDmgBonus: 0,
        etherDmgBonus: 0,
      },
    }],
    assumeFullBuffs: true,
  });

  assert.equal(result.activePanel.physicalDmgBonus, 30);
  assert.deepEqual(
    result.buffs.scopedDamageBonusEffects
      .filter((effect) => effect.id === "nanoka:equipment_33300_desc2")
      .map((effect) => [effect.percent, effect.scope?.skillCategories]),
    [[15, ["basic"]]],
  );
});
