import type {
  BuffCondition,
  BuffEffect,
  BuffRule,
  BuffScope,
  Element,
} from "../../src/domain/model/buff.js";

const VERSION = "3.2.1+17934514";
const CDN_ROOT = `https://static.nanoka.cc/zzz/${VERSION}/zh/character`;

function source(id: string, label: string, key: string) {
  return {
    type: "character" as const,
    id,
    label,
    provider: "nanoka" as const,
    version: VERSION,
    url: `${CDN_ROOT}/${id}.json`,
    key,
  };
}

function makeRule(input: {
  id: string;
  characterId: string;
  label: string;
  key: string;
  target: BuffRule["target"];
  timing?: BuffRule["timing"];
  trigger?: BuffRule["trigger"];
  condition?: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  durationSeconds?: number;
  refreshPolicy?: BuffRule["refreshPolicy"];
  coreLevel?: number;
  scopeNote?: string;
}): BuffRule {
  return {
    schemaVersion: 1,
    id: input.id,
    source: source(input.characterId, input.label, input.key),
    status: "verified",
    target: input.target,
    phase: "combat",
    timing: input.timing ?? "permanent",
    condition: input.condition ?? { type: "always" },
    effects: input.effects,
    rawDescription: input.rawDescription,
    notes: [
      `Nanoka 条目：${input.key}`,
      input.scopeNote,
    ].filter((value): value is string => Boolean(value)).join("；"),
    ...(input.trigger ? { trigger: input.trigger } : {}),
    ...(input.durationSeconds !== undefined ? { durationSeconds: input.durationSeconds } : {}),
    ...(input.refreshPolicy ? { refreshPolicy: input.refreshPolicy } : {}),
    ...(input.coreLevel === undefined ? {} : { coreLevel: input.coreLevel }),
  };
}

const scope = (value: BuffScope): BuffScope => value;
const bitten: BuffCondition = {
  type: "state",
  target: "enemy",
  state: "啮咬",
  equals: true,
};
const directAndPenetration = ["direct", "penetration"] as const;

const JIAN_LEVELS = [
  { id: "1261501", flat: 20, scale: 0.1 },
  { id: "1261502", flat: 25, scale: 0.11 },
  { id: "1261503", flat: 28, scale: 0.12 },
  { id: "1261504", flat: 31, scale: 0.13 },
  { id: "1261505", flat: 34, scale: 0.14 },
  { id: "1261506", flat: 37, scale: 0.15 },
  { id: "1261507", flat: 40, scale: 0.16 },
] as const;

const jianRules: BuffRule[] = JIAN_LEVELS.map((level, index) => {
  const key = `character:1261:passive:${level.id}:0`;
  return makeRule({
    id: `nanoka:character_1261_passive_${level.id}_assault_crit_profile`,
    characterId: "1261",
    label: "简｜核心被动：强击异常暴击区",
    key,
    target: "self",
    coreLevel: index + 1,
    condition: bitten,
    effects: [{
      kind: "crit-profile",
      operation: "add",
      zone: "强击异常暴击",
      critRate: {
        type: "source-stat",
        path: "self.anomalyProficiency",
        scale: level.scale,
        cap: 100,
        flat: level.flat,
      },
      critDamage: 50,
      scope: scope({ damageKinds: ["assault"] }),
    }],
    rawDescription: `对处于啮咬状态下的敌人造成的强击伤害有概率触发暴击，基础暴击率${level.flat}%，暴击伤害50%，每点异常精通使该效果的暴击率额外提升${level.scale * 100}%。`,
    scopeNote: "新增独立异常暴击区；暴击率上限为100%，超过部分不再增加。",
  });
});

