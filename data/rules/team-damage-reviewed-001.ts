import type {
  BuffCondition,
  BuffEffect,
  BuffRule,
  BuffScope,
  BuffSourceType,
} from "../../src/domain/model/buff.js";
import { buildExtraAbilityActivationCondition } from "../../src/domain/engine/extra-ability-condition.js";

const VERSION = "3.2.1+17934514";
const CDN_ROOT = `https://static.nanoka.cc/zzz/${VERSION}/zh`;

function source(
  type: BuffSourceType,
  id: string,
  label: string,
  key: string,
) {
  const path = type === "character" ? "character" :
    type === "weapon" ? "weapon" : "equipment";
  return {
    type,
    id,
    label,
    provider: "nanoka" as const,
    version: VERSION,
    url: `${CDN_ROOT}/${path}/${id}.json`,
    key,
  };
}

function rule(input: {
  id: string;
  sourceType: BuffSourceType;
  sourceId: string;
  label: string;
  key: string;
  target: BuffRule["target"];
  timing: BuffRule["timing"];
  condition?: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  cinemaAtLeast?: number;
  equippedCountAtLeast?: number;
  trigger?: BuffRule["trigger"];
  notes?: string;
}): BuffRule {
  return {
    schemaVersion: 1,
    id: input.id,
    source: source(input.sourceType, input.sourceId, input.label, input.key),
    status: "verified",
    target: input.target,
    phase: "combat",
    timing: input.timing,
    condition: input.condition ?? { type: "always" },
    effects: input.effects,
    rawDescription: input.rawDescription,
    ...(input.cinemaAtLeast === undefined ? {} : { cinemaAtLeast: input.cinemaAtLeast }),
    ...(input.equippedCountAtLeast === undefined ? {} : { equippedCountAtLeast: input.equippedCountAtLeast }),
    ...(input.trigger === undefined ? {} : { trigger: input.trigger }),
    ...(input.notes === undefined ? {} : { notes: input.notes }),
  };
}

const scope = (value: BuffScope): BuffScope => value;
const aliceExtra = buildExtraAbilityActivationCondition("1401");
const yuzuhaExtra: BuffCondition = {
  type: "any",
  conditions: [
    { type: "team-role", role: "异常" },
    { type: "team-match", relation: "camp" },
  ],
};

const yuzuhaCoreAttackCap = {
  type: "lookup" as const,
  path: "self.coreLevel",
  values: [0, 600, 700, 800, 900, 1000, 1100, 1200],
};

const aliceWeaponMastery = rule({
  id: "nanoka:weapon_14140_anomaly_mastery",
  sourceType: "weapon",
  sourceId: "14140",
  label: "十方锻星｜异常掌控",
  key: "weapon:14140:refinement",
  target: "self",
  timing: "on-entry",
  effects: [{
    kind: "stat",
    stat: "anomalyMastery",
    operation: "add-flat",
    value: {
      type: "lookup",
      path: "self.weaponRefinement",
      values: [0, 60, 69, 78, 87, 96],
    },
  }],
  rawDescription: "装备者的异常掌控提升60/69/78/87/96点。",
  notes: "音擎精炼等级由玩家构筑读取；满拐场景激活进入战场效果。",
});

const aliceExtraProficiency = rule({
  id: "nanoka:character_1401_passive_extra_anomaly_proficiency",
  sourceType: "character",
  sourceId: "1401",
  label: "爱丽丝｜额外能力：寻奇猎幽",
  key: "character:1401:passive:1401507:1",
  target: "self",
  timing: "permanent",
  condition: aliceExtra,
  effects: [{
    kind: "stat",
    stat: "anomalyProficiency",
    operation: "add-flat",
    value: {
      type: "source-stat",
      path: "self.anomalyMastery",
      offset: 140,
      scale: 1.6,
    },
  }],
  rawDescription: "队伍中存在另一名异常或支援角色时触发；异常掌控每超过140点，提升1.6点异常精通。",
});

const aliceDefenseShred = rule({
  id: "nanoka:character_1401_talent_1_defense_shred",
  sourceType: "character",
  sourceId: "1401",
  label: "爱丽丝｜影画1：掌心的芫荽",
  key: "character:1401:talent:1",
  target: "enemy",
  timing: "on-trigger",
  trigger: "attack-hit",
  cinemaAtLeast: 1,
  effects: [{ kind: "def-shred", operation: "add-percent", value: 20 }],
  rawDescription: "爱丽丝触发强击时，目标的防御力降低20%，持续30秒。",
  notes: "这是敌方 Debuff，不附加伤害作用域。",
});

