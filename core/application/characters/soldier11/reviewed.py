"""Reviewed Soldier 11 (1041) source identities and direct move mappings."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


SOLDIER11_ID = CharacterId("character:1041")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

BASIC_WARMUP_MOVE_ID = MoveId("move:soldier11:basic-warmup-sparks")
BASIC_SUPPRESSION_MOVE_ID = MoveId("move:soldier11:basic-fire-suppression")
POTENTIAL_FIREBURST_MOVE_ID = MoveId("move:soldier11:potential-fireburst")
DASH_PHYSICAL_MOVE_ID = MoveId("move:soldier11:dash-blazing-fire")
DASH_SUPPRESSION_MOVE_ID = MoveId("move:soldier11:dash-fire-suppression")
DODGE_COUNTER_MOVE_ID = MoveId("move:soldier11:dodge-counter-backfire")
SPECIAL_MOVE_ID = MoveId("move:soldier11:special-blazing-flame")
EX_SPECIAL_MOVE_ID = MoveId("move:soldier11:ex-special-fuel-on-flames")
CHAIN_MOVE_ID = MoveId("move:soldier11:chain-rising-flames")
ULTIMATE_MOVE_ID = MoveId("move:soldier11:ultimate-roaring-flames")
QUICK_ASSIST_MOVE_ID = MoveId("move:soldier11:assist-fire-support")
ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:soldier11:assist-rekindle")


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


_WARMUP_STAGES = ("一", "二", "三", "四")
_SUPPRESSION_STAGES = ("一", "二", "三", "四")

SOLDIER11_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-warmup-{stage}",
                BASIC_WARMUP_MOVE_ID,
                f"普通攻击：热身火花（{_WARMUP_STAGES[stage - 1]}段）",
                "普通攻击：热身火花",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_WARMUP_STAGES[stage - 1]}段伤害倍率",
                f"104100{stage * 2 - 1}",
                Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        *tuple(
            _move(
                f"basic-fire-suppression-{stage}",
                BASIC_SUPPRESSION_MOVE_ID,
                f"普通攻击：火力镇压（{_SUPPRESSION_STAGES[stage - 1]}段）",
                "普通攻击：火力镇压",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_SUPPRESSION_STAGES[stage - 1]}段伤害倍率",
                f"104100{stage * 2}",
                Element.FIRE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "dash-physical-blazing-fire",
            DASH_PHYSICAL_MOVE_ID,
            "冲刺攻击：炽火",
            "冲刺攻击：炽火",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1041012",
            Element.PHYSICAL,
        ),
        _move(
            "dash-fire-suppression",
            DASH_SUPPRESSION_MOVE_ID,
            "冲刺攻击：火力镇压",
            "冲刺攻击：火力镇压",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1041013",
            Element.FIRE,
        ),
        _move(
            "dodge-counter-backfire",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：逆火",
            "闪避反击：逆火",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1041015",
            Element.FIRE,
        ),
        _move(
            "special-blazing-flame",
            SPECIAL_MOVE_ID,
            "特殊技：烈火",
            "特殊技：烈火",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1041010",
            Element.FIRE,
        ),
        _move(
            "ex-special-fuel-on-flames",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：盛燃烈火",
            "强化特殊技：盛燃烈火",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1041011",
            Element.FIRE,
        ),
        _move(
            "chain-rising-flames",
            CHAIN_MOVE_ID,
            "连携技：昂扬烈焰",
            "连携技：昂扬烈焰",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1041016",
            Element.FIRE,
        ),
        _move(
            "ultimate-roaring-flames",
            ULTIMATE_MOVE_ID,
            "终结技：轰鸣烈焰",
            "终结技：轰鸣烈焰",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1041017",
            Element.FIRE,
        ),
        _move(
            "assist-fire-support",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：火力掩护",
            "快速支援：火力掩护",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1041019",
            Element.FIRE,
        ),
        _move(
            "assist-rekindle",
            ASSIST_FOLLOW_UP_MOVE_ID,
            "支援突击：重燃",
            "支援突击：重燃",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            "1041023",
            Element.FIRE,
        ),
    ),
    data_quality_notes=(
        "The raw record keeps separate Daze curves for these damage skills and three "
        "Parry Daze curves. The current request has no Daze result; no Daze multiplier "
        "is substituted for Direct damage.",
        "Potential charge/guard actions with no damage curve are not given invented "
        "damage entries. The raw Potential Fireburst curve is mapped only when a "
        "Potential level is selected.",
    ),
)

SOLDIER11_POTENTIAL_MOVES = (
    _move(
        "basic-fire-suppression-fifth",
        BASIC_SUPPRESSION_MOVE_ID,
        "普通攻击：火力镇压（第五段）",
        "普通攻击：火力镇压",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "五段伤害倍率",
        "1041024",
        Element.FIRE,
        relation=MultiplierRelation.SEQUENTIAL_STAGE,
        stage=5,
    ),
    _move(
        "basic-fire-suppression-fifth-enhanced",
        BASIC_SUPPRESSION_MOVE_ID,
        "强化普通攻击：火力镇压（第五段）",
        "普通攻击：火力镇压",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "强化普攻第五段伤害倍率",
        "1041025",
        Element.FIRE,
        relation=MultiplierRelation.SEQUENTIAL_STAGE,
        stage=5,
    ),
    _move(
        "potential-fireburst",
        POTENTIAL_FIREBURST_MOVE_ID,
        "潜能：普通攻击·火力迸发",
        "普通攻击:火力迸发",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
        "普通攻击:火力迸发伤害倍率",
        "1041027",
        Element.FIRE,
    ),
)


__all__ = [
    "ASSIST_FOLLOW_UP_MOVE_ID",
    "BASIC_SUPPRESSION_MOVE_ID",
    "BASIC_WARMUP_MOVE_ID",
    "CHAIN_MOVE_ID",
    "DASH_PHYSICAL_MOVE_ID",
    "DASH_SUPPRESSION_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "POTENTIAL_FIREBURST_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SOLDIER11_ID",
    "SOLDIER11_POTENTIAL_MOVES",
    "SOLDIER11_REVIEWED_MAPPING",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
