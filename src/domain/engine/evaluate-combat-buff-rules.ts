import type { FinalPanelStats, PanelModifier } from "../model/panel.js";
import type { SkillCategory } from "../model/character-build.js";
import type {
  BuffEffect,
  BuffPhase,
  BuffValue,
  BuffRule,
  BuffScope,
  BuffTarget,
  DamageBonusEffect,
} from "../model/buff.js";
import { evaluateBuffValue, evaluateCondition, type BuffEvaluationContext } from "./evaluate-buff-rules.js";
import { validateBuffRule } from "./validate-buff-rule.js";

export interface CombatMemberProfile {
  id: string;
  name: string;
  role: string;
  element: string;
  camp?: string;
  level: number;
  cinema: number;
  coreLevel: number;
  weaponId?: string;
  weaponRefinement?: number;
  hpPercent?: number;
  /** 局外初始值；动态 Buff 不应读取已经叠加局内 Buff 的面板。 */
  initialAtk?: number;
  initialImpact?: number;
  /** 可选的完整局外初始面板；未提供的字段回退到导入面板。 */
  initialPanel?: Partial<FinalPanelStats>;
  skillLevels?: Partial<Record<SkillCategory, number>>;
  driveDiscSetCounts: Readonly<Record<string, number>>;
  panel: FinalPanelStats;
}

export interface CombatBuffEvaluationInput {
  attackerId: string;
  team: readonly CombatMemberProfile[];
  enemyStates: Readonly<Record<string, boolean>>;
  assumeFullBuffs: boolean;
  /** 默认只解析局内规则；网页桥接可单独解析 panel 阶段的伤害类规则。 */
  phases?: readonly BuffPhase[];
  rules: readonly BuffRule[];
}

export interface CombatBuffApplication {
  ruleId: string;
  sourceMemberId?: string;
  sourceLabel: string;
  target: BuffTarget;
  effect: BuffEffect;
  /** 兼容普通数值效果的已求值结果。 */
  value?: number;
  /** 派生伤害相对倍率的已求值结果。 */
  multiplier?: number;
  /** 独立暴击区的已求值暴击率（百分点）。 */
  critRate?: number;
  /** 独立暴击区的已求值暴击伤害（百分点）。 */
  critDamage?: number;
  stacks: number;
}

export interface CombatBuffEvaluationResult {
  /** 已通过来源、等级、影画、装备、时机和条件门槛的规则。 */
  activeRuleIds: string[];
  applications: CombatBuffApplication[];
  warnings: string[];
}

interface WorkingMember extends CombatMemberProfile {
  panel: FinalPanelStats;
}

interface ActiveCombatRule {
  rule: BuffRule;
  sourceMemberId?: string;
  stacks: number;
}

function panelMember(member: CombatMemberProfile): Record<string, unknown> {
  const initialPanel = member.initialPanel ?? {};
  return {
    ...member,
    initialHp: initialPanel.hp ?? member.panel.hp,
    initialAtk: member.initialAtk ?? initialPanel.atk ?? member.panel.atk,
    initialDef: initialPanel.def ?? member.panel.def,
    initialImpact: member.initialImpact ?? initialPanel.impact ?? member.panel.impact,
    initialCritRate: initialPanel.critRate ?? member.panel.critRate,
    initialCritDmg: initialPanel.critDmg ?? member.panel.critDmg,
    initialAnomalyMastery: initialPanel.anomalyMastery ?? member.panel.anomalyMastery,
    initialAnomalyProficiency:
      initialPanel.anomalyProficiency ?? member.panel.anomalyProficiency,
    initialPenRate: initialPanel.penRate ?? member.panel.penRate,
    initialPenFlat: initialPanel.penFlat ?? member.panel.penFlat,
    initialEnergyRegen: initialPanel.energyRegen ?? member.panel.energyRegen,
    // 当前网页是满技能静态结算；正式导入的 CharacterBuild 若带有技能等级，
    // 会覆盖这个默认值。这样 Nanoka 的 CAL 公式不会因为旧页面配置尚未
    // 保存辅助角色技能等级而静默丢失。
    skillLevels: { special: 12, ...member.skillLevels },
    ...member.panel,
    panel: member.panel,
  };
}

function buildContext(
  source: WorkingMember,
  team: readonly WorkingMember[],
  attacker: WorkingMember,
  enemyStates: Readonly<Record<string, boolean>>,
): BuffEvaluationContext {
  const sourceView = panelMember(source);
  const teamViews = team.map(panelMember);
  return {
    values: {
      self: sourceView,
      team: {
        self: sourceView,
        members: teamViews,
      },
      "active-character": panelMember(attacker),
      enemy: { states: enemyStates },
    },
  };
}

