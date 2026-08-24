import {
  calculateAnomalyDamage,
  calculateAnomalyEffectStrength,
  type AnomalyDamageKind,
  type YifangDamageMode,
} from "../domain/engine/calculate-anomaly-damage.js";
import {
  calculateDisorderDamage,
  type DisorderSource,
  type DisorderVariant,
} from "../domain/engine/calculate-disorder-damage.js";
import {
  calculateTurbulenceDamage,
  type TurbulenceAnomalySource,
} from "../domain/engine/calculate-turbulence-damage.js";
import {
  calculatePanel,
} from "../domain/engine/calculate-panel.js";
import {
  resolveTeamDamageBuffs,
  type TeamDamageBuffResult,
  type TeamMemberDamageProfile,
} from "../domain/engine/resolve-team-damage-buffs.js";
import type {
  DefenseEffectModifier,
  MonsterMultiplierInput,
  ResistanceEffectModifier,
  VulnerabilityEffectModifier,
} from "../domain/engine/calculate-monster-multipliers.js";
import type { FinalPanelStats } from "../domain/model/panel.js";
import type { SkillCategory } from "../domain/model/character-build.js";
import {
  matchingDerivedDamageEffects,
  resolveIndependentCrit,
  type IndependentCritResolution,
} from "../domain/engine/resolve-damage-event-effects.js";
import {
  calculateDerivedAnomalyDamage,
  type DerivedAnomalyDamageTrace,
} from "../domain/engine/calculate-derived-anomaly-damage.js";
import type {
  ResolvedCritDamageBonus,
  ResolvedCritProfile,
  ResolvedDerivedDamage,
} from "../domain/engine/resolve-team-damage-buffs.js";
import { REVIEWED_BUFF_REGISTRY_VERSION, REVIEWED_BUFF_RULES } from "../../data/rules/reviewed-buff-registry.js";

export type WebDamageKind = "anomaly" | "assault" | "yifang" | "disorder" | "turbulence";

export interface WebMonsterInput {
  attackerLevel: number;
  monsterLevel: number;
  monsterDefenseAtLevel70: number;
  baseResistancePercent: number;
  defenseShredPercent: number;
  defenseIgnorePercent: number;
  penetrationRatePercent: number;
  penetrationFlat: number;
  resistanceShredPercent: number;
  resistanceIgnorePercent: number;
  vulnerabilityPercent: number;
  /** 已由队伍规则解析的、带 damage scope 的防御效果。 */
  defenseEffects?: readonly DefenseEffectModifier[];
  /** 已由队伍规则解析的、带 damage scope 的抗性效果。 */
  resistanceEffects?: readonly ResistanceEffectModifier[];
  /** 已由队伍规则解析的、带 damage scope 的易伤效果。 */
  vulnerabilityEffects?: readonly VulnerabilityEffectModifier[];
  damageKind: "anomaly" | "assault" | "yifang" | "disorder" | "turbulence";
  element: "physical" | "fire" | "ice" | "electric" | "ether" | "wind";
}

export interface WebDamageInput {
  characterLevel: number;
  attackPower: number;
  anomalyProficiency: number;
  normalDamageBonusPercent: number;
  anomalyEffectStrengthMultiplierPercent: number;
  damageKind: WebDamageKind;
  anomalySkillMultiplierPercent: number;
  anomalyDamageBonusPercent: number;
  anomalyCritMultiplier: number;
  /** 统一规则解析出的独立暴击区；有匹配项时替代手工预计算倍率。 */
  critProfiles?: readonly ResolvedCritProfile[];
  critDamageBonusEffects?: readonly ResolvedCritDamageBonus[];
  sourceMemberId?: string;
  triggererMemberId?: string;
  anomalySourceMemberId?: string;
  skillCategory?: SkillCategory;
  skillId?: string;
  /** 已激活的派生伤害规则；返回候选事件，不会把互斥事件擅自求和。 */
  derivedDamageEffects?: readonly ResolvedDerivedDamage[];
  extraDamageMultiplierPercent: number;
  extraDamageBonusPercent: number;
  yifangMode?: YifangDamageMode;
  disorderSource: DisorderSource;
  disorderVariant: DisorderVariant;
  remainingSeconds: number;
  fixedDisorderMultiplierPercent: number;
  disorderDamageBonusFromSourcePercent: number;
  disorderDamageBonusFromTriggererPercent: number;
  polarDisorderPercent: number;
  polarAnomalyMasterySkillMultiplierPercent: number;
  currentAnomalyMastery: number;
  triggererAttackPower: number;
  turbulenceSource: TurbulenceAnomalySource;
  windAnomalyPresent: boolean;
  additionalTurbulenceMultiplierPercent: number;
  turbulenceDamageBonusPercent: number;
  turbulenceCritMultiplier: number;
  monster: WebMonsterInput;
}

