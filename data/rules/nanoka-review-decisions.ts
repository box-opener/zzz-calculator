import type { BuffRule } from "../../src/domain/model/buff.js";
import { NANOKA_REVIEWED_BATCH_002_BY_KEY } from "./nanoka-reviewed-batch-002.js";
import { NANOKA_REVIEWED_BATCH_003_BY_KEY } from "./nanoka-reviewed-batch-003.js";
import { NANOKA_REVIEWED_BATCH_004_BY_KEY } from "./nanoka-reviewed-batch-004.js";

function rulesFor(key: string): readonly BuffRule[] {
  const rules = NANOKA_REVIEWED_BATCH_002_BY_KEY[key];
  if (!rules) throw new Error(`缺少第二批人工确认规则：${key}`);
  return rules;
}

function rulesForBatch003(key: string): readonly BuffRule[] {
  const rules = NANOKA_REVIEWED_BATCH_003_BY_KEY[key];
  if (!rules) throw new Error(`缺少第三批人工确认规则：${key}`);
  return rules;
}

function rulesForBatch004(key: string): readonly BuffRule[] {
  const rules = NANOKA_REVIEWED_BATCH_004_BY_KEY[key];
  if (!rules) throw new Error(`缺少第四批人工确认规则：${key}`);
  return rules;
}

export type NanokaReviewDecision =
  | { action: "ignore"; reason: string }
  | { action: "promote"; rule?: BuffRule | undefined; rules?: readonly BuffRule[]; reason: string };

/** 第一批人工审查结果：供版本化解析数据库重建时应用。 */
export const NANOKA_REVIEW_DECISIONS_BATCH_001: Readonly<Record<string, NanokaReviewDecision>> = {
  "character:1251:talent:6": {
    action: "promote",
    rules: rulesFor("character:1251:talent:6"),
    reason: "确认20%全属性伤害抗性降低，以及普通攻击：醉花月云转暴击伤害+100%；打断等级忽略。",
  },
  "character:1261:talent:2": {
    action: "promote",
    rules: rulesFor("character:1261:talent:2"),
    reason: "确认15%防御无视只作用于强击，不覆盖紊乱；强击异常暴击伤害区额外+50%。",
  },
  "character:1501:talent:1": {
    action: "promote",
    rules: rulesFor("character:1501:talent:1"),
    reason: "确认新增异放独立暴击区。",
  },
  "character:1561:talent:1": {
    action: "ignore",
    reason: "失衡暂不考虑；乱流、风化属于待补充的新伤害标签，等待后续完整数据。",
  },
  "character:1061:talent:2": {
    action: "promote",
    rules: rulesFor("character:1061:talent:2"),
    reason: "0.5%×20层=10%物理抗性降低，按默认全覆盖。",
  },
  "character:1111:passive:1111507:1": {
    action: "ignore",
    reason: "按审查结论暂不计算该额外感电伤害。",
  },
  "character:1111:passive:1111506:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1111:passive:1111501:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1111:passive:1111502:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1111:passive:1111503:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1111:passive:1111504:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1111:passive:1111505:1": {
    action: "ignore",
    reason: "与已审查的安东同一被动，仅为等级/内部编号差异，沿用忽略决定。",
  },
  "character:1141:passive:1141514:0": {
    action: "promote",
    reason: "审查确认当前解析候选正确，无需修改。",
  },
  "character:1141:passive:1141513:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1141:passive:1141508:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1141:passive:1141509:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1141:passive:1141510:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1141:passive:1141511:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1141:passive:1141512:0": {
    action: "promote",
    reason: "与已审查的莱卡恩同一被动，仅为等级/内部编号差异，沿用已确认解析。",
  },
  "character:1241:talent:4": {
    action: "promote",
    rules: rulesFor("character:1241:talent:4"),
    reason: "确认普通攻击和冲刺攻击默认无视25%以太伤害抗性。",
  },
  "character:1261:passive:1261507:0": {
    action: "promote",
    rules: rulesForBatch003("character:1261:passive:1261507:0"),
    reason: "确认新增强击异常暴击区。",
  },
  "character:1311:talent:1": {
    action: "promote",
    rules: rulesFor("character:1311:talent:1"),
    reason: "6%×3层=18%全属性抗性降低；忽略无敌。",
  },
};