function sourceMemberForRule(
  rule: BuffRule,
  team: readonly WorkingMember[],
): WorkingMember | undefined {
  switch (rule.source.type) {
    case "character":
      return team.find((member) => member.id === rule.source.id);
    case "weapon":
      return team.find((member) => member.weaponId === rule.source.id);
    case "drive-disc-set": {
      const required = rule.equippedCountAtLeast ?? 1;
      return team.find((member) =>
        (member.driveDiscSetCounts[rule.source.id] ?? 0) >= required,
      );
    }
    case "enemy":
    case "scenario":
      return undefined;
  }
}

export function targetAffectsAttacker(
  target: BuffTarget,
  sourceMemberId: string | undefined,
  attackerId: string,
): boolean {
  switch (target) {
    case "self":
      return sourceMemberId === attackerId;
    case "active-character":
    case "team":
    case "all-allies":
      return true;
    case "other-allies":
      return sourceMemberId !== undefined && sourceMemberId !== attackerId;
    case "enemy":
    case "all-enemies":
      return false;
  }
}

function clampStacks(rule: BuffRule, configured: number): number {
  return Math.max(
    rule.stacks?.min ?? 0,
    Math.min(rule.stacks?.max ?? configured, configured),
  );
}

type RuleModifierEffect = Extract<BuffEffect, { kind: "rule-modifier" }>;

function ruleModifierMatchesRule(
  modifier: RuleModifierEffect,
  targetRule: BuffRule,
): boolean {
  if (modifier.targetRuleId === targetRule.id) return true;

  // Nanoka 的影画文本通常只说“核心被动中的……额外提升”，没有给出
  // 另一条规则的机器 ID。解析器用 character_<id>_core 表示这个语义，
  // 这里按来源角色的 passive 条目绑定，避免为每个角色写专用代码。
  const coreTarget = modifier.targetRuleId.match(/^nanoka:character_(.+)_core$/);
  if (!coreTarget || targetRule.source.type !== "character") return false;
  return targetRule.source.id === coreTarget[1] &&
    targetRule.source.key?.includes(":passive:") === true;
}

function applyRuleModifierToValue(
  value: BuffValue,
  modifiers: readonly RuleModifierEffect["modifiers"][number][],
): BuffValue {
  if (typeof value === "number" || value.type !== "source-stat") return value;
  let scale = value.scale;
  let cap = value.cap;
  for (const modifier of modifiers) {
    if (modifier.field === "scale") scale += modifier.value;
    if (modifier.field === "cap" && typeof cap === "number") cap += modifier.value;
  }
  return {
    ...value,
    scale,
    ...(cap === undefined ? {} : { cap }),
  };
}

function applyRuleModifiers(active: readonly ActiveCombatRule[]): ActiveCombatRule[] {
  const modifierEntries = active.flatMap((entry) =>
    entry.rule.effects
      .filter((effect): effect is RuleModifierEffect => effect.kind === "rule-modifier")
      .map((effect) => ({ effect, source: entry })),
  );
  if (modifierEntries.length === 0) return [...active];

  return active.map((entry) => {
    if (entry.rule.effects.some((effect) => effect.kind === "rule-modifier")) return entry;
    const modifiers = modifierEntries
      .filter(({ effect }) => ruleModifierMatchesRule(effect, entry.rule))
      .flatMap(({ effect }) => effect.modifiers);
    if (modifiers.length === 0) return entry;

    const effects = entry.rule.effects.map((effect) => {
      if (effect.kind === "stat") {
        return { ...effect, value: applyRuleModifierToValue(effect.value, modifiers) };
      }
      return effect;
    });
    return { ...entry, rule: { ...entry.rule, effects } };
  });
}

function ruleTimingActive(
  rule: BuffRule,
  phases: readonly BuffPhase[],
  assumeFullBuffs: boolean,
): boolean {
  if (!phases.includes(rule.phase)) return false;
  if (rule.phase === "panel") return true;
  return assumeFullBuffs || rule.timing === "permanent";
}

function addWorkingStat(member: WorkingMember, stat: string, value: number): void {
  const key = stat as keyof FinalPanelStats;
  const current = member.panel[key];
  if (typeof current === "number") {
    (member.panel as unknown as Record<string, number>)[key] = current + value;
  } else if (key === "windDmgBonus") {
    (member.panel as unknown as Record<string, number>)[key] = value;
  }
}