const aliceCinema2Anomaly = rule({
  id: "nanoka:character_1401_talent_2_damage_bonus",
  sourceType: "character",
  sourceId: "1401",
  label: "爱丽丝｜影画2：剑尖的鼠尾草",
  key: "character:1401:talent:2",
  target: "self",
  timing: "on-trigger",
  trigger: "attack-hit",
  cinemaAtLeast: 2,
  effects: [{
    kind: "damage-bonus",
    operation: "add-percent",
    value: 15,
    scope: scope({ damageKinds: ["assault"] }),
  }, {
    kind: "damage-bonus",
    operation: "add-percent",
    value: 15,
    scope: scope({ damageKinds: ["disorder"] }),
    disorderAttribution: "source",
  }],
  rawDescription: "全队角色造成的强击伤害提升15%；物理异常状态下的敌人被结算的紊乱伤害提升15%。",
});

const aliceDisorderMultiplier = rule({
  id: "nanoka:character_1401_core_disorder_multiplier",
  sourceType: "character",
  sourceId: "1401",
  label: "爱丽丝｜核心被动：剑心双虹",
  key: "character:1401:passive:1401507:0",
  target: "self",
  timing: "on-trigger",
  trigger: "attack-hit",
  effects: [{
    kind: "multiplier",
    operation: "add-percent",
    value: 180,
    scope: scope({ damageKinds: ["disorder"] }),
  }],
  rawDescription: "物理异常状态下的敌人被触发紊乱效果时，每有1秒物理异常状态剩余时间，紊乱效果的伤害倍率提升18%，最多提升180%。",
});

const aliceWeaponPhysical = rule({
  id: "nanoka:weapon_14140_physical_damage",
  sourceType: "weapon",
  sourceId: "14140",
  label: "十方锻星｜两层物理伤害提升",
  key: "weapon:14140:refinement",
  target: "self",
  timing: "on-entry",
  effects: [{
    kind: "damage-bonus",
    operation: "add-percent",
    value: {
      type: "lookup",
      path: "self.weaponRefinement",
      values: [0, 40, 46, 52, 58, 64],
    },
  }],
  rawDescription: "触发强击时，装备者造成的物理伤害提升20%/23%/26%/29%/32%，最多叠加2层；进入接战状态时立即获得2层。",
});

const aliceFangedDamage = rule({
  id: "nanoka:set_32600_4pc_damage",
  sourceType: "drive-disc-set",
  sourceId: "32600",
  label: "獠牙重金属｜四件套",
  key: "equipment:32600:4pc",
  target: "self",
  timing: "on-trigger",
  trigger: "attack-hit",
  equippedCountAtLeast: 4,
  effects: [{ kind: "damage-bonus", operation: "add-percent", value: 35 }],
  rawDescription: "物理属性异常状态下的敌人受到的伤害提升35%。",
});

const yuzuhaWishAttack = rule({
  id: "nanoka:character_1411_core_team_attack",
  sourceType: "character",
  sourceId: "1411",
  label: "柚叶｜核心被动：狸之愿攻击力",
  key: "character:1411:passive:1411049:0",
  target: "all-allies",
  timing: "on-trigger",
  trigger: "attack-hit",
  effects: [{
    kind: "stat",
    stat: "atk",
    operation: "add-flat",
    value: {
      type: "source-stat",
      path: "self.atk",
      scale: 0.4,
      cap: yuzuhaCoreAttackCap,
    },
  }],
  rawDescription: "狸之愿提供等同于柚叶40%初始攻击力的攻击力加成，数值随核心被动等级有上限。",
});

const yuzuhaWishDamage = rule({
  id: "nanoka:character_1411_core_team_damage",
  sourceType: "character",
  sourceId: "1411",
  label: "柚叶｜核心被动：狸之愿伤害提升",
  key: "character:1411:passive:1411049:0",
  target: "all-allies",
  timing: "on-trigger",
  trigger: "attack-hit",
  effects: [{ kind: "damage-bonus", operation: "add-percent", value: 15 }],
  rawDescription: "拥有狸之愿效果的角色造成的伤害提升15%，持续40秒。",
});

function yuzuhaExtraRule(
  id: string,
  scale: number,
  cap: number,
  cinemaAtLeast: number | undefined,
  condition: BuffCondition,
): BuffRule {
  return rule({
    id,
    sourceType: "character",
    sourceId: "1411",
    label: "柚叶｜额外能力：人多乐趣大",
    key: "character:1411:passive:1411049:1",
    target: "all-allies",
    timing: "on-trigger",
    trigger: "skill-used",
    condition,
    ...(cinemaAtLeast === undefined ? {} : { cinemaAtLeast }),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: { type: "source-stat", path: "self.anomalyMastery", offset: 100, scale, cap },
      scope: scope({ damageKinds: ["assault", "anomaly"] }),
    }, {
      kind: "damage-bonus",
      operation: "add-percent",
      value: { type: "source-stat", path: "self.anomalyMastery", offset: 100, scale, cap },
      scope: scope({ damageKinds: ["disorder"] }),
      disorderAttribution: "source",
    }],
    rawDescription: "队伍中存在异常角色或同阵营角色时，异常掌控每超过100点，使属性异常伤害和紊乱伤害提升0.2%，最多提升20%。",
  });
}

