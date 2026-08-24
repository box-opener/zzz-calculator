/**
 * 紊乱/极性紊乱公共公式。
 *
 * 紊乱的异常效果强度来自异常状态的来源者，不来自触发紊乱的角色。
 * 百分比字段使用百分点；返回的 multiplier 字段使用倍率百分比换算后的实际倍率。
 */

import {
  calculateMonsterMultipliers,
  type MonsterMultiplierInput,
  type MonsterMultiplierResult,
} from "./calculate-monster-multipliers.js";

export type DisorderSource =
  | "physical"
  | "frost"
  | "burn"
  | "electric"
  | "corrosion"
  | "frost-ice"
  | "wind";

export type DisorderVariant = "normal" | "polar";

export interface DisorderDamageInput {
  /** 异常状态来源者的异常效果强度。 */
  sourceAnomalyEffectStrength: number;
  source: DisorderSource;
  variant: DisorderVariant;
  /** 不传时按游戏异常状态的最大持续时间计算。 */
  remainingSeconds?: number;
  /** 柳、柚叶 6 画等直接附加到紊乱基础倍率区的百分点。 */
  fixedDisorderMultiplierPercent?: number;
  /** “被结算的紊乱伤害提升”：作用于异常效果强度来源者。 */
  disorderDamageBonusFromSourcePercent?: number;
  /** “造成的紊乱伤害提升”：作用于本次紊乱触发者。 */
  disorderDamageBonusFromTriggererPercent?: number;
  monster: MonsterMultiplierInput;
  /** 极性紊乱造成原紊乱伤害的比例，例如 50 表示原紊乱最终值的 50%。 */
  polarDisorderPercent?: number;
  /** 柳极性紊乱的额外异常精通倍率，例如 3200 表示 32 倍。 */
  polarAnomalyMasterySkillMultiplierPercent?: number;
  currentAnomalyMastery?: number;
  triggererAttackPower?: number;
}

export interface DisorderDamageTrace {
  supported: true;
  source: DisorderSource;
  variant: DisorderVariant;
  remainingSeconds: number;
  timeCompensationPercent: number;
  fixedDisorderMultiplierPercent: number;
  baseMultiplierPercent: number;
  baseValue: number;
  sourceDisorderBonusZone: number;
  triggererDisorderBonusZone: number;
  disorderIndependentMultiplier: number;
  monsterMultiplier: number;
  monsterZones: MonsterMultiplierResult;
  finalDisorderValue: number;
  polarOriginalValue: number;
  polarAdditionalBaseValue: number;
  polarAdditionalFinalValue: number;
  finalValue: number;
}

export interface UnsupportedDisorderTrace {
  supported: false;
  reason: string;
  source: DisorderSource;
  variant: DisorderVariant;
}

export const DEFAULT_DISORDER_DURATION_SECONDS: Readonly<Record<DisorderSource, number>> = {
  physical: 10,
  frost: 10,
  burn: 10,
  electric: 10,
  corrosion: 10,
  "frost-ice": 20,
  wind: 10,
};

function assertFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) throw new Error(`${name} 必须是有限数字：${value}`);
}

function zone(percent: number): number {
  assertFinite("百分比", percent);
  return 1 + percent / 100;
}

function timeCompensationPercent(source: DisorderSource, remainingSeconds: number): number {
  switch (source) {
    case "physical":
    case "frost":
      return remainingSeconds * 7.5;
    case "burn":
      return (remainingSeconds / 0.5) * 50;
    case "electric":
      return remainingSeconds * 125;
    case "corrosion":
      return (remainingSeconds / 0.5) * 62.5;
    case "frost-ice":
      return remainingSeconds * 75;
    case "wind":
      return 0;
  }
}

