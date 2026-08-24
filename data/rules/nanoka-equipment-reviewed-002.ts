import type { BuffCondition, BuffEffect, BuffRule } from "../../src/domain/model/buff.js";

const VERSION = "3.2.1+17934514";
const ROOT = `https://static.nanoka.cc/zzz/${VERSION}/zh`;

function source(type: "weapon" | "drive-disc-set", id: string, label: string, key: string) {
  return {
    type,
    id,
    label,
    provider: "nanoka" as const,
    version: VERSION,
    url: `${ROOT}/${type === "weapon" ? "weapon" : "equipment"}/${id}.json`,
    key,
  };
}

function weaponReductionRule(
  refinement: number,
  value: number,
): BuffRule {
  return {
    schemaVersion: 1,
    id: `nanoka:weapon_12014_talent_${refinement}_damage_taken_reduction`,
    source: source("weapon", "12014", "「恒等式」-变格｜特殊声景", `weapon:12014:talent:${refinement}`),
    status: "verified",
    target: "enemy",
    phase: "combat",
    timing: "on-trigger",
    trigger: "damage-taken",
    weaponRefinement: refinement,
    durationSeconds: 12,
    exclusiveGroup: "weapon:12014:damage-taken-reduction",
    condition: { type: "always" },
    effects: [{ kind: "damage-taken-reduction", operation: "add-percent", value }],
    rawDescription: "受到敌方攻击时，攻击者造成的伤害降低" + `${value}%` + "，持续12秒。",
    notes: "按用户审查结论接收；这是受击触发的敌方输出减伤，不参与当前角色对敌人的输出伤害计算。",
  };
}

const weapon13016Condition: BuffCondition = {
  type: "compare",
  path: "self.hpPercent",
  operator: "greater-than-or-equal",
  value: 50,
};

function weapon13016Rule(
  refinement: number,
  damageReduction: number,
  statusReduction: number,
): BuffRule {
  const effects: BuffEffect[] = [
    { kind: "damage-taken-reduction", operation: "add-percent", value: damageReduction },
    { kind: "status-value-reduction", operation: "add-percent", status: "秽息浸染", value: statusReduction },
  ];
  return {
    schemaVersion: 1,
    id: `nanoka:weapon_13016_talent_${refinement}_damage_taken_reduction`,
    source: source("weapon", "13016", "光影刻刀｜胶片防护", `weapon:13016:talent:${refinement}`),
    status: "verified",
    target: "all-allies",
    phase: "combat",
    timing: "permanent",
    weaponRefinement: refinement,
    exclusiveGroup: "weapon:13016:team-protection",
    condition: weapon13016Condition,
    effects,
    rawDescription: "队伍中角色生命值大于等于50%，受到的伤害降低" + `${damageReduction}%` +
      "，受到的[秽息浸染]值降低" + `${statusReduction}%` + "，该效果全队唯一。",
    notes: "按用户审查结论接收；生命值条件由战斗状态提供，减伤和状态值降低不参与当前角色输出伤害计算。",
  };
}

function weapon14133Rule(
  refinement: number,
  proficiencyPerStack: number,
  buildupEfficiency: number,
): BuffRule {
  return {
    schemaVersion: 1,
    id: `nanoka:weapon_14133_talent_${refinement}_proficiency_stacks`,
    source: source("weapon", "14133", "飞鸟星梦｜银刺幽羽", `weapon:14133:talent:${refinement}`),
    status: "verified",
    target: "self",
    phase: "combat",
    timing: "on-trigger",
    trigger: "attack-hit",
    weaponRefinement: refinement,
    durationSeconds: 5,
    refreshPolicy: "refresh-duration",
    condition: { type: "always" },
    stacks: { mode: "derived", min: 0, max: 6, initial: 0 },
    effects: [{
      kind: "stat",
      stat: "anomalyProficiency",
      operation: "add-flat",
      value: { type: "per-stack", base: 0, perStack: proficiencyPerStack },
    }],
    rawDescription: `属性异常积蓄效率提升${buildupEfficiency}%；装备者造成以太伤害时，自身异常精通每层提升${proficiencyPerStack}点，持续5秒，最多叠加6层。`,
    notes: "修正自动装备规则把每层数值误当成固定总值的问题；静态满Buff计算按6层处理，积蓄效率不进入伤害数值。",
  };
}

export const NANOKA_EQUIPMENT_REVIEWED_BATCH_002: readonly BuffRule[] = [
  {
    schemaVersion: 1,
    id: "nanoka:equipment_31300_desc4_anomaly_buildup_resistance_shred",
    source: source("drive-disc-set", "31300", "自由蓝调｜4件套", "equipment:31300:desc4"),
    status: "verified",
    target: "enemy",
    phase: "combat",
    timing: "on-trigger",
    trigger: "attack-hit",
    durationSeconds: 8,
    exclusiveGroup: "equipment:31300:element-anomaly-resistance",
    condition: { type: "always" },
    effects: [{
      kind: "anomaly-buildup-resistance-shred",
      operation: "add-percent",
      value: 20,
      matchingSourceElement: true,
    }],
    rawDescription: "强化特殊技命中敌人时，根据装备者的属性类型，使目标对应属性异常积蓄抗性降低20%，持续8秒，相同属性类型的效果不可叠加。",
    notes: "按用户审查结论接收；对应属性由装备者元素决定，异常积蓄抗性计算尚未接入当前输出伤害引擎。",
  },
  {
    schemaVersion: 1,
    id: "nanoka:equipment_31500_desc4_damage_taken_reduction",
    source: source("drive-disc-set", "31500", "灵魂摇滚｜4件套", "equipment:31500:desc4"),
    status: "verified",
    target: "self",
    phase: "combat",
    timing: "on-trigger",
    trigger: "damage-taken",
    durationSeconds: 2.5,
    exclusiveGroup: "equipment:31500:damage-taken-reduction",
    condition: { type: "always" },
    effects: [{ kind: "damage-taken-reduction", operation: "add-percent", value: 40 }],
    rawDescription: "受到敌方攻击并损失生命值时，装备者受到的伤害降低40%，持续2.5秒，15秒内最多触发一次。",
    notes: "按用户审查结论接收；15秒内最多触发一次由战斗事件层控制。",
  },
  weaponReductionRule(1, 6),
  weaponReductionRule(2, 7),
  weaponReductionRule(3, 8),
  weaponReductionRule(4, 9),
  weaponReductionRule(5, 10),
  weapon13016Rule(1, 7.5, 10),
  weapon13016Rule(2, 8.6, 11.5),
  weapon13016Rule(3, 9.7, 13),
  weapon13016Rule(4, 10.8, 14.5),
  weapon13016Rule(5, 12, 16),
  weapon14133Rule(1, 20, 40),
  weapon14133Rule(2, 23, 46),
  weapon14133Rule(3, 26, 52),
  weapon14133Rule(4, 29, 58),
  weapon14133Rule(5, 32, 64),
];