function statTargets(
  target: BuffTarget,
  source: WorkingMember | undefined,
  team: readonly WorkingMember[],
  attacker: WorkingMember,
): readonly WorkingMember[] {
  switch (target) {
    case "self":
      return source ? [source] : [];
    case "active-character":
      return [attacker];
    case "team":
    case "all-allies":
      return team;
    case "other-allies":
      return source === undefined ? [] : team.filter((member) => member.id !== source.id);
    case "enemy":
    case "all-enemies":
      return [];
  }
}

function applyStatToWorkingMembers(
  target: BuffTarget,
  source: WorkingMember | undefined,
  team: readonly WorkingMember[],
  attacker: WorkingMember,
  effect: Extract<BuffEffect, { kind: "stat" }>,
  value: number,
): void {
  if (effect.operation === "add-flat") {
    for (const member of statTargets(target, source, team, attacker)) {
      addWorkingStat(member, effect.stat, value);
    }
  }
}

function cloneWorkingTeam(input: readonly CombatMemberProfile[]): WorkingMember[] {
  return input.map((member) => ({ ...member, panel: { ...member.panel } }));
}

function panelsEqual(
  left: readonly WorkingMember[],
  right: readonly WorkingMember[],
): boolean {
  if (left.length !== right.length) return false;
  return left.every((member, index) => {
    const other = right[index];
    if (!other || member.id !== other.id) return false;
    return (Object.keys(member.panel) as Array<keyof FinalPanelStats>)
      .every((key) => member.panel[key] === other.panel[key]);
  });
}

function resetWorkingPanels(
  target: WorkingMember[],
  baseline: readonly WorkingMember[],
): void {
  for (let index = 0; index < target.length; index += 1) {
    const base = baseline[index];
    const member = target[index];
    if (base && member) member.panel = { ...base.panel };
  }
}

function resolveActiveCombatRules(
  input: CombatBuffEvaluationInput,
  team: WorkingMember[],
  warnings: string[],
): ActiveCombatRule[] {
  const attacker = team.find((member) => member.id === input.attackerId);
  if (!attacker) throw new Error(`队伍中缺少伤害角色 ${input.attackerId}`);

  const active: ActiveCombatRule[] = [];
  for (const rule of input.rules) {
    const validation = validateBuffRule(rule);
    for (const issue of validation.issues) {
      warnings.push(`${rule.id}: ${issue.message}`);
    }
    if (!validation.valid || rule.status === "raw-only") continue;
    if (!ruleTimingActive(rule, input.phases ?? ["combat"], input.assumeFullBuffs)) continue;

    const source = sourceMemberForRule(rule, team);
    if (rule.source.type !== "scenario" && rule.source.type !== "enemy" && !source) {
      continue;
    }
    if (source && rule.cinemaAtLeast !== undefined && source.cinema < rule.cinemaAtLeast) {
      continue;
    }
    if (source && rule.coreLevel !== undefined && source.coreLevel !== rule.coreLevel) {
      continue;
    }
    if (source && rule.weaponRefinement !== undefined &&
        source.weaponRefinement !== rule.weaponRefinement) {
      continue;
    }

    const context = source
      ? buildContext(source, team, attacker, input.enemyStates)
      : { values: { enemy: { states: input.enemyStates } } };
    if (!evaluateCondition(rule.condition, context, input.assumeFullBuffs)) continue;

    const configuredStacks = input.assumeFullBuffs
      ? rule.stacks?.max ?? rule.stacks?.initial ?? 0
      : rule.stacks?.initial ?? 0;
    active.push({
      rule,
      ...(source ? { sourceMemberId: source.id } : {}),
      stacks: clampStacks(rule, configuredStacks),
    });
  }
  return applyRuleModifiers(active);
}

/**
 * 先把所有面板类 Buff 应用到工作面板，再用稳定后的面板求值所有规则。
 *
 * 这样动态表达式不会依赖规则数组顺序：例如爱丽丝的额外能力读取的是
 * 十方锻星已经加入后的异常掌控，而不是 UID 截图中的局外异常掌控。
 */
