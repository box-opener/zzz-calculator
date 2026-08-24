import type { BuffCondition, BuffEffect, BuffRule } from "../../src/domain/model/buff.js";

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

function rule(input: {
  id: string;
  characterId: string;
  label: string;
  key: string;
  target: BuffRule["target"];
  timing: BuffRule["timing"];
  condition: BuffCondition;
  effects: readonly BuffEffect[];
  rawDescription: string;
  coreLevel?: number;
  cinemaAtLeast?: number;
  trigger?: BuffRule["trigger"];
  scopeNote: string;
}): BuffRule {
  return {
    schemaVersion: 1,
    id: input.id,
    source: source(input.characterId, input.label, input.key),
    status: "verified",
    target: input.target,
    phase: "combat",
    timing: input.timing,
    condition: input.condition,
    effects: input.effects,
    rawDescription: input.rawDescription,
    notes: `Nanoka 条目：${input.key}；${input.scopeNote}`,
    ...(input.coreLevel === undefined ? {} : { coreLevel: input.coreLevel }),
    ...(input.cinemaAtLeast === undefined ? {} : { cinemaAtLeast: input.cinemaAtLeast }),
    ...(input.trigger === undefined ? {} : { trigger: input.trigger }),
  };
}

const selfState = (state: string): BuffCondition => ({
  type: "state",
  target: "self",
  state,
  equals: true,
});

/**
 * 这批是对 Nanoka 自动候选的语义审查修订，不是计算器内的角色特判：
 *
 * - 千夏核心候选把“猫的凝视在失衡时触发”错误地带到了攻击力 Buff 条件，
 *   且上限被解析成了 525；这里只保留天使协律下的动态初始攻击力转换。
 * - 耀嘉音特殊技的 CAL 文本是 7% + 技能等级 × 1.5% 暴击伤害，自动
 *   候选把它解析成了技能等级 + 8，12 级时会少 5%。
 */
