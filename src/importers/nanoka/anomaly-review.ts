import type { BuffRule } from "../../domain/model/buff.js";
import {
  nanokaReviewGroupKey,
  selectNanokaActionableReviewBatch,
  type NanokaParsedBuff,
} from "./parse-buff.js";

/**
 * 当前异常伤害模型真正会消费的 Nanoka 角色 Buff 语义。
 *
 * 这里不是新的解析器，也不会把条目自动写入规则注册表；它只负责从
 * “尚未人工确认”的角色候选中筛出值得继续审查的部分。技能动作文本、
 * 资源/能量、纯异常积蓄和纯直伤不会进入这张人工队列。
 */
const ANOMALY_DAMAGE_WORDS =
  /异常(?:伤害|效果强度|暴击)|属性异常(?:伤害|效果)|(?:触发|造成|结算|施加|处于|被)[^。；\n]{0,10}强击|强击(?:伤害|效果|暴击)|异放|紊乱|乱流|(?:风化|灼烧|感电|侵蚀|霜寒|冻结|碎冰)(?:伤害|效果|状态|异常|结算|触发|持续|剩余|倍率|施加|消除)|极性/;
const DAMAGE_ZONE_WORDS =
  /伤害提升|伤害提高|伤害增加|伤害加成|属性伤害提升|属性伤害提高|造成的伤害(?:提升|提高|增加|加成)|攻击力(?:提升|提高|增加|加成)|(?:提升|提高|增加|加成)[^。；\n]{0,25}攻击力(?:和|、|，|。|；|$)/;
const ANOMALY_STAT_WORDS =
  /(?:提升|提高|增加|加成)[^。；\n]{0,20}异常(?:精通|掌控)|异常(?:精通|掌控)(?:提升|提高|增加|加成)/;
const MONSTER_ZONE_WORDS =
  /抗性降低|抗性减少|抗性无视|无视.*抗性|防御力降低|防御力减少|防御力无视|无视.*防御|易伤/;
const DURATION_WORDS = /持续时间延长|持续时间增加|剩余时间|持续时间/;
const OUT_OF_SCOPE_ONLY_WORDS =
  /能量|闪能|喧响值|呼噜能量|支援点数|护盾|抗打断|无敌|异常积蓄|积蓄效率|积蓄值|回复|恢复|治疗|资源/;
const PURE_CRIT_WORDS = /暴击率|暴击伤害/;
const PURE_DAZE_WORDS = /失衡值|冲击力/;
const DIRECT_DAMAGE_WORDS = /额外造成|额外触发|造成.*属性伤害|造成.*伤害/;

export interface NanokaAnomalyReviewSelection {
  /** 所有尚未处理、且与当前异常模型相关的原始条目。 */
  candidates: readonly NanokaParsedBuff[];
  /** 剔除已写入规则/已作出结论后的待审条目。 */
  remaining: readonly NanokaParsedBuff[];
  /** 按现有角色被动等级/同语义去重后的本批代表条目。 */
  selected: readonly NanokaParsedBuff[];
  /** 候选中因已有规则或决定被剔除的原始条目数。 */
  excludedReviewed: number;
  /** 剩余待审条目的语义组数量。 */
  remainingGroups: number;
}

