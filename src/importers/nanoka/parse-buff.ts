import type {
  BuffCondition,
  BuffEffect,
  BuffExpression,
  BuffRule,
  BuffScope,
  BuffTarget,
  BuffTrigger,
  Element,
} from "../../domain/model/buff.js";
import type { SkillCategory, StatKey } from "../../domain/model/character-build.js";
import type { NanokaBuffReviewEntry } from "./detail-review.js";

export type NanokaBuffParseStatus = "parsed" | "review";
export type NanokaBuffReviewDisposition =
  | "ignored"
  | "auto-accepted"
  | "needs-review";

export interface NanokaParsedBuff {
  key: string;
  sourceUrl: string;
  rawText: string;
  displayText: string;
  status: NanokaBuffParseStatus;
  rule: BuffRule | null;
  /** 一条原文拆出的多条规则；单条规则继续使用 rule 兼容旧调用方。 */
  rules?: readonly BuffRule[];
  recognized: string[];
  issues: string[];
  disposition: NanokaBuffReviewDisposition;
  reviewReasons: string[];
}

export function renderNanokaBuffParseReview(
  version: string,
  parsed: readonly NanokaParsedBuff[],
): string {
  const issueCounts = new Map<string, number>();
  for (const item of parsed) {
    for (const issue of item.issues) {
      issueCounts.set(issue, (issueCounts.get(issue) ?? 0) + 1);
    }
  }
  const lines = [
    "# Nanoka Buff 结构化解析审查清单",
    "",
    "> 本文件由 Nanoka 中文详情 JSON 解析生成。无语义警告的确定性规则会自动接收；有疑点的条目仍保持 `partial`，不会进入当前计算。",
    "> 本文件是机器诊断全集，不是人工待办清单；人工只看 `nanoka-buff-review-queue-001.md`。",
    "",
    `- 数据版本：\`${version}\``,
    `- 候选总数：${parsed.length}`,
    `- 已识别出效果：${parsed.filter((item) => item.rule !== null).length}`,
    `- 无法生成规则：${parsed.filter((item) => item.rule === null).length}`,
    `- 需要审查：${parsed.filter((item) => item.issues.length > 0).length}`,
    `- 忽略（当前范围外）：${parsed.filter((item) => item.disposition === "ignored").length}`,
    `- 自动接收（无语义警告）：${parsed.filter((item) => item.disposition === "auto-accepted").length}`,
    `- 真正需要人工确认：${parsed.filter((item) => item.disposition === "needs-review").length}`,
    "",
    "## 问题统计",
    "",
    ...[...issueCounts.entries()]
      .sort((left, right) => right[1] - left[1])
      .map(([issue, count]) => `- ${count} 条：${issue}`),
    "",
  ];

  for (const item of parsed) {
    lines.push(
      `## ${item.key}`,
      "",
      `- 来源：${item.sourceUrl}`,
      `- 状态：${item.status}`,
      `- 审查分类：${item.disposition}`,
      `- 识别结果：${item.recognized.join("、") || "无"}`,
      `- 问题：${item.issues.join("；") || "无"}`,
      "- Nanoka 原文：",
      "```text",
      item.rawText,
      "```",
      "- 阅读文本：",
      "```text",
      item.displayText,
      "```",
      "- 当前解析候选：",
      "```json",
      JSON.stringify(reviewCandidate(item), null, 2),
      "```",
      "- 请确认：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

interface ParseState {
  effects: BuffEffect[];
  recognized: string[];
  issues: string[];
}

const ELEMENTS: Readonly<Record<string, Element>> = {
  物理: "physical",
  火: "fire",
  冰: "ice",
  电: "electric",
  以太: "ether",
  风: "wind",
};

const STAT_PATTERNS: readonly {
  pattern: RegExp;
  stat: StatKey;
  operation: "add-flat" | "add-percent";
}[] = [
  { pattern: /(生命值)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "hp", operation: "add-flat" },
  { pattern: /(攻击力)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "atk", operation: "add-flat" },
  { pattern: /(防御力)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "def", operation: "add-flat" },
  { pattern: /(冲击力)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "impact", operation: "add-flat" },
  { pattern: /(暴击率)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "critRate", operation: "add-flat" },
  { pattern: /(暴击伤害)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "critDmg", operation: "add-flat" },
  { pattern: /(穿透率)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "penRate", operation: "add-flat" },
  { pattern: /(异常精通)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "anomalyProficiency", operation: "add-flat" },
  { pattern: /(异常掌控)(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "anomalyMastery", operation: "add-flat" },
  { pattern: /(能量(?:获得效率|自动回复))(?:提升|增加|提高|加成|\+)([\d.]+)(%|点)?/g, stat: "energyRegen", operation: "add-flat" },
];

/**
 * 将 Nanoka 原文转换为“保守的结构化候选”。
 *
 * 解析器绝不把候选标为 verified。无法确定的语义写入 issues，并保留
 * 原始文本；只有人工确认后，才允许把结果移动到 data/rules/。
 */
export function parseNanokaBuffEntry(entry: NanokaBuffReviewEntry): NanokaParsedBuff {
  const state: ParseState = { effects: [], recognized: [], issues: [] };
  const text = entry.displayText;
  const isPanel = entry.section === "equipment" && entry.key.endsWith(":desc2");
  const sourceType = entry.kind === "equipment"
    ? "drive-disc-set"
    : entry.kind === "weapon"
      ? "weapon"
      : "character";
  const scope = parseScope(text, state);
  const skillCategory = entry.key.match(/:skill:(basic|dash|special|dodge|chain|ultimate|core|assist):/)?.[1] as SkillCategory | undefined;
  parseStatEffects(text, state, skillCategory);
  parseDamageEffects(text, state);
  parseDazeEffects(text, state, scope);
  parseDefenseEffects(text, state, scope);
  parseRuleModifierEffects(text, state, entry.id);
  parseDamageInstanceEffects(text, state, scope);
  parseShieldEffect(text, state);

  const { condition, trigger } = parseConditionAndTrigger(text, state);
  const duration = parseDuration(text, state);
  const stacks = parseStacks(text, state);
  const target = parseTarget(text, state);
  parseUnsupportedSemantics(text, state, isPanel);

  if (state.effects.length === 0) {
    state.issues.unshift("没有识别到当前 BuffRule 支持的效果，需要人工拆解。");
  }
  if (text.includes("；") || text.includes("\n")) {
    state.issues.push("原文包含多个分句，可能需要拆成多条规则或多个作用对象。");
  }
  if (stacks && !/每层/.test(text) && /最多叠加|上限/.test(text)) {
    state.issues.push("原文声明了叠层上限，但没有明确每层数值与总值关系。");
  }
  if (text.includes("处于失衡状态") && text.includes("未处于失衡状态")) {
    state.issues.push("同一原文包含互斥的失衡/未失衡条件，必须拆成多条规则。");
  }

  const sourceVersion = entry.sourceUrl.match(/\/zzz\/([^/]+)\//)?.[1] ?? "unknown";
  const rule = state.effects.length === 0 || state.issues.some((issue) => issue.startsWith("同一原文包含互斥"))
    ? null
    : buildRule({
        entry,
        sourceType,
        sourceVersion,
        isPanel,
        condition,
        trigger,
        duration,
        stacks,
        target,
        effects: state.effects,
        notes: state.issues,
      });
  const issues = unique(state.issues);
  const classification = classifyReviewDisposition(entry, text, rule, issues);
  const finalRule = classification.disposition === "auto-accepted" && rule
    ? {
        ...rule,
        status: "verified" as const,
        notes: "自动接收：解析结果无语义警告，已通过 BuffRule 校验。",
      }
    : rule;

  return {
    key: entry.key,
    sourceUrl: entry.sourceUrl,
    rawText: entry.rawText,
    displayText: entry.displayText,
    status: issues.length === 0 && finalRule ? "parsed" : "review",
    rule: finalRule,
    ...(finalRule ? { rules: [finalRule] } : {}),
    recognized: state.recognized,
    issues,
    disposition: classification.disposition,
    reviewReasons: classification.reasons,
  };
}

export function parseNanokaBuffEntries(
  entries: readonly NanokaBuffReviewEntry[],
): NanokaParsedBuff[] {
  return entries.map(parseNanokaBuffEntry);
}

/**
 * 只挑真正需要用户判断的条目，并按语义组去掉角色被动等级和音擎阶级重复。
 * 输入 entries 由 detail-review 按 key 排序，因此同组最后一项通常就是最高等级。
 */
export function selectNanokaActionableReviewBatch(
  parsed: readonly NanokaParsedBuff[],
  size: number,
): NanokaParsedBuff[] {
  if (!Number.isInteger(size) || size < 1) {
    throw new Error(`Nanoka 审查批次大小无效：${size}`);
  }
  const grouped = new Map<string, NanokaParsedBuff[]>();
  for (const item of parsed) {
    if (item.disposition !== "needs-review") continue;
    const group = nanokaReviewGroupKey(item);
    const items = grouped.get(group) ?? [];
    items.push(item);
    grouped.set(group, items);
  }
  return [...grouped.values()]
    .map((items) => items.reduce((selected, item) =>
      reviewRepresentativeRank(item) > reviewRepresentativeRank(selected) ? item : selected,
    ))
    .sort((left, right) => reviewPriority(right) - reviewPriority(left) || left.key.localeCompare(right.key))
    .slice(0, size);
}

/**
 * 选择装备审查清单：驱动盘每个 2/4 件套各审查一次，音擎按“同一把音擎、
 * 同一效果文本”合并精炼等级，并保留全部精炼原文供核对数值曲线。
 *
 * 这里不把 parser 的 auto-accepted 当成人工确认；它们也会进入清单，
 * 只是标记为“机器无语义警告”，仍需用户确认后才能迁移进 data/rules/。
 */
export function selectNanokaEquipmentReviewEntries(
  parsed: readonly NanokaParsedBuff[],
): NanokaParsedBuff[] {
  const grouped = new Map<string, NanokaParsedBuff[]>();
  for (const item of parsed) {
    if (!item.key.startsWith("weapon:") && !item.key.startsWith("equipment:")) continue;
    if (item.disposition === "ignored") continue;
    const group = nanokaReviewGroupKey(item);
    const members = grouped.get(group) ?? [];
    members.push(item);
    grouped.set(group, members);
  }
  return [...grouped.values()]
    .map((members) => members.reduce((selected, item) =>
      reviewRepresentativeRank(item) > reviewRepresentativeRank(selected) ? item : selected,
    ))
    .sort((left, right) => left.key.localeCompare(right.key));
}

export function renderNanokaEquipmentReviewQueue(
  version: string,
  allParsed: readonly NanokaParsedBuff[],
  selected: readonly NanokaParsedBuff[],
): string {
  const equipment = allParsed.filter((item) =>
    (item.key.startsWith("weapon:") || item.key.startsWith("equipment:")) &&
    item.disposition !== "ignored",
  );
  const ignored = allParsed.filter((item) =>
    (item.key.startsWith("weapon:") || item.key.startsWith("equipment:")) &&
    item.disposition === "ignored",
  );
  const groupKey = (item: NanokaParsedBuff): string => nanokaReviewGroupKey(item);
  const lines = [
    "# Nanoka 音擎与驱动盘 Buff 审查队列",
    "",
    "> 本清单直接来自 Nanoka 当前版本中文详情 JSON；旧版本地字典和历史规则不参与生成。",
    "> 音擎按同一效果的不同精炼等级合并展示，但每个等级原文都会保留；驱动盘按每套 2 件/4 件效果逐条展示。",
    "> 当前用户已确认音擎与驱动盘可直接解析；本文件保留迁移前的全量原文和解析快照。正式规则位于 data/rules/nanoka-equipment-reviewed-001.ts。",
    "",
    `- 数据版本：\`${version}\``,
    `- 待审查语义组：${selected.length}`,
    `- 音擎语义组：${selected.filter((item) => item.key.startsWith("weapon:")).length}`,
    `- 驱动盘效果：${selected.filter((item) => item.key.startsWith("equipment:")).length}`,
    `- 覆盖装备原始条目：${equipment.length}`,
    `- 机器无语义警告：${equipment.filter((item) => item.disposition === "auto-accepted").length}`,
    `- 需要人工判断：${equipment.filter((item) => item.disposition === "needs-review").length}`,
    `- 当前范围外未列入：${ignored.length}`,
    "",
    "## 审查方式",
    "",
    "每组只需要确认：Nanoka 原文的数值曲线、作用对象、触发条件、持续时间、叠层/刷新规则，以及是否应拆成多条 BuffRule。确认后再写入对应的版本化规则数据。",
    "",
  ];

  for (const item of selected) {
    const members = equipment.filter((candidate) => groupKey(candidate) === groupKey(item));
    lines.push(
      `## ${item.key}`,
      "",
      `- 语义组：\`${groupKey(item)}\``,
      `- 覆盖条目：${members.length} 条`,
      `- 机器状态：${item.disposition}`,
      `- 迁移状态：${item.rule !== null || (item.rules !== undefined && item.rules.length > 0) ? "已写入规则数据" : "未写入，见剩余待确认清单"}`,
      `- 来源：${item.sourceUrl}`,
      `- 识别结果：${item.recognized.join("、") || "无"}`,
      `- 需要确认原因：${item.reviewReasons.join("；") || "机器解析无语义警告，请确认后接收"}`,
      "- Nanoka 原文（含全部精炼等级/对应效果）：",
      "```text",
      members.map((member) => `${member.key}: ${member.displayText}`).join("\n"),
      "```",
      "- 当前解析候选：",
      "```json",
      JSON.stringify(reviewCandidate(item), null, 2),
      "```",
      "- 审查结论：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

export function renderNanokaEquipmentRemainingReviewQueue(
  version: string,
  allParsed: readonly NanokaParsedBuff[],
  selected: readonly NanokaParsedBuff[],
): string {
  const remaining = allParsed.filter((item) =>
    (item.key.startsWith("weapon:") || item.key.startsWith("equipment:")) &&
    item.disposition !== "ignored" &&
    item.rule === null &&
    (item.rules === undefined || item.rules.length === 0),
  );
  const groupKey = (item: NanokaParsedBuff): string => nanokaReviewGroupKey(item);
  const lines = [
    "# Nanoka 音擎与驱动盘剩余待确认规则",
    "",
    "> 其余装备规则已按用户确认直接写入版本化规则数据；这里只保留当前模型无法表达的效果。",
    "> 请确认这些效果是否需要扩展伤害引擎，或继续维持当前范围外状态。",
    "",
    `- 数据版本：\`${version}\``,
    `- 待确认语义组：${selected.length}`,
    `- 待确认原始条目：${remaining.length}`,
    "",
  ];
  if (selected.length === 0) {
    lines.push("当前没有剩余待确认的音擎或驱动盘规则。", "");
  }
  for (const item of selected) {
    const members = remaining.filter((candidate) => groupKey(candidate) === groupKey(item));
    lines.push(
      `## ${item.key}`,
      "",
      `- 语义组：\`${groupKey(item)}\``,
      `- 覆盖条目：${members.length} 条`,
      `- 来源：${item.sourceUrl}`,
      `- 需要确认原因：${item.reviewReasons.join("；") || item.issues.join("；")}`,
      "- Nanoka 原文（含全部精炼等级/对应效果）：",
      "```text",
      members.map((member) => `${member.key}: ${member.displayText}`).join("\n"),
      "```",
      "- 审查结论：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

export function renderNanokaActionableReviewQueue(
  version: string,
  allParsed: readonly NanokaParsedBuff[],
  selected: readonly NanokaParsedBuff[],
): string {
  const needsReview = allParsed.filter((item) => item.disposition === "needs-review");
  const uniqueGroups = new Set(needsReview.map((item) => nanokaReviewGroupKey(item)));
  const lines = [
    "# Nanoka Buff 真正需要人工确认的审查队列",
    "",
    "> 这里只保留会影响当前伤害/失衡/防御/抗性计算、且解析器无法安全决定的条目。",
    "> 能量、资源、技能等级、纯护盾流程等当前范围外内容已自动忽略；角色被动等级和音擎阶级已合并，每个语义只保留一条代表项。",
    "",
    `- 数据版本：\`${version}\``,
    `- 原始候选：${allParsed.length}`,
    `- 当前范围外自动忽略：${allParsed.filter((item) => item.disposition === "ignored").length}`,
    `- 无语义警告自动接收：${allParsed.filter((item) => item.disposition === "auto-accepted").length}`,
    `- 待确认原始条目：${needsReview.length}`,
    `- 待确认语义组：${uniqueGroups.size}`,
    `- 本批展示：${selected.length}`,
    "",
    "## 审查方式",
    "",
    "只需要确认：数值是否正确、作用对象是否正确、触发条件是否正确、是否需要拆成多条公式。无需审查能量回复、技能等级、护盾流程等已明确排除的内容。",
    "",
  ];
  for (const item of selected) {
    const groupKey = nanokaReviewGroupKey(item);
    const groupMembers = allParsed.filter((candidate) => nanokaReviewGroupKey(candidate) === groupKey);
    const pendingMembers = groupMembers.filter((candidate) => candidate.disposition === "needs-review");
    const handledMembers = groupMembers.length - pendingMembers.length;
    lines.push(
      `## ${item.key}`,
      "",
      `- 语义组：\`${groupKey}\``,
      `- 覆盖条目：${groupMembers.length} 条（待确认 ${pendingMembers.length} 条，已处理 ${handledMembers} 条）`,
      `- 覆盖 key：${groupMembers.map((candidate) => candidate.key).join("、")}`,
      `- 来源：${item.sourceUrl}`,
      `- 审查分类：${item.disposition}`,
      `- 识别结果：${item.recognized.join("、") || "无"}`,
      `- 需要确认的原因：${item.reviewReasons.join("；") || "结构无法安全确定"}`,
      "- Nanoka 原文：",
      "```text",
      item.rawText,
      "```",
      "- 当前解析候选：",
      "```json",
      JSON.stringify(reviewCandidate(item), null, 2),
      "```",
      "- 审查结论：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

function reviewCandidate(item: NanokaParsedBuff): BuffRule | readonly BuffRule[] | null {
  return item.rules && item.rules.length > 1 ? item.rules : item.rule;
}

function classifyReviewDisposition(
  entry: NanokaBuffReviewEntry,
  text: string,
  rule: BuffRule | null,
  issues: readonly string[],
): { disposition: NanokaBuffReviewDisposition; reasons: string[] } {
  const damageRelevant = /伤害|易伤|失衡值|防御力|抗性|穿透|暴击|攻击力|异常精通|异常掌控/.test(text);
  const outOfScope = /能量|闪能|喧响值|呼噜能量|支援点数|落霜|技能等级|护盾|护盾值|抗打断|无敌|异常积蓄|积蓄效率|回复|恢复/.test(text);
  const hasBuffModifier = /提升|增加|提高|降低|无视|额外造成|额外结算|加成/.test(text);

  // 技能详情中大量只是“造成某属性伤害”的倍率/动作说明，不是 Buff。
  // 只有出现明确的增减益、抗性无视或额外伤害语义时才进入 Buff 队列。
  if (entry.section === "character-skill" && !hasBuffModifier) {
    return {
      disposition: "ignored",
      reasons: ["这是技能伤害/动作说明，不是当前 Buff 规则范围。"],
    };
  }

  if (!damageRelevant && outOfScope) {
    return {
      disposition: "ignored",
      reasons: ["当前版本暂不计算能量、资源、技能等级、护盾流程或异常积蓄等语义。"],
    };
  }
  if (!damageRelevant && entry.section !== "equipment") {
    return {
      disposition: "ignored",
      reasons: ["原文不影响当前伤害、失衡、面板或抗性计算范围。"],
    };
  }
  const hardReviewIssues = issues.filter((issue) =>
    /没有识别到当前 BuffRule|涉及动态换算|同一原文包含互斥|声明了叠层上限|同名效果互斥|多个持续时间|不能按战前面板永久属性处理|涉及无敌|倍率改写/.test(issue),
  );
  if (rule && hardReviewIssues.length === 0) {
    return { disposition: "auto-accepted", reasons: [] };
  }
  return {
    disposition: "needs-review",
    reasons: hardReviewIssues.length > 0
      ? hardReviewIssues
      : issues.length > 0
        ? [...issues]
        : ["未能生成可校验的结构化规则。"],
  };
}

export function nanokaReviewGroupKey(
  item: Pick<NanokaParsedBuff, "key" | "displayText">,
): string {
  const passive = item.key.match(/^character:([^:]+):passive:\d+:(\d+)$/);
  if (passive) {
    return `character:${passive[1]}:passive:*:${passive[2]}:${normalizeSemanticText(item.displayText)}`;
  }
  const weaponTalent = item.key.match(/^weapon:([^:]+):talent:\d+$/);
  if (weaponTalent) {
    return `weapon:${weaponTalent[1]}:talent:*:${normalizeSemanticText(item.displayText)}`;
  }
  return item.key;
}

function normalizeSemanticText(text: string): string {
  return text
    .replace(/\d+(?:\.\d+)?%?/g, "<数值>")
    .replace(/\s+/g, "")
    .trim();
}

function reviewRepresentativeRank(item: NanokaParsedBuff): number {
  const passive = item.key.match(/:passive:(\d+):/);
  if (passive) return Number(passive[1]);
  const weaponTalent = item.key.match(/:talent:(\d+)$/);
  if (weaponTalent) return Number(weaponTalent[1]);
  return 0;
}

function reviewPriority(item: NanokaParsedBuff): number {
  let score = item.rule ? 0 : 20;
  if (/伤害/.test(item.displayText)) score += 30;
  if (/防御力|抗性|穿透/.test(item.displayText)) score += 20;
  if (/失衡值|暴击|攻击力/.test(item.displayText)) score += 15;
  if (/动态换算|分段条件|动作链|事件顺序|单次攻击/.test(item.issues.join("；"))) score += 10;
  if (item.key.includes(":passive:")) score += 5;
  return score;
}

function buildRule(input: {
  entry: NanokaBuffReviewEntry;
  sourceType: "character" | "weapon" | "drive-disc-set";
  sourceVersion: string;
  isPanel: boolean;
  condition: BuffCondition;
  trigger: BuffTrigger | undefined;
  duration: number | undefined;
  stacks: BuffRule["stacks"] | undefined;
  target: BuffTarget;
  effects: readonly BuffEffect[];
  notes: readonly string[];
}): BuffRule {
  const optional: Partial<BuffRule> = {};
  if (input.trigger) optional.trigger = input.trigger;
  if (input.duration !== undefined) optional.durationSeconds = input.duration;
  if (input.stacks) optional.stacks = input.stacks;
  if (input.entry.section === "character-talent" && input.entry.level !== undefined) {
    optional.cinemaAtLeast = input.entry.level;
  }
  const coreLevelDigit = input.entry.key.match(/^character:[^:]+:passive:\d+:0$/)?.[0].slice(-3, -2);
  if (input.entry.section === "character-passive" &&
      coreLevelDigit !== undefined && /^[1-7]$/.test(coreLevelDigit)) {
    optional.coreLevel = Number(coreLevelDigit);
  }
  if (input.entry.section === "weapon-talent" && input.entry.level !== undefined) {
    optional.weaponRefinement = input.entry.level;
  }
  if (input.entry.section === "equipment") {
    optional.equippedCountAtLeast = input.entry.key.endsWith(":desc4") ? 4 : 2;
  }
  if (input.notes.length > 0) optional.notes = input.notes.join("；");

  return {
    schemaVersion: 1,
    id: `nanoka:${input.entry.key.replaceAll(":", "_")}`,
    source: {
      type: input.sourceType,
      id: input.entry.id,
      label: `${input.entry.name}${input.entry.title ? `｜${input.entry.title}` : ""}`,
      provider: "nanoka",
      version: input.sourceVersion,
      url: input.entry.sourceUrl,
      key: input.entry.key,
    },
    status: "partial",
    target: input.target,
    phase: input.isPanel ? "panel" : "combat",
    timing: input.isPanel ? "permanent" : input.trigger ? "on-trigger" : "permanent",
    condition: input.condition,
    effects: input.effects,
    rawDescription: input.entry.rawText,
    ...optional,
  };
}

function parseStatEffects(
  text: string,
  state: ParseState,
  skillCategory?: SkillCategory,
): void {
  for (const item of STAT_PATTERNS) {
    for (const match of text.matchAll(item.pattern)) {
      const value = Number(match[2]);
      if (!Number.isFinite(value)) continue;
      const unit = match[3];
      const operation = unit === "%" ? "add-percent" : item.operation;
      const stat = percentStat(item.stat, unit === "%");
      state.effects.push({ kind: "stat", stat, operation, value });
      state.recognized.push(`stat:${stat}:${value}${unit ?? ""}`);
    }
  }

  // “提升效果等同于某角色初始攻击力的35%，最高不超过1200点”是
  // Nanoka 对支援角色战斗 Buff 的统一动态表达。它必须进入
  // self.initialAtk，而不是被误读为固定的35点攻击力。
  const initialAttackConversions = /攻击力提升[^。；\n]*?(?:([\d.]+)%初始攻击力|初始攻击力的([\d.]+)%)[^。；\n]*?(?:最高不超过|上限)([\d.]+)点/g;
  for (const match of text.matchAll(initialAttackConversions)) {
    const scale = Number(match[1] ?? match[2]);
    const cap = Number(match[3]);
    if (!Number.isFinite(scale) || !Number.isFinite(cap)) continue;
    state.effects.push({
      kind: "stat",
      stat: "atk",
      operation: "add-flat",
      value: { type: "source-stat", path: "self.initialAtk", scale: scale / 100, cap },
    });
    state.recognized.push(`dynamic-stat:atk:self.initialAtk:${scale}%:${cap}`);
  }

  // 技能详情中的 CAL 公式使用技能等级。当前满拐网页计算默认按技能12级，
  // 同时保留 self.skillLevels 路径，后续导入器提供技能等级时无需改规则数据。
  const calValue = /\{CAL:([\d.]+)\+AvatarSkillLevel\(1\)\*([\d.]+),100,2\}%/;
  const cal = text.match(calValue);
  if (cal) {
    const base = Number(cal[1]);
    const perLevel = Number(cal[2]);
    const sourcePath = `self.skillLevels.${skillCategory ?? "special"}`;
    if (Number.isFinite(base) && Number.isFinite(perLevel)) {
      const value = {
        type: "source-stat" as const,
        path: sourcePath,
        scale: perLevel * 100,
        flat: base * 100,
      };
      if (/造成的伤害提升\{CAL:/.test(text)) {
        state.effects.push({ kind: "damage-bonus", operation: "add-percent", value });
        state.recognized.push(`dynamic-damage-bonus:${sourcePath}`);
      }
      if (/暴击伤害提升\{CAL:/.test(text)) {
        state.effects.push({ kind: "stat", stat: "critDmg", operation: "add-percent", value });
        state.recognized.push(`dynamic-stat:critDmg:${sourcePath}`);
      }
    }
  }

  const elementStat = /((?:物理|火|冰|电|以太|风))(?:属性)?伤害(?:提升|增加|提高|加成|\+)([\d.]+)%/g;
  for (const match of text.matchAll(elementStat)) {
    const element = ELEMENTS[match[1] ?? ""];
    if (!element) continue;
    const stat = `${element}DmgBonus` as StatKey;
    const value = Number(match[2]);
    state.effects.push({ kind: "stat", stat, operation: "add-percent", value });
    state.recognized.push(`element-stat:${stat}:${value}%`);
  }
}

function percentStat(stat: StatKey, percent: boolean): StatKey {
  if (!percent) return stat;
  const percentMap: Partial<Record<StatKey, StatKey>> = {
    hp: "hpPct",
    atk: "atkPct",
    def: "defPct",
    impact: "impactPct",
    anomalyMastery: "anomalyMasteryPct",
  };
  return percentMap[stat] ?? stat;
}

function parseDamageEffects(
  text: string,
  state: ParseState,
): void {
  const pattern = /伤害(?:额外)?(?:提升|增加|提高|加成)(?:至|为)?([\d.]+)%/g;
  for (const match of text.matchAll(pattern)) {
    const matchIndex = match.index ?? 0;
    const prefix = text.slice(0, matchIndex);
    const afterMatch = text.slice(matchIndex);
    if (
      /(?:物理|火|冰|电|以太)(?:属性)?$/.test(prefix.slice(-5)) &&
      !afterMatch.startsWith("伤害额外")
    ) continue;
    if (/暴击$/.test(prefix.slice(-3))) continue;
    const value = Number(match[1]);
    // 作用域只取当前分句。整段原文经常同时列出多个技能，不能因为
    // 后文出现了“终结技”就把前面的“造成的伤害提升”误限成终结技。
    const clauseStart = Math.max(
      prefix.lastIndexOf("。"),
      prefix.lastIndexOf("；"),
      prefix.lastIndexOf("\n"),
    );
    const clauseEndCandidates = [
      text.indexOf("。", matchIndex),
      text.indexOf("；", matchIndex),
      text.indexOf("\n", matchIndex),
    ].filter((index) => index >= 0);
    const clauseEnd = clauseEndCandidates.length > 0
      ? Math.min(...clauseEndCandidates)
      : text.length;
    const clause = text.slice(clauseStart + 1, clauseEnd);
    const clauseScope = parseScope(clause, { effects: [], recognized: [], issues: [] });
    state.effects.push({
      kind: "damage-bonus",
      operation: "add-percent",
      value,
      ...(clauseScope ? { scope: clauseScope } : {}),
    });
    state.recognized.push(`damage-bonus:${value}%`);
  }

  const vulnerabilityPattern = /(?:失衡)?易伤(?:倍率)?(?:提升|增加|提高)(?:至|为)?([\d.]+)%/g;
  for (const match of text.matchAll(vulnerabilityPattern)) {
    const value = Number(match[1]);
    if (!Number.isFinite(value)) continue;
    state.effects.push({
      kind: "vulnerability",
      operation: "add-percent",
      value,
    });
    state.recognized.push(`vulnerability:${value}%`);
  }
}

function parseDazeEffects(
  text: string,
  state: ParseState,
  scope: BuffScope | undefined,
): void {
  const pattern = /失衡值(?:提升|增加|提高|加成)(?:至|为)?([\d.]+)%/g;
  for (const match of text.matchAll(pattern)) {
    const value = Number(match[1]);
    state.effects.push({
      kind: "daze-bonus",
      operation: "add-percent",
      value,
      ...(scope ? { scope } : {}),
    });
    state.recognized.push(`daze-bonus:${value}%`);
  }
}

function parseDefenseEffects(
  text: string,
  state: ParseState,
  scope: BuffScope | undefined,
): void {
  for (const match of text.matchAll(/防御力降低([\d.]+)%/g)) {
    const value = Number(match[1]);
    state.effects.push({ kind: "def-shred", operation: "add-percent", value });
    state.recognized.push(`def-shred:${value}%`);
  }
  const defenseIgnorePatterns = [
    /无视(?:目标)?防御力([\d.]+)%/g,
    /无视(?:目标)?([\d.]+)%防御力/g,
  ];
  const defenseIgnoreValues = new Set<number>();
  for (const pattern of defenseIgnorePatterns) {
    for (const match of text.matchAll(pattern)) {
      const value = Number(match[1]);
      if (!Number.isFinite(value) || defenseIgnoreValues.has(value)) continue;
      defenseIgnoreValues.add(value);
      state.effects.push({
        kind: "def-ignore",
        operation: "add-percent",
        value,
        ...(scope ? { scope } : {}),
      });
      state.recognized.push(`def-ignore:${value}%`);
    }
  }
  const resistance = /((?:物理|火|冰|电|以太))属性伤害抗性降低([\d.]+)%/g;
  for (const match of text.matchAll(resistance)) {
    const element = ELEMENTS[match[1] ?? ""];
    if (!element) continue;
    const value = Number(match[2]);
    state.effects.push({
      kind: "resistance-shred",
      operation: "add-percent",
      value,
      scope: { elements: [element] },
    });
    state.recognized.push(`resistance-shred:${element}:${value}%`);
  }
  const resistanceIgnore = /无视(?:目标)?([\d.]+)%((?:物理|火|冰|电|以太))属性伤害抗性/g;
  for (const match of text.matchAll(resistanceIgnore)) {
    const element = ELEMENTS[match[2] ?? ""];
    if (!element) continue;
    const value = Number(match[1]);
    state.effects.push({
      kind: "resistance-ignore",
      operation: "add-percent",
      value,
      scope: { elements: [element] },
    });
    state.recognized.push(`resistance-ignore:${element}:${value}%`);
  }
}

function parseDamageInstanceEffects(
  text: string,
  state: ParseState,
  scope: BuffScope | undefined,
): void {
  const pattern = /(?:额外)?(?:造成|结算)(?:[一-龥·：]+)?([\d.]+)%攻击力的\[?((?:物理|火|冰|电|以太|烈霜)(?:属性)?)?伤害\]?/g;
  for (const match of text.matchAll(pattern)) {
    const value = Number(match[1]);
    if (!Number.isFinite(value)) continue;
    const elementText = match[2]?.replace("属性", "");
    const element = elementText === "烈霜" ? "ice" : elementText ? ELEMENTS[elementText] : undefined;
    state.effects.push({
      kind: "damage-instance",
      operation: "add",
      damageKind: "direct",
      value: { type: "source-stat", path: "self.atk", scale: value / 100 },
      ...(element ? { element } : {}),
      ...(scope ? { scope } : {}),
    });
    state.recognized.push(`damage-instance:atk:${value}%`);
  }
  const defensePattern = /(?:额外)?(?:造成|结算)(?:[一-龥·：]+)?([\d.]+)%防御力的(?:[^；。\n]+)?伤害/g;
  for (const match of text.matchAll(defensePattern)) {
    const value = Number(match[1]);
    if (!Number.isFinite(value)) continue;
    state.effects.push({
      kind: "damage-instance",
      operation: "add",
      damageKind: "direct",
      value: { type: "source-stat", path: "self.def", scale: value / 100 },
      ...(scope ? { scope } : {}),
    });
    state.recognized.push(`damage-instance:def:${value}%`);
  }
}

function parseRuleModifierEffects(
  text: string,
  state: ParseState,
  characterId: string,
): void {
  const match = text.match(
    /核心被动[^。；\n]*攻击力提升效果额外提升([\d.]+)%[^。；\n]*上限额外提升([\d.]+)点/,
  );
  if (!match) return;
  const scale = Number(match[1]);
  const cap = Number(match[2]);
  if (!Number.isFinite(scale) || !Number.isFinite(cap)) return;
  state.effects.push({
    kind: "rule-modifier",
    targetRuleId: `nanoka:character_${characterId}_core`,
    modifiers: [
      { field: "scale", operation: "add", value: scale / 100 },
      { field: "cap", operation: "add", value: cap },
    ],
  });
  state.recognized.push(`rule-modifier:core:scale+${scale}%:cap+${cap}`);
}

function parseShieldEffect(text: string, state: ParseState): void {
  const match = text.match(/自身([\d.]+)%初始(冲击力|攻击力)\+([\d.]+)点的护盾/);
  if (!match) return;
  const sourcePath = match[2] === "冲击力" ? "self.initialImpact" : "self.initialAtk";
  const value: BuffExpression = {
    type: "source-stat",
    path: sourcePath,
    scale: Number(match[1]) / 100,
    flat: Number(match[3]),
  };
  state.effects.push({ kind: "shield", operation: "add-flat", value });
  state.recognized.push(`shield:${sourcePath}`);
}

function parseScope(text: string, state: ParseState): BuffScope | undefined {
  const skillCategories = new Set<SkillCategory>();
  if (/\[普通攻击(?=[\]：])/.test(text)) skillCategories.add("basic");
  if (/\[(?:特殊技|强化特殊技)(?=[\]：])/.test(text)) skillCategories.add("special");
  if (/\[闪避反击(?=[\]：])/.test(text)) skillCategories.add("dodge");
  if (/\[连携技(?=[\]：])/.test(text)) skillCategories.add("chain");
  if (/\[终结技(?=[\]：])/.test(text)) skillCategories.add("ultimate");
  if (/\[支援技|\[快速支援|\[招架支援|\[支援攻击/.test(text)) skillCategories.add("assist");
  if (/\[冲刺攻击/.test(text)) skillCategories.add("dash");

  const elements = [...text.matchAll(/((?:物理|火|冰|电|以太))(?:属性)?伤害/g)]
    .map((match) => ELEMENTS[match[1] ?? ""])
    .filter((element): element is Element => element !== undefined);
  const uniqueElements = unique(elements);
  if (skillCategories.size === 0 && uniqueElements.length === 0) return undefined;
  return {
    ...(skillCategories.size > 0 ? { skillCategories: [...skillCategories] } : {}),
    ...(uniqueElements.length > 0 ? { elements: uniqueElements } : {}),
  };
}

function parseConditionAndTrigger(
  text: string,
  state: ParseState,
): { condition: BuffCondition; trigger?: BuffTrigger } {
  const conditions: BuffCondition[] = [];
  const teamConditions: BuffCondition[] = [];
  if (/处于失衡状态下|处于失衡状态的敌人/.test(text)) {
    conditions.push({ type: "state", target: "enemy", state: "stunned", equals: true });
    state.recognized.push("condition:enemy.stunned");
  }
  if (/未处于失衡状态下|未处于失衡状态的敌人/.test(text)) {
    conditions.push({ type: "state", target: "enemy", state: "stunned", equals: false });
    state.recognized.push("condition:not-enemy.stunned");
  }
  if (/与自身属性或阵营相同的角色/.test(text)) {
    teamConditions.push(
      { type: "team-match", relation: "element" },
      { type: "team-match", relation: "role" },
      { type: "team-match", relation: "camp" },
    );
    state.recognized.push("condition:team-match:element|role|camp");
  }
  if (/与自身阵营相同的角色/.test(text) && !/与自身属性或阵营相同的角色/.test(text)) {
    teamConditions.push({ type: "team-match", relation: "camp" });
    state.recognized.push("condition:team-match:camp");
  }
  const roleMatches = [...text.matchAll(/(?:存在|或(?:其他)?)\[([^\]]+)\]角色/g)]
    .map((match) => match[1])
    .filter((role): role is string => Boolean(role));
  for (const role of unique(roleMatches)) {
    teamConditions.push({ type: "team-role", role });
    state.recognized.push(`condition:team-role:${role}`);
  }
  if (/其他可发动\[招架支援\]的角色/.test(text)) {
    teamConditions.push({ type: "team-role", role: "防护" });
    state.recognized.push("condition:team-role:防护");
  }
  if (teamConditions.length > 0) {
    conditions.push({ type: "any", conditions: uniqueConditions(teamConditions) });
  }
  const enemyState = text.match(/(?:敌人|目标)处于\[([^\]]+)\](?:状态)?/) ??
    text.match(/处于\[([^\]]+)\]状态下的敌人/);
  if (enemyState?.[1]) {
    conditions.push({ type: "state", target: "enemy", state: enemyState[1], equals: true });
    state.recognized.push(`condition:enemy.${enemyState[1]}`);
  }
  const hp = text.match(/生命值低于([\d.]+)%/);
  if (hp?.[1]) {
    conditions.push({
      type: "compare",
      path: "self.hpPercent",
      operator: "less-than",
      value: Number(hp[1]),
    });
    state.recognized.push(`condition:self.hpPercent<${hp[1]}`);
  }
  const selfState = text.match(/(?:自身|装备者|进入)\[([^\]]+)\](?:状态)?(?:中|期间|后|时)/);
  if (selfState?.[1]) {
    conditions.push({ type: "state", target: "self", state: selfState[1], equals: true });
    state.recognized.push(`condition:self.${selfState[1]}`);
  }

  let trigger: BuffTrigger | undefined;
  if (/命中/.test(text)) trigger = "attack-hit";
  else if (/发动|触发|消耗/.test(text)) trigger = "skill-used";
  else if (/成为.*当前操作角色|进入战场|进入.*状态/.test(text)) trigger = "state-entered";
  if (trigger) state.recognized.push(`trigger:${trigger}`);

  if (conditions.length === 0) {
    return {
      condition: { type: "always" },
      ...(trigger ? { trigger } : {}),
    };
  }
  return {
    condition: conditions.length === 1
      ? conditions[0] as BuffCondition
      : { type: "all", conditions },
    ...(trigger ? { trigger } : {}),
  };
}

function parseDuration(text: string, state: ParseState): number | undefined {
  const values = [...text.matchAll(/持续([\d.]+)秒/g)].map((match) => Number(match[1]));
  const uniqueValues = unique(values);
  if (uniqueValues.length > 1) {
    state.issues.push(`原文包含多个持续时间：${uniqueValues.join("、")} 秒。`);
  }
  if (uniqueValues.length > 0) {
    state.recognized.push(`duration:${uniqueValues[0]}s`);
    return uniqueValues[0];
  }
  return undefined;
}

function parseStacks(text: string, state: ParseState): BuffRule["stacks"] | undefined {
  const maxMatch = text.match(/最多叠加([\d.]+)层|上限([\d.]+)层/);
  if (!maxMatch) return undefined;
  const max = Number(maxMatch[1] ?? maxMatch[2]);
  if (!Number.isInteger(max) || max < 1) return undefined;
  state.recognized.push(`stacks:0-${max}`);
  return { mode: "derived", min: 0, max, initial: 0 };
}

function parseTarget(text: string, state: ParseState): BuffTarget {
  if (/防御力降低|抗性降低|易伤(?:倍率)?(?:提升|增加|提高)|目标.*减益|对目标施加/.test(text)) return "enemy";
  if (/当前操作中的角色|当前操作角色|入场角色/.test(text)) {
    state.recognized.push("target:active-character");
    return "active-character";
  }
  if (/全队|所有单位|队伍角色/.test(text)) {
    state.recognized.push("target:all-allies");
    return "all-allies";
  }
  return "self";
}

function parseUnsupportedSemantics(text: string, state: ParseState, isPanel: boolean): void {
  if (/异常积蓄|异常积蓄效率|属性异常积蓄/.test(text)) {
    state.issues.push("涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。");
  }
  if (/能量(?:回复|恢复|消耗|点|不足|大于|小于|上限)|闪能|喧响值|呼噜能量|回复|恢复/.test(text) && !/能量(?:获得效率|自动回复)提升/.test(text)) {
    state.issues.push("涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。");
  }
  const supportedSkillFormula = /\{CAL:[\d.]+\+AvatarSkillLevel\(1\)\*[\d.]+,100,2\}%/.test(text);
  if (/无敌|抗打断|伤害倍率|视为发动|技能等级/.test(text) && !supportedSkillFormula) {
    state.issues.push("涉及无敌、抗打断、倍率改写、技能等级或技能归类，当前模型不能安全表达。");
  }
  if (/受到的伤害降低|伤害降低|施加的护盾值提升|护盾值提升/.test(text) && !/的护盾/.test(text)) {
    state.issues.push("涉及减伤或护盾量倍率，当前模型没有对应的通用效果。");
  }
  const supportedInitialAttackConversion = /攻击力提升[^。；\n]*?(?:[\d.]+%初始攻击力|初始攻击力的[\d.]+%)[^。；\n]*?(?:最高不超过|上限)[\d.]+点/.test(text);
  const supportedRuleModifier = /核心被动[^。；\n]*攻击力提升效果额外提升[\d.]+%[^。；\n]*上限额外提升[\d.]+点/.test(text);
  if (/根据|每1点|每降低|越低|超过|低于.*后|额外提升/.test(text) && !supportedInitialAttackConversion && !supportedSkillFormula && !supportedRuleModifier) {
    state.issues.push("涉及动态换算或分段条件，需要确认公式和边界。");
  }
  if (/刷新|重置|结束|消耗|下一次|本次|当前招式|每层效果单独/.test(text)) {
    state.issues.push("涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。");
  }
  if (/同名被动效果之间不可叠加/.test(text)) {
    state.issues.push("包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。");
  }
  if (/第[一二三四五六七八九十\d]+段后|之后|随后|前置|发动后/.test(text)) {
    state.issues.push("包含前置动作或事件顺序，当前条件树尚未表达完整的动作链。");
  }
  if (isPanel && /触发|发动|命中|持续/.test(text)) {
    state.issues.push("驱动盘 2 件套候选包含战斗条件，不能按战前面板永久属性处理。");
  }
}

function unique<T>(values: readonly T[]): T[] {
  return [...new Set(values)];
}

function uniqueConditions(values: readonly BuffCondition[]): BuffCondition[] {
  const seen = new Set<string>();
  return values.filter((value) => {
    const key = JSON.stringify(value);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