export const NANOKA_REVIEWED_BATCH_005: readonly BuffRule[] = [
  ...[6, 7.5, 9, 10.2, 10.8, 11.4, 12].map((base, index) => rule({
    id: `nanoka:character_1211_passive_pen_rate_core_${index + 1}`,
    characterId: "1211",
    label: "丽娜｜核心被动：迷你毁灭拍档",
    key: `character:1211:passive:121150${index + 1}:0`,
    target: "other-allies",
    timing: "while-state",
    condition: selfState("邦布在场"),
    coreLevel: index + 1,
    trigger: "state-active",
    effects: [{
      kind: "stat",
      stat: "penRate",
      operation: "add-flat",
      value: {
        type: "source-stat",
        path: "self.penRate",
        scale: 0.25,
        flat: base,
        cap: 30,
      },
    }],
    rawDescription: `指派杜苏拉或安娜塔莎进行攻击时，队伍中其他角色的穿透率提升丽娜自身穿透率的25%+${base}%，最高提升30%。`,
    scopeNote: "作用对象是丽娜以外的队友；读取所有局内面板 Buff 收敛后的丽娜穿透率，并按30%上限截断。",
  })),
  rule({
    id: "nanoka:character_1331_extra_ability_corrosion_bonus",
    characterId: "1331",
    label: "薇薇安｜额外能力：预言之泪",
    key: "character:1331:passive:1331507:1",
    target: "all-allies",
    timing: "on-trigger",
    trigger: "skill-used",
    condition: {
      type: "any",
      conditions: [
        { type: "team-role", role: "异常" },
        { type: "team-match", relation: "element" },
      ],
    },
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 12,
      scope: { elements: ["ether"], damageKinds: ["assault", "disorder"] },
      disorderAttribution: "source",
    }],
    rawDescription: "队伍中存在其他异常角色或与自身属性相同的角色时，全队造成的侵蚀伤害和侵蚀状态被结算的紊乱伤害提升12%。",
    scopeNote: "额外能力必须由配队触发；只作用于侵蚀及侵蚀来源的紊乱，不进入普通增伤区，也不提高异放。",
  }),
  rule({
    id: "nanoka:character_1331_talent_1_anomaly_damage_taken",
    characterId: "1331",
    label: "薇薇安｜1画：《在春天走进果园》",
    key: "character:1331:talent:1",
    target: "enemy",
    timing: "while-state",
    cinemaAtLeast: 1,
    trigger: "state-active",
    condition: { type: "state", target: "self", state: "薇薇安的预言已施加", equals: true },
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: 16,
      scope: { damageKinds: ["anomaly", "assault", "disorder", "turbulence"] },
      disorderAttribution: "source",
    }],
    rawDescription: "处于[薇薇安的预言]下的目标受到的所有属性异常伤害和紊乱伤害提升16%。",
    scopeNote: "这是敌方状态下的异常独立增伤，不进入异常效果强度的普通增伤区；异放通过继承异常增伤区受益，不能再重复登记到异放专属增伤区。",
  }),
  rule({
    id: "nanoka:character_1431_passive_harmony",
    characterId: "1431",
    label: "叶瞬光｜核心被动：照破无明·合道",
    key: "character:1431:passive:1431507:0",
    target: "self",
    timing: "permanent",
    condition: { type: "always" },
    effects: [
      {
        kind: "stat",
        stat: "critRate",
        operation: "add-percent",
        value: {
          type: "lookup",
          path: "self.coreLevel",
          values: [0, 15, 17.5, 20, 22.5, 25, 27.5, 30],
        },
      },
      {
        kind: "damage-bonus",
        operation: "add-percent",
        value: {
          type: "lookup",
          path: "self.coreLevel",
          values: [0, 10, 12.5, 15, 17.5, 20, 22.5, 25],
        },
      },
    ],
    rawDescription: "进入战场时获得[合道]：暴击率和造成的伤害随核心被动等级提升；满级分别提升30%和25%。",
    scopeNote: "用核心等级查表替代七条互斥自动候选；合道只作用于叶瞬光本人。",
  }),
  rule({
    id: "nanoka:character_1431_passive_veil_vulnerability",
    characterId: "1431",
    label: "叶瞬光｜核心被动：以太帷幕·决裁",
    key: "character:1431:passive:1431507:0",
    target: "self",
    timing: "while-state",
    condition: selfState("以太帷幕·决裁"),
    trigger: "state-active",
    effects: [{
      kind: "stun-vulnerability-capture",
      operation: "replace",
      value: {
        type: "lookup",
        path: "self.cinema",
        values: [110, 110, 110, 110, 200, 200, 200],
      },
    }],
    rawDescription: "以太帷幕·决裁基于敌人当时的失衡易伤倍率生成仅供叶瞬光使用的帷幕易伤；默认上限110%，影画4后上限200%。",
    scopeNote: "帷幕易伤不是全队共享 Debuff；怪物自带失衡易伤与角色施加的失衡易伤先相加，再按上限截断。",
  }),
  rule({
    id: "nanoka:character_1491_passive_1491049_0",
    characterId: "1491",
    label: "千夏｜核心被动：可爱即正义",
    key: "character:1491:passive:1491049:0",
    target: "all-allies",
    timing: "while-state",
    condition: selfState("天使协律"),
    coreLevel: 7,
    trigger: "state-active",
    effects: [{
      kind: "stat",
      stat: "atk",
      operation: "add-flat",
      value: { type: "source-stat", path: "self.initialAtk", scale: 0.3, cap: 1050 },
    }],
    rawDescription: "处于[天使协律]状态下的角色的攻击力提升，提升数值等同于千夏30%初始攻击力，最高不超过1050点。",
    scopeNote: "按用户已确认的当前账号规则修订；只表达天使协律攻击力 Buff，不把猫的凝视触发条件带入本效果。",
  }),
  rule({
    id: "nanoka:character_1311_skill_special_1",
    characterId: "1311",
    label: "耀嘉音｜特殊技：咏叹华彩",
    key: "character:1311:skill:special:1",
    target: "all-allies",
    timing: "while-state",
    condition: selfState("咏叹华彩"),
    trigger: "state-active",
    effects: [
      {
        kind: "damage-bonus",
        operation: "add-percent",
        value: { type: "source-stat", path: "self.skillLevels.special", scale: 1, flat: 8 },
      },
      {
        kind: "stat",
        stat: "critDmg",
        operation: "add-percent",
        value: { type: "source-stat", path: "self.skillLevels.special", scale: 1.5, flat: 7 },
      },
    ],
    rawDescription: "耀嘉音进入[咏叹华彩]状态后，全队角色造成的伤害提升7%+特殊技等级×1%，全队角色暴击伤害提升7%+特殊技等级×1.5%。",
    scopeNote: "按 Nanoka CAL 表达式拆成两个独立动态效果；特殊技12级时分别为20%增伤和25%暴击伤害。",
  }),
];
