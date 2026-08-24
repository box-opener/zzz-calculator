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
  stacks?: BuffRule["stacks"];
  cinemaAtLeast?: number;
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
    ...(input.stacks ? { stacks: input.stacks } : {}),
    ...(input.cinemaAtLeast !== undefined ? { cinemaAtLeast: input.cinemaAtLeast } : {}),
  };
}

const scope = (value: BuffScope): BuffScope => value;
const all = (...conditions: BuffCondition[]): BuffCondition => ({ type: "all", conditions });
const any = (...conditions: BuffCondition[]): BuffCondition => ({ type: "any", conditions });

const anomalyElements: readonly Element[] = [
  "ether",
  "electric",
  "fire",
  "physical",
  "ice",
  "wind",
];

const anomalyDamageKinds = [
  "anomaly",
  "assault",
  "yifang",
  "disorder",
  "turbulence",
] as const;

const stunned: BuffCondition = {
  type: "state",
  target: "enemy",
  state: "stunned",
  equals: true,
};

const nanyuExtra: BuffCondition = any(
  { type: "team-role", role: "异常" },
  { type: "team-match", relation: "camp" },
);

const velinaExtra: BuffCondition = any(
  { type: "team-role", role: "异常" },
  { type: "team-match", relation: "element" },
);

const yifang = (
  ratios: readonly number[],
  mode: "multiply-original-anomaly" | "replace-anomaly",
  scopeValue?: BuffScope,
): BuffEffect[] => anomalyElements.map((element, index) => ({
  kind: "derived-damage",
  operation: "add",
  damageKind: "yifang",
  sourceDamageKind: "anomaly",
  mode,
  multiplier: ratios[index] ?? 0,
  element,
  ...(scopeValue === undefined ? {} : { scope: scope(scopeValue) }),
}));

const yifangPerStack = (
  ratios: readonly number[],
  perStackRatio: number,
): BuffEffect[] => anomalyElements.map((element, index) => {
  const base = ratios[index] ?? 0;
  return {
    kind: "derived-damage",
    operation: "add",
    damageKind: "yifang" as const,
    sourceDamageKind: "anomaly" as const,
    mode: "multiply-original-anomaly" as const,
    multiplier: { type: "per-stack" as const, base, perStack: base * perStackRatio },
    element,
  };
});

const yifangAdditionalPerStack = (ratios: readonly number[], perStackRatio: number): BuffEffect[] =>
  yifangPerStack(ratios.map(() => 0), perStackRatio).map((effect, index) => ({
    ...effect,
    multiplier: {
      type: "per-stack" as const,
      base: 0,
      perStack: (ratios[index] ?? 0) * perStackRatio,
    },
  }));

