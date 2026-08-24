import type { BuffRule, BuffSourceType } from "../../src/domain/model/buff.js";
import { DRIVE_DISC_2PC_RULES } from "./drive-disc-2pc.js";
import { NANOKA_REVIEWED_BATCH_001 } from "./nanoka-reviewed-batch-001.js";
import { NANOKA_REVIEWED_BATCH_002 } from "./nanoka-reviewed-batch-002.js";
import { NANOKA_REVIEWED_BATCH_003 } from "./nanoka-reviewed-batch-003.js";
import { NANOKA_REVIEWED_BATCH_004 } from "./nanoka-reviewed-batch-004.js";
import { NANOKA_REVIEWED_BATCH_005 } from "./nanoka-reviewed-batch-005.js";
import {
  NANOKA_COMPILED_AUTO_ACCEPTED_RULES,
  NANOKA_COMPILED_AUTO_ACCEPTED_VERSION,
} from "./nanoka-compiled-auto.js";
import { NANOKA_EQUIPMENT_REVIEWED_RULES } from "./nanoka-equipment-reviewed-001.js";
import { NANOKA_EQUIPMENT_REVIEWED_BATCH_002 } from "./nanoka-equipment-reviewed-002.js";
import { TEAM_DAMAGE_REVIEWED_RULES } from "./team-damage-reviewed-001.js";

/**
 * 当前静态规则注册表对应的 Nanoka 数据版本。
 *
 * 这里是“已经人工审查并允许进入计算”的规则集合，不是 Nanoka 的原始
 * 解析结果。原始候选和未确认条目仍保留在 data/compiled 中，避免把未审查
 * 的文本误当成可计算规则。
 */
export const REVIEWED_BUFF_REGISTRY_VERSION = NANOKA_COMPILED_AUTO_ACCEPTED_VERSION;

function uniqueRules(rules: readonly BuffRule[]): readonly BuffRule[] {
  const byId = new Map<string, BuffRule>();
  for (const rule of rules) {
    const previous = byId.get(rule.id);
    if (previous !== undefined) {
      throw new Error(`重复的已审查 BuffRule id：${rule.id}`);
    }
    byId.set(rule.id, rule);
  }
  return [...byId.values()];
}

function rulesOfType(
  rules: readonly BuffRule[],
  type: BuffSourceType,
): readonly BuffRule[] {
  return rules.filter((rule) => rule.source.type === type);
}

const reviewedNanokaCharacterRules: readonly BuffRule[] = [
  ...NANOKA_REVIEWED_BATCH_001,
  ...NANOKA_REVIEWED_BATCH_002,
  ...NANOKA_REVIEWED_BATCH_003,
  ...NANOKA_REVIEWED_BATCH_004,
  ...NANOKA_REVIEWED_BATCH_005,
];

const reviewedEquipmentOverrideKeys = new Set(
  NANOKA_EQUIPMENT_REVIEWED_BATCH_002.map(semanticRuleKey),
);
const reviewedNanokaEquipmentRules: readonly BuffRule[] = [
  ...NANOKA_EQUIPMENT_REVIEWED_RULES.filter(
    (rule) => !reviewedEquipmentOverrideKeys.has(semanticRuleKey(rule)),
  ),
  ...NANOKA_EQUIPMENT_REVIEWED_BATCH_002,
];

const reviewedTeamRulesByType = (type: BuffSourceType): readonly BuffRule[] =>
  rulesOfType(TEAM_DAMAGE_REVIEWED_RULES, type);

const reviewedNanokaEquipmentRulesByType = (type: BuffSourceType): readonly BuffRule[] =>
  rulesOfType(reviewedNanokaEquipmentRules, type);

const reviewedDriveDiscTwoPieceRules: readonly BuffRule[] = Object.values(
  DRIVE_DISC_2PC_RULES,
).flat();

