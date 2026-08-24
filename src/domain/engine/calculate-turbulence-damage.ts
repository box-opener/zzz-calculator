/**
 * 乱流公共公式。
 *
 * 乱流由风化状态触发，但异常效果强度继承被结算的非风属性异常来源者。
 * 本模块只负责纯数学；风异常施加者和非风异常来源者的角色关系由战斗状态层提供。
 */

import {
  calculateMonsterMultipliers,
  type MonsterMultiplierInput,
  type MonsterMultiplierResult,
} from "./calculate-monster-multipliers.js";

export type TurbulenceAnomalySource =
  | "physical"
  | "frost"
  | "burn"
  | "electric"
  | "corrosion"
  | "frost-ice";

export interface TurbulenceDamageInput {
  /** 只有场上存在风化时，乱流才允许触发。 */
  windAnomalyPresent: boolean;
  /** 被结算的非风属性异常类型；风化只是触发乱流的“打火机”。 */
  sourceAnomaly: TurbulenceAnomalySource;
  /** 非风异常来源者的异常效果强度，不是风异常施加者的面板值。 */
  sourceAnomalyEffectStrength: number;
  /** 不传时按异常状态最大持续时间计算；持续时间延长可传入超过基础上限的值。 */
  remainingSeconds?: number;
  /** 维琳娜额外能力等直接加到乱流倍率区的附加倍率。 */
  additionalTurbulenceMultiplierPercent?: number;
  /** 乱流增伤区，例如维琳娜专武、额外能力提供的乱流增伤。 */
  turbulenceDamageBonusPercent?: number;
  /** 只有简提供乱流暴击；传入最终暴击倍率，例如1或2。 */
  turbulenceCritMultiplier?: number;
  monster: MonsterMultiplierInput;
}

export interface TurbulenceDamageTrace {
  supported: true;
  sourceAnomaly: TurbulenceAnomalySource;
  remainingSeconds: number;
  baseMultiplierPercent: number;
  durationMultiplierPercent: number;
  baseAndDurationMultiplierPercent: number;
  additionalTurbulenceMultiplierPercent: number;
  totalMultiplierPercent: number;
  baseValue: number;
  turbulenceDamageBonusZone: number;
  turbulenceCritZone: number;
  turbulenceIndependentMultiplier: number;
  monsterMultiplier: number;
  monsterZones: MonsterMultiplierResult;
  finalValue: number;
}

export interface UnsupportedTurbulenceTrace {
  supported: false;
  reason: string;
  sourceAnomaly: TurbulenceAnomalySource;
}

export const DEFAULT_TURBULENCE_DURATION_SECONDS: Readonly<Record<TurbulenceAnomalySource, number>> = {
  physical: 10,
  frost: 10,
  burn: 10,
  electric: 10,
  corrosion: 10,
  "frost-ice": 20,
};

const TURBULENCE_BASE_MULTIPLIER_PERCENT: Readonly<Record<TurbulenceAnomalySource, number>> = {
  physical: 800,
  frost: 1300,
  burn: 900,
  electric: 650,
  corrosion: 650,
  "frost-ice": 0,
};

function assertFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) throw new Error(`${name} 必须是有限数字：${value}`);
}

function percentZone(percent: number): number {
  assertFinite("百分比", percent);
  return 1 + percent / 100;
}

function durationMultiplierPercent(
  source: TurbulenceAnomalySource,
  remainingSeconds: number,
): number {
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
  }
}

export function calculateTurbulenceDamage(
  input: TurbulenceDamageInput,
): TurbulenceDamageTrace | UnsupportedTurbulenceTrace {
  if (!input.windAnomalyPresent) {
    return {
      supported: false,
      reason: "场上不存在风化，乱流不会触发。",
      sourceAnomaly: input.sourceAnomaly,
    };
  }

  assertFinite("sourceAnomalyEffectStrength", input.sourceAnomalyEffectStrength);
  const remainingSeconds = input.remainingSeconds ?? DEFAULT_TURBULENCE_DURATION_SECONDS[input.sourceAnomaly];
  const additionalMultiplierPercent = input.additionalTurbulenceMultiplierPercent ?? 0;
  const turbulenceDamageBonusPercent = input.turbulenceDamageBonusPercent ?? 0;
  const turbulenceCritMultiplier = input.turbulenceCritMultiplier ?? 1;
  assertFinite("remainingSeconds", remainingSeconds);
  if (remainingSeconds < 0) {
    throw new Error(`remainingSeconds 不能小于0：${remainingSeconds}`);
  }
  assertFinite("additionalTurbulenceMultiplierPercent", additionalMultiplierPercent);
  assertFinite("turbulenceDamageBonusPercent", turbulenceDamageBonusPercent);
  assertFinite("turbulenceCritMultiplier", turbulenceCritMultiplier);

  const baseMultiplierPercent = TURBULENCE_BASE_MULTIPLIER_PERCENT[input.sourceAnomaly];
  const durationPercent = durationMultiplierPercent(input.sourceAnomaly, remainingSeconds);
  const baseAndDurationMultiplierPercent = baseMultiplierPercent + durationPercent;
  const totalMultiplierPercent = baseAndDurationMultiplierPercent + additionalMultiplierPercent;
  const baseValue = input.sourceAnomalyEffectStrength * totalMultiplierPercent / 100;
  const turbulenceDamageBonusZone = percentZone(turbulenceDamageBonusPercent);
  const turbulenceCritZone = turbulenceCritMultiplier;
  const turbulenceIndependentMultiplier = turbulenceDamageBonusZone * turbulenceCritZone;
  const monsterZones = calculateMonsterMultipliers(input.monster);
  const monsterMultiplier = monsterZones.multiplier;
  const finalValue = baseValue * turbulenceIndependentMultiplier * monsterMultiplier;

  return {
    supported: true,
    sourceAnomaly: input.sourceAnomaly,
    remainingSeconds,
    baseMultiplierPercent,
    durationMultiplierPercent: durationPercent,
    baseAndDurationMultiplierPercent,
    additionalTurbulenceMultiplierPercent: additionalMultiplierPercent,
    totalMultiplierPercent,
    baseValue,
    turbulenceDamageBonusZone,
    turbulenceCritZone,
    turbulenceIndependentMultiplier,
    monsterMultiplier,
    monsterZones,
    finalValue,
  };
}
