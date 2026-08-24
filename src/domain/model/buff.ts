import type { SkillCategory, StatKey } from "./character-build.js";

export type BuffSupportStatus = "raw-only" | "partial" | "verified";

export type BuffSourceType =
  | "character"
  | "weapon"
  | "drive-disc-set"
  | "enemy"
  | "scenario";

export type BuffSourceProvider =
  | "nanoka"
  | "miyoushe"
  | "legacy"
  | "manual"
  | "reference";

export interface BuffSource {
  type: BuffSourceType;
  id: string;
  label: string;
  provider: BuffSourceProvider;
  version?: string;
  url?: string;
  key?: string;
}

export type BuffTarget =
  | "self"
  | "active-character"
  | "team"
  | "all-allies"
  | "other-allies"
  | "enemy"
  | "all-enemies";

export type BuffPhase = "panel" | "combat";

export type BuffTiming =
  | "permanent"
  | "on-entry"
  | "on-trigger"
  | "while-state"
  | "after-trigger";

export type BuffTrigger =
  | "attack-hit"
  | "damage-taken"
  | "skill-used"
  | "character-switched-out"
  | "state-entered"
  | "state-active"
  | "manual";

export type BuffRefreshPolicy = "refresh-duration" | "replace" | "none";

export type ConditionTarget = "self" | "active-character" | "team" | "enemy";

export type ConditionValue = string | number | boolean;

export type ConditionOperator =
  | "equals"
  | "not-equals"
  | "greater-than"
  | "greater-than-or-equal"
  | "less-than"
  | "less-than-or-equal";

export type BuffCondition =
  | { type: "always" }
  | { type: "all"; conditions: readonly BuffCondition[] }
  | { type: "any"; conditions: readonly BuffCondition[] }
  | { type: "not"; condition: BuffCondition }
  | {
      type: "compare";
      path: string;
      operator: ConditionOperator;
      value: ConditionValue;
    }
  | {
      type: "state";
      target: ConditionTarget;
      state: string;
      equals?: boolean;
    }
  | {
      type: "team-match";
      relation: "element" | "role" | "camp";
      equals?: boolean;
    }
  | {
      type: "team-role";
      role: string;
      equals?: boolean;
    }
  | {
      type: "team-role-count";
      role: string;
      operator: ConditionOperator;
      value: number;
    };

export interface BuffStackRule {
  mode: "manual" | "derived";
  min: number;
  max: number;
  initial: number;
  rampSeconds?: number;
}

export type BuffExpression =
  | { type: "constant"; value: number }
  | {
      type: "source-stat";
      path: string;
      scale: number;
      offset?: number;
      cap?: number | BuffExpression;
      flat?: number;
    }
  | {
      type: "lookup";
      path: string;
      values: readonly number[];
    }
  | { type: "per-stack"; base: number; perStack: number };

export type BuffValue = number | BuffExpression;

export type Element = "physical" | "fire" | "ice" | "electric" | "ether" | "wind";

export type DamageKind =
  | "direct"
  | "anomaly"
  | "yifang"
  | "yaobian"
  | "turbulence"
  | "assault"
  | "disorder"
  | "daze"
  | "penetration";

export interface BuffScope {
  skillCategories?: readonly SkillCategory[];
  skillIds?: readonly string[];
  elements?: readonly Element[];
  damageKinds?: readonly DamageKind[];
}

export interface StatBuffEffect {
  kind: "stat";
  stat: StatKey;
  operation: "add-flat" | "add-percent";
  value: BuffValue;
}

export interface DamageBonusEffect {
  kind: "damage-bonus";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
  /** 紊乱增伤的归属：来源者或触发者。未填写时由作用对象和伤害上下文决定。 */
  disorderAttribution?: "source" | "triggerer";
}