const batch003Promote = (key: string, reason: string): NanokaReviewDecision => ({
  action: "promote",
  rules: rulesForBatch003(key),
  reason,
});

const batch003Ignore = (reason: string): NanokaReviewDecision => ({
  action: "ignore",
  reason,
});

const jianBatch003Decisions = Object.fromEntries(
  ["1261501", "1261502", "1261503", "1261504", "1261505", "1261506", "1261507"]
    .map((level) => [
      `character:1261:passive:${level}:0`,
      batch003Promote(
        `character:1261:passive:${level}:0`,
        "确认新增强击异常暴击区：暴击伤害50%，暴击率为基础值加异常精通转化值，暴击率上限100%。",
      ),
    ]),
) as Readonly<Record<string, NanokaReviewDecision>>;

const vivianBatch003Decisions = Object.fromEntries(
  ["1331501", "1331502", "1331503", "1331504", "1331505", "1331506", "1331507"]
    .map((level) => [
      `character:1331:passive:${level}:0`,
      batch003Promote(
        `character:1331:passive:${level}:0`,
        "确认新增异放伤害：由异常精通转化比例乘本次对应属性异常伤害，使用异放伤害标签；预言等后续机制另行细化。",
      ),
    ]),
) as Readonly<Record<string, NanokaReviewDecision>>;

const xixifuBatch003Decisions = Object.fromEntries(
  ["1521049", "1521050", "1521051", "1521052", "1521053", "1521054", "1521055"]
    .map((level) => [
      `character:1521:passive:${level}:0`,
      batch003Ignore("希希芙该核心被动机制复杂，当前暂不处理资源、能量换算和蚀骨流程。"),
    ]),
) as Readonly<Record<string, NanokaReviewDecision>>;

/** 第二批合并语义组的审查结果；同一核心被动的所有等级一次性应用。 */
export const NANOKA_REVIEW_DECISIONS_BATCH_002: Readonly<Record<string, NanokaReviewDecision>> = {
  ...jianBatch003Decisions,
  ...vivianBatch003Decisions,
  "character:1341:talent:1": batch003Promote(
    "character:1341:talent:1",
    "确认全队直伤/贯穿伤害无视15%全属性抗性，持续50秒并刷新；不作用于异常标签伤害。",
  ),
  "character:1371:talent:2": batch003Promote(
    "character:1371:talent:2",
    "确认两个效果：终结技/强化特殊技以太抗性无视15%，以及新增强化特殊技符法千重·破的1200%贯穿力伤害；其余资源链暂不处理。",
  ),
  "character:1431:talent:2": batch003Promote(
    "character:1431:talent:2",
    "只保留明心境·飞光和斩妄开天造成伤害无视40%防御力。",
  ),
  "character:1451:talent:1": batch003Promote(
    "character:1451:talent:1",
    "确认巡梦童谣状态下直伤/贯穿伤害无视18%全属性抗性，其他效果忽略。",
  ),
  "character:1511:talent:1": batch003Promote(
    "character:1511:talent:1",
    "确认全属性抗性降低18%，所有伤害标签均可享受；其他效果忽略。",
  ),
  "character:1541:talent:6": batch003Promote(
    "character:1541:talent:6",
    "确认异常/异放/紊乱伤害无视15%全属性抗性，并新增一次对应属性200%异常伤害的异放。",
  ),
  ...xixifuBatch003Decisions,
};

const batch004Promote = (key: string, reason: string): NanokaReviewDecision => ({
  action: "promote",
  rules: rulesForBatch004(key),
  reason,
});

const batch004PromoteExisting = (reason: string): NanokaReviewDecision => ({
  action: "promote",
  reason,
});

