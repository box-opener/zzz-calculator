import type { BuffCondition, BuffEffect, BuffRule, BuffScope } from "../../src/domain/model/buff.js";

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
  condition?: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  scopeNote?: string;
}): BuffRule {
  return {
    schemaVersion: 1,
    id: input.id,
    source: source(input.characterId, input.label, input.key),
    status: "verified",
    target: input.target,
    phase: "combat",
    timing: "permanent",
    condition: input.condition ?? { type: "always" },
    effects: input.effects,
    rawDescription: input.rawDescription,
    notes: [
      `Nanoka 条目：${input.key}`,
      input.scopeNote,
    ].filter((value): value is string => Boolean(value)).join("；"),
  };
}

const scope = (value: BuffScope): BuffScope => value;
const bitten: BuffCondition = {
  type: "state",
  target: "enemy",
  state: "啮咬",
  equals: true,
};

export const NANOKA_REVIEWED_BATCH_002: readonly BuffRule[] = [
  makeRule({
    id: "nanoka:character_1251_talent_6_crit_damage",
    characterId: "1251",
    label: "青衣｜天赋：醉花月云转",
    key: "character:1251:talent:6",
    target: "self",
    effects: [{
      kind: "crit-damage-bonus",
      operation: "add-percent",
      value: 100,
      scope: scope({ skillCategories: ["basic"] }),
    }],
    rawDescription: "普通攻击：醉花月云转的暴击伤害额外提升100%。",
    scopeNote: "打断等级不影响当前伤害计算，只迁移该技能的暴击伤害加成。",
  }),
  makeRule({
    id: "nanoka:character_1251_talent_6_resistance_shred",
    characterId: "1251",
    label: "青衣｜天赋：醉花月云转抗性降低",
    key: "character:1251:talent:6",
    target: "enemy",
    effects: [{
      kind: "resistance-shred",
      operation: "add-percent",
      value: 20,
    }],
    rawDescription: "普通攻击：醉花月云转命中敌人时，目标的全属性伤害抗性降低20%，持续15秒。",
    scopeNote: "按审查结论默认视为已触发；无元素 scope 表示全属性。",
  }),
  makeRule({
    id: "nanoka:character_1261_talent_2_assault_def_ignore",
    characterId: "1261",
    label: "简｜天赋：啮咬强击无视防御",
    key: "character:1261:talent:2",
    target: "enemy",
    condition: bitten,
    effects: [{
      kind: "def-ignore",
      operation: "add-percent",
      value: 15,
      scope: scope({ damageKinds: ["assault"] }),
    }],
    rawDescription: "简攻击命中处于啮咬状态下的敌人，或队伍中任意角色对处于啮咬状态下的敌人触发强击时，将会无视其15%防御力，当强击伤害触发暴击时，其暴击伤害额外提升50%。",
    scopeNote: "按用户确认：该15%防御无视只作用于强击，紊乱不会继承强击的防御无视。",
  }),
  makeRule({
    id: "nanoka:character_1261_talent_2_assault_crit_damage",
    characterId: "1261",
    label: "简｜天赋：强击异常暴击伤害",
    key: "character:1261:talent:2",
    target: "self",
    condition: bitten,
    effects: [{
      kind: "crit-damage-bonus",
      operation: "add-percent",
      value: 50,
      scope: scope({ damageKinds: ["assault"] }),
    }],
    rawDescription: "强击伤害触发暴击时，强击暴击伤害额外提升50%。",
    scopeNote: "按审查结论将异常暴击区从默认150%提高到200%。",
  }),
  makeRule({
    id: "nanoka:character_1501_talent_1_yifang_crit_profile",
    characterId: "1501",
    label: "爱芮｜天赋：异放暴击区",
    key: "character:1501:talent:1",
    target: "self",
    effects: [{
      kind: "crit-profile",
      operation: "add",
      zone: "异放",
      critRate: {
        type: "source-stat",
        path: "self.initialAnomalyMastery",
        scale: 0.5,
        offset: 100,
        flat: 25,
      },
      critDamage: 25,
      scope: scope({ skillCategories: ["basic", "special"] }),
    }],
    rawDescription: "爱芮触发异放时新增独立暴击区：基础暴击率25%，暴击伤害25%；初始异常掌控超过100点后，每超过1点使该暴击率额外提升0.5%。",
    scopeNote: "以异放作为独立暴击区；以太异常积蓄抗性无视暂不进入当前模型。",
  }),
  makeRule({
    id: "nanoka:character_1061_talent_2_physical_resistance_shred",
    characterId: "1061",
    label: "可琳｜天赋：物理抗性降低",
    key: "character:1061:talent:2",
    target: "enemy",
    effects: [{
      kind: "resistance-shred",
      operation: "add-percent",
      value: 10,
      scope: scope({ elements: ["physical"] }),
    }],
    rawDescription: "强化特殊技、连携技或终结技命中敌人时，目标的物理伤害抗性下降0.5%，最多叠加20层。",
    scopeNote: "0.5%×20层=10%；按审查结论默认全覆盖。",
  }),
  makeRule({
    id: "nanoka:character_1241_talent_4_ether_resistance_ignore",
    characterId: "1241",
    label: "朱鸢｜天赋：以太抗性无视",
    key: "character:1241:talent:4",
    target: "self",
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 25,
      scope: scope({
        skillCategories: ["basic", "dash"],
        elements: ["ether"],
      }),
    }],
    rawDescription: "消耗强化霰弹攻击命中敌人时，普通攻击：请勿抵抗与冲刺攻击：火力压制无视目标25%以太伤害抗性。",
    scopeNote: "按审查结论默认视为已触发。",
  }),
  makeRule({
    id: "nanoka:character_1311_talent_1_all_resistance_shred",
    characterId: "1311",
    label: "耀嘉音｜天赋：全属性抗性降低",
    key: "character:1311:talent:1",
    target: "enemy",
    effects: [{
      kind: "resistance-shred",
      operation: "add-percent",
      value: 18,
    }],
    rawDescription: "耀嘉音攻击命中敌人时，目标的全属性伤害抗性降低6%，最多叠加3层。",
    scopeNote: "6%×3层=18%；忽略无敌和喧响值。",
  }),
];

export const NANOKA_REVIEWED_BATCH_002_BY_KEY: Readonly<Record<string, readonly BuffRule[]>> =
  NANOKA_REVIEWED_BATCH_002.reduce<Record<string, BuffRule[]>>((groups, rule) => {
    const key = rule.source.key ?? rule.id;
    (groups[key] ??= []).push(rule);
    return groups;
  }, {});
