import type {
  BuffCondition,
  BuffEffect,
  BuffRule,
  BuffScope,
  Element,
} from "../../src/domain/model/buff.js";
import { buildExtraAbilityActivationCondition } from "../../src/domain/engine/extra-ability-condition.js";

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
  phase?: BuffRule["phase"];
  timing?: BuffRule["timing"];
  condition?: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  scopeNote?: string;
  trigger?: BuffRule["trigger"];
  durationSeconds?: number;
}): BuffRule {
  const notes = [
    `Nanoka 条目：${input.key}`,
    `额外能力队伍触发沿用旧版已存在的同属性/同职业/同阵营判断；需要时另加角色专属职业条件。`,
    input.scopeNote,
  ].filter((value): value is string => Boolean(value));
  return {
    schemaVersion: 1,
    id: input.id,
    source: source(input.characterId, input.label, input.key),
    status: "verified",
    target: input.target,
    phase: input.phase ?? "combat",
    timing: input.timing ?? "permanent",
    condition: input.condition ?? { type: "always" },
    effects: input.effects,
    rawDescription: input.rawDescription,
    notes: notes.join("；"),
    ...(input.trigger ? { trigger: input.trigger } : {}),
    ...(input.durationSeconds !== undefined ? { durationSeconds: input.durationSeconds } : {}),
  };
}

const extra = (characterId: string): BuffCondition =>
  buildExtraAbilityActivationCondition(characterId);

const stunned: BuffCondition = {
  type: "state",
  target: "enemy",
  state: "stunned",
  equals: true,
};

const all = (...conditions: BuffCondition[]): BuffCondition => ({
  type: "all",
  conditions,
});

const any = (...conditions: BuffCondition[]): BuffCondition => ({
  type: "any",
  conditions,
});

const scope = (value: BuffScope): BuffScope => value;

