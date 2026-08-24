/**
 * 防御区和抗性区迁移自旧版实际结算逻辑；易伤区使用当前统一规则。
 *
 * 单位约定：所有百分比字段使用百分点，例如20表示20%。
 * 该模块只处理怪物乘区，不处理角色技能倍率或角色自身增伤区。
 */

import type { DamageKind, BuffScope, Element } from "../model/buff.js";
import type { SkillCategory } from "../model/character-build.js";

export interface MonsterVulnerabilityInput {
  /** 战斗状态层已经汇总后的当前有效易伤，例如30表示+30%。 */
  currentVulnerabilityPercent: number;
  /** 由具体易伤来源处理后的上限，例如110%易伤对应2.1。 */
  maxMultiplier?: number;
  /** 由 BuffRule 汇总的敌方易伤 Debuff。 */
  additionalEffects?: readonly VulnerabilityEffectModifier[];
  damageScope?: DamageScopeContext;
}

export interface DamageScopeContext {
  damageKind?: DamageKind;
  skillCategory?: SkillCategory;
  skillId?: string;
  element?: Element;
}

export interface ResistanceEffectModifier {
  /** shred 是全局/作用域减抗 Debuff，ignore 是作用域抗性无视。 */
  kind: "shred" | "ignore";
  percent: number;
  /** 保留规则来源，供网页把减抗与本次攻击的抗性无视分别展示。 */
  sourceId?: string;
  label?: string;
  scope?: BuffScope;
}

export interface VulnerabilityEffectModifier {
  percent: number;
  /** 保留规则来源，供桥接层去重和网页展示易伤组成。 */
  sourceId?: string;
  label?: string;
  scope?: BuffScope;
}

export interface DefenseEffectModifier {
  /** shred 是挂在敌人身上的防御削减 Debuff，ignore 是攻击作用域内的防御无视。 */
  kind: "shred" | "ignore";
  percent: number;
  scope?: BuffScope;
}

export interface MonsterMultiplierInput {
  /** 旧版用于防御常数的角色等级。 */
  attackerLevel: number;
  /** 目标等级，用于旧版防御曲线缩放。 */
  monsterLevel: number;
  /** Nanoka/旧版目标在Lv.70的基础防御。 */
  monsterDefenseAtLevel70: number;
  /** 本次伤害标签对应的目标基础抗性。 */
  baseResistancePercent: number;
  defenseShredPercent?: number;
  defenseIgnorePercent?: number;
  penetrationRatePercent?: number;
  penetrationFlat?: number;
  /** 已经由战斗 Buff 状态层激活的防御效果。 */
  defenseEffects?: readonly DefenseEffectModifier[];
  resistanceShredPercent?: number;
  resistanceIgnorePercent?: number;
  /** 当前攻击上下文；没有上下文时不会误应用带作用域的无视抗性。 */
  damageScope?: DamageScopeContext;
  /** 已经由战斗 Buff 状态层激活的抗性效果。 */
  resistanceEffects?: readonly ResistanceEffectModifier[];
  vulnerabilityEffects?: readonly VulnerabilityEffectModifier[];
  vulnerability: MonsterVulnerabilityInput;
}

export interface DefenseZoneTrace {
  attackerDefenseConstant: number;
  monsterDefenseAtLevel70: number;
  monsterDefense: number;
  defenseShredPercent: number;
  defenseIgnorePercent: number;
  penetrationRatePercent: number;
  penetrationFlat: number;
  effectiveDefense: number;
  zone: number;
}

export interface ResistanceZoneTrace {
  baseResistancePercent: number;
  resistanceShredPercent: number;
  resistanceIgnorePercent: number;
  effectiveResistancePercent: number;
  zone: number;
}

export interface VulnerabilityZoneTrace {
  currentVulnerabilityPercent: number;
  uncappedPercent: number;
  maxMultiplier?: number;
  zone: number;
}

export interface MonsterMultiplierResult {
  defense: DefenseZoneTrace;
  resistance: ResistanceZoneTrace;
  vulnerability: VulnerabilityZoneTrace;
  multiplier: number;
}

/** 旧版 app.js 的 DEFENCE_CURVE，索引0对应Lv.1。 */
export const DEFENSE_CURVE: readonly number[] = [
  100, 108, 116, 124, 132, 142, 152, 164, 176, 188, 200, 214, 228, 242, 258,
  274, 290, 306, 324, 344, 362, 382, 402, 422, 444, 466, 490, 512, 536, 562,
  586, 612, 638, 666, 694, 722, 750, 780, 810, 842, 872, 904, 938, 970, 1004,
  1038, 1074, 1110, 1146, 1184, 1220, 1258, 1298, 1338, 1378, 1418, 1460, 1502,
  1544, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588,
  1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588,
  1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588, 1588,
  1588,
];

