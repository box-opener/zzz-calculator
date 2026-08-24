import type {
  BuffCondition,
  BuffEffect,
  BuffExpression,
  BuffRule,
  BuffValue,
} from "../model/buff.js";
import type { StatKey } from "../model/character-build.js";

export type BuffIssueSeverity = "error" | "warning";

export interface BuffValidationIssue {
  path: string;
  message: string;
  severity: BuffIssueSeverity;
}

export interface BuffValidationResult {
  valid: boolean;
  issues: BuffValidationIssue[];
}

const STAT_KEYS: ReadonlySet<string> = new Set<StatKey>([
  "hp",
  "hpPct",
  "atk",
  "atkPct",
  "def",
  "defPct",
  "impact",
  "impactPct",
  "critRate",
  "critDmg",
  "penRate",
  "penFlat",
  "anomalyProficiency",
  "anomalyMastery",
  "anomalyMasteryPct",
  "energyRegen",
  "energyRegenPct",
  "physicalDmgBonus",
  "fireDmgBonus",
  "iceDmgBonus",
  "electricDmgBonus",
  "etherDmgBonus",
  "windDmgBonus",
]);

const TARGETS = new Set([
  "self",
  "active-character",
  "team",
  "all-allies",
  "other-allies",
  "enemy",
  "all-enemies",
]);

const SOURCE_TYPES = new Set([
  "character",
  "weapon",
  "drive-disc-set",
  "enemy",
  "scenario",
]);
const SOURCE_PROVIDERS = new Set([
  "nanoka",
  "miyoushe",
  "legacy",
  "manual",
  "reference",
]);
const CONDITION_TARGETS = new Set(["self", "active-character", "team", "enemy"]);
const CONDITION_OPERATORS = new Set([
  "equals",
  "not-equals",
  "greater-than",
  "greater-than-or-equal",
  "less-than",
  "less-than-or-equal",
]);

