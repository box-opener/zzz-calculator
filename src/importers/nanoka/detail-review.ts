import {
  buildNanokaDetailUrl,
  type NanokaDetailKind,
  type NanokaDetailSnapshot,
  type NanokaManifest,
} from "./client.js";

export type NanokaBuffReviewSection =
  | "character-skill"
  | "character-passive"
  | "character-talent"
  | "weapon-talent"
  | "equipment";

export interface NanokaBuffReviewEntry {
  key: string;
  kind: NanokaDetailKind;
  id: string;
  name: string;
  section: NanokaBuffReviewSection;
  level?: number;
  title?: string;
  rawText: string;
  displayText: string;
  sourceUrl: string;
}

const BUFF_CANDIDATE_WORDS = [
  "提升",
  "增加",
  "降低",
  "回复",
  "恢复",
  "获得",
  "提供",
  "叠加",
  "层",
  "持续",
  "触发",
  "消耗",
  "护盾",
  "抗性",
  "穿透",
  "伤害",
  "失衡值",
  "异常掌控",
  "异常精通",
  "暴击",
  "攻击力",
  "防御力",
  "能量",
];

/**
 * 从 Nanoka 详情 JSON 提取“待人工确认”的原文候选。
 *
 * 这里故意不生成 BuffRule：提取器只负责保留官方文本和来源，
 * 触发条件、作用对象、持续时间和叠层语义必须在审查后再写入规则。
 */
export function extractNanokaBuffReviewEntries(
  snapshot: NanokaDetailSnapshot,
): NanokaBuffReviewEntry[] {
  const entries: NanokaBuffReviewEntry[] = [];
  for (const [id, detail] of Object.entries(snapshot.details.character)) {
    collectCharacterEntries(entries, snapshot, id, detail);
  }
  for (const [id, detail] of Object.entries(snapshot.details.weapon)) {
    collectWeaponEntries(entries, snapshot, id, detail);
  }
  for (const [id, detail] of Object.entries(snapshot.details.equipment)) {
    collectEquipmentEntries(entries, snapshot, id, detail);
  }
  return entries.sort(compareEntries);
}