function resolveWorkingCombatPanels(
  activeRules: readonly ActiveCombatRule[],
  team: WorkingMember[],
  baseline: readonly WorkingMember[],
  attacker: WorkingMember,
  enemyStates: Readonly<Record<string, boolean>>,
): void {
  let previous = cloneWorkingTeam(baseline);
  for (let iteration = 0; iteration < 8; iteration += 1) {
    const evaluationTeam = cloneWorkingTeam(previous);
    const evaluationAttacker = evaluationTeam.find((member) => member.id === attacker.id);
    if (!evaluationAttacker) return;
    resetWorkingPanels(team, baseline);
    for (const active of activeRules) {
      const evaluationSource = active.sourceMemberId === undefined
        ? undefined
        : evaluationTeam.find((member) => member.id === active.sourceMemberId);
      const outputSource = active.sourceMemberId === undefined
        ? undefined
        : team.find((member) => member.id === active.sourceMemberId);
      const context = evaluationSource
        ? buildContext(evaluationSource, evaluationTeam, evaluationAttacker, enemyStates)
        : { values: {} };
      for (const effect of active.rule.effects) {
        if (effect.kind !== "stat" || !('value' in effect)) continue;
        const value = evaluateBuffValue(effect.value, context, active.stacks);
        if (value === undefined) continue;
        applyStatToWorkingMembers(
          active.rule.target,
          outputSource,
          team,
          attacker,
          effect,
          value,
        );
      }
    }
    if (panelsEqual(team, previous)) return;
    previous = cloneWorkingTeam(team);
  }
}

export function evaluateCombatBuffRules(
  input: CombatBuffEvaluationInput,
): CombatBuffEvaluationResult {
  const warnings: string[] = [];
  const applications: CombatBuffApplication[] = [];
  const team = cloneWorkingTeam(input.team);
  const attacker = team.find((member) => member.id === input.attackerId);
  if (!attacker) throw new Error(`队伍中缺少伤害角色 ${input.attackerId}`);

  const baseline = cloneWorkingTeam(input.team);
  const activeRules = resolveActiveCombatRules(input, team, warnings);
  resolveWorkingCombatPanels(activeRules, team, baseline, attacker, input.enemyStates);

  for (const active of activeRules) {
    const source = active.sourceMemberId === undefined
      ? undefined
      : team.find((member) => member.id === active.sourceMemberId);
    const context = source
      ? buildContext(source, team, attacker, input.enemyStates)
      : { values: { enemy: { states: input.enemyStates } } };
    for (const effect of active.rule.effects) {
      if (effect.kind === "rule-modifier") continue;
      const sourceMemberId = source?.id;
      const affectsAttacker = targetAffectsAttacker(active.rule.target, sourceMemberId, input.attackerId);
      const isEnemyEffect = active.rule.target === "enemy" || active.rule.target === "all-enemies";
      if (!affectsAttacker && !isEnemyEffect) continue;

      let evaluated: Pick<CombatBuffApplication, "value" | "multiplier" | "critRate" | "critDamage"> = {};
      if ("value" in effect) {
        const value = evaluateBuffValue(effect.value, context, active.stacks);
        if (value === undefined) {
          warnings.push(`${active.rule.id}: 无法解析效果数值，未应用 ${effect.kind}。`);
          continue;
        }
        evaluated = { value };
      } else if (effect.kind === "derived-damage") {
        const multiplier = evaluateBuffValue(effect.multiplier, context, active.stacks);
        if (multiplier === undefined) {
          warnings.push(`${active.rule.id}: 无法解析派生伤害倍率，未应用 ${effect.kind}。`);
          continue;
        }
        evaluated = { multiplier };
      } else if (effect.kind === "crit-profile") {
        const critRate = evaluateBuffValue(effect.critRate, context, active.stacks);
        const critDamage = evaluateBuffValue(effect.critDamage, context, active.stacks);
        if (critRate === undefined || critDamage === undefined) {
          warnings.push(`${active.rule.id}: 无法解析独立暴击区，未应用 ${effect.kind}。`);
          continue;
        }
        evaluated = { critRate, critDamage };
      }
      applications.push({
        ruleId: active.rule.id,
        ...(sourceMemberId === undefined ? {} : { sourceMemberId }),
        sourceLabel: active.rule.source.label,
        target: active.rule.target,
        effect,
        ...evaluated,
        stacks: active.stacks,
      });
    }
  }

  return {
    activeRuleIds: activeRules.map((entry) => entry.rule.id),
    applications,
    warnings,
  };
}

export function scopeHasDamageKind(
  scope: BuffScope | undefined,
  damageKind: string,
): boolean {
  return scope?.damageKinds === undefined || scope.damageKinds.includes(damageKind as never);
}

export function isUnscopedDamageBonus(effect: DamageBonusEffect): boolean {
  const scope = effect.scope;
  return scope === undefined || (
    scope.damageKinds === undefined &&
    scope.skillCategories === undefined &&
    scope.skillIds === undefined
  );
}

export function panelModifierFromApplication(
  application: CombatBuffApplication,
): PanelModifier | undefined {
  if (application.effect.kind !== "stat" || application.value === undefined) return undefined;
  return {
    sourceId: application.ruleId,
    label: application.sourceLabel,
    stat: application.effect.stat,
    value: application.value,
  };
}