/** 第四批异常伤害复审结果；空白结论不在这里登记，继续留在人工队列。 */
export const NANOKA_REVIEW_DECISIONS_BATCH_003: Readonly<Record<string, NanokaReviewDecision>> = {
  "character:1561:passive:1561507:1": batch004Promote(
    "character:1561:passive:1561507:1",
    "忽略异常积蓄抗性降低；保留30%失衡值提升、风化/乱流10%对应增伤，并加入终结技680%异放。",
  ),
  "character:1581:talent:2": batch004Promote(
    "character:1581:talent:2",
    "确认2画异化系数+20%；异常类伤害（不含耀变）无视15%防御力，幻色消失后的8秒延长交由状态层。",
  ),
  "character:1091:passive:1091507:1": batch004PromoteExisting(
    "解析候选与审查结论一致，沿用现有普通攻击伤害提升与冰抗性无视规则。",
  ),
  "character:1161:passive:1161507:0": batch004Promote(
    "character:1161:passive:1161507:0",
    "士气喷发期间目标冰、火抗性均降低15%，持续30秒；其余资源和失衡持续时间机制忽略。",
  ),
  "character:1511:passive:1511055:1": batch004Promote(
    "character:1511:passive:1511055:1",
    "失衡期间可造成两次25%原紊乱伤害的极性紊乱；失衡易伤倍率提高30%。",
  ),
  "character:1541:passive:1541507:0": batch004Promote(
    "character:1541:passive:1541507:0",
    "异常掌控超过150后转化自身异常精通和全队异放增伤；处刑式·绝裁登记635%对应属性异放。",
  ),
  "character:1561:passive:1561507:0": batch004Promote(
    "character:1561:passive:1561507:0",
    "按局外能量自动回复换算造成的伤害与异常掌控；乱流倍率+150%；登记145%/255%两种互斥异放分支。",
  ),
  "character:1581:passive:1581507:0": batch004Promote(
    "character:1581:passive:1581507:0",
    "确认异化系数为异常效果强度独立乘区：异常精通0.02%与三名异常角色额外10%相加。耀变后续倍率链暂不在本批展开。",
  ),
  "character:1071:passive:1071507:0": {
    action: "ignore",
    reason: "无需解析，不影响伤害。",
  },
  "character:1091:passive:1091507:0": batch004PromoteExisting(
    "仅保留已确认的霜灼·破1500%攻击力无标签直接伤害，沿用现有规则。",
  ),
  "character:1171:skill:special:5": batch004Promote(
    "character:1171:skill:special:5",
    "只登记一次对应属性异放；原属性异常倍率采用乘原属性异常语义，忽略流火计数、无敌和衔接。",
  ),
  "character:1181:skill:special:4": batch004Promote(
    "character:1181:skill:special:4",
    "只登记一次对应属性异放；原属性异常倍率采用乘原属性异常语义，忽略脉冲、电能和资源链。",
  ),
  "character:1221:talent:2": batch004Promote(
    "character:1221:talent:2",
    "2画满突刺时极性紊乱倍率为原紊乱伤害50%，由20%+2×15%得到。",
  ),
  "character:1221:talent:4": batch004Promote(
    "character:1221:talent:4",
    "识破是挂在敌人身上的Debuff，穿透率+16%对全队、所有伤害标签生效。",
  ),
  "character:1401:skill:basic:1": batch004Promote(
    "character:1401:skill:basic:1",
    "三段蓄力普通攻击登记一次713%极性强击伤害。",
  ),
  "character:1511:passive:1511055:0": batch004Promote(
    "character:1511:passive:1511055:0",
    "忽略异常积蓄与重拍资源；保留异常精通+120、动态冲击力、颤音异放、全队伤害+25%。",
  ),
  "character:1511:talent:2": batch004Promote(
    "character:1511:talent:2",
    "失衡期间每层颤音使核心异放倍率额外+10%，极性紊乱次数上限由2变3。",
  ),
};