export interface WebCalculationResult {
  damageKind: WebDamageKind;
  effectStrength: ReturnType<typeof calculateAnomalyEffectStrength>;
  critResolution: IndependentCritResolution;
  derivedCandidates: readonly {
    effect: ResolvedDerivedDamage;
    critResolution: IndependentCritResolution;
    trace: DerivedAnomalyDamageTrace;
  }[];
  trace: ReturnType<typeof calculateAnomalyDamage> |
    ReturnType<typeof calculateDisorderDamage> |
    ReturnType<typeof calculateTurbulenceDamage>;
}

export interface WebTeamStateInput {
  attackerId: string;
  team: readonly TeamMemberDamageProfile[];
  enemyStates?: Readonly<Record<string, boolean>>;
  assumeFullBuffs: boolean;
}

export interface WebTeamStateResult {
  /** 统一规则解析后，伤害角色的局内面板。 */
  activePanel: FinalPanelStats;
  /** 统一规则解析出的伤害、面板、敌方乘区 Buff。 */
  buffs: TeamDamageBuffResult;
}

export interface WebEngineStatus {
  engine: "new";
  registryVersion: string;
  reviewedRuleCount: number;
  legacyPath: string;
}

function mergePanelDamageBuffs(
  combat: TeamDamageBuffResult,
  panel: TeamDamageBuffResult,
): TeamDamageBuffResult {
  return {
    ...combat,
    normalDamageBonusPercent: combat.normalDamageBonusPercent + panel.normalDamageBonusPercent,
    normalDamageBonusSources: [...panel.normalDamageBonusSources, ...combat.normalDamageBonusSources],
    damageBonusSources: [...panel.damageBonusSources, ...combat.damageBonusSources],
    scopedDamageBonusEffects: [...panel.scopedDamageBonusEffects, ...combat.scopedDamageBonusEffects],
    anomalyDamageBonusPercent: combat.anomalyDamageBonusPercent + panel.anomalyDamageBonusPercent,
    disorderDamageBonusFromSourcePercent:
      combat.disorderDamageBonusFromSourcePercent + panel.disorderDamageBonusFromSourcePercent,
    disorderDamageBonusFromTriggererPercent:
      combat.disorderDamageBonusFromTriggererPercent + panel.disorderDamageBonusFromTriggererPercent,
    fixedDisorderMultiplierPercent:
      combat.fixedDisorderMultiplierPercent + panel.fixedDisorderMultiplierPercent,
    additionalTurbulenceMultiplierPercent:
      combat.additionalTurbulenceMultiplierPercent + panel.additionalTurbulenceMultiplierPercent,
    turbulenceDamageBonusPercent:
      combat.turbulenceDamageBonusPercent + panel.turbulenceDamageBonusPercent,
    yifangDamageBonusPercent: combat.yifangDamageBonusPercent + panel.yifangDamageBonusPercent,
    anomalyEffectStrengthMultiplierPercent:
      combat.anomalyEffectStrengthMultiplierPercent + panel.anomalyEffectStrengthMultiplierPercent,
    damageInstances: [...panel.damageInstances, ...combat.damageInstances],
    derivedDamageEffects: [...panel.derivedDamageEffects, ...combat.derivedDamageEffects],
    critProfiles: [...panel.critProfiles, ...combat.critProfiles],
    critDamageBonusEffects: [
      ...panel.critDamageBonusEffects,
      ...combat.critDamageBonusEffects,
    ],
    damageConversions: [...panel.damageConversions, ...combat.damageConversions],
    warnings: [...panel.warnings, ...combat.warnings],
  };
}

function monsterInput(input: WebMonsterInput): MonsterMultiplierInput {
  return {
    attackerLevel: input.attackerLevel,
    monsterLevel: input.monsterLevel,
    monsterDefenseAtLevel70: input.monsterDefenseAtLevel70,
    baseResistancePercent: input.baseResistancePercent,
    defenseShredPercent: input.defenseShredPercent,
    defenseIgnorePercent: input.defenseIgnorePercent,
    penetrationRatePercent: input.penetrationRatePercent,
    penetrationFlat: input.penetrationFlat,
    resistanceShredPercent: input.resistanceShredPercent,
    resistanceIgnorePercent: input.resistanceIgnorePercent,
    ...(input.defenseEffects === undefined ? {} : { defenseEffects: input.defenseEffects }),
    ...(input.resistanceEffects === undefined ? {} : { resistanceEffects: input.resistanceEffects }),
    ...(input.vulnerabilityEffects === undefined ? {} : { vulnerabilityEffects: input.vulnerabilityEffects }),
    damageScope: {
      damageKind: input.damageKind,
      element: input.element,
    },
    vulnerability: {
      currentVulnerabilityPercent: input.vulnerabilityPercent,
    },
  };
}