const PHASES = new Set(["panel", "combat"]);
const TIMINGS = new Set([
  "permanent",
  "on-entry",
  "on-trigger",
  "while-state",
  "after-trigger",
]);
const TRIGGERS = new Set([
  "attack-hit",
  "damage-taken",
  "skill-used",
  "character-switched-out",
  "state-entered",
  "state-active",
  "manual",
]);
const REFRESH_POLICIES = new Set(["refresh-duration", "replace", "none"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function addIssue(
  issues: BuffValidationIssue[],
  path: string,
  message: string,
  severity: BuffIssueSeverity = "error",
): void {
  issues.push({ path, message, severity });
}

function validateValue(
  value: unknown,
  path: string,
  issues: BuffValidationIssue[],
): value is BuffValue {
  if (typeof value === "number" && Number.isFinite(value)) return true;
  if (!isRecord(value) || typeof value.type !== "string") {
    addIssue(issues, path, "效果数值必须是有限数字或受支持的表达式。");
    return false;
  }

  if (value.type === "constant") {
    if (typeof value.value !== "number" || !Number.isFinite(value.value)) {
      addIssue(issues, `${path}.value`, "constant 表达式必须包含有限数字。");
      return false;
    }
    return true;
  }

  if (value.type === "source-stat") {
    if (typeof value.path !== "string" || value.path.length === 0) {
      addIssue(issues, `${path}.path`, "source-stat 必须指定来源属性路径。");
    }
    if (typeof value.scale !== "number" || !Number.isFinite(value.scale)) {
      addIssue(issues, `${path}.scale`, "source-stat.scale 必须是有限数字。");
    }
    for (const key of ["offset", "flat"] as const) {
      if (value[key] !== undefined &&
          (typeof value[key] !== "number" || !Number.isFinite(value[key]))) {
        addIssue(issues, `${path}.${key}`, `${key} 必须是有限数字。`);
      }
    }
    if (value.cap !== undefined) {
      if (typeof value.cap === "number") {
        if (!Number.isFinite(value.cap)) {
          addIssue(issues, `${path}.cap`, "cap 必须是有限数字或表达式。");
        }
      } else {
        validateValue(value.cap, `${path}.cap`, issues);
      }
    }
    return true;
  }

  if (value.type === "lookup") {
    if (typeof value.path !== "string" || value.path.length === 0) {
      addIssue(issues, `${path}.path`, "lookup 必须指定来源属性路径。");
    }
    if (!Array.isArray(value.values) || value.values.length === 0 ||
        value.values.some((item) => typeof item !== "number" || !Number.isFinite(item))) {
      addIssue(issues, `${path}.values`, "lookup.values 必须是非空有限数字数组。");
    }
    return true;
  }

  if (value.type === "per-stack") {
    if (typeof value.base !== "number" || !Number.isFinite(value.base)) {
      addIssue(issues, `${path}.base`, "per-stack.base 必须是有限数字。");
    }
    if (
      typeof value.perStack !== "number" ||
      !Number.isFinite(value.perStack)
    ) {
      addIssue(issues, `${path}.perStack`, "per-stack.perStack 必须是有限数字。");
    }
    return true;
  }

  addIssue(issues, `${path}.type`, `不支持的效果表达式类型 ${value.type}。`);
  return false;
}

function validateCondition(
  condition: unknown,
  path: string,
  issues: BuffValidationIssue[],
): condition is BuffCondition {
  if (!isRecord(condition) || typeof condition.type !== "string") {
    addIssue(issues, path, "条件必须包含 type。");
    return false;
  }

  switch (condition.type) {
    case "always":
      return true;
    case "all":
    case "any":
      if (!Array.isArray(condition.conditions) || condition.conditions.length === 0) {
        addIssue(issues, `${path}.conditions`, `${condition.type} 条件不能为空。`);
        return false;
      }
      condition.conditions.forEach((child, index) =>
        validateCondition(child, `${path}.conditions[${index}]`, issues),
      );
      return true;
    case "not":
      return validateCondition(condition.condition, `${path}.condition`, issues);
    case "compare":
      if (typeof condition.path !== "string" || condition.path.length === 0) {
        addIssue(issues, `${path}.path`, "比较条件必须指定路径。");
      }
      if (
        typeof condition.operator !== "string" ||
        !CONDITION_OPERATORS.has(condition.operator)
      ) {
        addIssue(issues, `${path}.operator`, "比较条件包含不支持的运算符。");
      }
      if (
        typeof condition.value !== "string" &&
        typeof condition.value !== "number" &&
        typeof condition.value !== "boolean"
      ) {
        addIssue(issues, `${path}.value`, "比较条件的值必须是字符串、数字或布尔值。");
      }
      return true;
    case "state":
      if (
        typeof condition.target !== "string" ||
        !CONDITION_TARGETS.has(condition.target)
      ) {
        addIssue(issues, `${path}.target`, "状态条件包含不支持的目标。");
      }
      if (typeof condition.state !== "string" || condition.state.length === 0) {
        addIssue(issues, `${path}.state`, "状态条件必须指定状态名称。");
      }
      if (
        condition.equals !== undefined &&
        typeof condition.equals !== "boolean"
      ) {
        addIssue(issues, `${path}.equals`, "状态条件 equals 必须是布尔值。");
      }
      return true;
    case "team-match":
      if (condition.relation !== "element" &&
          condition.relation !== "role" &&
          condition.relation !== "camp") {
        addIssue(issues, `${path}.relation`, "队伍匹配条件只支持 element、role 或 camp。");
      }
      if (
        condition.equals !== undefined &&
        typeof condition.equals !== "boolean"
      ) {
        addIssue(issues, `${path}.equals`, "队伍匹配条件 equals 必须是布尔值。");
      }
      return true;
    case "team-role":
      if (typeof condition.role !== "string" || condition.role.length === 0) {
        addIssue(issues, `${path}.role`, "队伍职业条件必须指定职业名称。");
      }
      if (
        condition.equals !== undefined &&
        typeof condition.equals !== "boolean"
      ) {
        addIssue(issues, `${path}.equals`, "队伍职业条件 equals 必须是布尔值。");
      }
      return true;
    case "team-role-count":
      if (typeof condition.role !== "string" || condition.role.length === 0) {
        addIssue(issues, `${path}.role`, "队伍职业数量条件必须指定职业名称。");
      }
      if (typeof condition.operator !== "string" || !CONDITION_OPERATORS.has(condition.operator)) {
        addIssue(issues, `${path}.operator`, "队伍职业数量条件 operator 无效。");
      }
      if (typeof condition.value !== "number" || !Number.isFinite(condition.value)) {
        addIssue(issues, `${path}.value`, "队伍职业数量条件 value 必须是有限数字。");
      }
      return true;
    default:
      addIssue(issues, `${path}.type`, `不支持的条件类型 ${condition.type}。`);
      return false;
  }
}

function validateEffect(
  effect: unknown,
  path: string,
  issues: BuffValidationIssue[],
): effect is BuffEffect {
  if (!isRecord(effect) || typeof effect.kind !== "string") {
    addIssue(issues, path, "效果必须包含 kind。");
    return false;
  }

  if (effect.kind === "stat") {
    if (typeof effect.stat !== "string" || !STAT_KEYS.has(effect.stat)) {
      addIssue(issues, `${path}.stat`, `不支持的面板属性 ${String(effect.stat)}。`);
    }
    if (effect.operation !== "add-flat" && effect.operation !== "add-percent") {
      addIssue(issues, `${path}.operation`, "stat 效果只支持 add-flat 或 add-percent。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  const percentKinds = new Set([
    "damage-bonus",
    "crit-damage-bonus",
    "daze-bonus",
    "def-ignore",
    "def-shred",
  "resistance-shred",
    "resistance-ignore",
    "anomaly-buildup-resistance-shred",
    "damage-taken-reduction",
    "anomaly-effect-strength-multiplier",
    "polar-disorder",
    "vulnerability",
  ]);
  if (percentKinds.has(effect.kind)) {
    if (effect.operation !== "add-percent") {
      addIssue(issues, `${path}.operation`, `${effect.kind} 只支持 add-percent。`);
    }
    validateValue(effect.value, `${path}.value`, issues);
    if (effect.kind === "anomaly-buildup-resistance-shred" &&
        effect.matchingSourceElement !== undefined &&
        typeof effect.matchingSourceElement !== "boolean") {
      addIssue(issues, `${path}.matchingSourceElement`, "matchingSourceElement 必须是布尔值。");
    }
    if (effect.kind === "polar-disorder" && effect.maxTriggers !== undefined) {
      const maxTriggers = effect.maxTriggers;
      if (typeof maxTriggers !== "number" || !Number.isInteger(maxTriggers) || maxTriggers < 1) {
        addIssue(issues, `${path}.maxTriggers`, "polar-disorder.maxTriggers 必须是正整数。");
      }
    }
    return true;
  }

  if (effect.kind === "stun-vulnerability-capture") {
    if (effect.operation !== "replace") {
      addIssue(issues, `${path}.operation`, "stun-vulnerability-capture 只支持 replace。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  if (effect.kind === "status-value-reduction") {
    if (effect.operation !== "add-percent") {
      addIssue(issues, `${path}.operation`, "status-value-reduction 只支持 add-percent。");
    }
    if (typeof effect.status !== "string" || effect.status.length === 0) {
      addIssue(issues, `${path}.status`, "status-value-reduction 必须指定状态名称。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  if (effect.kind === "multiplier") {
    if (effect.operation !== "add-percent" && effect.operation !== "multiply") {
      addIssue(issues, `${path}.operation`, "multiplier 只支持 add-percent 或 multiply。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  if (effect.kind === "shield") {
    if (effect.operation !== "add-flat") {
      addIssue(issues, `${path}.operation`, "shield 只支持 add-flat。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  if (effect.kind === "damage-instance") {
    if (effect.operation !== "add") {
      addIssue(issues, `${path}.operation`, "damage-instance 只支持 add。");
    }
    if (
      effect.damageKind !== "direct" &&
      effect.damageKind !== "anomaly" &&
      effect.damageKind !== "yifang" &&
      effect.damageKind !== "yaobian" &&
      effect.damageKind !== "turbulence" &&
      effect.damageKind !== "assault" &&
      effect.damageKind !== "disorder" &&
      effect.damageKind !== "daze" &&
      effect.damageKind !== "penetration"
    ) {
      addIssue(issues, `${path}.damageKind`, "damage-instance 包含不支持的伤害类别。");
    }
    validateValue(effect.value, `${path}.value`, issues);
    return true;
  }

  if (effect.kind === "derived-damage") {
    if (effect.operation !== "add") {
      addIssue(issues, `${path}.operation`, "derived-damage 只支持 add。");
    }
    const damageKinds = new Set([
      "direct",
      "anomaly",
      "yifang",
      "yaobian",
      "turbulence",
      "assault",
      "disorder",
      "daze",
      "penetration",
    ]);
    if (!damageKinds.has(String(effect.damageKind))) {
      addIssue(issues, `${path}.damageKind`, "derived-damage 包含不支持的目标伤害类别。");
    }
    if (!damageKinds.has(String(effect.sourceDamageKind))) {
      addIssue(issues, `${path}.sourceDamageKind`, "derived-damage 包含不支持的来源伤害类别。");
    }
    validateValue(effect.multiplier, `${path}.multiplier`, issues);
    if (effect.inheritElement !== undefined && typeof effect.inheritElement !== "boolean") {
      addIssue(issues, `${path}.inheritElement`, "inheritElement 必须是布尔值。");
    }
    return true;
  }

  if (effect.kind === "damage-conversion") {
    if (effect.from !== "physical" &&
        effect.from !== "fire" &&
        effect.from !== "ice" &&
        effect.from !== "electric" &&
        effect.from !== "ether") {
      addIssue(issues, `${path}.from`, "damage-conversion 包含不支持的来源元素。");
    }
    if (effect.to !== "direct" &&
        effect.to !== "anomaly" &&
        effect.to !== "yifang" &&
        effect.to !== "yaobian" &&
        effect.to !== "turbulence" &&
        effect.to !== "disorder" &&
        effect.to !== "daze" &&
        effect.to !== "penetration") {
      addIssue(issues, `${path}.to`, "damage-conversion 包含不支持的目标伤害类别。");
    }
    return true;
  }

  if (effect.kind === "crit-profile") {
    if (effect.operation !== "add") {
      addIssue(issues, `${path}.operation`, "crit-profile 只支持 add。");
    }
    if (typeof effect.zone !== "string" || effect.zone.length === 0) {
      addIssue(issues, `${path}.zone`, "crit-profile 必须指定独立暴击区名称。");
    }
    validateValue(effect.critRate, `${path}.critRate`, issues);
    validateValue(effect.critDamage, `${path}.critDamage`, issues);
    return true;
  }

  if (effect.kind === "rule-modifier") {
    if (typeof effect.targetRuleId !== "string" || effect.targetRuleId.length === 0) {
      addIssue(issues, `${path}.targetRuleId`, "rule-modifier 必须指定目标规则。");
    }
    if (!Array.isArray(effect.modifiers) || effect.modifiers.length === 0) {
      addIssue(issues, `${path}.modifiers`, "rule-modifier 至少需要一个修改项。");
    } else {
      effect.modifiers.forEach((modifier, index) => {
        if (!isRecord(modifier)) {
          addIssue(issues, `${path}.modifiers[${index}]`, "修改项必须是对象。");
          return;
        }
        if (modifier.field !== "scale" && modifier.field !== "cap") {
          addIssue(issues, `${path}.modifiers[${index}].field`, "只支持修改 scale 或 cap。");
        }
        if (modifier.operation !== "add") {
          addIssue(issues, `${path}.modifiers[${index}].operation`, "只支持 add 修改。");
        }
        if (typeof modifier.value !== "number" || !Number.isFinite(modifier.value)) {
          addIssue(issues, `${path}.modifiers[${index}].value`, "修改值必须是有限数字。");
        }
      });
    }
    return true;
  }

  addIssue(issues, `${path}.kind`, `不支持的效果类型 ${effect.kind}。`);
  return false;
}

function validateStacks(
  stacks: unknown,
  path: string,
  issues: BuffValidationIssue[],
): void {
  if (!isRecord(stacks)) {
    addIssue(issues, path, "叠层配置必须是对象。");
    return;
  }
  if (stacks.mode !== "manual" && stacks.mode !== "derived") {
    addIssue(issues, `${path}.mode`, "叠层模式必须是 manual 或 derived。");
  }
  for (const key of ["min", "max", "initial"] as const) {
    if (typeof stacks[key] !== "number" || !Number.isInteger(stacks[key])) {
      addIssue(issues, `${path}.${key}`, `${key} 必须是整数。`);
    }
  }
  if (
    typeof stacks.min === "number" &&
    typeof stacks.max === "number" &&
    stacks.min > stacks.max
  ) {
    addIssue(issues, path, "叠层最小值不能大于最大值。");
  }
  if (
    typeof stacks.initial === "number" &&
    typeof stacks.min === "number" &&
    typeof stacks.max === "number" &&
    (stacks.initial < stacks.min || stacks.initial > stacks.max)
  ) {
    addIssue(issues, `${path}.initial`, "初始层数必须处于最小值和最大值之间。");
  }
  if (
    stacks.rampSeconds !== undefined &&
    (typeof stacks.rampSeconds !== "number" ||
      !Number.isFinite(stacks.rampSeconds) ||
      stacks.rampSeconds <= 0)
  ) {
    addIssue(issues, `${path}.rampSeconds`, "叠层完成时间必须是正数。");
  }
}

export function validateBuffRule(input: unknown): BuffValidationResult {
  const issues: BuffValidationIssue[] = [];
  if (!isRecord(input)) {
    return {
      valid: false,
      issues: [{ path: "", message: "Buff 规则必须是对象。", severity: "error" }],
    };
  }

  if (input.schemaVersion !== 1) {
    addIssue(issues, "schemaVersion", "当前只支持 BuffRule schemaVersion 1。");
  }
  if (typeof input.id !== "string" || input.id.length === 0) {
    addIssue(issues, "id", "Buff 规则必须有非空 id。");
  }
  if (!isRecord(input.source)) {
    addIssue(issues, "source", "Buff 规则必须保留来源信息。");
  } else {
    for (const key of ["type", "id", "label", "provider"] as const) {
      if (typeof input.source[key] !== "string" || input.source[key].length === 0) {
        addIssue(issues, `source.${key}`, `来源字段 ${key} 不能为空。`);
      }
    }
    if (typeof input.source.type === "string" && !SOURCE_TYPES.has(input.source.type)) {
      addIssue(issues, "source.type", `不支持的来源类型 ${input.source.type}。`);
    }
    if (
      typeof input.source.provider === "string" &&
      !SOURCE_PROVIDERS.has(input.source.provider)
    ) {
      addIssue(issues, "source.provider", `不支持的来源提供方 ${input.source.provider}。`);
    }
    if (input.source.provider === "nanoka" &&
        input.source.key !== undefined &&
        typeof input.source.key !== "string") {
      addIssue(issues, "source.key", "Nanoka 来源 key 必须是字符串。");
    }
  }
  if (!new Set(["raw-only", "partial", "verified"]).has(input.status as string)) {
    addIssue(issues, "status", "支持状态必须是 raw-only、partial 或 verified。");
  }
  if (typeof input.target !== "string" || !TARGETS.has(input.target)) {
    addIssue(issues, "target", `不支持的作用对象 ${String(input.target)}。`);
  }
  if (typeof input.phase !== "string" || !PHASES.has(input.phase)) {
    addIssue(issues, "phase", `不支持的阶段 ${String(input.phase)}。`);
  }
  if (typeof input.timing !== "string" || !TIMINGS.has(input.timing)) {
    addIssue(issues, "timing", `不支持的生效时机 ${String(input.timing)}。`);
  }
  validateCondition(input.condition, "condition", issues);
  if (!Array.isArray(input.effects) || input.effects.length === 0) {
    addIssue(issues, "effects", "Buff 规则至少需要一个效果。");
  } else {
    input.effects.forEach((effect, index) =>
      validateEffect(effect, `effects[${index}]`, issues),
    );
  }
  if (typeof input.rawDescription !== "string" || input.rawDescription.length === 0) {
    addIssue(issues, "rawDescription", "必须保留原始效果描述。");
  }
  if (input.stacks !== undefined) {
    validateStacks(input.stacks, "stacks", issues);
  }
  if (
    input.durationSeconds !== undefined &&
    (typeof input.durationSeconds !== "number" ||
      !Number.isFinite(input.durationSeconds) ||
      input.durationSeconds <= 0)
  ) {
    addIssue(issues, "durationSeconds", "持续时间必须是正数。");
  }
  if (input.phase === "panel" && input.timing !== "permanent") {
    addIssue(
      issues,
      "timing",
      "战前面板规则不能依赖战斗触发时机。",
      "warning",
    );
  }
  if (input.trigger !== undefined &&
      (typeof input.trigger !== "string" || !TRIGGERS.has(input.trigger))) {
    addIssue(issues, "trigger", `不支持的触发事件 ${String(input.trigger)}。`);
  }
  if (input.refreshPolicy !== undefined &&
      (typeof input.refreshPolicy !== "string" || !REFRESH_POLICIES.has(input.refreshPolicy))) {
    addIssue(issues, "refreshPolicy", `不支持的刷新策略 ${String(input.refreshPolicy)}。`);
  }
  if (input.refreshPolicy === "refresh-duration" && input.durationSeconds === undefined) {
    addIssue(issues, "refreshPolicy", "刷新持续时间的规则必须指定 durationSeconds。");
  }
  if (input.cinemaAtLeast !== undefined &&
      (typeof input.cinemaAtLeast !== "number" ||
        !Number.isInteger(input.cinemaAtLeast) ||
        input.cinemaAtLeast < 0)) {
    addIssue(issues, "cinemaAtLeast", "影画要求必须是非负整数。");
  }
  if (input.coreLevel !== undefined &&
      (typeof input.coreLevel !== "number" ||
        !Number.isInteger(input.coreLevel) ||
        input.coreLevel < 1 || input.coreLevel > 7)) {
    addIssue(issues, "coreLevel", "核心被动等级必须是1到7之间的整数。");
  }
  if (input.equippedCountAtLeast !== undefined &&
      (typeof input.equippedCountAtLeast !== "number" ||
        !Number.isInteger(input.equippedCountAtLeast) ||
        input.equippedCountAtLeast < 1 || input.equippedCountAtLeast > 6)) {
    addIssue(issues, "equippedCountAtLeast", "套装件数要求必须是1到6之间的整数。");
  }
  if (input.weaponRefinement !== undefined &&
      (typeof input.weaponRefinement !== "number" ||
        !Number.isInteger(input.weaponRefinement) ||
        input.weaponRefinement < 1 || input.weaponRefinement > 5)) {
    addIssue(issues, "weaponRefinement", "音擎精炼档位必须是1到5之间的整数。");
  }
  if (input.status === "verified" && input.rawDescription === "") {
    addIssue(issues, "status", "verified 规则必须有可追溯的原始描述。");
  }

  return {
    valid: issues.every((issue) => issue.severity !== "error"),
    issues,
  };
}

export function assertValidBuffRule(rule: BuffRule): void {
  const result = validateBuffRule(rule);
  const errors = result.issues.filter((issue) => issue.severity === "error");
  if (errors.length > 0) {
    throw new Error(errors.map((issue) => `${issue.path}: ${issue.message}`).join("; "));
  }
}

export type { BuffExpression };