const batch004Rules: BuffRule[] = [
  makeRule({
    id: "nanoka:character_1561_passive_1561507_1_wind_anomaly_damage",
    characterId: "1561",
    label: "维琳娜｜额外能力：风化与乱流增伤",
    key: "character:1561:passive:1561507:1",
    target: "self",
    condition: velinaExtra,
    effects: [
      {
        kind: "damage-bonus",
        operation: "add-percent",
        value: 10,
        scope: scope({ damageKinds: ["anomaly", "turbulence"] }),
      },
      { kind: "daze-bonus", operation: "add-percent", value: 30 },
    ],
    rawDescription: "队伍中存在其他异常角色或与自身属性相同的角色时，维琳娜造成的风化和乱流伤害提升10%，失衡值提升30%。",
    scopeNote: "忽略异常积蓄抗性降低；风化进入异常独立区，乱流进入乱流增伤区。",
  }),
  makeRule({
    id: "nanoka:character_1561_passive_1561507_1_yifang",
    characterId: "1561",
    label: "维琳娜｜额外能力：终结技异放",
    key: "character:1561:passive:1561507:1",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: velinaExtra,
    effects: yifang([6.8, 6.8, 6.8, 6.8, 6.8, 6.8], "replace-anomaly", { skillCategories: ["ultimate"] }),
    rawDescription: "维琳娜终结技重击命中风属性异常目标时，额外结算一次680%倍率的风属性异放。",
    scopeNote: "原文为‘属性异常伤害’而非‘原属性异常’，按异放替换倍率处理；风属性异常状态和技能命中由事件层确认。",
  }),
  makeRule({
    id: "nanoka:character_1581_passive_1581507_0_anomaly_coefficient",
    characterId: "1581",
    label: "蕾米埃尔｜核心：异化系数",
    key: "character:1581:passive:1581507:0",
    target: "self",
    effects: [{
      kind: "anomaly-effect-strength-multiplier",
      operation: "add-percent",
      value: { type: "source-stat", path: "self.anomalyProficiency", scale: 0.02 },
    }],
    rawDescription: "蕾米埃尔的异化系数为自身异常精通的0.02%。",
    scopeNote: "异化系数是异常效果强度的独立乘区来源，最终按1+异化系数参与异常效果强度计算。",
  }),
  makeRule({
    id: "nanoka:character_1581_passive_1581507_0_anomaly_team_bonus",
    characterId: "1581",
    label: "蕾米埃尔｜核心：三名异常角色异化系数",
    key: "character:1581:passive:1581507:0",
    target: "self",
    condition: { type: "team-role-count", role: "异常", operator: "equals", value: 3 },
    effects: [{
      kind: "anomaly-effect-strength-multiplier",
      operation: "add-percent",
      value: 10,
    }],
    rawDescription: "队伍中异常角色数量为3时，蕾米埃尔的异化系数额外提升10%。",
  }),
  makeRule({
    id: "nanoka:character_1581_talent_2_anomaly_def_ignore",
    characterId: "1581",
    label: "蕾米埃尔｜天赋：异常伤害防御无视",
    key: "character:1581:talent:2",
    target: "enemy",
    condition: all(
      { type: "team-role-count", role: "异常", operator: "greater-than-or-equal", value: 1 },
      { type: "state", target: "enemy", state: "幻色", equals: true },
    ),
    cinemaAtLeast: 2,
    durationSeconds: 8,
    effects: [{
      kind: "def-ignore",
      operation: "add-percent",
      value: 15,
      scope: scope({ damageKinds: anomalyDamageKinds }),
    }],
    rawDescription: "蕾米埃尔2画中，队伍异常角色对幻色效果下敌人的异常类伤害无视15%防御力，幻色消失后额外持续8秒。",
    scopeNote: "异常类伤害包括属性异常、强击、异放、紊乱和乱流，不包括耀变；幻色状态及8秒延长由战斗状态层提供。",
  }),
  makeRule({
    id: "nanoka:character_1091_passive_1091507_0_frostbreak",
    characterId: "1091",
    label: "星见雅｜霜灼·破",
    key: "character:1091:passive:1091507:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: { type: "state", target: "enemy", state: "冰焰", equals: true },
    effects: [{
      kind: "damage-instance",
      operation: "add",
      damageKind: "direct",
      value: { type: "source-stat", path: "self.atk", scale: 15 },
      element: "ice",
    }],
    rawDescription: "星见雅对附着冰焰的敌人施加霜寒时触发霜灼·破，造成1500%攻击力的烈霜直接伤害。",
    scopeNote: "只保留新增无标签直接伤害；异常积蓄、冰焰状态和资源由事件层处理。",
  }),
  makeRule({
    id: "nanoka:character_1161_passive_1161507_0_ice_fire_resistance_shred",
    characterId: "1161",
    label: "莱特｜核心：士气喷发减抗",
    key: "character:1161:passive:1161507:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: { type: "state", target: "enemy", state: "士气喷发", equals: true },
    durationSeconds: 30,
    refreshPolicy: "refresh-duration",
    effects: [{
      kind: "resistance-shred",
      operation: "add-percent",
      value: 15,
      scope: scope({ elements: ["ice", "fire"] }),
    }],
    rawDescription: "士气喷发状态下，轻拳起攻或刺拳连击命中时，目标冰、火属性伤害抗性降低15%，持续30秒。",
    scopeNote: "按审查结论补全冰属性；资源、冲击力和溃败持续时间不进入本条。",
  }),
  makeRule({
    id: "nanoka:character_1511_passive_1511055_1_polar_disorder",
    characterId: "1511",
    label: "南宫羽｜额外能力：极性紊乱与失衡易伤",
    key: "character:1511:passive:1511055:1",
    target: "enemy",
    condition: all(nanyuExtra, stunned),
    timing: "on-trigger",
    trigger: "attack-hit",
    durationSeconds: 15,
    refreshPolicy: "refresh-duration",
    effects: [
      { kind: "polar-disorder", operation: "add-percent", value: 25, maxTriggers: 2 },
      { kind: "vulnerability", operation: "add-percent", value: 30 },
    ],
    rawDescription: "队伍满足额外能力且敌人失衡时，南宫羽的重击可触发两次25%原紊乱伤害的极性紊乱；敌人失衡易伤倍率提高30%。",
    scopeNote: "极性紊乱附加值与普通紊乱一样继续经过紊乱增伤区和怪物乘区；默认按满层、满时长处理。",
  }),
  makeRule({
    id: "nanoka:character_1541_passive_1541507_anomaly_mastery",
    characterId: "1541",
    label: "普罗米娅｜核心：异常掌控转异常精通",
    key: "character:1541:passive:1541507:0",
    target: "self",
    effects: [{
      kind: "stat",
      stat: "anomalyProficiency",
      operation: "add-flat",
      value: { type: "source-stat", path: "self.anomalyMastery", offset: 150, scale: 1.5 },
    }],
    rawDescription: "初始异常掌控超过150点后，每超过1点提升自身1.5点异常精通。",
    scopeNote: "读取稳定的局内面板值；初始异常掌控字段尚未单独建模时沿用当前面板异常掌控字段。",
  }),
  makeRule({
    id: "nanoka:character_1541_passive_1541507_team_yifang_bonus",
    characterId: "1541",
    label: "普罗米娅｜核心：全队异放增伤",
    key: "character:1541:passive:1541507:0",
    target: "all-allies",
    effects: [{
      kind: "damage-bonus",
      operation: "add-percent",
      value: { type: "source-stat", path: "self.anomalyMastery", offset: 150, scale: 0.35 },
      scope: scope({ damageKinds: ["yifang"] }),
    }],
    rawDescription: "初始异常掌控超过150点后，每超过1点提升全队造成的异放伤害0.35%。",
    scopeNote: "作用于全队异放独立增伤区，不作用于普通异常、紊乱或乱流。",
  }),
  makeRule({
    id: "nanoka:character_1541_passive_1541507_yifang",
    characterId: "1541",
    label: "普罗米娅｜核心：处刑式·绝裁异放",
    key: "character:1541:passive:1541507:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: yifang([6.35, 6.35, 6.35, 6.35, 6.35, 6.35], "replace-anomaly", { skillCategories: ["special"] }),
    rawDescription: "强化特殊技：处刑式·绝裁终结一击命中处于任意属性异常的目标时，触发一次固定635%对应属性异常伤害的异放。",
    scopeNote: "对应属性由事件层选择；原文不是‘原属性异常’，按异放替换倍率处理。",
  }),
  makeRule({
    id: "nanoka:character_1561_passive_1561507_0_panel_conversion",
    characterId: "1561",
    label: "维琳娜｜核心：能量自动回复转面板",
    key: "character:1561:passive:1561507:0",
    target: "self",
    effects: [
      {
        kind: "damage-bonus",
        operation: "add-percent",
        value: { type: "source-stat", path: "self.energyRegen", offset: 1.2, scale: 21, cap: 35 },
      },
      {
        kind: "stat",
        stat: "anomalyMastery",
        operation: "add-flat",
        value: { type: "source-stat", path: "self.energyRegen", offset: 1.2, scale: 50, cap: 84 },
      },
      {
        kind: "multiplier",
        operation: "add-percent",
        value: 150,
        scope: scope({ damageKinds: ["turbulence"] }),
      },
    ],
    rawDescription: "初始能量自动回复超过1.2时，每超过0.01，造成的伤害提升0.21%（最多35%），异常掌控提升0.5点（最多84点）；特定乱流倍率提升150%。",
    scopeNote: "能量自动回复读取局外面板值；乱流150%进入乱流倍率区，不是乱流增伤区。",
  }),
  makeRule({
    id: "nanoka:character_1561_passive_1561507_0_micro_yifang",
    characterId: "1561",
    label: "维琳娜｜核心：微域气旋异放",
    key: "character:1561:passive:1561507:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: [{
      kind: "derived-damage",
      operation: "add",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "replace-anomaly",
      multiplier: 1.45,
      element: "wind",
    }],
    rawDescription: "微域气旋消散爆炸命中风属性异常目标时，触发一次145%风属性异常异放。",
    scopeNote: "微域/广域两种爆炸倍率互斥，具体选择由事件层确定；本条只保存145%分支。",
  }),
  makeRule({
    id: "nanoka:character_1561_passive_1561507_0_wide_yifang",
    characterId: "1561",
    label: "维琳娜｜核心：广域气旋异放",
    key: "character:1561:passive:1561507:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: [{
      kind: "derived-damage",
      operation: "add",
      damageKind: "yifang",
      sourceDamageKind: "anomaly",
      mode: "replace-anomaly",
      multiplier: 2.55,
      element: "wind",
    }],
    rawDescription: "广域气旋消散爆炸命中风属性异常目标时，触发一次255%风属性异常异放。",
    scopeNote: "微域/广域两种爆炸倍率互斥，具体选择由事件层确定；本条只保存255%分支。",
  }),
  makeRule({
    id: "nanoka:character_1581_talent_2_anomaly_coefficient_bonus",
    characterId: "1581",
    label: "蕾米埃尔｜2画：异化系数",
    key: "character:1581:talent:2",
    target: "self",
    cinemaAtLeast: 2,
    effects: [{
      kind: "anomaly-effect-strength-multiplier",
      operation: "add-percent",
      value: 20,
    }],
    rawDescription: "蕾米埃尔2画使异化系数提升20%。",
    scopeNote: "按审查说明作为异常效果强度独立乘区的百分点直接相加。",
  }),
  makeRule({
    id: "nanoka:character_1171_skill_special_5_yifang",
    characterId: "1171",
    label: "柏妮思｜特殊技：余烬异放",
    key: "character:1171:skill:special:5",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: yifang([4.8, 2.4, 6, 0.4, 0.6, 0.24], "multiply-original-anomaly"),
    rawDescription: "招式重击命中属性异常目标时，按对应属性原属性异常伤害倍率触发一次异放：以太480%、电240%、火600%、物理40%、冰60%、风24%。",
    scopeNote: "原文明确写出‘原属性异常’，采用异放倍率乘原属性异常倍率；前置流火和余烬计数由事件层处理。",
  }),
  makeRule({
    id: "nanoka:character_1181_skill_special_4_yifang",
    characterId: "1181",
    label: "安东｜特殊技：脉冲异放",
    key: "character:1181:skill:special:4",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: yifang([5.6, 2.8, 7, 0.5, 0.7, 0.28], "multiply-original-anomaly"),
    rawDescription: "脉冲手雷命中属性异常目标时，按对应属性原属性异常伤害倍率触发一次异放：以太560%、电280%、火700%、物理50%、冰70%、风28%。",
    scopeNote: "原文明确写出‘原属性异常’，采用异放倍率乘原属性异常倍率；脉冲层数和手雷选择由事件层处理。",
  }),
  makeRule({
    id: "nanoka:character_1221_talent_2_polar_disorder",
    characterId: "1221",
    label: "柳｜2画：极性紊乱倍率",
    key: "character:1221:talent:2",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    cinemaAtLeast: 2,
    effects: [{ kind: "polar-disorder", operation: "add-percent", value: 50, maxTriggers: 1 }],
    rawDescription: "2画下，强化特殊技下落攻击触发的极性紊乱倍率按满突刺层数提升至原紊乱伤害的50%。",
    scopeNote: "15%基础值提升为20%+2×15%=50%；极性紊乱最终值仍经过紊乱增伤区和怪物乘区。",
  }),
  makeRule({
    id: "nanoka:character_1221_talent_4_identify_penetration",
    characterId: "1221",
    label: "柳｜4画：识破穿透率 Debuff",
    key: "character:1221:talent:4",
    target: "all-allies",
    timing: "while-state",
    condition: { type: "state", target: "enemy", state: "识破", equals: true },
    cinemaAtLeast: 4,
    durationSeconds: 15,
    effects: [{ kind: "stat", stat: "penRate", operation: "add-flat", value: 16 }],
    rawDescription: "识破状态下，敌人受到攻击时本次攻击的穿透率提升16%。",
    scopeNote: "按审查结论作为挂在敌人身上的全队 Debuff；所有伤害标签均可享受，不是柳本人攻击专属无视抗性。",
  }),
  makeRule({
    id: "nanoka:character_1401_skill_basic_1_polar_assault",
    characterId: "1401",
    label: "爱丽丝｜普通攻击：星芒圆舞曲极性强击",
    key: "character:1401:skill:basic:1",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    effects: [{
      kind: "damage-instance",
      operation: "add",
      damageKind: "assault",
      value: { type: "source-stat", path: "self.atk", scale: 7.13 },
      element: "physical",
    }],
    rawDescription: "三段蓄力普通攻击终结一击触发一次713%倍率的极性强击伤害。",
    scopeNote: "极性强击的异常伤害结算由事件层按强击公式处理；这里只登记一次713%强击实例。",
  }),
  makeRule({
    id: "nanoka:character_1511_passive_1511055_0_panel_stats",
    characterId: "1511",
    label: "南宫羽｜核心：异常精通与冲击力",
    key: "character:1511:passive:1511055:0",
    target: "self",
    effects: [
      { kind: "stat", stat: "anomalyProficiency", operation: "add-flat", value: 120 },
      {
        kind: "stat",
        stat: "impact",
        operation: "add-flat",
        value: { type: "source-stat", path: "self.anomalyMastery", offset: 110, scale: 1 },
      },
    ],
    rawDescription: "南宫羽异常精通提升120点；初始异常掌控超过110点时，每超过1点提升自身1点冲击力。",
    scopeNote: "忽略异常积蓄与重拍资源；动态冲击力读取当前登记的异常掌控字段。",
  }),
  makeRule({
    id: "nanoka:character_1511_passive_1511055_0_yifang",
    characterId: "1511",
    label: "南宫羽｜核心：颤音异放",
    key: "character:1511:passive:1511055:0",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: stunned,
    stacks: { mode: "derived", min: 0, max: 4, initial: 4 },
    effects: yifangPerStack([7.2, 3.6, 9, 0.63, 0.9, 0.36], 0.25),
    rawDescription: "失衡期间颤音清除时触发对应属性异放：基础倍率为720%/360%/900%/63%/90%/36%，每层颤音额外提升25%。",
    scopeNote: "按满4层计算；原属性异常倍率语义由事件层按对应异常结算。",
  }),
  makeRule({
    id: "nanoka:character_1511_passive_1511055_0_team_damage",
    characterId: "1511",
    label: "南宫羽｜核心：全队伤害提升",
    key: "character:1511:passive:1511055:0",
    target: "all-allies",
    timing: "on-trigger",
    trigger: "attack-hit",
    durationSeconds: 30,
    refreshPolicy: "refresh-duration",
    effects: [{ kind: "damage-bonus", operation: "add-percent", value: 25 }],
    rawDescription: "南宫羽普通攻击或强化特殊技命中后，使全队造成的伤害提升25%，持续30秒，重复触发刷新。",
    scopeNote: "按满拐默认激活；事件层应将触发限制在对应招式命中。",
  }),
  makeRule({
    id: "nanoka:character_1511_talent_2_yifang_bonus",
    characterId: "1511",
    label: "南宫羽｜2画：颤音异放倍率",
    key: "character:1511:talent:2",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: stunned,
    cinemaAtLeast: 2,
    stacks: { mode: "derived", min: 0, max: 4, initial: 4 },
    effects: yifangAdditionalPerStack([7.2, 3.6, 9, 0.63, 0.9, 0.36], 0.1),
    rawDescription: "2画下，失衡期间每层颤音使核心被动异放伤害比例额外提升10%。",
    scopeNote: "作为核心异放倍率的附加部分登记；按满4层处理，实际事件中与核心异放合并。",
  }),
  makeRule({
    id: "nanoka:character_1511_talent_2_polar_disorder_count",
    characterId: "1511",
    label: "南宫羽｜2画：极性紊乱次数",
    key: "character:1511:talent:2",
    target: "enemy",
    timing: "on-trigger",
    trigger: "attack-hit",
    condition: stunned,
    cinemaAtLeast: 2,
    effects: [{ kind: "polar-disorder", operation: "add-percent", value: 25, maxTriggers: 3 }],
    rawDescription: "2画下，失衡期间极性紊乱的可触发次数由2次提升至3次。",
    scopeNote: "倍率仍为原紊乱伤害的25%；这里只提升次数上限。",
  }),
];

export const NANOKA_REVIEWED_BATCH_004: readonly BuffRule[] = batch004Rules;

export const NANOKA_REVIEWED_BATCH_004_BY_KEY: Readonly<Record<string, readonly BuffRule[]>> =
  batch004Rules.reduce<Record<string, BuffRule[]>>((groups, rule) => {
    const key = rule.source.key ?? rule.id;
    (groups[key] ??= []).push(rule);
    return groups;
  }, {});
