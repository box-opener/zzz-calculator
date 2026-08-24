import type { NanokaCharacterProfile } from "../../importers/nanoka/profile.js";
import type { NanokaParsedBuff } from "../../importers/nanoka/parse-buff.js";
import { evaluateBuffValue, evaluateCondition } from "../engine/evaluate-buff-rules.js";
import {
  evaluateCombatBuffRules,
  type CombatMemberProfile,
} from "../engine/evaluate-combat-buff-rules.js";
import { validateBuffRule } from "../engine/validate-buff-rule.js";
import type {
  BuffCondition,
  BuffEffect,
  BuffRule,
  BuffValue,
} from "../model/buff.js";
import type { FinalPanelStats } from "../model/panel.js";

export type CharacterRuleAuditSeverity = "error" | "gap" | "info";

export interface CharacterRuleAuditIssue {
  severity: CharacterRuleAuditSeverity;
  code:
    | "invalid-rule"
    | "missing-auto-rule"
    | "positive-scenario-not-found"
    | "positive-scenario-not-activated"
    | "cinema-boundary-failed"
    | "core-level-boundary-failed"
    | "condition-not-discriminating"
    | "unresolved-review-group"
    | "deferred-out-of-scope-group"
    | "unconsumed-effect"
    | "no-reviewed-rules";
  characterId: string;
  characterName: string;
  message: string;
  ruleId?: string;
  sourceKey?: string;
  effectKind?: BuffEffect["kind"];
}

export interface CharacterRuleAuditCharacter {
  id: string;
  name: string;
  role?: string;
  element?: string;
  camp?: string;
  candidateEntries: number;
  ignoredEntries: number;
  reviewedRules: number;
  activatedRules: number;
  pendingReviewGroups: number;
  deferredOutOfScopeGroups: number;
  integrationGaps: number;
  errors: number;
  status: "ok" | "gap" | "error";
  ruleChecks: CharacterRuleAuditCheck[];
  issues: CharacterRuleAuditIssue[];
}

export interface CharacterRuleAuditCheck {
  ruleId: string;
  label: string;
  sourceKey?: string;
  phase: BuffRule["phase"];
  target: BuffRule["target"];
  effectKinds: BuffEffect["kind"][];
  unconsumedEffectKinds: BuffEffect["kind"][];
  positiveScenarioFound: boolean;
  activated: boolean;
  positiveTeamIds?: string[];
  enemyStates?: Readonly<Record<string, boolean>>;
  cinemaBoundaryPassed?: boolean;
  coreLevelBoundaryPassed?: boolean;
  conditionBoundaryPassed?: boolean;
}

export interface CharacterRuleAuditReport {
  schemaVersion: 1;
  sourceVersion: string;
  generatedAt: string;
  summary: {
    characters: number;
    candidateEntries: number;
    reviewedRules: number;
    activatedRules: number;
    pendingReviewGroups: number;
    deferredOutOfScopeGroups: number;
    integrationGaps: number;
    errors: number;
    charactersOk: number;
    charactersWithGaps: number;
    charactersWithErrors: number;
  };
  unsupportedEffectKinds: Readonly<Record<string, number>>;
  characters: CharacterRuleAuditCharacter[];
}

export interface CharacterRuleAuditInput {
  sourceVersion: string;
  generatedAt?: string;
  profiles: readonly NanokaCharacterProfile[];
  entries: readonly NanokaParsedBuff[];
  rules: readonly BuffRule[];
}

const EMPTY_PANEL: FinalPanelStats = {
  hp: 10000,
  atk: 3000,
  def: 800,
  impact: 120,
  critRate: 50,
  critDmg: 100,
  anomalyMastery: 200,
  anomalyProficiency: 500,
  penRate: 0,
  penFlat: 0,
  energyRegen: 1.2,
  physicalDmgBonus: 30,
  fireDmgBonus: 30,
  iceDmgBonus: 30,
  electricDmgBonus: 30,
  etherDmgBonus: 30,
  windDmgBonus: 30,
};