const YIFANG_LEVELS = [
  { id: "1331501", ratios: [0.00307, 0.0016, 0.004, 0.00037, 0.00054, 0.00016] },
  { id: "1331502", ratios: [0.00359, 0.00186, 0.00466, 0.00044, 0.00063, 0.00018] },
  { id: "1331503", ratios: [0.00411, 0.00212, 0.00532, 0.00051, 0.00072, 0.00021] },
  { id: "1331504", ratios: [0.00463, 0.00238, 0.00598, 0.00058, 0.00081, 0.00024] },
  { id: "1331505", ratios: [0.00515, 0.00264, 0.00664, 0.00065, 0.0009, 0.00026] },
  { id: "1331506", ratios: [0.00565, 0.0029, 0.0073, 0.0007, 0.00099, 0.00029] },
  { id: "1331507", ratios: [0.00615, 0.0032, 0.008, 0.00075, 0.00108, 0.00032] },
] as const;

const YIFANG_ELEMENTS: readonly Element[] = [
  "ether",
  "electric",
  "fire",
  "physical",
  "ice",
  "wind",
];

const yifangRules: BuffRule[] = YIFANG_LEVELS.map((level, index) => {
  const key = `character:1331:passive:${level.id}:0`;
  const effects: BuffEffect[] = level.ratios.map((ratio, index) => {
    const element = YIFANG_ELEMENTS[index] as Element;
    return {
      kind: "derived-damage",
      operation: "add",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "multiply-original-anomaly",
      multiplier: {
        type: "source-stat",
        path: "self.anomalyProficiency",
        scale: ratio,
      },
      element,
      scope: scope({ skillCategories: ["basic"], elements: [element] }),
    };
  });
  return makeRule({
    id: `nanoka:character_1331_passive_${level.id}_yifang_damage`,
    characterId: "1331",
    label: "薇薇安｜核心被动：异放伤害",
    key,
    target: "enemy",
    coreLevel: index + 1,
    timing: "on-trigger",
    trigger: "attack-hit",
    effects,
    rawDescription: "普通攻击命中处于属性异常状态的目标时，额外结算一次异放伤害；异放倍率为每10点异常精通对应的属性比例乘本次属性异常伤害。",
    scopeNote: "异放作为独立伤害标签，可继续承接异放增伤与抗性无视；薇薇安的预言和飞羽流程暂不迁移。",
  });
});