export function isNanokaAnomalyDamageRelevant(item: NanokaParsedBuff): boolean {
  if (!item.key.startsWith("character:")) return false;

  const text = item.displayText;
  const hasAnomalyLabel = ANOMALY_DAMAGE_WORDS.test(text);
  const hasAnomalyStatText = ANOMALY_STAT_WORDS.test(text);
  const hasAnomalyText = hasAnomalyLabel || hasAnomalyStatText;
  const hasDamageZoneText = DAMAGE_ZONE_WORDS.test(text);
  const hasMonsterZoneText = MONSTER_ZONE_WORDS.test(text);
  const hasDurationText = DURATION_WORDS.test(text) && hasAnomalyText;
  const effects = item.rules ?? (item.rule ? [item.rule] : []);
  const effectKinds = new Set(effects.flatMap((rule) => rule.effects.map((effect) => effect.kind)));
  const hasGlobalMonsterDebuff = effectKinds.has("def-shred") || effectKinds.has("resistance-shred");
  const hasOnlyIgnoreText = /无视.*(?:抗性|防御)|(?:抗性|防御).*无视/.test(text) &&
    !hasGlobalMonsterDebuff && !hasAnomalyLabel && !hasDamageZoneText;
  const hasAnomalyDerivedDamage = hasAnomalyLabel && effects.some((rule) =>
    rule.effects.some((effect) =>
      effect.kind === "derived-damage" || effect.kind === "damage-instance" || effect.kind === "damage-conversion",
    ),
  );
  const hasScopedDamageOnlyText =
    /(?:余烬|追加攻击|断离|普通攻击[:：]|强化特殊技[:：]|特殊技[:：]|终结技[:：]|连携技[:：]|技能|招式)[^。；\n]{0,30}伤害(?:提升|提高|增加|加成)/.test(text) &&
    !hasAnomalyLabel;
  const hasAnomalyStat = effects.some((rule) =>
    rule.effects.some((effect) =>
      effect.kind === "stat" &&
      (effect.stat === "atk" || effect.stat === "anomalyProficiency" || effect.stat === "anomalyMastery"),
    ),
  ) || hasAnomalyStatText;
  // 异常积蓄、资源和回复本身不进入异常伤害结算；若同一原文同时挂了
  // 减抗/减防/伤害区，则保留，因为后者会改变实际伤害。
  if (OUT_OF_SCOPE_ONLY_WORDS.test(text) &&
      !hasAnomalyText && !hasDamageZoneText && !hasMonsterZoneText && !hasAnomalyStat) {
    return false;
  }

  // 普通暴击率/暴击伤害不等于异常暴击区；当前只有明确绑定异常类别的
  // 暴击语义才需要审查。
  if (PURE_CRIT_WORDS.test(text) && !hasAnomalyLabel && !hasAnomalyDerivedDamage) {
    return false;
  }

  // 当前异常公式中的无视防御/无视抗性必须与伤害标签匹配。没有异常标签、
  // 只是“追加攻击/自身攻击”作用域的 ignore，不会覆盖异常、异放、紊乱
  // 或乱流；真正的全队 Debuff 则由 def-shred/resistance-shred 保留。
  if (hasOnlyIgnoreText) return false;

  // “余烬/追加攻击/某个招式的伤害提升”是该直伤实例自己的区间，不能
  // 因为出现“伤害提升”四个字就当成异常效果强度的普通增伤区。
  if (hasScopedDamageOnlyText && !hasGlobalMonsterDebuff && !hasAnomalyStat) return false;

  // 只有失衡值/冲击力的规则不影响本轮异常伤害；失衡易伤或同时带伤害
  // 区的条目仍然保留。
  if (PURE_DAZE_WORDS.test(text) && !hasDamageZoneText && !hasMonsterZoneText && !hasAnomalyLabel) {
    return false;
  }

  // 技能文本中“造成一次普通属性伤害”是动作描述，不是异常派生伤害。
  // 明确写出异常类别，或解析成派生/实例伤害的条目才保留。
  if (DIRECT_DAMAGE_WORDS.test(text) && !hasAnomalyLabel && !hasAnomalyDerivedDamage && !hasMonsterZoneText) {
    return false;
  }

  return hasAnomalyLabel || hasDamageZoneText || hasMonsterZoneText || hasDurationText || hasAnomalyStat || hasAnomalyDerivedDamage;
}