/** 旧版 app.js 的角色等级防御常数，Lv.60及以上固定为794。 */
export const ATTACKER_DEFENSE_CONSTANTS: Readonly<Record<number, number>> = {
  1: 50, 2: 54, 3: 58, 4: 62, 5: 66, 6: 71, 7: 76, 8: 82, 9: 88, 10: 94,
  11: 100, 12: 107, 13: 114, 14: 121, 15: 129, 16: 137, 17: 145, 18: 153, 19: 162, 20: 172,
  21: 181, 22: 191, 23: 201, 24: 211, 25: 222, 26: 233, 27: 245, 28: 256, 29: 268, 30: 281,
  31: 293, 32: 306, 33: 319, 34: 333, 35: 347, 36: 361, 37: 375, 38: 390, 39: 405, 40: 421,
  41: 436, 42: 452, 43: 469, 44: 485, 45: 502, 46: 519, 47: 537, 48: 555, 49: 573, 50: 592,
  51: 610, 52: 629, 53: 649, 54: 669, 55: 689, 56: 709, 57: 730, 58: 751, 59: 772,
};

function assertFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) throw new Error(`${name} 必须是有限数字：${value}`);
}

function resolveAttackerDefenseConstant(level: number): number {
  assertFinite("attackerLevel", level);
  if (level < 1) throw new Error(`attackerLevel 必须不小于1：${level}`);
  return level >= 60 ? 794 : ATTACKER_DEFENSE_CONSTANTS[Math.floor(level)] ?? 794;
}

function resolveDefenseCurve(level: number): number {
  assertFinite("monsterLevel", level);
  if (level < 1) throw new Error(`monsterLevel 必须不小于1：${level}`);
  return DEFENSE_CURVE[Math.floor(level) - 1] ?? 1588;
}

export function calculateDefenseZone(input: MonsterMultiplierInput): DefenseZoneTrace {
  assertFinite("monsterDefenseAtLevel70", input.monsterDefenseAtLevel70);
  const attackerDefenseConstant = resolveAttackerDefenseConstant(input.attackerLevel);
  const monsterDefenseAtLevel70 = input.monsterDefenseAtLevel70;
  const curveAtLevel = resolveDefenseCurve(input.monsterLevel);
  const curveAtLevel70 = DEFENSE_CURVE[69] ?? 1588;
  const monsterDefense = monsterDefenseAtLevel70 * curveAtLevel / curveAtLevel70;
  const effectTotals = input.defenseEffects?.reduce(
    (totals, effect) => {
      assertFinite("defenseEffects.percent", effect.percent);
      if (!matchesDamageScope(effect.scope, input.damageScope)) return totals;
      if (effect.kind === "shred") totals.shred += effect.percent;
      else totals.ignore += effect.percent;
      return totals;
    },
    { shred: 0, ignore: 0 },
  ) ?? { shred: 0, ignore: 0 };
  const defenseShredPercent = (input.defenseShredPercent ?? 0) + effectTotals.shred;
  const defenseIgnorePercent = (input.defenseIgnorePercent ?? 0) + effectTotals.ignore;
  const penetrationRatePercent = input.penetrationRatePercent ?? 0;
  const penetrationFlat = input.penetrationFlat ?? 0;
  for (const [name, value] of Object.entries({
    defenseShredPercent,
    defenseIgnorePercent,
    penetrationRatePercent,
    penetrationFlat,
  })) {
    assertFinite(name, value);
  }

  // 与旧版完全一致：防御削减/无视 → 穿透率 → 固定穿透 → 下限0。
  const effectiveDefense = Math.max(
    0,
    monsterDefense * (1 - (defenseShredPercent + defenseIgnorePercent) / 100) *
      (1 - penetrationRatePercent / 100) - penetrationFlat,
  );
  const zone = attackerDefenseConstant / (effectiveDefense + attackerDefenseConstant);

  return {
    attackerDefenseConstant,
    monsterDefenseAtLevel70,
    monsterDefense,
    defenseShredPercent,
    defenseIgnorePercent,
    penetrationRatePercent,
    penetrationFlat,
    effectiveDefense,
    zone,
  };
}