const DIRECTLY_CONSUMED_EFFECTS = new Set<BuffEffect["kind"]>([
  "stat",
  "damage-bonus",
  "def-shred",
  "def-ignore",
  "resistance-shred",
  "resistance-ignore",
  "anomaly-effect-strength-multiplier",
  "polar-disorder",
  "vulnerability",
  "stun-vulnerability-capture",
  "derived-damage",
  "crit-profile",
  "crit-damage-bonus",
  "rule-modifier",
]);

export function normalizeCharacterSemanticKey(key: string): string {
  return key.replace(
    /^(character:[^:]+:passive:)\d+(:\d+)$/,
    "$1*$2",
  );
}

export function findMissingAutoAcceptedCharacterRules(
  entries: readonly NanokaParsedBuff[],
  rules: readonly BuffRule[],
): string[] {
  const registeredSemanticKeys = new Set(
    rules
      .filter((rule) => rule.source.type === "character")
      .map((rule) => rule.source.key)
      .filter((key): key is string => key !== undefined)
      .map(normalizeCharacterSemanticKey),
  );
  return entries
    .filter((entry) => entry.key.startsWith("character:") && entry.disposition === "auto-accepted")
    .filter((entry) => !registeredSemanticKeys.has(normalizeCharacterSemanticKey(entry.key)))
    .map((entry) => entry.key)
    .sort();
}

