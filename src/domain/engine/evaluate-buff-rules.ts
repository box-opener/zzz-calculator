import type { PanelModifier } from "../model/panel.js";
import type {
  BuffCondition,
  BuffExpression,
  BuffRule,
  BuffValue,
} from "../model/buff.js";
import { validateBuffRule } from "./validate-buff-rule.js";

export interface BuffEvaluationContext {
  values: Readonly<Record<string, unknown>>;
  stacks?: Readonly<Record<string, number>>;
}

export interface PanelBuffEvaluationResult {
  modifiers: PanelModifier[];
  warnings: string[];
}

function getPath(values: Readonly<Record<string, unknown>>, path: string): unknown {
  return path.split(".").reduce<unknown>((current, key) => {
    if (typeof current !== "object" || current === null) return undefined;
    return (current as Record<string, unknown>)[key];
  }, values);
}

function compare(left: unknown, operator: string, right: unknown): boolean {
  switch (operator) {
    case "equals":
      return left === right;
    case "not-equals":
      return left !== right;
    case "greater-than":
      return typeof left === "number" && typeof right === "number" && left > right;
    case "greater-than-or-equal":
      return typeof left === "number" && typeof right === "number" && left >= right;
    case "less-than":
      return typeof left === "number" && typeof right === "number" && left < right;
    case "less-than-or-equal":
      return typeof left === "number" && typeof right === "number" && left <= right;
    default:
      return false;
  }
}

function teamHasRelation(
  values: Readonly<Record<string, unknown>>,
  relation: "element" | "role" | "camp",
): boolean {
  const team = getPath(values, "team");
  if (typeof team !== "object" || team === null) return false;
  const record = team as Record<string, unknown>;

  const directKeys = {
    element: ["hasSameElement", "sameElement"],
    role: ["hasSameRole", "sameRole"],
    camp: ["hasSameCamp", "sameCamp"],
  } as const;
  for (const key of directKeys[relation]) {
    if (record[key] === true) return true;
  }

  const members = record.members;
  if (!Array.isArray(members)) return false;
  const self = record.self;
  if (typeof self !== "object" || self === null) return false;
  const selfValue = (self as Record<string, unknown>)[relation];
  if (typeof selfValue !== "string") return false;
  const selfId = (self as Record<string, unknown>).id;
  return members.some((member) => {
    if (typeof member !== "object" || member === null || member === self) return false;
    const memberRecord = member as Record<string, unknown>;
    if (selfId !== undefined && memberRecord.id === selfId) return false;
    return memberRecord[relation] === selfValue;
  });
}

function teamHasRole(
  values: Readonly<Record<string, unknown>>,
  role: string,
): boolean {
  const team = getPath(values, "team");
  if (typeof team !== "object" || team === null) return false;
  const record = team as Record<string, unknown>;
  const self = record.self;
  const selfId = typeof self === "object" && self !== null
    ? (self as Record<string, unknown>).id
    : undefined;
  const hasRole = record.hasRole;
  if (typeof hasRole === "object" && hasRole !== null &&
      (hasRole as Record<string, unknown>)[role] === true) {
    return true;
  }
  if (Array.isArray(record.roles) && record.roles.includes(role)) return true;
  if (!Array.isArray(record.members)) return false;
  return record.members.some((member) => {
    if (typeof member !== "object" || member === null) return false;
    const memberRecord = member as Record<string, unknown>;
    if (selfId !== undefined && memberRecord.id === selfId) return false;
    return memberRecord.role === role;
  });
}

function teamRoleCount(
  values: Readonly<Record<string, unknown>>,
  role: string,
): number {
  const members = getPath(values, "team.members");
  if (!Array.isArray(members)) return 0;
  return members.filter((member) =>
    typeof member === "object" && member !== null &&
    (member as Record<string, unknown>).role === role,
  ).length;
}

