import type {
  BuffPhase,
  BuffRule,
  BuffScope,
  DamageBonusEffect,
  DamageKind,
  DerivedDamageMode,
  Element,
} from "../model/buff.js";
import type { PanelModifier } from "../model/panel.js";
import type {
  DefenseEffectModifier,
  ResistanceEffectModifier,
  VulnerabilityEffectModifier,
} from "./calculate-monster-multipliers.js";
import {
  evaluateCombatBuffRules,
  isUnscopedDamageBonus,
  panelModifierFromApplication,
  targetAffectsAttacker,
  type CombatBuffApplication,
  type CombatMemberProfile,
} from "./evaluate-combat-buff-rules.js";
import { REVIEWED_BUFF_RULES } from "../../../data/rules/reviewed-buff-registry.js";

export type TeamMemberDamageProfile = CombatMemberProfile;

export interface TeamDamageBuffInput {
  attackerId: string;
  team: readonly TeamMemberDamageProfile[];
  enemyStates?: Readonly<Record<string, boolean>>;
  /** 满拐场景：持续时间、层数和已触发的命中条件均按最大值处理。 */
  assumeFullBuffs: boolean;
  /** 默认只处理 combat；用于单独提取 panel 阶段的伤害增益时显式传入。 */
  phases?: readonly BuffPhase[];
  /** 可注入版本化规则；未传入时使用当前已确认规则注册表。 */
  rules?: readonly BuffRule[];
}

export interface TeamBuffActivation {
  id: string;
  label: string;
  value?: number;
  note: string;
}

export type DamageBonusZone =
  | "normal"
  | "anomaly"
  | "disorder-source"
  | "disorder-triggerer"
  | "yifang"
  | "turbulence";

export interface DamageBonusSource {
  id: string;
  label: string;
  value: number;
  zone: DamageBonusZone;
}

export interface ScopedDamageBonusEffect {
  id: string;
  label: string;
  percent: number;
  scope?: DamageBonusEffect["scope"];
}

export interface StunVulnerabilityCapture {
  id: string;
  label: string;
  /** 帷幕易伤加成上限（百分点），110 表示最终易伤区最多 ×2.10。 */
  maxBonusPercent: number;
}

interface ResolvedRuleEffectBase {
  id: string;
  label: string;
  sourceMemberId?: string;
  scope?: BuffScope;
}

/** 已求值但尚未绑定到某一次主攻击的附加伤害事件。 */
export interface ResolvedDamageInstance extends ResolvedRuleEffectBase {
  damageKind: DamageKind;
  baseValue: number;
  element?: Element;
}

/** 已求值的派生伤害定义；由具体来源伤害事件决定是否结算。 */
export interface ResolvedDerivedDamage extends ResolvedRuleEffectBase {
  damageKind: DamageKind;
  sourceDamageKind: DamageKind;
  multiplier: number;
  mode?: DerivedDamageMode;
  element?: Element;
  inheritElement: boolean;
}

/** 独立暴击区，不与角色普通暴击面板混合。 */
export interface ResolvedCritProfile extends ResolvedRuleEffectBase {
  zone: string;
  critRatePercent: number;
  critDamagePercent: number;
}

export interface ResolvedCritDamageBonus extends ResolvedRuleEffectBase {
  percent: number;
}

export interface ResolvedDamageConversion extends ResolvedRuleEffectBase {
  from: Element;
  to: DamageKind;
}