const yuzuhaExtraBase = yuzuhaExtraRule(
  "nanoka:character_1411_extra_anomaly_damage_c0",
  0.2,
  20,
  undefined,
  { type: "all", conditions: [yuzuhaExtra, { type: "compare", path: "self.cinema", operator: "less-than", value: 1 }] },
);
const yuzuhaExtraCinema1 = yuzuhaExtraRule(
  "nanoka:character_1411_extra_anomaly_damage",
  0.26,
  26,
  1,
  yuzuhaExtra,
);

const yuzuhaCinema1Resistance = rule({
  id: "nanoka:character_1411_talent_1_resistance_shred",
  sourceType: "character",
  sourceId: "1411",
  label: "柚叶｜影画1：幸运体质",
  key: "character:1411:talent:1",
  target: "enemy",
  timing: "while-state",
  cinemaAtLeast: 1,
  condition: { type: "state", target: "enemy", state: "sweet-frightened", equals: true },
  effects: [{ kind: "resistance-shred", operation: "add-percent", value: 10 }],
  rawDescription: "甜蜜惊吓状态下，敌人的全属性伤害抗性降低10%。",
});

const yuzuhaCinema2Damage = rule({
  id: "nanoka:character_1411_talent_2_team_damage",
  sourceType: "character",
  sourceId: "1411",
  label: "柚叶｜影画2：趣友云集",
  key: "character:1411:talent:2",
  target: "all-allies",
  timing: "on-trigger",
  trigger: "skill-used",
  cinemaAtLeast: 2,
  effects: [{ kind: "damage-bonus", operation: "add-percent", value: 15 }],
  rawDescription: "强化特殊技或终结技命中后，全队角色造成的伤害提升15%。",
});

const moonlightDamage = rule({
  id: "nanoka:set_33400_4pc_team_damage",
  sourceType: "drive-disc-set",
  sourceId: "33400",
  label: "月光骑士颂｜四件套",
  key: "equipment:33400:4pc",
  target: "all-allies",
  timing: "on-trigger",
  trigger: "skill-used",
  condition: { type: "compare", path: "self.role", operator: "equals", value: "支援" },
  equippedCountAtLeast: 4,
  effects: [{ kind: "damage-bonus", operation: "add-percent", value: 18 }],
  rawDescription: "支援角色发动强化特殊技或终结技后，全队角色造成的伤害提升18%。",
});

const weepingCradleDamage = rule({
  id: "nanoka:weapon_14121_team_damage",
  sourceType: "weapon",
  sourceId: "14121",
  label: "啜泣摇篮｜惩·罚",
  key: "weapon:14121:refinement",
  target: "all-allies",
  timing: "after-trigger",
  trigger: "attack-hit",
  effects: [{
    kind: "damage-bonus",
    operation: "add-percent",
    value: {
      type: "lookup",
      path: "self.weaponRefinement",
      values: [0, 20.2, 24.5, 30, 35.5, 39.8],
    },
  }],
  rawDescription: "装备者攻击命中敌人时，所有单位对目标造成的伤害提升；持续期间每0.5秒额外提升，最多额外提升19.8%。",
  notes: "满拐场景视为命中后3秒已达到最大层数。",
});

const triggerCinema1Vulnerability = rule({
  id: "nanoka:character_1361_talent_1_vulnerability_bonus",
  sourceType: "character",
  sourceId: "1361",
  label: "「扳机」｜影画1：核心被动易伤提升",
  key: "character:1361:talent:1",
  target: "enemy",
  timing: "on-trigger",
  trigger: "attack-hit",
  cinemaAtLeast: 1,
  effects: [{ kind: "vulnerability", operation: "add-percent", value: 20 }],
  rawDescription: "通过[核心被动：破隙幽瞳]施加的失衡易伤倍率额外提升20%。",
  notes: "该20%是核心被动35%常态失衡易伤的影画增量；满拐场景随核心被动一同生效。",
});

export const TEAM_DAMAGE_REVIEWED_RULES: readonly BuffRule[] = [
  aliceWeaponMastery,
  aliceExtraProficiency,
  aliceDefenseShred,
  aliceCinema2Anomaly,
  aliceDisorderMultiplier,
  aliceWeaponPhysical,
  aliceFangedDamage,
  yuzuhaWishAttack,
  yuzuhaWishDamage,
  yuzuhaExtraBase,
  yuzuhaExtraCinema1,
  yuzuhaCinema1Resistance,
  yuzuhaCinema2Damage,
  moonlightDamage,
  weepingCradleDamage,
  triggerCinema1Vulnerability,
];