export function evaluateCondition(
  condition: BuffCondition,
  context: BuffEvaluationContext,
  assumeFullBuffs = false,
): boolean {
  switch (condition.type) {
    case "always":
      return true;
    case "all":
      return condition.conditions.every((child) =>
        evaluateCondition(child, context, assumeFullBuffs));
    case "any":
      return condition.conditions.some((child) =>
        evaluateCondition(child, context, assumeFullBuffs));
    case "not":
      return !evaluateCondition(condition.condition, context, assumeFullBuffs);
    case "compare":
      return compare(getPath(context.values, condition.path), condition.operator, condition.value);
    case "state": {
      const path = `${condition.target}.states.${condition.state}`;
      const expected = condition.equals ?? true;
      // 满 Buff 是静态计算模式：角色自身的战斗状态默认已经建立；
      // 敌方状态仍由目标面板显式提供，避免无条件打开失衡/啮咬等条件。
      if (assumeFullBuffs && expected && condition.target !== "enemy") return true;
      return getPath(context.values, path) === expected;
    }
    case "team-match":
      return teamHasRelation(context.values, condition.relation) === (condition.equals ?? true);
    case "team-role":
      return teamHasRole(context.values, condition.role) === (condition.equals ?? true);
    case "team-role-count":
      return compare(
        teamRoleCount(context.values, condition.role),
        condition.operator,
        condition.value,
      );
  }
}

function evaluateExpression(
  expression: BuffExpression,
  context: BuffEvaluationContext,
  stacks: number,
): number | undefined {
  if (expression.type === "constant") return expression.value;
  if (expression.type === "per-stack") {
    return expression.base + expression.perStack * stacks;
  }
  if (expression.type === "lookup") {
    return evaluateLookup(expression, context);
  }

  const source = getPath(context.values, expression.path);
  if (typeof source !== "number" || !Number.isFinite(source)) return undefined;
  const offset = expression.offset ?? 0;
  const flat = expression.flat ?? 0;
  const adjustedSource = Math.max(0, source - offset);
  const uncapped = adjustedSource * expression.scale + flat;
  if (expression.cap === undefined) return uncapped;
  const cap = typeof expression.cap === "number"
    ? expression.cap
    : evaluateExpression(expression.cap, context, stacks);
  return cap === undefined ? undefined : Math.min(cap, uncapped);
}

function evaluateLookup(
  expression: Extract<BuffExpression, { type: "lookup" }>,
  context: BuffEvaluationContext,
): number | undefined {
  const source = getPath(context.values, expression.path);
  if (typeof source !== "number" || !Number.isFinite(source)) return undefined;
  const index = Math.trunc(source);
  return expression.values[index];
}

function evaluateExpressionValue(
  expression: BuffExpression,
  context: BuffEvaluationContext,
  stacks: number,
): number | undefined {
  return expression.type === "lookup"
    ? evaluateLookup(expression, context)
    : evaluateExpression(expression, context, stacks);
}

export function evaluateBuffValue(
  value: BuffValue,
  context: BuffEvaluationContext,
  stacks: number,
): number | undefined {
  return typeof value === "number"
    ? value
    : evaluateExpressionValue(value, context, stacks);
}

export function evaluatePanelBuffRules(
  rules: readonly BuffRule[],
  context: BuffEvaluationContext = { values: {} },
): PanelBuffEvaluationResult {
  const modifiers: PanelModifier[] = [];
  const warnings: string[] = [];

  for (const rule of rules) {
    const validation = validateBuffRule(rule);
    for (const issue of validation.issues) {
      warnings.push(`${rule.id}: ${issue.message}`);
    }
    if (!validation.valid) continue;
    if (rule.status === "raw-only") {
      warnings.push(`${rule.id}: 规则仍是 raw-only，未应用到面板。`);
      continue;
    }
    if (rule.phase !== "panel") {
      warnings.push(`${rule.id}: 战斗 Buff 不在战前面板阶段应用。`);
      continue;
    }
    if (rule.timing !== "permanent") {
      warnings.push(`${rule.id}: 非永久 Buff 不在战前面板阶段应用。`);
      continue;
    }
    if (rule.target !== "self") {
      warnings.push(`${rule.id}: 当前面板计算只支持作用于自身的 Buff。`);
      continue;
    }
    if (!evaluateCondition(rule.condition, context)) continue;

    const configuredStacks = context.stacks?.[rule.id] ?? rule.stacks?.initial ?? 0;
    const stacks = Math.max(
      rule.stacks?.min ?? 0,
      Math.min(rule.stacks?.max ?? configuredStacks, configuredStacks),
    );

    for (const effect of rule.effects) {
      if (effect.kind !== "stat") {
        warnings.push(`${rule.id}: ${effect.kind} 效果暂不能进入战前面板。`);
        continue;
      }
      const value = evaluateBuffValue(effect.value, context, stacks);
      if (value === undefined) {
        warnings.push(`${rule.id}: 无法解析效果数值，未应用 ${effect.stat}。`);
        continue;
      }
      modifiers.push({
        sourceId: rule.id,
        label: rule.source.label,
        stat: effect.stat,
        value,
      });
    }
  }

  return { modifiers, warnings };
}