const batch003Rules: BuffRule[] = [
  ...jianRules,
  ...yifangRules,
  makeRule({
    id: "nanoka:character_1341_talent_1_direct_penetration_resistance_ignore",
    characterId: "1341",
    label: "照｜天赋：全队直伤抗性无视",
    key: "character:1341:talent:1",
    target: "all-allies",
    timing: "on-trigger",
    trigger: "character-switched-out",
    durationSeconds: 50,
    refreshPolicy: "refresh-duration",
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 15,
      scope: scope({ damageKinds: directAndPenetration }),
    }],
    rawDescription: "照被切换为非当前操作角色时，使全队角色造成的直伤和贯穿伤害无视目标15%全属性伤害抗性，持续50秒，重复触发刷新持续时间。",
    scopeNote: "不作用于异常、紊乱、异放、耀变或乱流等异常标签伤害。",
  }),
  makeRule({
    id: "nanoka:character_1371_talent_2_ether_resistance_ignore",
    characterId: "1371",
    label: "仪玄｜天赋：以太抗性无视",
    key: "character:1371:talent:2",
    target: "self",
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 15,
      scope: scope({ skillCategories: ["special", "ultimate"], elements: ["ether"] }),
    }],
    rawDescription: "终结技或强化特殊技造成伤害时，无视目标15%以太伤害抗性。",
    scopeNote: "只保留该天赋中的以太抗性无视效果。",
  }),
  makeRule({
    id: "nanoka:character_1371_talent_2_penetration_skill",
    characterId: "1371",
    label: "仪玄｜天赋：符法千重·破",
    key: "character:1371:talent:2",
    target: "self",
    effects: [{
      kind: "damage-instance",
      operation: "add",
      damageKind: "penetration",
      value: { type: "source-stat", path: "self.penFlat", scale: 12 },
      scope: scope({ skillCategories: ["special"] }),
    }],
    rawDescription: "新增强化特殊技：符法千重·破，造成1200%贯穿力的贯穿伤害。",
    scopeNote: "资源消耗、聚墨层数及触发链暂不迁移。",
  }),
  makeRule({
    id: "nanoka:character_1431_talent_2_defense_ignore",
    characterId: "1431",
    label: "仪玄｜天赋：明心境技能无视防御",
    key: "character:1431:talent:2",
    target: "self",
    effects: [{
      kind: "def-ignore",
      operation: "add-percent",
      value: 40,
      scope: scope({ skillCategories: ["special", "ultimate"] }),
    }],
    rawDescription: "强化特殊技：明心境·飞光与终结技：斩妄开天造成的伤害无视目标40%防御力。",
    scopeNote: "只保留这两个技能的防御无视效果。",
  }),
  makeRule({
    id: "nanoka:character_1451_talent_1_direct_penetration_resistance_ignore",
    characterId: "1451",
    label: "卢西娅｜天赋：巡梦童谣抗性无视",
    key: "character:1451:talent:1",
    target: "all-allies",
    timing: "while-state",
    condition: { type: "state", target: "team", state: "巡梦童谣", equals: true },
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 18,
      scope: scope({ damageKinds: directAndPenetration }),
    }],
    rawDescription: "巡梦童谣状态下，全队直伤和贯穿伤害无视敌人18%全属性伤害抗性。",
    scopeNote: "不作用于异常、紊乱、异放、耀变或乱流等异常标签伤害；回音与状态循环暂不迁移。",
  }),
  makeRule({
    id: "nanoka:character_1511_talent_1_all_resistance_shred",
    characterId: "1511",
    label: "南宫羽｜天赋：全属性抗性降低",
    key: "character:1511:talent:1",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    durationSeconds: 40,
    refreshPolicy: "refresh-duration",
    effects: [{
      kind: "resistance-shred",
      operation: "add-percent",
      value: 18,
    }],
    rawDescription: "强化特殊技或普通攻击命中敌人时，使敌人的全属性伤害抗性降低18%，持续40秒，重复触发刷新持续时间。",
    scopeNote: "所有伤害标签均可享受该全属性减抗；重拍回复暂不迁移。",
  }),
  makeRule({
    id: "nanoka:character_1541_talent_6_anomaly_yifang_resistance_ignore",
    characterId: "1541",
    label: "普罗米娅｜天赋：异常/异放/紊乱抗性无视",
    key: "character:1541:talent:6",
    target: "self",
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 15,
      scope: scope({ damageKinds: ["anomaly", "yifang", "disorder"] }),
    }],
    rawDescription: "普罗米娅造成的属性异常、异放和紊乱伤害无视敌人15%全属性伤害抗性。",
    scopeNote: "寒蚀值、喧响值及触发冷却暂不迁移。",
  }),
  makeRule({
    id: "nanoka:character_1541_talent_6_yifang_damage",
    characterId: "1541",
    label: "普罗米娅｜天赋：额外异放",
    key: "character:1541:talent:6",
    target: "enemy",
    timing: "on-trigger",
    trigger: "manual",
    effects: [{
      kind: "derived-damage",
      operation: "add",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "replace-anomaly",
      multiplier: 2,
      inheritElement: true,
    }],
    rawDescription: "消耗霜刑触发异放时，额外触发一次特殊异放，固定结算对应属性异常伤害200%的异放伤害。",
    scopeNote: "额外异放的触发事件和15秒冷却待战斗事件模型补齐后接入。",
  }),
];

export const NANOKA_REVIEWED_BATCH_003: readonly BuffRule[] = batch003Rules;

export const NANOKA_REVIEWED_BATCH_003_BY_KEY: Readonly<Record<string, readonly BuffRule[]>> =
  batch003Rules.reduce<Record<string, BuffRule[]>>((groups, rule) => {
    const key = rule.source.key ?? rule.id;
    (groups[key] ??= []).push(rule);
    return groups;
  }, {});
