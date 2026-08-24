/**
 * 异常伤害公共公式。
 *
 * 这里使用“百分点”和“倍率”两种明确单位：
 * - `*Percent` 字段使用百分点，例如 20 表示 20%；
 * - `*Multiplier` 字段使用乘区倍率，例如 1.2 表示 ×1.2。
 *
 * 本模块只负责纯数学，不负责判断状态是否触发、技能是否命中或敌人当前状态。
 */

import {
  calculateMonsterMultipliers,
  type MonsterMultiplierInput,
  type MonsterMultiplierResult,
} from "./calculate-monster-multipliers.js";

export type AnomalyDamageKind =
  | "anomaly"
  | "assault"
  | "disorder"
  | "yifang"
  | "yaobian"
  | "turbulence";

/**
 * 异放的两种游戏内语义，不能只根据 damageKind="yifang" 猜测。
 * - multiply-original-anomaly：额外结算一次原属性异常伤害，倍率继续乘原异常倍率；
 * - replace-anomaly：直接结算自身给出的属性异常倍率，不再乘原异常倍率。
 */
export type YifangDamageMode = "multiply-original-anomaly" | "replace-anomaly";

export interface AnomalyEffectStrengthInput {
  characterLevel: number;
  anomalyProficiency: number;
  normalDamageBonusPercent: number;
  attackPower: number;
  /** 异化系数等直接作用于异常效果强度的独立乘区。 */
  anomalyEffectStrengthMultiplierPercent?: number;
}

export interface AnomalyEffectStrengthResult {
  attackLevelCoefficient: number;
  anomalyProficiencyZone: number;
  normalDamageZone: number;
  anomalyEffectStrengthMultiplierZone: number;
  value: number;
}

export interface AnomalyDamageInput {
  kind: AnomalyDamageKind;
  anomalyEffectStrength: number;
  /** kind=yifang 时必须明确选择两种异放语义之一。 */
  yifangMode?: YifangDamageMode;
  anomalySkillMultiplierPercent: number;
  /** 异常增伤区，例如 20 表示 ×1.2。 */
  anomalyDamageBonusPercent: number;
  /** 异常暴击区直接传最终倍率，例如 1、1.5 或简的独立暴击倍率。 */
  anomalyCritMultiplier: number;
  /** 异放/耀变/乱流/紊乱等额外异常类别的技能倍率。 */
  extraDamageMultiplierPercent?: number;
  /** 额外异常类别自己的增伤区，例如异放增伤。 */
  extraDamageBonusPercent?: number;
  monster: MonsterMultiplierInput;
}

export interface AnomalyDamageTrace {
  anomalyEffectStrength: number;
  yifangMode?: YifangDamageMode;
  anomalySkillMultiplier: number;
  extraDamageMultiplier: number;
  baseValue: number;
  anomalyDamageZone: number;
  anomalyCritZone: number;
  extraDamageZone: number;
  independentMultiplier: number;
  defenseZone: number;
  resistanceZone: number;
  vulnerabilityZone: number;
  monsterMultiplier: number;
  monsterZones: MonsterMultiplierResult;
  finalValue: number;
}

function assertFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) throw new Error(`${name} 必须是有限数字：${value}`);
}

function percentZone(percent: number): number {
  assertFinite("百分比", percent);
  return 1 + percent / 100;
}