export interface TeamDamageBuffResult {
  /** 局内 Buff 产生的面板修正；不会回写或污染 UID/截图得到的局外面板。 */
  combatPanelModifiers: PanelModifier[];
  /** 进入异常效果强度普通增伤区的额外百分点。 */
  normalDamageBonusPercent: number;
  /** 普通增伤区的声明式来源明细，供网页审查和回归测试使用。 */
  normalDamageBonusSources: DamageBonusSource[];
  /** 其余伤害独立区的声明式来源明细。 */
  damageBonusSources: DamageBonusSource[];
  /** 带技能/伤害类别作用域的普通增伤，结算具体 DamageEvent 时再匹配。 */
  scopedDamageBonusEffects: ScopedDamageBonusEffect[];
  /** 进入属性异常独立增伤区的额外百分点。 */
  anomalyDamageBonusPercent: number;
  /** 分别记录紊乱来源者和触发者归属，避免以后两者被混成一个来源。 */
  disorderDamageBonusFromSourcePercent: number;
  disorderDamageBonusFromTriggererPercent: number;
  fixedDisorderMultiplierPercent: number;
  additionalTurbulenceMultiplierPercent: number;
  turbulenceDamageBonusPercent: number;
  yifangDamageBonusPercent: number;
  anomalyEffectStrengthMultiplierPercent: number;
  polarDisorderPercent: number;
  polarDisorderMaxTriggers: number;
  defenseEffects: DefenseEffectModifier[];
  resistanceEffects: ResistanceEffectModifier[];
  vulnerabilityEffects: VulnerabilityEffectModifier[];
  /** 仅对当前攻击者生效的失衡易伤快照规则。 */
  stunVulnerabilityCaptures: StunVulnerabilityCapture[];
  /** 由规则产生、但不应直接并入当前主攻击跳字的独立伤害事件。 */
  damageInstances: ResolvedDamageInstance[];
  /** 从属性异常等来源事件派生的异放/耀变等伤害。 */
  derivedDamageEffects: ResolvedDerivedDamage[];
  /** 强击异常暴击、异放暴击等独立暴击区。 */
  critProfiles: ResolvedCritProfile[];
  /** 对普通或独立暴击区追加的暴击伤害。 */
  critDamageBonusEffects: ResolvedCritDamageBonus[];
  /** 属性伤害标签转换，例如冰伤转贯穿伤害。 */
  damageConversions: ResolvedDamageConversion[];
  activatedBuffs: TeamBuffActivation[];
  warnings: string[];
}

function addActivation(
  result: TeamDamageBuffResult,
  application: CombatBuffApplication,
): void {
  result.activatedBuffs.push({
    id: application.ruleId,
    label: application.sourceLabel,
    ...(application.value === undefined ? {} : { value: application.value }),
    note: "规则已满足来源、队伍、装备、影画和当前状态条件；满拐场景按最大触发状态处理。",
  });
}