export function auditCharacterRules(
  input: CharacterRuleAuditInput,
): CharacterRuleAuditReport {
  const characterRules = input.rules.filter((rule) => rule.source.type === "character");
  const characterEntries = input.entries.filter((entry) => entry.key.startsWith("character:"));
  const rulesByCharacter = groupBy(characterRules, (rule) => rule.source.id);
  const entriesByCharacter = groupBy(characterEntries, (entry) => characterIdFromKey(entry.key));
  const registeredSemanticKeys = new Set(
    characterRules
      .map((rule) => rule.source.key)
      .filter((key): key is string => key !== undefined)
      .map(normalizeCharacterSemanticKey),
  );
  const unsupportedEffectKinds: Record<string, number> = {};

  const profileMap = new Map(input.profiles.map((profile) => [profile.id, profile]));
  const allCharacterIds = new Set([
    ...input.profiles.map((profile) => profile.id),
    ...characterRules.map((rule) => rule.source.id),
    ...characterEntries.map((entry) => characterIdFromKey(entry.key)),
  ]);

  const characters = [...allCharacterIds]
    .sort(compareIds)
    .map((characterId) => {
      const profile = profileMap.get(characterId) ?? {
        id: characterId,
        name: characterRules.find((rule) => rule.source.id === characterId)?.source.label ??
          `角色 ${characterId}`,
      };
      const rules = rulesByCharacter.get(characterId) ?? [];
      const entries = entriesByCharacter.get(characterId) ?? [];
      const issues: CharacterRuleAuditIssue[] = [];
      const ruleChecks: CharacterRuleAuditCheck[] = [];
      const issue = (
        value: Omit<CharacterRuleAuditIssue, "characterId" | "characterName">,
      ): void => {
        issues.push({
          ...value,
          characterId,
          characterName: profile.name,
        });
      };

      if (rules.length === 0) {
        issue({
          severity: "info",
          code: "no-reviewed-rules",
          message: "当前注册表没有该角色的已审查规则。",
        });
      }

      const unresolvedGroups = new Map<string, NanokaParsedBuff>();
      const deferredGroups = new Map<string, NanokaParsedBuff>();
      for (const entry of entries) {
        if (entry.disposition === "ignored") continue;
        const semanticKey = normalizeCharacterSemanticKey(entry.key);
        const registered = registeredSemanticKeys.has(semanticKey);
        if (entry.disposition === "auto-accepted" && !registered) {
          issue({
            severity: "error",
            code: "missing-auto-rule",
            sourceKey: entry.key,
            message: "解析器已自动接收该条目，但统一注册表没有对应规则。",
          });
        }
        if (entry.disposition === "needs-review" && !registered) {
          if (entryNeedsDamageAudit(entry)) unresolvedGroups.set(semanticKey, entry);
          else deferredGroups.set(semanticKey, entry);
        }
      }
      for (const entry of unresolvedGroups.values()) {
        issue({
          severity: "gap",
          code: "unresolved-review-group",
          sourceKey: entry.key,
          message: entry.reviewReasons.join("；") || "该语义组仍需要人工审查。",
        });
      }
      for (const entry of deferredGroups.values()) {
        issue({
          severity: "info",
          code: "deferred-out-of-scope-group",
          sourceKey: entry.key,
          message: "该文本只涉及动作、无敌、抗打断、资源或其他非伤害结算机制，已从人工 Buff 待办中剔除。",
        });
      }

      let activatedRules = 0;
      for (const rule of rules) {
        const unconsumedKinds = [...new Set(
          rule.effects.filter((effect) => !effectIsConsumed(effect)).map((effect) => effect.kind),
        )];
        let activated = false;
        let sourceBoundaries: SourceBoundaryResult = {};
        let conditionBoundaryPassed: boolean | undefined;
        const validation = validateBuffRule(rule);
        if (!validation.valid) {
          issue({
            severity: "error",
            code: "invalid-rule",
            ruleId: rule.id,
            ...sourceKeyOf(rule),
            message: validation.issues.map((item) => item.message).join("；"),
          });
          continue;
        }

        const scenario = findPositiveScenario(rule, profile, input.profiles);
        if (!scenario) {
          issue({
            severity: "error",
            code: "positive-scenario-not-found",
            ruleId: rule.id,
            ...sourceKeyOf(rule),
            message: "无法用当前角色数据库构造满足该规则条件的三人队伍。",
          });
        } else {
          const evaluation = evaluateCombatBuffRules({
            attackerId: characterId,
            team: scenario.team,
            enemyStates: scenario.enemyStates,
            assumeFullBuffs: true,
            phases: [rule.phase],
            rules: [rule],
          });
          if (evaluation.activeRuleIds.includes(rule.id)) {
            activatedRules += 1;
            activated = true;
          } else {
            issue({
              severity: "error",
              code: "positive-scenario-not-activated",
              ruleId: rule.id,
              ...sourceKeyOf(rule),
              message: "正向虚拟场景满足条件，但战斗规则求值器没有激活该规则。",
            });
          }

          sourceBoundaries = auditSourceBoundaries(rule, scenario, issue);
          conditionBoundaryPassed = auditConditionBoundary(rule, scenario, issue);
        }

        for (const effectKind of unconsumedKinds) {
          unsupportedEffectKinds[effectKind] = (unsupportedEffectKinds[effectKind] ?? 0) + 1;
          issue({
            severity: "gap",
            code: "unconsumed-effect",
            ruleId: rule.id,
            ...sourceKeyOf(rule),
            effectKind,
            message: `规则已经登记，但当前队伍伤害汇总器尚未消费 ${effectKind} 效果。`,
          });
        }
        ruleChecks.push({
          ruleId: rule.id,
          label: rule.source.label,
          ...sourceKeyOf(rule),
          phase: rule.phase,
          target: rule.target,
          effectKinds: [...new Set(rule.effects.map((effect) => effect.kind))],
          unconsumedEffectKinds: unconsumedKinds,
          positiveScenarioFound: scenario !== undefined,
          activated,
          ...(scenario === undefined ? {} : {
            positiveTeamIds: scenario.team.map((member) => member.id),
            enemyStates: scenario.enemyStates,
          }),
          ...sourceBoundaries,
          ...(conditionBoundaryPassed === undefined ? {} : { conditionBoundaryPassed }),
        });
      }

      const errors = issues.filter((item) => item.severity === "error").length;
      const pendingReviewGroups = unresolvedGroups.size;
      const integrationGaps = issues.filter((item) => item.code === "unconsumed-effect").length;
      const status = errors > 0 ? "error" :
        pendingReviewGroups > 0 || integrationGaps > 0 ? "gap" : "ok";
      return {
        id: characterId,
        name: profile.name,
        ...(profile.role === undefined ? {} : { role: profile.role }),
        ...(profile.element === undefined ? {} : { element: profile.element }),
        ...(profile.camp === undefined ? {} : { camp: profile.camp }),
        candidateEntries: entries.length,
        ignoredEntries: entries.filter((entry) => entry.disposition === "ignored").length,
        reviewedRules: rules.length,
        activatedRules,
        pendingReviewGroups,
        deferredOutOfScopeGroups: deferredGroups.size,
        integrationGaps,
        errors,
        status,
        ruleChecks,
        issues,
      } satisfies CharacterRuleAuditCharacter;
    });

  return {
    schemaVersion: 1,
    sourceVersion: input.sourceVersion,
    generatedAt: input.generatedAt ?? new Date().toISOString(),
    summary: {
      characters: characters.length,
      candidateEntries: characters.reduce((sum, item) => sum + item.candidateEntries, 0),
      reviewedRules: characters.reduce((sum, item) => sum + item.reviewedRules, 0),
      activatedRules: characters.reduce((sum, item) => sum + item.activatedRules, 0),
      pendingReviewGroups: characters.reduce((sum, item) => sum + item.pendingReviewGroups, 0),
      deferredOutOfScopeGroups: characters.reduce((sum, item) => sum + item.deferredOutOfScopeGroups, 0),
      integrationGaps: characters.reduce((sum, item) => sum + item.integrationGaps, 0),
      errors: characters.reduce((sum, item) => sum + item.errors, 0),
      charactersOk: characters.filter((item) => item.status === "ok").length,
      charactersWithGaps: characters.filter((item) => item.status === "gap").length,
      charactersWithErrors: characters.filter((item) => item.status === "error").length,
    },
    unsupportedEffectKinds: Object.fromEntries(
      Object.entries(unsupportedEffectKinds).sort((left, right) => right[1] - left[1]),
    ),
    characters,
  };
}

