import type { DamageKind, Element } from "../model/buff.js";
import type { DamageScopeContext } from "./calculate-monster-multipliers.js";
import { matchesDamageScope } from "./calculate-monster-multipliers.js";
import type {
  ResolvedCritDamageBonus,
  ResolvedCritProfile,
  ResolvedDamageConversion,
  ResolvedDerivedDamage,
  TeamDamageBuffResult,
} from "./resolve-team-damage-buffs.js";

export interface DamageEventContext extends DamageScopeContext {
  damageKind: DamageKind;
  element: Element;
  /** 伤害归属者；用于以后区分前台攻击与后台协同伤害。 */
  sourceMemberId?: string;
  /** 触发本次结算的角色；紊乱、异放可与异常来源者不同。 */
  triggererMemberId?: string;
  /** 场上异常效果强度的来源者；派生异常伤害从这里继承强度。 */
  anomalySourceMemberId?: string;
}

export interface ResolvedDamageEventContext extends DamageEventContext {
  originalDamageKind: DamageKind;
  appliedConversions: readonly ResolvedDamageConversion[];
}

export interface CritZoneTrace {
  zone: string;
  critRatePercent: number;
  critDamagePercent: number;
  critDamageBonusPercent: number;
  expectedMultiplier: number;
  sources: readonly string[];
}

export interface IndependentCritResolution {
  multiplier: number;
  zones: readonly CritZoneTrace[];
}

function sourceMatches(
  effect: { sourceMemberId?: string },
  context: DamageEventContext,
): boolean {
  return effect.sourceMemberId === undefined || context.sourceMemberId === undefined ||
    effect.sourceMemberId === context.sourceMemberId;
}

/**
 * 先做伤害标签转换，再由后续所有增伤、无视抗性和怪物乘区读取同一上下文。
 * 转换规则本身只描述数据，不在这里识别任何角色。
 */
export function resolveDamageEventContext(
  context: DamageEventContext,
  conversions: readonly ResolvedDamageConversion[],
): ResolvedDamageEventContext {
  let damageKind = context.damageKind;
  const applied: ResolvedDamageConversion[] = [];
  for (const conversion of conversions) {
    if (!sourceMatches(conversion, context)) continue;
    if (conversion.from !== context.element) continue;
    if (!matchesDamageScope(conversion.scope, { ...context, damageKind })) continue;
    damageKind = conversion.to;
    applied.push(conversion);
  }
  return {
    ...context,
    originalDamageKind: context.damageKind,
    damageKind,
    appliedConversions: applied,
  };
}

function matchingCritDamageBonus(
  bonuses: readonly ResolvedCritDamageBonus[],
  context: DamageEventContext,
): { percent: number; sources: string[] } {
  const matched = bonuses.filter((effect) =>
    sourceMatches(effect, context) && matchesDamageScope(effect.scope, context));
  return {
    percent: matched.reduce((sum, effect) => sum + effect.percent, 0),
    sources: matched.map((effect) => effect.label),
  };
}

/**
 * 求独立暴击区的期望倍率：1 + 暴击率 × 暴击伤害。
 * 同名 zone 是同一个暴击区的不同等级/重复声明，取可用的最高档而不叠加；
 * 不同 zone 才作为彼此独立的乘区相乘。
 */
export function resolveIndependentCrit(
  context: DamageEventContext,
  profiles: readonly ResolvedCritProfile[],
  bonuses: readonly ResolvedCritDamageBonus[] = [],
): IndependentCritResolution {
  const byZone = new Map<string, ResolvedCritProfile[]>();
  for (const profile of profiles) {
    if (!sourceMatches(profile, context)) continue;
    if (!matchesDamageScope(profile.scope, context)) continue;
    const group = byZone.get(profile.zone) ?? [];
    group.push(profile);
    byZone.set(profile.zone, group);
  }
  const bonus = matchingCritDamageBonus(bonuses, context);
  const zones = [...byZone.entries()].map(([zone, group]): CritZoneTrace => {
    const critRatePercent = Math.max(...group.map((profile) => profile.critRatePercent));
    const critDamagePercent = Math.max(...group.map((profile) => profile.critDamagePercent));
    const critDamageBonusPercent = bonus.percent;
    const expectedMultiplier = 1 +
      Math.max(0, Math.min(100, critRatePercent)) / 100 *
      (critDamagePercent + critDamageBonusPercent) / 100;
    return {
      zone,
      critRatePercent,
      critDamagePercent,
      critDamageBonusPercent,
      expectedMultiplier,
      sources: [...new Set([...group.map((profile) => profile.label), ...bonus.sources])],
    };
  });
  return {
    multiplier: zones.reduce((product, zone) => product * zone.expectedMultiplier, 1),
    zones,
  };
}

/** 返回能由当前来源伤害事件触发的派生伤害定义。 */
export function matchingDerivedDamageEffects(
  context: DamageEventContext,
  effects: readonly ResolvedDerivedDamage[],
): ResolvedDerivedDamage[] {
  return effects.filter((effect) => {
    const triggererMemberId = context.triggererMemberId ?? context.sourceMemberId;
    const triggererContext: DamageEventContext = {
      ...context,
      ...(triggererMemberId === undefined ? {} : { sourceMemberId: triggererMemberId }),
    };
    if (!sourceMatches(effect, triggererContext)) return false;
    if (effect.sourceDamageKind !== context.damageKind &&
        !(effect.sourceDamageKind === "anomaly" && context.damageKind === "assault")) {
      return false;
    }
    if (effect.element !== undefined && effect.element !== context.element) return false;
    return matchesDamageScope(effect.scope, context);
  });
}

export function resolveTeamDamageEventContext(
  context: DamageEventContext,
  buffs: Pick<TeamDamageBuffResult, "damageConversions">,
): ResolvedDamageEventContext {
  return resolveDamageEventContext(context, buffs.damageConversions);
}