function addDamageBonus(
  result: TeamDamageBuffResult,
  application: CombatBuffApplication,
  effect: DamageBonusEffect,
): void {
  if (application.value === undefined) return;

  if (isUnscopedDamageBonus(effect)) {
    result.normalDamageBonusPercent += application.value;
    result.normalDamageBonusSources.push({
      id: application.ruleId,
      label: application.sourceLabel,
      value: application.value,
      zone: "normal",
    });
    return;
  }


  const damageKinds = effect.scope?.damageKinds ?? [];
  const belongsToAnomalyIndependentZone = damageKinds.some((kind) =>
    kind === "assault" || kind === "anomaly" || kind === "disorder" ||
    kind === "yifang" || kind === "turbulence"
  );
  if (!belongsToAnomalyIndependentZone) {
    result.scopedDamageBonusEffects.push({
      id: application.ruleId,
      label: application.sourceLabel,
      percent: application.value,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
  }

  if (damageKinds.includes("assault") || damageKinds.includes("anomaly")) {
    result.anomalyDamageBonusPercent += application.value;
    result.damageBonusSources.push({
      id: application.ruleId,
      label: application.sourceLabel,
      value: application.value,
      zone: "anomaly",
    });
  }
  if (damageKinds.includes("disorder")) {
    if (effect.disorderAttribution === "triggerer") {
      result.disorderDamageBonusFromTriggererPercent += application.value;
      result.damageBonusSources.push({
        id: application.ruleId,
        label: application.sourceLabel,
        value: application.value,
        zone: "disorder-triggerer",
      });
    } else {
      result.disorderDamageBonusFromSourcePercent += application.value;
      result.damageBonusSources.push({
        id: application.ruleId,
        label: application.sourceLabel,
        value: application.value,
        zone: "disorder-source",
      });
    }
  }
  if (damageKinds.includes("yifang")) {
    result.yifangDamageBonusPercent += application.value;
    result.damageBonusSources.push({
      id: application.ruleId,
      label: application.sourceLabel,
      value: application.value,
      zone: "yifang",
    });
  }
  if (damageKinds.includes("turbulence")) {
    result.turbulenceDamageBonusPercent += application.value;
    result.damageBonusSources.push({
      id: application.ruleId,
      label: application.sourceLabel,
      value: application.value,
      zone: "turbulence",
    });
  }
}

function elementMatchesAttacker(
  scope: DamageBonusEffect["scope"],
  attackerElement: string,
): boolean {
  if (scope?.elements === undefined) return true;
  const aliases: Readonly<Record<string, string>> = {
    physical: "物理",
    fire: "火",
    ice: "冰",
    electric: "电",
    ether: "以太",
    wind: "风",
  };
  return scope.elements.some((element) =>
    element === attackerElement || aliases[element] === attackerElement,
  );
}

function resolveApplication(
  result: TeamDamageBuffResult,
  application: CombatBuffApplication,
  attackerId: string,
  attackerElement: string,
): void {
  addActivation(result, application);
  const effect = application.effect;

  if (effect.kind === "stat") {
    if (!targetAffectsAttacker(application.target, application.sourceMemberId, attackerId)) return;
    const modifier = panelModifierFromApplication(application);
    if (modifier) result.combatPanelModifiers.push(modifier);
    return;
  }
  if (effect.kind === "damage-bonus") {
    if (!elementMatchesAttacker(effect.scope, attackerElement)) return;
    addDamageBonus(result, application, effect);
    return;
  }
  if (effect.kind === "def-shred" && application.value !== undefined) {
    result.defenseEffects.push({
      kind: "shred",
      percent: application.value,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "def-ignore" && application.value !== undefined) {
    result.defenseEffects.push({
      kind: "ignore",
      percent: application.value,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "resistance-shred" && application.value !== undefined) {
    result.resistanceEffects.push({
      kind: "shred",
      percent: application.value,
      sourceId: application.ruleId,
      label: application.sourceLabel,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "resistance-ignore" && application.value !== undefined) {
    result.resistanceEffects.push({
      kind: "ignore",
      percent: application.value,
      sourceId: application.ruleId,
      label: application.sourceLabel,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "multiplier" && application.value !== undefined &&
      effect.operation === "add-percent" && effect.scope?.damageKinds?.includes("disorder")) {
    result.fixedDisorderMultiplierPercent += application.value;
    return;
  }
  if (effect.kind === "multiplier" && application.value !== undefined &&
      effect.operation === "add-percent" && effect.scope?.damageKinds?.includes("turbulence")) {
    result.additionalTurbulenceMultiplierPercent += application.value;
    return;
  }
  if (effect.kind === "anomaly-effect-strength-multiplier" && application.value !== undefined) {
    result.anomalyEffectStrengthMultiplierPercent += application.value;
    return;
  }
  if (effect.kind === "polar-disorder" && application.value !== undefined) {
    result.polarDisorderPercent = Math.max(result.polarDisorderPercent, application.value);
    if (effect.maxTriggers !== undefined) {
      result.polarDisorderMaxTriggers = Math.max(result.polarDisorderMaxTriggers, effect.maxTriggers);
    }
    return;
  }
  if (effect.kind === "vulnerability" && application.value !== undefined) {
    result.vulnerabilityEffects.push({
      percent: application.value,
      sourceId: application.ruleId,
      label: application.sourceLabel,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "stun-vulnerability-capture" && application.value !== undefined) {
    result.stunVulnerabilityCaptures.push({
      id: application.ruleId,
      label: application.sourceLabel,
      maxBonusPercent: application.value,
    });
    return;
  }
  if (effect.kind === "damage-instance" && application.value !== undefined) {
    result.damageInstances.push({
      id: application.ruleId,
      label: application.sourceLabel,
      ...(application.sourceMemberId === undefined
        ? {}
        : { sourceMemberId: application.sourceMemberId }),
      damageKind: effect.damageKind,
      baseValue: application.value,
      ...(effect.element === undefined ? {} : { element: effect.element }),
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "derived-damage" && application.multiplier !== undefined) {
    result.derivedDamageEffects.push({
      id: application.ruleId,
      label: application.sourceLabel,
      ...(application.sourceMemberId === undefined
        ? {}
        : { sourceMemberId: application.sourceMemberId }),
      damageKind: effect.damageKind,
      sourceDamageKind: effect.sourceDamageKind,
      multiplier: application.multiplier,
      ...(effect.mode === undefined ? {} : { mode: effect.mode }),
      ...(effect.element === undefined ? {} : { element: effect.element }),
      inheritElement: effect.inheritElement ?? false,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "crit-profile" &&
      application.critRate !== undefined && application.critDamage !== undefined) {
    result.critProfiles.push({
      id: application.ruleId,
      label: application.sourceLabel,
      ...(application.sourceMemberId === undefined
        ? {}
        : { sourceMemberId: application.sourceMemberId }),
      zone: effect.zone,
      critRatePercent: Math.max(0, Math.min(100, application.critRate)),
      critDamagePercent: application.critDamage,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "crit-damage-bonus" && application.value !== undefined) {
    result.critDamageBonusEffects.push({
      id: application.ruleId,
      label: application.sourceLabel,
      ...(application.sourceMemberId === undefined
        ? {}
        : { sourceMemberId: application.sourceMemberId }),
      percent: application.value,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
    return;
  }
  if (effect.kind === "damage-conversion") {
    result.damageConversions.push({
      id: application.ruleId,
      label: application.sourceLabel,
      ...(application.sourceMemberId === undefined
        ? {}
        : { sourceMemberId: application.sourceMemberId }),
      from: effect.from,
      to: effect.to,
      ...(effect.scope === undefined ? {} : { scope: effect.scope }),
    });
  }
}

export function resolveTeamDamageBuffs(
  input: TeamDamageBuffInput,
): TeamDamageBuffResult {
  const result: TeamDamageBuffResult = {
    combatPanelModifiers: [],
    normalDamageBonusPercent: 0,
    normalDamageBonusSources: [],
    damageBonusSources: [],
    scopedDamageBonusEffects: [],
    anomalyDamageBonusPercent: 0,
    disorderDamageBonusFromSourcePercent: 0,
    disorderDamageBonusFromTriggererPercent: 0,
    fixedDisorderMultiplierPercent: 0,
    additionalTurbulenceMultiplierPercent: 0,
    turbulenceDamageBonusPercent: 0,
    yifangDamageBonusPercent: 0,
    anomalyEffectStrengthMultiplierPercent: 0,
    polarDisorderPercent: 0,
    polarDisorderMaxTriggers: 0,
    defenseEffects: [],
    resistanceEffects: [],
    vulnerabilityEffects: [],
    stunVulnerabilityCaptures: [],
    damageInstances: [],
    derivedDamageEffects: [],
    critProfiles: [],
    critDamageBonusEffects: [],
    damageConversions: [],
    activatedBuffs: [],
    warnings: [],
  };
  const evaluations = evaluateCombatBuffRules({
    attackerId: input.attackerId,
    team: input.team,
    enemyStates: input.enemyStates ?? {},
    assumeFullBuffs: input.assumeFullBuffs,
    phases: input.phases ?? ["combat"],
    rules: input.rules ?? REVIEWED_BUFF_RULES,
  });
  result.warnings.push(...evaluations.warnings);
  const attacker = input.team.find((member) => member.id === input.attackerId);
  const attackerElement = attacker?.element ?? "";
  for (const application of evaluations.applications) {
    resolveApplication(result, application, input.attackerId, attackerElement);
  }
  return result;
}