function normalizeNanokaSemanticKey(key: string | undefined): string | undefined {
  if (key === undefined) return undefined;
  // Nanoka 会把同一个核心被动的不同等级拆成不同数字 ID；它们在
  // 审查层属于同一个语义组。这里仅用于“人工审查覆盖自动候选”匹配，
  // 不会合并自动规则本身，因此没有人工覆盖时仍保留所有等级数据。
  const passive = key.match(/^character:([^:]+):passive:\d+:(\d+)$/);
  if (passive) return `character:${passive[1]}:passive:*:${passive[2]}`;
  const equipment = key.match(/^equipment:([^:]+):(desc2|desc4|2pc|4pc)$/);
  if (equipment) {
    const pieceKey = equipment[2] ?? "";
    const piece = pieceKey.endsWith("2") ? "2pc" : "4pc";
    return `equipment:${equipment[1]}:${piece}`;
  }
  return key;
}

function semanticRuleKey(rule: BuffRule): string {
  const key = normalizeNanokaSemanticKey(rule.source.key);
  return [rule.source.type, rule.source.id, key ?? rule.id].join(":");
}

const explicitlyReviewedSemanticKeys = new Set(
  [
    ...reviewedNanokaCharacterRules,
    ...TEAM_DAMAGE_REVIEWED_RULES,
    ...NANOKA_EQUIPMENT_REVIEWED_RULES,
    ...NANOKA_EQUIPMENT_REVIEWED_BATCH_002,
    ...reviewedDriveDiscTwoPieceRules,
  ].map(semanticRuleKey),
);

const compiledAutoAcceptedRules = NANOKA_COMPILED_AUTO_ACCEPTED_RULES.filter(
  (rule) => !explicitlyReviewedSemanticKeys.has(semanticRuleKey(rule)),
);

/** 已确认的角色 Buff：Nanoka 三批规则 + 当前回归场景中已确认的角色规则。 */
export const REVIEWED_CHARACTER_BUFF_RULES: readonly BuffRule[] = uniqueRules([
  ...reviewedNanokaCharacterRules,
  ...reviewedTeamRulesByType("character"),
  ...compiledAutoAcceptedRules.filter((rule) => rule.source.type === "character"),
]);

/** 已确认的音擎 Buff。音擎突破次数不作为规则字段；这里只读取精炼等级。 */
export const REVIEWED_WEAPON_BUFF_RULES: readonly BuffRule[] = uniqueRules([
  ...reviewedTeamRulesByType("weapon"),
  ...reviewedNanokaEquipmentRulesByType("weapon"),
  ...compiledAutoAcceptedRules.filter((rule) => rule.source.type === "weapon"),
]);

/** 已确认的驱动盘 Buff：2 件套和当前已审查的 4 件套规则。 */
export const REVIEWED_DRIVE_DISC_BUFF_RULES: readonly BuffRule[] = uniqueRules([
  ...reviewedDriveDiscTwoPieceRules,
  ...reviewedTeamRulesByType("drive-disc-set"),
  ...reviewedNanokaEquipmentRulesByType("drive-disc-set"),
  ...compiledAutoAcceptedRules.filter((rule) => rule.source.type === "drive-disc-set"),
]);

/** 计算引擎默认消费的全部已审查规则。 */
export const REVIEWED_BUFF_RULES: readonly BuffRule[] = uniqueRules([
  // 这里的顺序只用于稳定输出；动态面板表达式由解析器的统一收敛阶段求值，
  // 不依赖音擎规则必须排在角色规则之前。
  ...reviewedNanokaCharacterRules,
  ...TEAM_DAMAGE_REVIEWED_RULES,
  ...reviewedNanokaEquipmentRules,
  ...reviewedDriveDiscTwoPieceRules,
  ...compiledAutoAcceptedRules,
]);

export const REVIEWED_BUFF_RULES_BY_ID: Readonly<Record<string, BuffRule>> =
  Object.fromEntries(REVIEWED_BUFF_RULES.map((rule) => [rule.id, rule]));
