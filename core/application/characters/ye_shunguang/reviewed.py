"""Reviewed Ye Shunguang semantic mapping used by the compiler.

The values in this module are manually reviewed semantic decisions derived
from the supplied character extraction.  Raw field extraction lives in
``source.py``; this module is deliberately not a general natural-language
parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation


class YeElementMode(StrEnum):
    PHYSICAL = "physical"
    LINREN = "linren"
    ENTRY = "entry"


@dataclass(frozen=True, slots=True)
class YeDamageParameter:
    variant_key: str
    label: str
    parameter_name: str
    levels: tuple[float, float, float]
    condition_key: str | None = None

    def value_for_level(self, level: int) -> float | None:
        values = {12: self.levels[0], 14: self.levels[1], 16: self.levels[2]}
        return values.get(level)


@dataclass(frozen=True, slots=True)
class YeMoveSpec:
    entry_key: str
    move_id: MoveId
    display_name: str
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]
    original_text: str
    parameters: tuple[YeDamageParameter, ...]
    multiplier_relation: MultiplierRelation
    element_mode: YeElementMode
    stage_index: int | None = None
    requires_mingxin: bool = False
    repeat_parameter_key: str | None = None


@dataclass(frozen=True, slots=True)
class YeShunguangReviewedSource:
    character_id: CharacterId
    name: str
    role: str
    element: Element
    core_passive_name: str
    core_passive_text: str
    core_damage_levels: tuple[tuple[float, float], ...]
    extra_ability_name: str
    extra_ability_text: str
    cinema_texts: tuple[tuple[int, str], ...]
    cinema_names: tuple[str, ...]
    moves: tuple[YeMoveSpec, ...]
    data_quality_notes: tuple[str, ...] = ()


def _parameter(
    variant_key: str,
    parameter_name: str,
    levels: tuple[float, float, float],
    *,
    condition_key: str | None = None,
) -> YeDamageParameter:
    return YeDamageParameter(
        variant_key=variant_key,
        label=parameter_name,
        parameter_name=parameter_name,
        levels=levels,
        condition_key=condition_key,
    )


def _move(
    entry_key: str,
    move_id: str,
    display_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    original_text: str,
    parameters: tuple[YeDamageParameter, ...],
    relation: MultiplierRelation,
    *,
    element_mode: YeElementMode = YeElementMode.PHYSICAL,
    stage_index: int | None = None,
    requires_mingxin: bool = False,
    repeat_parameter_key: str | None = None,
) -> YeMoveSpec:
    return YeMoveSpec(
        entry_key=entry_key,
        move_id=MoveId(move_id),
        display_name=display_name,
        skill_group=skill_group,
        damage_tags=damage_tags,
        original_text=original_text,
        parameters=parameters,
        multiplier_relation=relation,
        element_mode=element_mode,
        stage_index=stage_index,
        requires_mingxin=requires_mingxin,
        repeat_parameter_key=repeat_parameter_key,
    )


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_DODGE = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_ASSIST = frozenset({DamageTag.ASSIST})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})

MINGXIN_CONDITION_KEY = "mingxin_active"
ENTRY_LINREN_CONDITION_KEY = "entry_move_uses_linren"
HAS_QINGMING_CONDITION_KEY = "has_qingming_sword_force"
WITHOUT_QINGMING_CONDITION_KEY = "without_qingming_sword_force"
YIN_NORMAL_CONDITION_KEY = "normal_yin_canglan"
PERFECT_DODGE_CONDITION_KEY = "perfect_dodge"
FLOWING_CLOUD_COUNT_PARAMETER_KEY = "flowing_cloud_sword_count"


YE_SHUNGUANG_MOVES: tuple[YeMoveSpec, ...] = (
    _move(
        "basic-fast-1",
        "move:basic-fast",
        "普通攻击：快剑（一段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "点按普通攻击发动：向前方进行至多四段的斩击，造成物理伤害。",
        (_parameter("stage-1", "一段伤害倍率", (159.7, 174.3, 188.9)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
    ),
    _move(
        "basic-fast-2",
        "move:basic-fast",
        "普通攻击：快剑（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "点按普通攻击发动：向前方进行至多四段的斩击，造成物理伤害。",
        (_parameter("stage-2", "二段伤害倍率", (488.3, 532.7, 577.1)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
    ),
    _move(
        "basic-fast-3",
        "move:basic-fast",
        "普通攻击：快剑（三段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "点按普通攻击发动：向前方进行至多四段的斩击，造成物理伤害。",
        (_parameter("stage-3", "三段伤害倍率", (250.0, 272.8, 295.6)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=3,
    ),
    _move(
        "basic-fast-4",
        "move:basic-fast",
        "普通攻击：快剑（四段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "点按普通攻击发动：向前方进行至多四段的斩击，造成物理伤害。",
        (_parameter("stage-4", "四段伤害倍率", (736.5, 803.5, 870.5)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=4,
    ),
    _move(
        "basic-cloud",
        "move:basic-cloud",
        "普通攻击：流云剑意",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "长按普通攻击发动：快速发动多道剑气，造成物理伤害，可以通过长按延长攻击。",
        (_parameter("per-sword", "每道剑气伤害倍率", (234.4, 255.8, 277.2)),),
        MultiplierRelation.UNIT_REPEAT,
        repeat_parameter_key=FLOWING_CLOUD_COUNT_PARAMETER_KEY,
    ),
    _move(
        "basic-mingxin-fenshui-1",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（一段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下并处于地面时，点按普通攻击发动：向前方进行至多三段的斩击，造成物理伤害。",
        (_parameter("stage-1", "一段伤害倍率", (225.9, 246.5, 267.1)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-fenshui-2",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下并处于地面时，点按普通攻击发动：向前方进行至多三段的斩击，造成物理伤害。",
        (_parameter("stage-2", "二段伤害倍率", (312.1, 340.5, 368.9)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-fenshui-3",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（三段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下并处于地面时，点按普通攻击发动：向前方进行至多三段的斩击，造成物理伤害。",
        (_parameter("stage-3", "三段伤害倍率", (433.3, 472.7, 512.1)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=3,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-fuyao",
        "move:basic-mingxin-fuyao",
        "普通攻击：明心境·扶摇势",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下，拥有青溟剑势时，第二段分水行后点按普通攻击发动：快速发动升空攻击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (182.3, 198.9, 215.5)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-ji",
        "move:basic-mingxin-zhanliuguang-ji",
        "普通攻击：明心境·斩流光 极",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在斩流光灭发动后，拥有青溟剑势时，点按普通攻击发动：向前方进行大范围斩击，造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (1209.8, 1319.8, 1429.8)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-1",
        "move:basic-mingxin-zhanliuguang",
        "普通攻击：明心境·斩流光（一段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下并处于空中时，点按普通攻击发动：向前下方进行至多两段的斩击，造成物理伤害。",
        (_parameter("stage-1", "一段伤害倍率", (241.7, 263.7, 285.7)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-2",
        "move:basic-mingxin-zhanliuguang",
        "普通攻击：明心境·斩流光（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "在明心境状态下并处于空中时，点按普通攻击发动：向前下方进行至多两段的斩击，造成物理伤害。",
        (_parameter("stage-2", "二段伤害倍率", (313.8, 342.4, 371.0)),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-mie",
        "move:basic-mingxin-zhanliuguang-mie",
        "普通攻击：明心境·斩流光 灭",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "发动第二段斩流光后点按普通攻击发动：发动下坠攻击，依据是否拥有青溟剑势使用不同伤害倍率。",
        (
            _parameter(
                "with-sword-force",
                "有青溟剑势时伤害倍率",
                (1783.3, 1945.5, 2107.7),
                condition_key=HAS_QINGMING_CONDITION_KEY,
            ),
            _parameter(
                "without-sword-force",
                "无青溟剑势时伤害倍率",
                (320.5, 349.7, 378.9),
                condition_key=WITHOUT_QINGMING_CONDITION_KEY,
            ),
        ),
        MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        requires_mingxin=True,
    ),
    _move(
        "dodge-dash",
        "move:dodge-dash",
        "冲刺攻击：如影疾行",
        SkillGroup.DODGE,
        _DODGE,
        "闪避时点按普通攻击发动：向前方进行斩击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (210.6, 229.8, 249.0)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "dodge-counter",
        "move:dodge-counter",
        "闪避反击：燕袭",
        SkillGroup.DODGE,
        _COUNTER,
        "触发极限闪避后点按普通攻击发动：跃起并向前方进行刺击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (692.8, 755.8, 818.8)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "special-yin-canglan",
        "move:special-yin-canglan",
        "特殊技：引沧澜",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        "点按特殊攻击发动：根据是否触发极限闪避，对敌人发动快速剑气或飞剑攻击，造成物理伤害。",
        (
            _parameter(
                "normal",
                "伤害倍率",
                (197.9, 215.9, 233.9),
                condition_key=YIN_NORMAL_CONDITION_KEY,
            ),
            _parameter(
                "perfect-dodge",
                "触发极限闪避伤害倍率",
                (632.7, 690.3, 747.9),
                condition_key=PERFECT_DODGE_CONDITION_KEY,
            ),
        ),
        MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
    ),
    _move(
        "special-dingfengbo",
        "move:special-dingfengbo",
        "强化特殊技：定风波",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        "能量足够时点按强化特殊攻击发动：对敌人造成突进斩击和飞剑攻击，造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (2357.6, 2572.0, 2786.4)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "special-mingxin-fuyiqu",
        "move:special-mingxin-fuyiqu",
        "特殊技：明心境·拂衣去",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        "在明心境状态下处于地面时点按强化特殊攻击发动：发动快速的后撤斩击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (142.5, 155.5, 168.5)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "special-mingxin-guichen",
        "move:special-mingxin-guichen",
        "强化特殊技：明心境·归尘",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        "在明心境状态下点按终结技或剑势耗尽时长按强化特殊攻击发动：对大范围敌人造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (2322.7, 2533.9, 2745.1)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "chain-zhanxiesui",
        "move:chain-zhanxiesui",
        "连携技：斩邪祟",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        "触发连携技时选择对应角色发动：对前方大范围敌人发动强力斩击，造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (1743.9, 1902.5, 2061.1)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "ultimate-zhuyunjingting",
        "move:ultimate-zhuyunjingting",
        "终结技：逐云惊霆",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        "喧响等级达到极时点按终结技发动：进入明心境，开启以太帷幕·决裁，获得6点青溟剑势，并造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (3850.0, 4200.0, 4550.0)),),
        MultiplierRelation.COMPLETE,
        element_mode=YeElementMode.ENTRY,
    ),
    _move(
        "chain-mingxin-chejinglei",
        "move:chain-mingxin-chejinglei",
        "连携技：明心境·掣惊雷",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        "在明心境状态下触发连携技时选择对应角色发动：对前方大范围敌人发动强力斩击，造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (1817.2, 1982.4, 2147.6)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "ultimate-zhanwangkaitian",
        "move:ultimate-zhanwangkaitian",
        "终结技：斩妄开天",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        "在明心境状态下点按终结技或剑势耗尽后长按强化特殊攻击发动：召唤巨剑，对敌人造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (6168.7, 6729.5, 7290.3)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "assist-zhaoying",
        "move:assist-zhaoying",
        "登场技：照影",
        SkillGroup.ASSIST,
        _ASSIST,
        "拥有6点青溟剑势时在非明心境状态下从后场切换至前场发动：进入明心境，开启以太帷幕·决裁，对前方大范围敌人造成物理伤害。",
        (_parameter("complete", "伤害倍率", (800.8, 873.6, 946.4)),),
        MultiplierRelation.COMPLETE,
        element_mode=YeElementMode.ENTRY,
    ),
    _move(
        "assist-yuanshou",
        "move:assist-yuanshou",
        "快速支援：援守",
        SkillGroup.ASSIST,
        _ASSIST,
        "当前操作角色被击飞时点按切换发动：跃起并向前方进行刺击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (161.9, 176.7, 191.5)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "assist-zhige",
        "move:assist-zhige",
        "支援突击：止戈",
        SkillGroup.ASSIST,
        _ASSIST,
        "发动招架支援后点按普通攻击发动：造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (828.4, 903.8, 979.2)),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "assist-mingxin-ceying",
        "move:assist-mingxin-ceying",
        "快速支援：明心境·策应",
        SkillGroup.ASSIST,
        _ASSIST,
        "在明心境状态下当前操作角色被击飞时点按切换发动：向前方进行一次斩击，造成物理伤害。",
        (_parameter("complete", "伤害倍率", (135.5, 147.9, 160.3)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "assist-mingxin-baoyi",
        "move:assist-mingxin-baoyi",
        "支援突击：明心境·抱一",
        SkillGroup.ASSIST,
        _ASSIST,
        "在明心境状态下发动招架支援后点按普通攻击发动：造成大量物理伤害。",
        (_parameter("complete", "伤害倍率", (860.1, 938.3, 1016.5)),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
)


YE_SHUNGUANG_REVIEWED_SOURCE = YeShunguangReviewedSource(
    character_id=CharacterId("character:1431"),
    name="叶瞬光",
    role="强攻",
    element=Element.PHYSICAL,
    core_passive_name="核心被动：照破无明",
    core_passive_text=(
        "非明心境状态且未拥有6点青溟剑势时，部分攻击会缓慢积攒青溟剑势；"
        "任意方式获得青溟剑势时，每溢出1点青溟剑势，将转化为1层载物效果，"
        "至多叠加3层，在退出明心境状态时，会消耗所有载物获得对应层数的青溟剑势。"
        "进入战场时，获得合道效果，暴击率提升，造成的伤害提升。"
        "释放终结技：逐云惊霆或登场技：照影后，叶瞬光将进入明心境状态，并开启以太帷幕·决裁；"
        "明心境状态下，叶瞬光使用更加强力的招式，造成的物理伤害均为凛刃伤害。"
        "以太帷幕·决裁持续期间，敌人进入帷幕时将基于其此时的失衡易伤倍率附加帷幕易伤，"
        "叶瞬光发动的招式不计算敌人的失衡易伤，转而计算帷幕易伤。"
    ),
    core_damage_levels=(
        (0.15, 0.10),
        (0.175, 0.125),
        (0.20, 0.15),
        (0.225, 0.175),
        (0.25, 0.20),
        (0.275, 0.225),
        (0.30, 0.25),
    ),
    extra_ability_name="额外能力：溯影惊鸿",
    extra_ability_text=(
        "队伍中存在支援或防护角色时触发：队友开启任意以太帷幕时，获得3点青溟剑势，"
        "若自身已经处于明心境状态，则会转化为3层载物效果。"
    ),
    cinema_texts=(
        (
            1,
            "进入战场时，获得6点青溟剑势；核心被动中合道效果额外使造成的伤害提升10%，无视目标20%防御力。",
        ),
        (
            2,
            "载物可叠加层数提升至6层，观止可叠加至9层；明心境状态下每消耗1点青溟剑势获得1层观止；飞光和斩妄开天造成的伤害无视目标40%防御力。",
        ),
        (
            4,
            "进入战场时获得1000点喧响值；以太帷幕·决裁提供的帷幕易伤加成上限提升至200%。",
        ),
        (
            6,
            "进入战场时获得2层明灯愿；每次进入明心境获得1层明灯愿，至多4层；拥有3层时将归尘替换为斩妄开天；归尘和斩妄开天最后一击额外造成1500%攻击力的物理伤害。",
        ),
    ),
    cinema_names=("梦中身", "光与影", "共黯尘", "明灯愿"),
    moves=YE_SHUNGUANG_MOVES,
    data_quality_notes=(
        "强化特殊技：明心境·飞光的消耗1点与消耗6点倍率字段在来源数据中相同，按实现规范视为错误字段并忽略。",
    ),
)