export function getWebEngineStatus(): WebEngineStatus {
  return {
    engine: "new",
    registryVersion: REVIEWED_BUFF_REGISTRY_VERSION,
    reviewedRuleCount: REVIEWED_BUFF_RULES.length,
    legacyPath: "../index.html",
  };
}

export function calculateWebDamage(input: WebDamageInput): WebCalculationResult {
  const effectStrength = calculateAnomalyEffectStrength({
    characterLevel: input.characterLevel,
    anomalyProficiency: input.anomalyProficiency,
    normalDamageBonusPercent: input.normalDamageBonusPercent,
    attackPower: input.attackPower,
    anomalyEffectStrengthMultiplierPercent: input.anomalyEffectStrengthMultiplierPercent,
  });
  const monster = monsterInput(input.monster);
  // 物理异常来源的乱流继承强击独立暴击区；其他乱流不借用普通暴击。
  const critContextDamageKind = input.damageKind === "turbulence" &&
      input.turbulenceSource === "physical"
    ? "assault"
    : input.damageKind;
  const critContextElement = critContextDamageKind === "assault"
    ? "physical"
    : input.monster.element;
  const critResolution = resolveIndependentCrit({
    damageKind: critContextDamageKind,
    element: critContextElement,
    ...(input.sourceMemberId === undefined ? {} : { sourceMemberId: input.sourceMemberId }),
    ...(input.skillCategory === undefined ? {} : { skillCategory: input.skillCategory }),
    ...(input.skillId === undefined ? {} : { skillId: input.skillId }),
  }, input.critProfiles ?? [], input.critDamageBonusEffects ?? []);
  const anomalyCritMultiplier = critResolution.zones.length > 0
    ? critResolution.multiplier
    : input.anomalyCritMultiplier;
  const derivedCandidates = input.damageKind === "anomaly" || input.damageKind === "assault"
    ? matchingDerivedDamageEffects({
        damageKind: input.damageKind,
        element: input.monster.element,
        ...(input.sourceMemberId === undefined ? {} : { sourceMemberId: input.sourceMemberId }),
        ...(input.triggererMemberId === undefined
          ? {}
          : { triggererMemberId: input.triggererMemberId }),
        ...(input.anomalySourceMemberId === undefined
          ? {}
          : { anomalySourceMemberId: input.anomalySourceMemberId }),
        ...(input.skillCategory === undefined ? {} : { skillCategory: input.skillCategory }),
        ...(input.skillId === undefined ? {} : { skillId: input.skillId }),
      }, input.derivedDamageEffects ?? []).map((effect) => {
        const element = effect.inheritElement || effect.element === undefined
          ? input.monster.element
          : effect.element;
        const derivedCritResolution = resolveIndependentCrit({
          damageKind: effect.damageKind,
          element,
          ...(effect.sourceMemberId === undefined
            ? {}
            : { sourceMemberId: effect.sourceMemberId }),
          ...(input.skillCategory === undefined ? {} : { skillCategory: input.skillCategory }),
          ...(input.skillId === undefined ? {} : { skillId: input.skillId }),
        }, input.critProfiles ?? [], input.critDamageBonusEffects ?? []);
        const trace = calculateDerivedAnomalyDamage({
          effect,
          anomalyEffectStrength: effectStrength.value,
          sourceAnomalySkillMultiplierPercent: input.anomalySkillMultiplierPercent,
          anomalyDamageBonusPercent: input.anomalyDamageBonusPercent,
          anomalyCritMultiplier: derivedCritResolution.zones.length > 0
            ? derivedCritResolution.multiplier
            : 1,
          derivedDamageBonusPercent: input.extraDamageBonusPercent,
          monster: monsterInput({
            ...input.monster,
            damageKind: effect.damageKind === "yifang" ? "yifang" : input.monster.damageKind,
            element,
          }),
        });
        return { effect, critResolution: derivedCritResolution, trace };
      })
    : [];

  if (input.damageKind === "disorder") {
    return {
      damageKind: input.damageKind,
      effectStrength,
      critResolution,
      derivedCandidates,
      trace: calculateDisorderDamage({
        sourceAnomalyEffectStrength: effectStrength.value,
        source: input.disorderSource,
        variant: input.disorderVariant,
        remainingSeconds: input.remainingSeconds,
        fixedDisorderMultiplierPercent: input.fixedDisorderMultiplierPercent,
        disorderDamageBonusFromSourcePercent: input.disorderDamageBonusFromSourcePercent,
        disorderDamageBonusFromTriggererPercent: input.disorderDamageBonusFromTriggererPercent,
        monster,
        polarDisorderPercent: input.polarDisorderPercent,
        polarAnomalyMasterySkillMultiplierPercent: input.polarAnomalyMasterySkillMultiplierPercent,
        currentAnomalyMastery: input.currentAnomalyMastery,
        triggererAttackPower: input.triggererAttackPower,
      }),
    };
  }

  if (input.damageKind === "turbulence") {
    return {
      damageKind: input.damageKind,
      effectStrength,
      critResolution,
      derivedCandidates,
      trace: calculateTurbulenceDamage({
        windAnomalyPresent: input.windAnomalyPresent,
        sourceAnomaly: input.turbulenceSource,
        sourceAnomalyEffectStrength: effectStrength.value,
        remainingSeconds: input.remainingSeconds,
        additionalTurbulenceMultiplierPercent: input.additionalTurbulenceMultiplierPercent,
        turbulenceDamageBonusPercent: input.turbulenceDamageBonusPercent,
        turbulenceCritMultiplier: critResolution.zones.length > 0
          ? critResolution.multiplier
          : input.turbulenceCritMultiplier,
        monster,
      }),
    };
  }

  const anomalyKind: AnomalyDamageKind = input.damageKind;
  return {
    damageKind: input.damageKind,
    effectStrength,
    critResolution,
    derivedCandidates,
    trace: calculateAnomalyDamage({
      kind: anomalyKind,
      anomalyEffectStrength: effectStrength.value,
      ...(input.damageKind === "yifang" && input.yifangMode !== undefined
        ? { yifangMode: input.yifangMode }
        : {}),
      anomalySkillMultiplierPercent: input.anomalySkillMultiplierPercent,
      anomalyDamageBonusPercent: input.anomalyDamageBonusPercent,
      anomalyCritMultiplier,
      ...(input.damageKind === "yifang"
        ? {
            extraDamageMultiplierPercent: input.extraDamageMultiplierPercent,
            extraDamageBonusPercent: input.extraDamageBonusPercent,
          }
        : {}),
      monster,
    }),
  };
}