export const NANOKA_REVIEWED_BATCH_001: readonly BuffRule[] = [
  makeRule({
    id: "nanoka:character_1011_core_daze",
    characterId: "1011",
    label: "安比｜核心被动：波动电压",
    key: "character:1011:passive:1011507:0",
    target: "self",
    effects: [{
      kind: "daze-bonus",
      operation: "add-percent",
      value: 64,
      scope: scope({ skillCategories: ["basic", "special"] }),
    }],
    rawDescription: "安比在普通攻击第三段后发动普通攻击：落雷、特殊技或强化特殊技时，招式造成的失衡值提升64%。",
    scopeNote: "按审查结论采用最高等级数值；不再追踪前置的普通攻击第三段。",
  }),
  makeRule({
    id: "nanoka:character_1021_core_damage",
    characterId: "1021",
    label: "猫又｜核心被动：猫步诡影",
    key: "character:1021:passive:1021507:0",
    target: "self",
    effects: [{ kind: "damage-bonus", operation: "add-percent", value: 60 }],
    rawDescription: "猫又闪避反击或快速支援命中敌人时，自身造成的伤害提升60%。",
    scopeNote: "忽略呼噜能量与触发顺序，按审查结论直接采用最高伤害路线。",
  }),
  makeRule({
    id: "nanoka:character_1021_extra_damage",
    characterId: "1021",
    label: "猫又｜额外能力：猫步秀",
    key: "character:1021:passive:1021507:1",
    target: "self",
    condition: extra("1021"),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 70,
      scope: scope({ skillCategories: ["special"] }),
    }],
    rawDescription: "队伍中存在支援角色或与自身属性或阵营相同的角色时触发：猫又发动闪避：尾巴失踪术或队伍中任意角色对敌人施加强击效果后，猫又强化特殊技或闪避反击命中时造成的伤害提升35%，该效果最多可叠加2层。",
    scopeNote: "两层35%合并为一次70%伤害加成；按最高层数计算，不追踪强击和消费顺序。",
  }),
  makeRule({
    id: "nanoka:character_1031_core_def_shred",
    characterId: "1031",
    label: "妮可｜核心被动：机关箱",
    key: "character:1031:passive:1031507:0",
    target: "enemy",
    effects: [{ kind: "def-shred", operation: "add-percent", value: 40 }],
    rawDescription: "妮可在特殊技、强化特殊技、连携技、终结技等招式中上弹并强化普通攻击与冲刺攻击；强化子弹或能量场命中敌人时，目标的防御力降低40%。",
    scopeNote: "忽略持续时间，保留防御力降低数值。",
  }),
  makeRule({
    id: "nanoka:character_1031_extra_ether_damage",
    characterId: "1031",
    label: "妮可｜额外能力：残心",
    key: "character:1031:passive:1031507:1",
    target: "all-allies",
    condition: extra("1031"),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 25,
      scope: scope({ elements: ["ether"] }),
    }],
    rawDescription: "队伍中存在与自身属性或阵营相同的角色时触发：妮可通过核心被动：机关箱对敌人施加减益效果时，所有单位对目标造成的以太伤害额外提升25%。",
    scopeNote: "按审查结论作为普通伤害加成，进入与驱动盘5号位主词条相同的加算区。",
  }),
  makeRule({
    id: "nanoka:character_1041_extra_fire_damage",
    characterId: "1041",
    label: "「11号」｜额外能力：热血驱动",
    key: "character:1041:passive:1041507:1",
    target: "self",
    condition: extra("1041"),
    effects: [{ kind: "stat", stat: "fireDmgBonus", operation: "add-percent", value: 10 }],
    rawDescription: "队伍中存在与自身属性或阵营相同的角色时触发：「11号」造成的火属性伤害提升10%。",
  }),
  makeRule({
    id: "nanoka:character_1041_extra_stunned_fire_damage",
    characterId: "1041",
    label: "「11号」｜额外能力：失衡追加",
    key: "character:1041:passive:1041507:1",
    target: "self",
    condition: all(extra("1041"), stunned),
    effects: [{ kind: "stat", stat: "fireDmgBonus", operation: "add-percent", value: 22.5 }],
    rawDescription: "攻击处于失衡状态下的敌人时，该火属性伤害增益效果额外提升22.5%。",
    scopeNote: "与基础10%拆成两条，失衡时合计32.5%。",
  }),
  makeRule({
    id: "nanoka:character_1051_core_penetration_from_hp",
    characterId: "1051",
    label: "伊德海莉｜核心被动：拾梦空想",
    key: "character:1051:passive:1051507:0",
    target: "self",
    phase: "panel",
    effects: [{
      kind: "stat",
      stat: "penFlat",
      operation: "add-flat",
      value: { type: "source-stat", path: "self.maxHp", scale: 0.1 },
    }],
    rawDescription: "伊德海莉会额外根据自身最大生命值提高贯穿力，每1点最大生命值将提高0.1点贯穿力。",
    scopeNote: "最大生命值换算为贯穿力；生命低于50%的其他动态增益另行处理。",
  }),
  makeRule({
    id: "nanoka:character_1051_core_ice_penetration_conversion",
    characterId: "1051",
    label: "伊德海莉｜冰伤贯穿化",
    key: "character:1051:passive:1051507:0",
    target: "self",
    effects: [{ kind: "damage-conversion", from: "ice", to: "penetration" }],
    rawDescription: "伊德海莉发动招式造成的冰属性伤害均为贯穿伤害，无视敌人防御，使用贯穿力作为招式伤害倍率。",
  }),
  makeRule({
    id: "nanoka:character_1051_core_max_damage",
    characterId: "1051",
    label: "伊德海莉｜核心被动：低生命值伤害",
    key: "character:1051:passive:1051507:0",
    target: "self",
    condition: { type: "compare", path: "self.hpPercent", operator: "less-than-or-equal", value: 50 },
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 100,
      scope: scope({ elements: ["ice"], damageKinds: ["penetration"] }),
    }],
    rawDescription: "当伊德海莉生命值低于50%时，获得的增益效果达到最大值，攻击造成的伤害最多提升100%。",
    scopeNote: "按审查结论采用最大增益；只作用于冰属性贯穿伤害。",
  }),
  makeRule({
    id: "nanoka:character_1061_extra_stunned_damage",
    characterId: "1061",
    label: "可琳｜额外能力：协同作战",
    key: "character:1061:passive:1061507:1",
    target: "self",
    condition: all(extra("1061"), stunned),
    effects: [{ kind: "damage-bonus", operation: "add-percent", value: 35 }],
    rawDescription: "队伍中存在与自身属性或阵营相同的角色时触发：可琳攻击命中处于失衡状态下的敌人时，自身造成的伤害提升35%。",
  }),
  makeRule({
    id: "nanoka:character_1071_extra_team_damage",
    characterId: "1071",
    label: "凯撒｜额外能力：协同作战",
    key: "character:1071:passive:1071507:1",
    target: "all-allies",
    condition: extra("1071"),
    effects: [{ kind: "damage-bonus", operation: "add-percent", value: 25 }],
    rawDescription: "队伍中存在其他可发动招架支援的角色或与自身阵营相同的角色时触发：凯撒触发精准格挡、防御反击、招架支援或发动普通攻击：此路不通时，使全队角色对其造成的伤害提升25%，持续30秒。",
    durationSeconds: 30,
    scopeNote: "额外能力触发条件沿用旧逻辑，并由Nanoka职业字段提供防护职业判断。",
  }),
  makeRule({
    id: "nanoka:character_1081_core_damage",
    characterId: "1081",
    label: "比利｜核心被动：蹲姿射击",
    key: "character:1081:passive:1081507:0",
    target: "self",
    effects: [{ kind: "damage-bonus", operation: "add-percent", value: 50 }],
    rawDescription: "比利在普通攻击中进入蹲姿射击后，自身造成的伤害提升50%。",
    scopeNote: "按审查结论采用最高伤害路线，忽略蹲姿进入与退出事件。",
  }),
  makeRule({
    id: "nanoka:character_1081_extra_ultimate_damage",
    characterId: "1081",
    label: "比利｜额外能力：星徽骑士",
    key: "character:1081:passive:1081507:1",
    target: "self",
    condition: extra("1081"),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 100,
      scope: scope({ skillCategories: ["ultimate"] }),
    }],
    rawDescription: "队伍中存在与自身属性或阵营相同的角色时触发：比利发动连携技后，下次发动终结技时，招式造成的伤害提升50%，最多叠加2次。",
    scopeNote: "两层50%合并为终结技100%加成。",
  }),
  makeRule({
    id: "nanoka:character_1091_extra_frostmoon_damage",
    characterId: "1091",
    label: "星见雅｜额外能力：霜月架势",
    key: "character:1091:passive:1091507:1",
    target: "self",
    condition: any(
      extra("1091"),
      { type: "team-role", role: "支援" },
      { type: "team-role", role: "异常" },
    ),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 60,
      scope: scope({ skillCategories: ["basic"] }),
    }],
    rawDescription: "队伍中存在支援角色或与自身阵营相同的角色或其他异常角色时触发：普通攻击：霜月造成的伤害提升60%。",
    scopeNote: "只保留普通攻击：霜月的直接伤害加成。",
  }),
  makeRule({
    id: "nanoka:character_1091_extra_frostmoon_resistance_ignore",
    characterId: "1091",
    label: "星见雅｜额外能力：霜月架势抗性无视",
    key: "character:1091:passive:1091507:1",
    target: "self",
    condition: any(
      extra("1091"),
      { type: "team-role", role: "支援" },
      { type: "team-role", role: "异常" },
    ),
    effects: [{
      kind: "resistance-ignore",
      operation: "add-percent",
      value: 30,
      scope: scope({ skillCategories: ["basic"], elements: ["ice"] }),
    }],
    rawDescription: "队伍中任意角色触发紊乱效果时，在下一次霜月架势期间，普通攻击：霜月将无视目标30%冰属性伤害抗性。",
    scopeNote: "按审查结论视为已触发的普通攻击：霜月增益。",
  }),
  makeRule({
    id: "nanoka:character_1101_core_daze",
    characterId: "1101",
    label: "珂蕾妲｜核心被动：爆破锤",
    key: "character:1101:passive:1101507:0",
    target: "self",
    effects: [{
      kind: "daze-bonus",
      operation: "add-percent",
      value: 60,
      scope: scope({ skillCategories: ["special"] }),
    }],
    rawDescription: "珂蕾妲发动强化特殊技，或消耗熔炉升温发动强化普通攻击时，招式造成的失衡值提升60%。",
  }),
  makeRule({
    id: "nanoka:character_1101_extra_chain_damage",
    characterId: "1101",
    label: "珂蕾妲｜额外能力：白祇管理学",
    key: "character:1101:passive:1101507:1",
    target: "self",
    condition: all(
      any(
        extra("1101"),
        { type: "team-role", role: "命破" },
        { type: "team-role", role: "锋御" },
      ),
      stunned,
    ),
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 70,
      scope: scope({ skillCategories: ["chain"] }),
    }],
    rawDescription: "队伍中存在与自身属性或阵营相同的角色或命破或锋御角色时触发：当目标陷入失衡状态后，连携技对其造成的伤害提升35%，最多叠加2层。",
    scopeNote: "两层35%合并为连携技70%；忽略失衡结束时重置。",
  }),
  makeRule({
    id: "nanoka:character_1121_core_atk_from_def",
    characterId: "1121",
    label: "本｜核心被动：守卫",
    key: "character:1121:passive:1121507:0",
    target: "self",
    phase: "panel",
    effects: [{
      kind: "stat",
      stat: "atk",
      operation: "add-flat",
      value: { type: "source-stat", path: "self.initialDef", scale: 0.8 },
    }],
    rawDescription: "本的初始攻击力随初始防御力提升，提升效果等同于自身初始防御力的80%。",
    scopeNote: "只迁移初始防御力转初始攻击力；护盾另有战斗触发，不在本条中。",
  }),
];

export const NANOKA_REVIEWED_BATCH_001_BY_ID: Readonly<Record<string, BuffRule>> =
  Object.fromEntries(NANOKA_REVIEWED_BATCH_001.map((rule) => [rule.id, rule]));

export type ReviewedElement = Element;
