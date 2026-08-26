"""Reviewed Ye Shunguang semantic mapping used by the compiler.

The values in this module are manually reviewed semantic decisions derived
from the supplied character extraction.  Raw field extraction lives in
``source.py``; this module is deliberately not a general natural-language
parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.types import DamageTag, MoveId, SkillGroup

from ...moves import MultiplierRelation


class YeElementMode(StrEnum):
    PHYSICAL = "physical"
    LINREN = "linren"
    ENTRY = "entry"


@dataclass(frozen=True, slots=True)
class YeDamageParameter:
    variant_key: str
    parameter_name: str
    condition_key: str | None = None


@dataclass(frozen=True, slots=True)
class YeMoveSpec:
    entry_key: str
    move_id: MoveId
    display_name: str
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]
    source_name: str
    parameters: tuple[YeDamageParameter, ...]
    multiplier_relation: MultiplierRelation
    element_mode: YeElementMode
    stage_index: int | None = None
    requires_mingxin: bool = False
    repeat_parameter_key: str | None = None


@dataclass(frozen=True, slots=True)
class YeShunguangReviewedMapping:
    moves: tuple[YeMoveSpec, ...]
    data_quality_notes: tuple[str, ...] = ()


def _parameter(
    variant_key: str,
    parameter_name: str,
    *,
    condition_key: str | None = None,
) -> YeDamageParameter:
    return YeDamageParameter(
        variant_key=variant_key,
        parameter_name=parameter_name,
        condition_key=condition_key,
    )


def _move(
    entry_key: str,
    move_id: str,
    display_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    parameters: tuple[YeDamageParameter, ...],
    relation: MultiplierRelation,
    *,
    element_mode: YeElementMode = YeElementMode.PHYSICAL,
    stage_index: int | None = None,
    requires_mingxin: bool = False,
    repeat_parameter_key: str | None = None,
    source_name: str | None = None,
) -> YeMoveSpec:
    return YeMoveSpec(
        entry_key=entry_key,
        move_id=MoveId(move_id),
        display_name=display_name,
        skill_group=skill_group,
        damage_tags=damage_tags,
        source_name=source_name or display_name,
        parameters=parameters,
        multiplier_relation=relation,
        element_mode=element_mode,
        stage_index=stage_index,
        requires_mingxin=requires_mingxin,
        repeat_parameter_key=repeat_parameter_key,
    )


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset(
    {DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}
)
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
        (_parameter("stage-1", "一段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
        source_name="普通攻击：快剑",
    ),
    _move(
        "basic-fast-2",
        "move:basic-fast",
        "普通攻击：快剑（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-2", "二段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
        source_name="普通攻击：快剑",
    ),
    _move(
        "basic-fast-3",
        "move:basic-fast",
        "普通攻击：快剑（三段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-3", "三段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=3,
        source_name="普通攻击：快剑",
    ),
    _move(
        "basic-fast-4",
        "move:basic-fast",
        "普通攻击：快剑（四段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-4", "四段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=4,
        source_name="普通攻击：快剑",
    ),
    _move(
        "basic-cloud",
        "move:basic-cloud",
        "普通攻击：流云剑意",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("per-sword", "每道剑气伤害倍率"),),
        MultiplierRelation.UNIT_REPEAT,
        repeat_parameter_key=FLOWING_CLOUD_COUNT_PARAMETER_KEY,
    ),
    _move(
        "basic-mingxin-fenshui-1",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（一段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-1", "一段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
        requires_mingxin=True,
        source_name="普通攻击：明心境·分水行",
    ),
    _move(
        "basic-mingxin-fenshui-2",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-2", "二段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
        requires_mingxin=True,
        source_name="普通攻击：明心境·分水行",
    ),
    _move(
        "basic-mingxin-fenshui-3",
        "move:basic-mingxin-fenshui",
        "普通攻击：明心境·分水行（三段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-3", "三段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=3,
        requires_mingxin=True,
        source_name="普通攻击：明心境·分水行",
    ),
    _move(
        "basic-mingxin-fuyao",
        "move:basic-mingxin-fuyao",
        "普通攻击：明心境·扶摇势",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-ji",
        "move:basic-mingxin-zhanliuguang-ji",
        "普通攻击：明心境·斩流光 极",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "basic-mingxin-zhanliuguang-1",
        "move:basic-mingxin-zhanliuguang",
        "普通攻击：明心境·斩流光（一段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-1", "一段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=1,
        requires_mingxin=True,
        source_name="普通攻击：明心境·斩流光",
    ),
    _move(
        "basic-mingxin-zhanliuguang-2",
        "move:basic-mingxin-zhanliuguang",
        "普通攻击：明心境·斩流光（二段）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (_parameter("stage-2", "二段伤害倍率"),),
        MultiplierRelation.SEQUENTIAL_STAGE,
        stage_index=2,
        requires_mingxin=True,
        source_name="普通攻击：明心境·斩流光",
    ),
    _move(
        "basic-mingxin-zhanliuguang-mie",
        "move:basic-mingxin-zhanliuguang-mie",
        "普通攻击：明心境·斩流光 灭",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        (
            _parameter(
                "with-sword-force",
                "有青溟剑势时伤害倍率",
                condition_key=HAS_QINGMING_CONDITION_KEY,
            ),
            _parameter(
                "without-sword-force",
                "无青溟剑势时伤害倍率",
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
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "dodge-counter",
        "move:dodge-counter",
        "闪避反击：燕袭",
        SkillGroup.DODGE,
        _COUNTER,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "special-yin-canglan",
        "move:special-yin-canglan",
        "特殊技：引沧澜",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        (
            _parameter(
                "normal",
                "伤害倍率",
                condition_key=YIN_NORMAL_CONDITION_KEY,
            ),
            _parameter(
                "perfect-dodge",
                "触发极限闪避伤害倍率",
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
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "special-mingxin-fuyiqu",
        "move:special-mingxin-fuyiqu",
        "特殊技：明心境·拂衣去",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "special-mingxin-guichen",
        "move:special-mingxin-guichen",
        "强化特殊技：明心境·归尘",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "chain-zhanxiesui",
        "move:chain-zhanxiesui",
        "连携技：斩邪祟",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "ultimate-zhuyunjingting",
        "move:ultimate-zhuyunjingting",
        "终结技：逐云惊霆",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        element_mode=YeElementMode.ENTRY,
    ),
    _move(
        "chain-mingxin-chejinglei",
        "move:chain-mingxin-chejinglei",
        "连携技：明心境·掣惊雷",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "ultimate-zhanwangkaitian",
        "move:ultimate-zhanwangkaitian",
        "终结技：斩妄开天",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "assist-zhaoying",
        "move:assist-zhaoying",
        "登场技：照影",
        SkillGroup.ASSIST,
        _ASSIST,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        element_mode=YeElementMode.ENTRY,
    ),
    _move(
        "assist-yuanshou",
        "move:assist-yuanshou",
        "快速支援：援守",
        SkillGroup.ASSIST,
        _ASSIST,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "assist-zhige",
        "move:assist-zhige",
        "支援突击：止戈",
        SkillGroup.ASSIST,
        _ASSIST,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
    ),
    _move(
        "assist-mingxin-ceying",
        "move:assist-mingxin-ceying",
        "快速支援：明心境·策应",
        SkillGroup.ASSIST,
        _ASSIST,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
    _move(
        "assist-mingxin-baoyi",
        "move:assist-mingxin-baoyi",
        "支援突击：明心境·抱一",
        SkillGroup.ASSIST,
        _ASSIST,
        (_parameter("complete", "伤害倍率"),),
        MultiplierRelation.COMPLETE,
        requires_mingxin=True,
    ),
)


YE_SHUNGUANG_REVIEWED_MAPPING = YeShunguangReviewedMapping(
    moves=YE_SHUNGUANG_MOVES,
    data_quality_notes=(
        "强化特殊技：明心境·飞光的消耗1点与消耗6点倍率字段在来源数据中相同，按实现规范视为错误字段并忽略。",
    ),
)