/**
 * 浏览器旧页面的队伍桥接入口。
 *
 * 旧页面仍负责展示和编辑配置，但不能再用旧的 CHAR_BUFFS_CONFIG 顺序
 * 推导局内面板。这里统一走已审查规则，并先收敛所有面板类 Buff，再计算
 * 依赖局内面板的角色能力（例如十方锻星 -> 爱丽丝额外能力）。
 *
 * 2 件套属于局外面板，旧页面在 pass1 已经计入，因此这里只消费 combat
 * 阶段规则，避免把 2 件套重复加到局内面板。
 */
export function resolveWebTeamState(input: WebTeamStateInput): WebTeamStateResult {
  const combatBuffs = resolveTeamDamageBuffs({
    attackerId: input.attackerId,
    team: input.team,
    enemyStates: input.enemyStates ?? {},
    assumeFullBuffs: input.assumeFullBuffs,
    rules: REVIEWED_BUFF_RULES.filter((rule) => rule.phase === "combat"),
  });
  // panel 阶段的面板 stat 已由旧页面 pass1 计入，不能再次应用；但诸如
  // “2 件套使普通攻击伤害提升”属于伤害规则，必须进入实际结算和来源追踪。
  const panelDamageBuffs = resolveTeamDamageBuffs({
    attackerId: input.attackerId,
    team: input.team,
    enemyStates: input.enemyStates ?? {},
    assumeFullBuffs: input.assumeFullBuffs,
    phases: ["panel"],
    rules: REVIEWED_BUFF_RULES.filter((rule) => rule.phase === "panel"),
  });
  const buffs = mergePanelDamageBuffs(combatBuffs, panelDamageBuffs);
  const attacker = input.team.find((member) => member.id === input.attackerId);
  if (!attacker) {
    throw new Error(`队伍中缺少伤害角色 ${input.attackerId}`);
  }

  const activePanel = calculatePanel({
    character: attacker.panel,
    weaponBaseAtk: 0,
    modifiers: buffs.combatPanelModifiers,
  }).final;
  return { activePanel, buffs };
}