export function calculateResistanceZone(input: MonsterMultiplierInput): ResistanceZoneTrace {
  const baseResistancePercent = input.baseResistancePercent;
  const effectTotals = input.resistanceEffects?.reduce(
    (totals, effect) => {
      assertFinite("resistanceEffects.percent", effect.percent);
      if (!matchesDamageScope(effect.scope, input.damageScope)) return totals;
      if (effect.kind === "shred") totals.shred += effect.percent;
      else totals.ignore += effect.percent;
      return totals;
    },
    { shred: 0, ignore: 0 },
  ) ?? { shred: 0, ignore: 0 };
  const resistanceShredPercent = (input.resistanceShredPercent ?? 0) + effectTotals.shred;
  const resistanceIgnorePercent = (input.resistanceIgnorePercent ?? 0) + effectTotals.ignore;
  for (const [name, value] of Object.entries({
    baseResistancePercent,
    resistanceShredPercent,
    resistanceIgnorePercent,
  })) {
    assertFinite(name, value);
  }

  // 旧版实际伤害函数没有把负抗性截回-100%，因此这里保留原始线性结果。
  const effectiveResistancePercent = baseResistancePercent -
    resistanceShredPercent - resistanceIgnorePercent;
  const zone = 1 - effectiveResistancePercent / 100;

  return {
    baseResistancePercent,
    resistanceShredPercent,
    resistanceIgnorePercent,
    effectiveResistancePercent,
    zone,
  };
}

/** 全部伤害效果共用的作用域匹配；任何声明过但上下文缺失的维度都不匹配。 */
export function matchesDamageScope(
  scope: BuffScope | undefined,
  context: DamageScopeContext | undefined,
): boolean {
  if (scope === undefined) return true;
  if (context === undefined) return false;
  if (scope.damageKinds !== undefined &&
      (context.damageKind === undefined || !scope.damageKinds.includes(context.damageKind))) {
    return false;
  }
  if (scope.skillCategories !== undefined &&
      (context.skillCategory === undefined || !scope.skillCategories.includes(context.skillCategory))) {
    return false;
  }
  if (scope.skillIds !== undefined &&
      (context.skillId === undefined || !scope.skillIds.includes(context.skillId))) {
    return false;
  }
  if (scope.elements !== undefined &&
      (context.element === undefined || !scope.elements.includes(context.element))) {
    return false;
  }
  return true;
}

export function calculateVulnerabilityZone(input: MonsterVulnerabilityInput): VulnerabilityZoneTrace {
  const currentVulnerabilityPercent = input.currentVulnerabilityPercent;
  assertFinite("currentVulnerabilityPercent", currentVulnerabilityPercent);
  const additionalPercent = input.additionalEffects?.reduce((sum, effect) => {
    assertFinite("vulnerabilityEffects.percent", effect.percent);
    if (!matchesDamageScope(effect.scope, input.damageScope)) return sum;
    return sum + effect.percent;
  }, 0) ?? 0;
  if (input.maxMultiplier !== undefined) {
    assertFinite("maxMultiplier", input.maxMultiplier);
    if (input.maxMultiplier < 0) throw new Error(`maxMultiplier 不能小于0：${input.maxMultiplier}`);
  }

  const uncappedPercent = 100 + currentVulnerabilityPercent + additionalPercent;
  const uncappedZone = uncappedPercent / 100;
  const zone = input.maxMultiplier === undefined
    ? uncappedZone
    : Math.min(input.maxMultiplier, uncappedZone);

  return {
    currentVulnerabilityPercent,
    uncappedPercent,
    ...(input.maxMultiplier === undefined ? {} : { maxMultiplier: input.maxMultiplier }),
    zone,
  };
}

export function calculateMonsterMultipliers(input: MonsterMultiplierInput): MonsterMultiplierResult {
  const defense = calculateDefenseZone(input);
  const resistance = calculateResistanceZone(input);
  const additionalVulnerabilityEffects = [
    ...(input.vulnerability.additionalEffects ?? []),
    ...(input.vulnerabilityEffects ?? []),
  ];
  const vulnerabilityInput: MonsterVulnerabilityInput = {
    ...input.vulnerability,
    ...(additionalVulnerabilityEffects.length > 0
      ? { additionalEffects: additionalVulnerabilityEffects }
      : {}),
    ...(input.damageScope !== undefined ? { damageScope: input.damageScope } : {}),
  };
  const vulnerability = calculateVulnerabilityZone({
    ...vulnerabilityInput,
  });

  return {
    defense,
    resistance,
    vulnerability,
    multiplier: defense.zone * resistance.zone * vulnerability.zone,
  };
}
