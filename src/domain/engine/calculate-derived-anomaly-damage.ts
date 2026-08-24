import {
  calculateAnomalyDamage,
  type AnomalyDamageTrace,
} from "./calculate-anomaly-damage.js";
import type { MonsterMultiplierInput } from "./calculate-monster-multipliers.js";
import type { ResolvedDerivedDamage } from "./resolve-team-damage-buffs.js";

export interface DerivedAnomalyDamageInput {
  effect: ResolvedDerivedDamage;
  anomalyEffectStrength: number;
  /** 被结算的原属性异常倍率，例如强击713%。 */
  sourceAnomalySkillMultiplierPercent: number;
  anomalyDamageBonusPercent: number;
  anomalyCritMultiplier: number;
  /** 派生类别自己的独立增伤区，例如异放增伤。 */
  derivedDamageBonusPercent: number;
  monster: MonsterMultiplierInput;
}

export interface DerivedAnomalyDamageTrace {
  effectId: string;
  label: string;
  mode: "multiply-original-anomaly" | "replace-anomaly";
  configuredMultiplier: number;
  anomalySkillMultiplierPercent: number;
  extraDamageMultiplierPercent: number;
  damage: AnomalyDamageTrace;
}

/**
 * 按已确认的两种异放语义，把声明式派生规则转换为异常公式输入。
 * multiplier 的单位是“倍数”：2 表示200%，6.8表示680%。
 */
export function calculateDerivedAnomalyDamage(
  input: DerivedAnomalyDamageInput,
): DerivedAnomalyDamageTrace {
  if (input.effect.damageKind !== "yifang") {
    throw new Error(`当前派生异常计算只支持 yifang：${input.effect.damageKind}`);
  }
  const mode = input.effect.mode;
  if (mode === undefined) {
    throw new Error(`异放规则 ${input.effect.id} 缺少 mode，不能猜测倍率语义。`);
  }
  const anomalySkillMultiplierPercent = mode === "replace-anomaly"
    ? input.effect.multiplier * 100
    : input.sourceAnomalySkillMultiplierPercent;
  const extraDamageMultiplierPercent = mode === "replace-anomaly"
    ? 100
    : input.effect.multiplier * 100;
  const damage = calculateAnomalyDamage({
    kind: "yifang",
    yifangMode: mode,
    anomalyEffectStrength: input.anomalyEffectStrength,
    anomalySkillMultiplierPercent,
    anomalyDamageBonusPercent: input.anomalyDamageBonusPercent,
    anomalyCritMultiplier: input.anomalyCritMultiplier,
    extraDamageMultiplierPercent,
    extraDamageBonusPercent: input.derivedDamageBonusPercent,
    monster: input.monster,
  });
  return {
    effectId: input.effect.id,
    label: input.effect.label,
    mode,
    configuredMultiplier: input.effect.multiplier,
    anomalySkillMultiplierPercent,
    extraDamageMultiplierPercent,
    damage,
  };
}