export function selectNanokaAnomalyReviewQueue(
  parsed: readonly NanokaParsedBuff[],
  reviewedGroups: ReadonlySet<string>,
  size: number,
): NanokaAnomalyReviewSelection {
  const candidates = parsed.filter(isNanokaAnomalyDamageRelevant);
  const pending = candidates.filter((item) => item.disposition === "needs-review");
  const remaining = pending.filter((item) => !reviewedGroups.has(nanokaReviewGroupKey(item)));
  const selected = selectNanokaActionableReviewBatch(remaining, size);
  return {
    candidates,
    remaining,
    selected,
    excludedReviewed: pending.length - remaining.length,
    remainingGroups: new Set(remaining.map((item) => nanokaReviewGroupKey(item))).size,
  };
}

export function reviewedNanokaRuleGroup(rule: BuffRule): string | null {
  const key = rule.source.key;
  if (!key) return null;
  return nanokaReviewGroupKey({
    key,
    displayText: rule.rawDescription.replace(/<[^>]+>/g, ""),
  });
}

export function renderNanokaAnomalyReviewQueue(
  version: string,
  parsed: readonly NanokaParsedBuff[],
  selection: NanokaAnomalyReviewSelection,
): string {
  const lines = [
    "# Nanoka 异常伤害专用复审队列",
    "",
    "> 本清单只针对当前异常伤害模型仍未确认的角色 Buff。已写入规则、已作出忽略/提升结论的语义组不会重复出现。",
    "> 本批仍只需要确认：数值、作用对象、触发条件、持续/刷新/叠层语义，以及它属于异常、异放、紊乱、乱流还是普通伤害区。",
    "",
    `- 数据版本：\`${version}\``,
    `- 角色候选原始条目：${parsed.filter((item) => item.key.startsWith("character:")).length}`,
    `- 与当前异常模型相关的候选：${selection.candidates.length}`,
    `- 其中尚未确认：${selection.candidates.filter((item) => item.disposition === "needs-review").length}`,
    `- 已由规则/决定处理并剔除：${selection.excludedReviewed}`,
    `- 当前剩余待审原始条目：${selection.remaining.length}`,
    `- 当前剩余待审语义组：${selection.remainingGroups}`,
    `- 本批展示：${selection.selected.length}`,
    "",
    "## 本次复筛采用的范围",
    "",
    "- 保留：异常效果强度相关的攻击力/异常精通/异常掌控、普通/属性/异常/异放/紊乱/乱流增伤、异常暴击、异放/紊乱/乱流派生伤害、持续时间，以及敌方防御/抗性/易伤。",
    "- 后续按上下文区分：挂在敌人身上的减防/减抗 Debuff，与只对当前攻击标签生效的防御/抗性无视。",
    "- 暂不列入：纯能量/资源/护盾/治疗/异常积蓄、纯失衡值，以及没有异常标签的普通直伤动作文本和普通暴击文本。",
    "- 紊乱默认按满持续时间处理；只有明确影响紊乱来源者、触发者或持续时间的语义才进入队列。",
    "",
    "## 审查批次 001",
    "",
  ];

  for (const item of selection.selected) {
    const group = nanokaReviewGroupKey(item);
    const members = selection.remaining.filter((candidate) => nanokaReviewGroupKey(candidate) === group);
    lines.push(
      `### ${item.key}`,
      "",
      `- 语义组：\`${group}\``,
      `- 覆盖待审条目：${members.length} 条`,
      `- 覆盖 key：${members.map((member) => member.key).join("、")}`,
      `- 来源：${item.sourceUrl}`,
      `- 机器识别：${item.recognized.join("、") || "无"}`,
      `- 机器提示：${item.reviewReasons.join("；") || item.issues.join("；") || "需要人工确认异常语义和作用域"}`,
      "- Nanoka 原文：",
      "```text",
      item.rawText,
      "```",
      "- 当前解析候选：",
      "```json",
      JSON.stringify(item.rules && item.rules.length > 1 ? item.rules : item.rule, null, 2),
      "```",
      "- 审查结论：",
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}