export function calculateAnomalyEffectStrength(
  input: AnomalyEffectStrengthInput,
): AnomalyEffectStrengthResult {
  assertFinite("characterLevel", input.characterLevel);
  assertFinite("anomalyProficiency", input.anomalyProficiency);
  assertFinite("normalDamageBonusPercent", input.normalDamageBonusPercent);
  assertFinite("attackPower", input.attackPower);
  const anomalyEffectStrengthMultiplierPercent = input.anomalyEffectStrengthMultiplierPercent ?? 0;
  assertFinite("anomalyEffectStrengthMultiplierPercent", anomalyEffectStrengthMultiplierPercent);
  if (input.characterLevel < 1) {
    throw new Error(`characterLevel 必须不小于1：${input.characterLevel}`);
  }

  const attackLevelCoefficient = 1 + (input.characterLevel - 1) / 59;
  const anomalyProficiencyZone = input.anomalyProficiency / 100;
  const normalDamageZone = percentZone(input.normalDamageBonusPercent);
  const anomalyEffectStrengthMultiplierZone = percentZone(anomalyEffectStrengthMultiplierPercent);
  const value = attackLevelCoefficient *
    anomalyProficiencyZone *
    normalDamageZone *
    anomalyEffectStrengthMultiplierZone *
    input.attackPower;

  return {
    attackLevelCoefficient,
    anomalyProficiencyZone,
    normalDamageZone,
    anomalyEffectStrengthMultiplierZone,
    value,
  };
}

export function calculateAnomalyDamage(input: AnomalyDamageInput): AnomalyDamageTrace {
  if (input.kind === "disorder" || input.kind === "turbulence") {
    throw new Error(`${input.kind} 必须使用对应的专用计算函数，不能套用通用异常公式。`);
  }
  assertFinite("anomalyEffectStrength", input.anomalyEffectStrength);
  assertFinite("anomalySkillMultiplierPercent", input.anomalySkillMultiplierPercent);
  assertFinite("anomalyDamageBonusPercent", input.anomalyDamageBonusPercent);
  assertFinite("anomalyCritMultiplier", input.anomalyCritMultiplier);
  if (input.extraDamageMultiplierPercent !== undefined) {
    assertFinite("extraDamageMultiplierPercent", input.extraDamageMultiplierPercent);
  }
  if (input.extraDamageBonusPercent !== undefined) {
    assertFinite("extraDamageBonusPercent", input.extraDamageBonusPercent);
  }
  if (input.kind === "yifang" && input.yifangMode === undefined) {
    throw new Error("异放必须明确 yifangMode：multiply-original-anomaly 或 replace-anomaly。");
  }
  if (input.kind !== "yifang" && input.yifangMode !== undefined) {
    throw new Error("yifangMode 只能用于 damageKind=yifang。");
  }

  const anomalySkillMultiplier = input.anomalySkillMultiplierPercent / 100;
  const configuredExtraDamageMultiplier = (input.extraDamageMultiplierPercent ?? 100) / 100;
  const extraDamageMultiplier = input.kind === "yifang" && input.yifangMode === "replace-anomaly"
    ? 1
    : configuredExtraDamageMultiplier;
  const baseValue = input.anomalyEffectStrength *
    anomalySkillMultiplier *
    extraDamageMultiplier;
  const anomalyDamageZone = percentZone(input.anomalyDamageBonusPercent);
  const anomalyCritZone = input.anomalyCritMultiplier;
  const extraDamageZone = percentZone(input.extraDamageBonusPercent ?? 0);
  const independentMultiplier = anomalyDamageZone *
    anomalyCritZone *
    (input.kind === "anomaly" || input.kind === "assault"
      ? 1
      : extraDamageZone);
  const monsterZones = calculateMonsterMultipliers(input.monster);
  const monsterMultiplier = monsterZones.multiplier;
  const finalValue = baseValue * independentMultiplier * monsterMultiplier;

  return {
    anomalyEffectStrength: input.anomalyEffectStrength,
    ...(input.yifangMode === undefined ? {} : { yifangMode: input.yifangMode }),
    anomalySkillMultiplier,
    extraDamageMultiplier,
    baseValue,
    anomalyDamageZone,
    anomalyCritZone,
    extraDamageZone,
    independentMultiplier,
    defenseZone: monsterZones.defense.zone,
    resistanceZone: monsterZones.resistance.zone,
    vulnerabilityZone: monsterZones.vulnerability.zone,
    monsterMultiplier,
    monsterZones,
    finalValue,
  };
}
