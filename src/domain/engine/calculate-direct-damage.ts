import {
  calculateMonsterMultipliers,
  matchesDamageScope,
  type DamageScopeContext,
  type MonsterMultiplierInput,
  type MonsterMultiplierResult,
} from "./calculate-monster-multipliers.js";
import {
  resolveDamageEventContext,
  type DamageEventContext,
  type ResolvedDamageEventContext,
} from "./resolve-damage-event-effects.js";
import type {
  ResolvedDamageInstance,
  TeamDamageBuffResult,
} from "./resolve-team-damage-buffs.js";

export interface DirectDamageInput {
  /** 攻击力/防御力/贯穿力与招式倍率相乘后的基础值。 */
  baseValue: number;
  damageKind: "direct" | "penetration";
  damageBonusPercent: number;
  critRatePercent: number;
  critDamagePercent: number;
  /** 必定暴击事件；未设置时按暴击率给出期望值。 */
  guaranteedCrit?: boolean;
  monster: MonsterMultiplierInput;
}

export interface DirectDamageTrace {
  baseValue: number;
  damageKind: "direct" | "penetration";
  damageBonusZone: number;
  critRate: number;
  critDamageZone: number;
  monsterZones: MonsterMultiplierResult;
  defenseZone: number;
  resistanceZone: number;
  vulnerabilityZone: number;
  monsterMultiplier: number;
  nonCritValue: number;
  critValue: number;
  expectedValue: number;
}

export interface ResolvedDamageInstanceInput {
  instance: ResolvedDamageInstance;
  /** 触发附加伤害的主攻击；用于检查“强化特殊技命中时”等条件。 */
  triggerContext?: DamageScopeContext;
  /** 没写元素的实例从当前攻击继承元素。 */
  fallbackElement: DamageEventContext["element"];
  baseDamageBonusPercent: number;
  baseCritRatePercent: number;
  baseCritDamagePercent: number;
  guaranteedCrit?: boolean;
  buffs: Pick<TeamDamageBuffResult,
    | "normalDamageBonusPercent"
    | "scopedDamageBonusEffects"
    | "critDamageBonusEffects"
    | "damageConversions"
    | "defenseEffects"
    | "resistanceEffects"
    | "vulnerabilityEffects">;
  monster: MonsterMultiplierInput;
}

export interface ResolvedDamageInstanceTrace extends DirectDamageTrace {
  instanceId: string;
  label: string;
  eventContext: ResolvedDamageEventContext;
  scopedDamageBonusPercent: number;
  critDamageBonusPercent: number;
}

export interface UnsupportedDamageInstanceTrace {
  supported: false;
  instanceId: string;
  reason: string;
}

function assertFinite(name: string, value: number): void {
  if (!Number.isFinite(value)) throw new Error(`${name} 必须是有限数字：${value}`);
}

export function calculateDirectDamage(input: DirectDamageInput): DirectDamageTrace {
  assertFinite("baseValue", input.baseValue);
  assertFinite("damageBonusPercent", input.damageBonusPercent);
  assertFinite("critRatePercent", input.critRatePercent);
  assertFinite("critDamagePercent", input.critDamagePercent);
  const damageBonusZone = 1 + input.damageBonusPercent / 100;
  const critRate = input.guaranteedCrit
    ? 1
    : Math.max(0, Math.min(1, input.critRatePercent / 100));
  const critDamageZone = 1 + input.critDamagePercent / 100;
  const monsterZones = calculateMonsterMultipliers(input.monster);
  // 贯穿伤害无视防御，但仍保留抗性区与易伤区。
  const defenseZone = input.damageKind === "penetration" ? 1 : monsterZones.defense.zone;
  const resistanceZone = monsterZones.resistance.zone;
  const vulnerabilityZone = monsterZones.vulnerability.zone;
  const monsterMultiplier = defenseZone * resistanceZone * vulnerabilityZone;
  const nonCritValue = input.baseValue * damageBonusZone * monsterMultiplier;
  const critValue = nonCritValue * critDamageZone;
  const expectedValue = nonCritValue * (1 - critRate) + critValue * critRate;
  return {
    baseValue: input.baseValue,
    damageKind: input.damageKind,
    damageBonusZone,
    critRate,
    critDamageZone,
    monsterZones,
    defenseZone,
    resistanceZone,
    vulnerabilityZone,
    monsterMultiplier,
    nonCritValue,
    critValue,
    expectedValue,
  };
}

/**
 * 结算一条已经由 BuffRule 求值出的直伤/贯穿附加事件。
 * 这里不推断触发次数；四枚子弹、三道激光等必须由事件数据明确提供。
 */
export function calculateResolvedDamageInstance(
  input: ResolvedDamageInstanceInput,
): ResolvedDamageInstanceTrace | UnsupportedDamageInstanceTrace {
  if (input.instance.damageKind !== "direct" && input.instance.damageKind !== "penetration") {
    return {
      supported: false,
      instanceId: input.instance.id,
      reason: `${input.instance.damageKind} 不是直伤/贯穿实例，必须交给对应类别公式。`,
    };
  }
  if (input.instance.scope !== undefined &&
      !matchesDamageScope(input.instance.scope, input.triggerContext)) {
    return {
      supported: false,
      instanceId: input.instance.id,
      reason: "当前主攻击不满足附加伤害的触发作用域。",
    };
  }
  const eventContext = resolveDamageEventContext({
    damageKind: input.instance.damageKind,
    element: input.instance.element ?? input.fallbackElement,
    ...(input.instance.sourceMemberId === undefined
      ? {}
      : { sourceMemberId: input.instance.sourceMemberId }),
  }, input.buffs.damageConversions);
  if (eventContext.damageKind !== "direct" && eventContext.damageKind !== "penetration") {
    return {
      supported: false,
      instanceId: input.instance.id,
      reason: `标签转换后的 ${eventContext.damageKind} 不属于直伤/贯穿公式。`,
    };
  }
  const scopedDamageBonusPercent = input.buffs.scopedDamageBonusEffects
    .filter((effect) => matchesDamageScope(effect.scope, eventContext))
    .reduce((sum, effect) => sum + effect.percent, 0);
  const critDamageBonusPercent = input.buffs.critDamageBonusEffects
    .filter((effect) => matchesDamageScope(effect.scope, eventContext))
    .reduce((sum, effect) => sum + effect.percent, 0);
  const trace = calculateDirectDamage({
    baseValue: input.instance.baseValue,
    damageKind: eventContext.damageKind,
    damageBonusPercent: input.baseDamageBonusPercent +
      input.buffs.normalDamageBonusPercent + scopedDamageBonusPercent,
    critRatePercent: input.baseCritRatePercent,
    critDamagePercent: input.baseCritDamagePercent + critDamageBonusPercent,
    ...(input.guaranteedCrit === undefined ? {} : { guaranteedCrit: input.guaranteedCrit }),
    monster: {
      ...input.monster,
      damageScope: eventContext,
      defenseEffects: [
        ...(input.monster.defenseEffects ?? []),
        ...input.buffs.defenseEffects,
      ],
      resistanceEffects: [
        ...(input.monster.resistanceEffects ?? []),
        ...input.buffs.resistanceEffects,
      ],
      vulnerabilityEffects: [
        ...(input.monster.vulnerabilityEffects ?? []),
        ...input.buffs.vulnerabilityEffects,
      ],
    },
  });
  return {
    ...trace,
    instanceId: input.instance.id,
    label: input.instance.label,
    eventContext,
    scopedDamageBonusPercent,
    critDamageBonusPercent,
  };
}