export function renderCharacterRuleAuditMarkdown(report: CharacterRuleAuditReport): string {
  const lines = [
    "# 全角色 Buff 规则自动审计",
    "",
    "> 本报告使用 Nanoka 角色标签和虚拟三人队构造正反场景，不要求账号实际拥有角色。",
    "> `error` 表示规则或自动迁移断裂；`gap` 表示仍待审查，或规则已经登记但主伤害链尚未消费。",
    "",
    `- 数据版本：\`${report.sourceVersion}\``,
    `- 生成时间：${report.generatedAt}`,
    `- 角色：${report.summary.characters}`,
    `- 已登记角色规则：${report.summary.reviewedRules}`,
    `- 正向场景成功激活：${report.summary.activatedRules}`,
    `- 阻断错误：${report.summary.errors}`,
    `- 待审语义组：${report.summary.pendingReviewGroups}`,
    `- 已剔除的非伤害机制语义组：${report.summary.deferredOutOfScopeGroups}`,
    `- 主链未消费效果：${report.summary.integrationGaps}`,
    "",
    "## 总览",
    "",
    "| ID | 角色 | 职业 | 已登记 | 已激活 | 待审组 | 非伤害文本 | 接入缺口 | 错误 | 状态 |",
    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ...report.characters.map((item) =>
      `| ${item.id} | ${item.name} | ${item.role ?? "未知"} | ${item.reviewedRules} | ${item.activatedRules} | ${item.pendingReviewGroups} | ${item.deferredOutOfScopeGroups} | ${item.integrationGaps} | ${item.errors} | ${item.status} |`
    ),
    "",
    "## 尚未接入主伤害链的效果类型",
    "",
    ...renderCountList(report.unsupportedEffectKinds),
    "",
    "## 阻断错误",
    "",
    ...renderIssueList(report.characters.flatMap((item) => item.issues).filter((item) => item.severity === "error")),
    "",
    "## 各角色待办",
    "",
  ];

  for (const character of report.characters.filter((item) => item.status !== "ok")) {
    lines.push(
      `### ${character.id}｜${character.name}`,
      "",
      ...renderIssueList(character.issues.filter((item) => item.severity !== "info")),
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

interface PositiveScenario {
  team: CombatMemberProfile[];
  enemyStates: Record<string, boolean>;
}

interface SourceBoundaryResult {
  cinemaBoundaryPassed?: boolean;
  coreLevelBoundaryPassed?: boolean;
}

function findPositiveScenario(
  rule: BuffRule,
  profile: NanokaCharacterProfile,
  profiles: readonly NanokaCharacterProfile[],
): PositiveScenario | undefined {
  const source = memberForRule(profile, rule);
  applyPositiveCompareValues(rule.condition, source);
  const enemyStates = collectStates(rule.condition, "enemy", true);
  const helperProfiles = profiles.filter((item) => item.id !== profile.id);

  for (const helpers of helperCombinations(helperProfiles)) {
    const team = [source, ...helpers.map((item) => memberForProfile(item))];
    const context = conditionContext(source, team, enemyStates, true);
    if (evaluateCondition(rule.condition, context, true)) {
      return { team, enemyStates };
    }
  }
  return undefined;
}

function auditSourceBoundaries(
  rule: BuffRule,
  scenario: PositiveScenario,
  issue: (value: Omit<CharacterRuleAuditIssue, "characterId" | "characterName">) => void,
): SourceBoundaryResult {
  const result: SourceBoundaryResult = {};
  if (rule.cinemaAtLeast !== undefined && rule.cinemaAtLeast > 0) {
    const team = cloneTeam(scenario.team);
    const source = team.find((member) => member.id === rule.source.id);
    if (source) source.cinema = rule.cinemaAtLeast - 1;
    const evaluation = evaluateCombatBuffRules({
      attackerId: rule.source.id,
      team,
      enemyStates: scenario.enemyStates,
      assumeFullBuffs: true,
      phases: [rule.phase],
      rules: [rule],
    });
    const passed = !evaluation.activeRuleIds.includes(rule.id);
    result.cinemaBoundaryPassed = passed;
    if (!passed) {
      issue({
        severity: "error",
        code: "cinema-boundary-failed",
        ruleId: rule.id,
        ...sourceKeyOf(rule),
        message: `影画低于 ${rule.cinemaAtLeast} 时规则仍被激活。`,
      });
    }
  }

  if (rule.coreLevel !== undefined) {
    const team = cloneTeam(scenario.team);
    const source = team.find((member) => member.id === rule.source.id);
    if (source) source.coreLevel = rule.coreLevel === 7 ? 6 : rule.coreLevel + 1;
    const evaluation = evaluateCombatBuffRules({
      attackerId: rule.source.id,
      team,
      enemyStates: scenario.enemyStates,
      assumeFullBuffs: true,
      phases: [rule.phase],
      rules: [rule],
    });
    const passed = !evaluation.activeRuleIds.includes(rule.id);
    result.coreLevelBoundaryPassed = passed;
    if (!passed) {
      issue({
        severity: "error",
        code: "core-level-boundary-failed",
        ruleId: rule.id,
        ...sourceKeyOf(rule),
        message: `核心等级不是 ${rule.coreLevel} 时规则仍被激活。`,
      });
    }
  }
  return result;
}

function auditConditionBoundary(
  rule: BuffRule,
  scenario: PositiveScenario,
  issue: (value: Omit<CharacterRuleAuditIssue, "characterId" | "characterName">) => void,
): boolean | undefined {
  if (rule.condition.type === "always") return undefined;
  const source = cloneMember(scenario.team[0] as CombatMemberProfile);
  source.role = "__不匹配__";
  source.element = "__不匹配__";
  source.camp = "__不匹配__";
  applyNegativeCompareValues(rule.condition, source);
  const enemyStates = collectStates(rule.condition, "enemy", false);
  const context = conditionContext(source, [source], enemyStates, false);
  const passed = !evaluateCondition(rule.condition, context, false);
  if (!passed) {
    issue({
      severity: "gap",
      code: "condition-not-discriminating",
      ruleId: rule.id,
      ...sourceKeyOf(rule),
      message: "自动构造的反向条件仍为真，需要补充该规则的专用反例。",
    });
  }
  return passed;
}

function effectIsConsumed(effect: BuffEffect): boolean {
  if (DIRECTLY_CONSUMED_EFFECTS.has(effect.kind)) return true;
  if (effect.kind !== "multiplier") return false;
  return effect.operation === "add-percent" &&
    effect.scope?.damageKinds?.some((kind) => kind === "disorder" || kind === "turbulence") === true;
}

function entryNeedsDamageAudit(entry: NanokaParsedBuff): boolean {
  const text = entry.displayText;
  const isSkillDescription = entry.key.includes(":skill:");
  const explicitDamageModifier = /(?:造成的|属性异常|紊乱|异放|乱流|强击|攻击力|防御力|暴击率|暴击伤害|异常精通|异常掌控|穿透率|伤害抗性|失衡易伤|积蓄效率|失衡值).{0,24}(?:提升|提高|增加|降低|无视|加成)/.test(text) ||
    /(?:提升|提高|增加|降低|无视).{0,24}(?:伤害|攻击力|防御力|暴击|异常|抗性|穿透|失衡)/.test(text);
  if (isSkillDescription && !explicitDamageModifier) return false;
  if (explicitDamageModifier) return true;
  return entry.recognized.some((value) =>
    /^(?:stat|damage-bonus|daze-bonus|def-|resistance-|crit-|multiplier|derived-damage|damage-instance)/.test(value),
  );
}

function sourceKeyOf(rule: BuffRule): { sourceKey?: string } {
  return rule.source.key === undefined ? {} : { sourceKey: rule.source.key };
}

function memberForRule(profile: NanokaCharacterProfile, rule: BuffRule): CombatMemberProfile {
  const member = memberForProfile(profile);
  member.cinema = rule.cinemaAtLeast ?? 6;
  member.coreLevel = rule.coreLevel ?? 7;
  return member;
}

function memberForProfile(profile: NanokaCharacterProfile): CombatMemberProfile {
  return {
    id: profile.id,
    name: profile.name,
    role: profile.role ?? "未知",
    element: profile.element ?? "未知",
    ...(profile.camp === undefined ? {} : { camp: profile.camp }),
    level: 60,
    cinema: 6,
    coreLevel: 7,
    hpPercent: 100,
    initialAtk: EMPTY_PANEL.atk,
    initialImpact: EMPTY_PANEL.impact,
    driveDiscSetCounts: {},
    panel: { ...EMPTY_PANEL },
  };
}

function conditionContext(
  source: CombatMemberProfile,
  team: readonly CombatMemberProfile[],
  enemyStates: Readonly<Record<string, boolean>>,
  positiveStates: boolean,
) {
  const stateNames = new Set<string>();
  const selfView = {
    ...source,
    ...source.panel,
    panel: source.panel,
    states: new Proxy({}, { get: () => positiveStates }),
  };
  const members = team.map((member) => member.id === source.id
    ? selfView
    : { ...member, ...member.panel, panel: member.panel, states: {} });
  return {
    values: {
      self: selfView,
      team: { self: selfView, members, states: Object.fromEntries([...stateNames].map((name) => [name, positiveStates])) },
      "active-character": selfView,
      enemy: { states: enemyStates },
    },
  };
}

function applyPositiveCompareValues(condition: BuffCondition, member: CombatMemberProfile): void {
  for (const compare of collectCompareConditions(condition)) {
    setCompareValue(member, compare.path, satisfyingNumber(compare.operator, compare.value));
  }
}

function applyNegativeCompareValues(condition: BuffCondition, member: CombatMemberProfile): void {
  for (const compare of collectCompareConditions(condition)) {
    setCompareValue(member, compare.path, failingNumber(compare.operator, compare.value));
  }
}

type CompareCondition = Extract<BuffCondition, { type: "compare" }>;

function collectCompareConditions(condition: BuffCondition): CompareCondition[] {
  if (condition.type === "compare") return [condition];
  if (condition.type === "all" || condition.type === "any") {
    return condition.conditions.flatMap(collectCompareConditions);
  }
  if (condition.type === "not") return collectCompareConditions(condition.condition);
  return [];
}

function setCompareValue(member: CombatMemberProfile, path: string, value: unknown): void {
  if (path === "self.hpPercent" && typeof value === "number") member.hpPercent = value;
  if (path === "self.cinema" && typeof value === "number") member.cinema = value;
}

function satisfyingNumber(operator: string, value: string | number | boolean): unknown {
  if (typeof value !== "number") return value;
  if (operator === "greater-than") return value + 1;
  if (operator === "greater-than-or-equal") return value;
  if (operator === "less-than") return value - 1;
  if (operator === "less-than-or-equal") return value;
  if (operator === "not-equals") return value + 1;
  return value;
}

function failingNumber(operator: string, value: string | number | boolean): unknown {
  if (typeof value !== "number") return operator === "equals" ? "__不匹配__" : value;
  if (operator === "greater-than") return value;
  if (operator === "greater-than-or-equal") return value - 1;
  if (operator === "less-than") return value;
  if (operator === "less-than-or-equal") return value + 1;
  if (operator === "not-equals") return value;
  return value + 1;
}

function collectStates(
  condition: BuffCondition,
  target: "enemy" | "self" | "team" | "active-character",
  value: boolean,
): Record<string, boolean> {
  const result: Record<string, boolean> = {};
  const visit = (current: BuffCondition): void => {
    if (current.type === "state" && current.target === target) {
      result[current.state] = value ? (current.equals ?? true) : !(current.equals ?? true);
    } else if (current.type === "all" || current.type === "any") {
      current.conditions.forEach(visit);
    } else if (current.type === "not") {
      visit(current.condition);
    }
  };
  visit(condition);
  return result;
}

function* helperCombinations(
  profiles: readonly NanokaCharacterProfile[],
): Generator<readonly NanokaCharacterProfile[]> {
  yield [];
  for (const profile of profiles) yield [profile];
  for (let left = 0; left < profiles.length; left += 1) {
    for (let right = left + 1; right < profiles.length; right += 1) {
      const first = profiles[left];
      const second = profiles[right];
      if (first && second) yield [first, second];
    }
  }
}

function characterIdFromKey(key: string): string {
  return key.split(":")[1] ?? "unknown";
}

function compareIds(left: string, right: string): number {
  return left.localeCompare(right, "en", { numeric: true });
}

function groupBy<T>(values: readonly T[], key: (value: T) => string): Map<string, T[]> {
  const result = new Map<string, T[]>();
  for (const value of values) {
    const group = key(value);
    const items = result.get(group) ?? [];
    items.push(value);
    result.set(group, items);
  }
  return result;
}

function cloneMember(member: CombatMemberProfile): CombatMemberProfile {
  return { ...member, panel: { ...member.panel }, driveDiscSetCounts: { ...member.driveDiscSetCounts } };
}

function cloneTeam(team: readonly CombatMemberProfile[]): CombatMemberProfile[] {
  return team.map(cloneMember);
}

function renderCountList(values: Readonly<Record<string, number>>): string[] {
  const entries = Object.entries(values);
  return entries.length === 0
    ? ["- 无"]
    : entries.map(([kind, count]) => `- ${kind}：${count} 条`);
}

function renderIssueList(issues: readonly CharacterRuleAuditIssue[]): string[] {
  if (issues.length === 0) return ["- 无"];
  return issues.map((issue) => {
    const source = issue.ruleId ?? issue.sourceKey ?? "无规则ID";
    return `- **${issue.severity}｜${issue.code}**｜\`${source}\`：${issue.message}`;
  });
}

/** 单独导出，供测试验证动态值在虚拟面板中可求值。 */
export function auditBuffValueCanResolve(
  value: BuffValue,
  profile: NanokaCharacterProfile,
): boolean {
  const member = memberForProfile(profile);
  return evaluateBuffValue(value, conditionContext(member, [member], {}, true), 99) !== undefined;
}