export function calculateDisorderDamage(
  input: DisorderDamageInput,
): DisorderDamageTrace | UnsupportedDisorderTrace {
  if (input.source === "wind" && input.variant === "normal") {
    return {
      supported: false,
      reason: "风化不会结算普通紊乱，只能参与极性紊乱。",
      source: input.source,
      variant: input.variant,
    };
  }

  assertFinite("sourceAnomalyEffectStrength", input.sourceAnomalyEffectStrength);
  const remainingSeconds = input.remainingSeconds ?? DEFAULT_DISORDER_DURATION_SECONDS[input.source];
  const fixedDisorderMultiplierPercent = input.fixedDisorderMultiplierPercent ?? 0;
  const sourceBonusPercent = input.disorderDamageBonusFromSourcePercent ?? 0;
  const triggererBonusPercent = input.disorderDamageBonusFromTriggererPercent ?? 0;
  assertFinite("remainingSeconds", remainingSeconds);
  if (remainingSeconds < 0) {
    throw new Error(`remainingSeconds 不能小于0：${remainingSeconds}`);
  }
  assertFinite("fixedDisorderMultiplierPercent", fixedDisorderMultiplierPercent);
  assertFinite("disorderDamageBonusFromSourcePercent", sourceBonusPercent);
  assertFinite("disorderDamageBonusFromTriggererPercent", triggererBonusPercent);

  const timePercent = input.variant === "polar" && input.source === "wind"
    ? 0
    : timeCompensationPercent(input.source, remainingSeconds);
  const baseMultiplierPercent = 450 + timePercent + fixedDisorderMultiplierPercent;
  const baseValue = input.sourceAnomalyEffectStrength * baseMultiplierPercent / 100;
  const sourceDisorderBonusZone = zone(sourceBonusPercent);
  const triggererDisorderBonusZone = zone(triggererBonusPercent);
  // 两个归属不同，但都进入同一个“紊乱增伤区”，因此同区百分比相加后只转换一次倍率。
  const disorderIndependentMultiplier = zone(sourceBonusPercent + triggererBonusPercent);
  const monsterZones = calculateMonsterMultipliers(input.monster);
  const monsterMultiplier = monsterZones.multiplier;
  const finalDisorderValue = baseValue * disorderIndependentMultiplier * monsterMultiplier;

  const polarOriginalValue = input.variant === "polar"
    ? finalDisorderValue * requirePolarPercent(input.polarDisorderPercent) / 100
    : 0;

  let polarAdditionalBaseValue = 0;
  if (input.polarAnomalyMasterySkillMultiplierPercent !== undefined) {
    const mastery = input.currentAnomalyMastery;
    const attackPower = input.triggererAttackPower;
    if (mastery === undefined || attackPower === undefined || attackPower === 0) {
      throw new Error("极性紊乱异常精通附加伤害需要 currentAnomalyMastery 和非零 triggererAttackPower。");
    }
    assertFinite("polarAnomalyMasterySkillMultiplierPercent", input.polarAnomalyMasterySkillMultiplierPercent);
    assertFinite("currentAnomalyMastery", mastery);
    assertFinite("triggererAttackPower", attackPower);
    polarAdditionalBaseValue = input.sourceAnomalyEffectStrength *
      (input.polarAnomalyMasterySkillMultiplierPercent / 100) *
      (mastery / attackPower);
  }
  const polarAdditionalFinalValue = polarAdditionalBaseValue *
    disorderIndependentMultiplier *
    monsterMultiplier;

  return {
    supported: true,
    source: input.source,
    variant: input.variant,
    remainingSeconds,
    timeCompensationPercent: timePercent,
    fixedDisorderMultiplierPercent,
    baseMultiplierPercent,
    baseValue,
    sourceDisorderBonusZone,
    triggererDisorderBonusZone,
    disorderIndependentMultiplier,
    monsterMultiplier,
    monsterZones,
    finalDisorderValue,
    polarOriginalValue,
    polarAdditionalBaseValue,
    polarAdditionalFinalValue,
    finalValue: input.variant === "polar"
      ? polarOriginalValue + polarAdditionalFinalValue
      : finalDisorderValue,
  };
}

function requirePolarPercent(value: number | undefined): number {
  if (value === undefined) {
    throw new Error("极性紊乱需要明确提供 polarDisorderPercent，不能默认按100%计算。");
  }
  assertFinite("polarDisorderPercent", value);
  return value;
}