export interface CritDamageBonusEffect {
  kind: "crit-damage-bonus";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface DazeBonusEffect {
  kind: "daze-bonus";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface DefIgnoreEffect {
  kind: "def-ignore";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface DefenseShredEffect {
  kind: "def-shred";
  operation: "add-percent";
  value: BuffValue;
  /** 通常为空：挂在敌人身上的防御削减 Debuff 对所有伤害生效。 */
  scope?: BuffScope;
}

export interface ResistanceShredEffect {
  kind: "resistance-shred";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface ResistanceIgnoreEffect {
  kind: "resistance-ignore";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface AnomalyBuildupResistanceShredEffect {
  kind: "anomaly-buildup-resistance-shred";
  operation: "add-percent";
  value: BuffValue;
  /** 根据装备者元素选择对应属性的异常积蓄抗性。 */
  matchingSourceElement?: boolean;
  scope?: BuffScope;
}

export interface DamageTakenReductionEffect {
  kind: "damage-taken-reduction";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

export interface StatusValueReductionEffect {
  kind: "status-value-reduction";
  operation: "add-percent";
  status: string;
  value: BuffValue;
}

/** 直接作用于异常效果强度的独立乘区，例如异化系数。 */
export interface AnomalyEffectStrengthMultiplierEffect {
  kind: "anomaly-effect-strength-multiplier";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

/** 极性紊乱对原紊乱最终值的比例；事件层同时读取最大触发次数。 */
export interface PolarDisorderEffect {
  kind: "polar-disorder";
  operation: "add-percent";
  value: BuffValue;
  maxTriggers?: number;
  scope?: BuffScope;
}

/** 挂在敌人身上的易伤 Debuff，进入怪物易伤乘区。 */
export interface VulnerabilityEffect {
  kind: "vulnerability";
  operation: "add-percent";
  value: BuffValue;
  scope?: BuffScope;
}

/**
 * 将目标当时的失衡易伤倍率快照为仅供来源角色使用的易伤区。
 *
 * 叶瞬光的「以太帷幕·决裁」属于这种效果：它不会给敌人挂一个全队共享
 * Debuff，而是让叶瞬光自己的伤害改用帷幕易伤，并对快照值设置上限。
 * value 表示易伤加成上限（百分点），例如 110 表示易伤区最多 ×2.10。
 */
export interface StunVulnerabilityCaptureEffect {
  kind: "stun-vulnerability-capture";
  operation: "replace";
  value: BuffValue;
  scope?: BuffScope;
}

export interface MultiplierEffect {
  kind: "multiplier";
  operation: "add-percent" | "multiply";
  value: BuffValue;
  scope?: BuffScope;
}

export interface ShieldEffect {
  kind: "shield";
  operation: "add-flat";
  value: BuffValue;
}

export interface DamageInstanceEffect {
  kind: "damage-instance";
  operation: "add";
  damageKind: DamageKind;
  value: BuffValue;
  element?: Element;
  scope?: BuffScope;
}

/**
 * 从一次已有伤害派生的额外伤害，例如“按本次异常伤害的 200% 结算异放”。
 * 这类效果保留来源伤害类别，避免把相对倍率误当成攻击力或穿透力倍率。
 */
export type DerivedDamageMode = "multiply-original-anomaly" | "replace-anomaly";

export interface DerivedDamageEffect {
  kind: "derived-damage";
  operation: "add";
  damageKind: DamageKind;
  sourceDamageKind: DamageKind;
  multiplier: BuffValue;
  /**
   * 异放必须区分“原属性异常倍率再乘一次”和“直接替换为自身倍率”。
   * 其他派生伤害暂不填写，由对应伤害类别的公式解释。
   */
  mode?: DerivedDamageMode;
  element?: Element;
  inheritElement?: boolean;
  scope?: BuffScope;
}

export interface DamageConversionEffect {
  kind: "damage-conversion";
  from: Element;
  to: DamageKind;
  scope?: BuffScope;
}

export interface CritProfileEffect {
  kind: "crit-profile";
  operation: "add";
  /** 独立暴击区名称，例如「异放」或「强击异常暴击」。 */
  zone: string;
  critRate: BuffValue;
  critDamage: BuffValue;
  scope?: BuffScope;
}

export interface RuleModifierEffect {
  kind: "rule-modifier";
  targetRuleId: string;
  modifiers: readonly {
    field: "scale" | "cap";
    operation: "add";
    value: number;
  }[];
}

export type BuffEffect =
  | StatBuffEffect
  | DamageBonusEffect
  | CritDamageBonusEffect
  | DazeBonusEffect
  | DefIgnoreEffect
  | DefenseShredEffect
  | ResistanceShredEffect
  | ResistanceIgnoreEffect
  | AnomalyBuildupResistanceShredEffect
  | DamageTakenReductionEffect
  | StatusValueReductionEffect
  | AnomalyEffectStrengthMultiplierEffect
  | PolarDisorderEffect
  | VulnerabilityEffect
  | StunVulnerabilityCaptureEffect
  | MultiplierEffect
  | ShieldEffect
  | DamageInstanceEffect
  | DerivedDamageEffect
  | DamageConversionEffect
  | CritProfileEffect
  | RuleModifierEffect;

export interface BuffRule {
  schemaVersion: 1;
  id: string;
  source: BuffSource;
  status: BuffSupportStatus;
  target: BuffTarget;
  phase: BuffPhase;
  timing: BuffTiming;
  condition: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  trigger?: BuffTrigger;
  stacks?: BuffStackRule;
  durationSeconds?: number;
  refreshPolicy?: BuffRefreshPolicy;
  cinemaAtLeast?: number;
  /** Nanoka 核心被动的具体等级；同一核心的不同等级是替换关系，不是叠加关系。 */
  coreLevel?: number;
  exclusiveGroup?: string;
  /** 驱动盘套装来源至少需要装备的件数。 */
  equippedCountAtLeast?: number;
  /** Nanoka 音擎详情的精炼档位；同一语义的五档规则只激活当前档位。 */
  weaponRefinement?: number;
  notes?: string;
}