export function renderNanokaBuffReview(
  snapshot: NanokaDetailSnapshot,
  entries = extractNanokaBuffReviewEntries(snapshot),
): string {
  const counts = countBySection(entries);
  const lines = [
    "# Nanoka 官方 Buff 原文审查清单",
    "",
    "> 这是从 Nanoka 详情 JSON 直接生成的候选清单。旧版 `dict/`、`app.js` 和历史审查单不参与生成。",
    "> 本文件中的“原文”保留了 Nanoka 的颜色和图标标记；“阅读文本”只移除了显示标记，不能视为重新措辞。",
    "",
    `- 来源：https://zzz.nanoka.cc/`,
    `- 数据版本：\`${snapshot.version}\``,
    `- 语言：\`${snapshot.locale}\``,
    `- 生成时间：${snapshot.fetchedAt}`,
    `- 候选条目：${entries.length}`,
    "",
    "## 数量",
    "",
    ...Object.entries(counts).map(([section, count]) => `- ${section}：${count}`),
    "",
    "## 审查约定",
    "",
    "1. 先确认原文是否对应当前游戏版本，再确认触发事件、作用对象、持续时间、叠层和消费规则。",
    "2. 只把已确认的条目迁移为 `BuffRule`；未确认条目保持 `raw-only`，不进入计算。",
    "3. 审查结论必须引用条目的来源 URL 和 `key`，不能只引用角色名或旧规则 ID。",
    "",
  ];

  let previousGroup = "";
  for (const entry of entries) {
    const group = `${entry.section}:${entry.id}`;
    if (group !== previousGroup) {
      lines.push(`## ${entry.section}｜${entry.id}｜${entry.name}`, "");
      previousGroup = group;
    }
    lines.push(
      `### ${entry.key}`,
      "",
      `- 来源：${entry.sourceUrl}`,
      `- 层级：${entry.level === undefined ? "固定文本" : entry.level}`,
      `- 标题：${entry.title ?? "无"}`,
      "- 原文：",
      "```text",
      entry.rawText,
      "```",
      "- 阅读文本：",
      "```text",
      entry.displayText,
      "```",
      "- 审查结论：待确认",
      "- 备注：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

/**
 * 为人工审查挑选去重后的代表条目：被动/音擎只保留当前最高等级，
 * 避免首批审查被同一条规则的 1~7 级数值占满；全量报告仍保留所有等级。
 */
export function selectNanokaReviewBatch(
  entries: readonly NanokaBuffReviewEntry[],
  size: number,
): NanokaBuffReviewEntry[] {
  if (!Number.isInteger(size) || size < 1) {
    throw new Error(`Nanoka 审查批次大小无效：${size}`);
  }
  const selected = new Map<string, NanokaBuffReviewEntry>();
  for (const entry of entries) {
    const group = reviewGroupKey(entry);
    const current = selected.get(group);
    if (!current || (entry.level ?? 0) > (current.level ?? 0)) {
      selected.set(group, entry);
    }
  }
  return [...selected.values()]
    .sort(compareReviewPriority)
    .slice(0, size);
}

function collectCharacterEntries(
  entries: NanokaBuffReviewEntry[],
  snapshot: NanokaDetailSnapshot,
  id: string,
  detail: NanokaManifest,
): void {
  const name = stringValue(detail.name) ?? `角色 ${id}`;
  const sourceUrl = buildNanokaDetailUrl(snapshot.version, snapshot.locale, "character", id);
  const passive = recordValue(detail.passive);
  const levels = recordValue(passive?.level);
  if (levels) {
    for (const [levelKey, levelValue] of Object.entries(levels)) {
      const level = recordValue(levelValue);
      const names = stringArray(level?.name);
      const descriptions = stringArray(level?.desc);
      for (let index = 0; index < descriptions.length; index += 1) {
        const title = names[index] ?? names[0];
        addEntry(entries, {
          key: `character:${id}:passive:${levelKey}:${index}`,
          kind: "character",
          id,
          name,
          section: "character-passive",
          level: numberValue(level?.level) ?? Number(levelKey),
          ...(title ? { title } : {}),
          rawText: descriptions[index] as string,
          sourceUrl,
        });
      }
    }
  }

  const talents = recordValue(detail.talent);
  if (talents) {
    for (const [talentKey, talentValue] of Object.entries(talents)) {
      const talent = recordValue(talentValue);
      const text = stringValue(talent?.desc);
      if (text) {
        const title = stringValue(talent?.name);
        addEntry(entries, {
          key: `character:${id}:talent:${talentKey}`,
          kind: "character",
          id,
          name,
          section: "character-talent",
          level: numberValue(talent?.level) ?? Number(talentKey),
          ...(title ? { title } : {}),
          rawText: text,
          sourceUrl,
        });
      }
    }
  }

  const skills = recordValue(detail.skill);
  if (skills) {
    for (const [skillKey, skillValue] of Object.entries(skills)) {
      const skill = recordValue(skillValue);
      const descriptions = skill?.description;
      if (!Array.isArray(descriptions)) continue;
      for (const [index, descriptionValue] of descriptions.entries()) {
        const description = recordValue(descriptionValue);
        const text = stringValue(description?.desc);
        if (!text || !looksLikeBuffCandidate(text)) continue;
        const title = stringValue(description?.name);
        addEntry(entries, {
          key: `character:${id}:skill:${skillKey}:${index}`,
          kind: "character",
          id,
          name,
          section: "character-skill",
          ...(title ? { title } : {}),
          rawText: text,
          sourceUrl,
        });
      }
    }
  }
}

function collectWeaponEntries(
  entries: NanokaBuffReviewEntry[],
  snapshot: NanokaDetailSnapshot,
  id: string,
  detail: NanokaManifest,
): void {
  const name = stringValue(detail.name) ?? `音擎 ${id}`;
  const sourceUrl = buildNanokaDetailUrl(snapshot.version, snapshot.locale, "weapon", id);
  const talents = recordValue(detail.talents);
  if (!talents) return;
  for (const [levelKey, talentValue] of Object.entries(talents)) {
    const talent = recordValue(talentValue);
    const text = stringValue(talent?.desc);
    if (!text) continue;
    const title = stringValue(talent?.name);
    addEntry(entries, {
      key: `weapon:${id}:talent:${levelKey}`,
      kind: "weapon",
      id,
      name,
      section: "weapon-talent",
      level: Number(levelKey),
      ...(title ? { title } : {}),
      rawText: text,
      sourceUrl,
    });
  }
}

function collectEquipmentEntries(
  entries: NanokaBuffReviewEntry[],
  snapshot: NanokaDetailSnapshot,
  id: string,
  detail: NanokaManifest,
): void {
  const name = stringValue(detail.name) ?? `驱动盘 ${id}`;
  const sourceUrl = buildNanokaDetailUrl(snapshot.version, snapshot.locale, "equipment", id);
  for (const field of ["desc2", "desc4"] as const) {
    const text = stringValue(detail[field]);
    if (!text) continue;
    addEntry(entries, {
      key: `equipment:${id}:${field}`,
      kind: "equipment",
      id,
      name,
      section: "equipment",
      title: field === "desc2" ? "2件套" : "4件套",
      rawText: text,
      sourceUrl,
    });
  }
}

function addEntry(
  entries: NanokaBuffReviewEntry[],
  entry: Omit<NanokaBuffReviewEntry, "displayText">,
): void {
  entries.push({
    ...entry,
    displayText: stripNanokaMarkup(entry.rawText),
  });
}

export function stripNanokaMarkup(text: string): string {
  return text
    .replace(/<color=[^>]*>/g, "")
    .replace(/<\/color>/g, "")
    .replace(/<IconMap:[^>]+>/g, "")
    .replace(/<[^>]+>/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n[ \t]+/g, "\n")
    .trim();
}

function looksLikeBuffCandidate(text: string): boolean {
  return BUFF_CANDIDATE_WORDS.some((word) => text.includes(word));
}

function countBySection(
  entries: readonly NanokaBuffReviewEntry[],
): Record<string, number> {
  return entries.reduce<Record<string, number>>((counts, entry) => {
    counts[entry.section] = (counts[entry.section] ?? 0) + 1;
    return counts;
  }, {});
}

function compareEntries(left: NanokaBuffReviewEntry, right: NanokaBuffReviewEntry): number {
  return left.section.localeCompare(right.section) ||
    Number(left.id) - Number(right.id) ||
    left.key.localeCompare(right.key);
}

function reviewGroupKey(entry: NanokaBuffReviewEntry): string {
  if (entry.section === "character-passive") {
    return entry.key.replace(/:passive:\d+:(\d+)$/, ":passive:*:$1");
  }
  if (entry.section === "weapon-talent") {
    return entry.key.replace(/:talent:\d+$/, ":talent:*");
  }
  return entry.key;
}

function compareReviewPriority(
  left: NanokaBuffReviewEntry,
  right: NanokaBuffReviewEntry,
): number {
  const priority: Record<NanokaBuffReviewSection, number> = {
    "character-passive": 0,
    "character-talent": 1,
    "weapon-talent": 2,
    equipment: 3,
    "character-skill": 4,
  };
  return priority[left.section] - priority[right.section] || compareEntries(left, right);
}

function recordValue(value: unknown): NanokaManifest | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as NanokaManifest)
    : undefined;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}
