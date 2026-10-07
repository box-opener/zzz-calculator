"""Reviewed Nanoka 3.2 move identities for Yanagi (character:1221)."""

from __future__ import annotations

from core.types import (
    AnomalyRecordId,
    CharacterId,
    DamageTag,
    Element,
    MoveId,
    SkillGroup,
)

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


YANAGI_ID = CharacterId("character:1221")
YANAGI_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:character:1221:electric-shock"
)
POLARITY_TARGET_HAS_ACTIVE_ANOMALY = ScenarioConditionId(
    "condition:yanagi:target-has-active-anomaly"
)

BASIC_UPPER_MOVE_ID = MoveId("move:yanagi:basic-upper-stance")
BASIC_LOWER_MOVE_ID = MoveId("move:yanagi:basic-lower-stance")
DASH_ATTACK_MOVE_ID = MoveId("move:yanagi:dash-attack")
DODGE_COUNTER_MOVE_ID = MoveId("move:yanagi:dodge-counter")
SPECIAL_FLOWING_TURN_MOVE_ID = MoveId("move:yanagi:special-flowing-turn")
EX_SPECIAL_MOONLIT_FLOW_MOVE_ID = MoveId("move:yanagi:ex-special-moonlit-flow")
CHAIN_STAR_AND_MOON_MOVE_ID = MoveId("move:yanagi:chain-star-and-moon")
ULTIMATE_THUNDER_SHADOW_MOVE_ID = MoveId("move:yanagi:ultimate-thunder-shadow")
QUICK_ASSIST_FLOWER_SLASH_MOVE_ID = MoveId("move:yanagi:quick-assist-flower-slash")
ASSIST_STRIKE_FLYING_THISTLE_MOVE_ID = MoveId(
    "move:yanagi:assist-strike-flying-thistle"
)

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _stage(
    *,
    key: str,
    move_id: MoveId,
    stance_label: str,
    source_stance: str,
    stage: int,
    curve_id: str,
    element: Element,
) -> NanokaMoveSpec:
    stage_name = ("一", "二", "三", "四", "五")[stage - 1]
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=f"普通攻击：夜见尊神乐（{stance_label}·{stage_name}段）",
        source_name=source_stance,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=f"{stage_name}段伤害倍率",
                source_skill_id=curve_id,
            ),
        ),
        multiplier_relation=MultiplierRelation.SEQUENTIAL_STAGE,
        element=element,
        stage_index=stage,
    )


def _parameter(
    key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=display_name,
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
        multiplier_relation=MultiplierRelation.COMPLETE,
        element=element,
    )


YANAGI_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _stage(
                key=f"basic-upper-{stage}",
                move_id=BASIC_UPPER_MOVE_ID,
                stance_label="上弦",
                source_stance="架势：上弦",
                stage=stage,
                curve_id=f"122100{stage}",
                element=Element.PHYSICAL if stage <= 2 else Element.ELECTRIC,
            )
            for stage in range(1, 6)
        ),
        *tuple(
            _stage(
                key=f"basic-lower-{stage}",
                move_id=BASIC_LOWER_MOVE_ID,
                stance_label="下弦",
                source_stance="架势：下弦",
                stage=stage,
                curve_id=f"12210{stage + 5:02d}",
                element=Element.PHYSICAL if stage <= 2 else Element.ELECTRIC,
            )
            for stage in range(1, 6)
        ),
        _parameter(
            "dash-flyby",
            DASH_ATTACK_MOVE_ID,
            "冲刺攻击：飞掠",
            "冲刺攻击：飞掠",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1221013",
            Element.PHYSICAL,
        ),
        _parameter(
            "dodge-counter-swift-counter",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：疾反",
            "闪避反击：疾反",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1221014",
            Element.ELECTRIC,
        ),
        _parameter(
            "special-flowing-turn",
            SPECIAL_FLOWING_TURN_MOVE_ID,
            "特殊技：流转",
            "特殊技：流转",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1221011",
            Element.ELECTRIC,
        ),
        _parameter(
            "ex-special-moonlit-flow-thrust",
            EX_SPECIAL_MOONLIT_FLOW_MOVE_ID,
            "强化特殊技：月华流转（突刺）",
            "强化特殊技：月华流转",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "突刺攻击伤害倍率",
            "1221022",
            Element.ELECTRIC,
        ),
        _parameter(
            "ex-special-moonlit-flow-downfall",
            EX_SPECIAL_MOONLIT_FLOW_MOVE_ID,
            "强化特殊技：月华流转（下落攻击）",
            "强化特殊技：月华流转",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "下落攻击伤害倍率",
            "1221023",
            Element.ELECTRIC,
        ),
        _parameter(
            "chain-star-and-moon",
            CHAIN_STAR_AND_MOON_MOVE_ID,
            "连携技：星月相随",
            "连携技：星月相随",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1221015",
            Element.ELECTRIC,
        ),
        _parameter(
            "ultimate-thunder-shadow",
            ULTIMATE_THUNDER_SHADOW_MOVE_ID,
            "终结技：雷影天华",
            "终结技：雷影天华",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1221016",
            Element.ELECTRIC,
        ),
        _parameter(
            "quick-assist-flower-slash",
            QUICK_ASSIST_FLOWER_SLASH_MOVE_ID,
            "快速支援：风华斩",
            "快速支援：风华斩",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1221017",
            Element.ELECTRIC,
        ),
        _parameter(
            "assist-strike-flying-thistle",
            ASSIST_STRIKE_FLYING_THISTLE_MOVE_ID,
            "支援突击：飞絮刺",
            "支援突击：飞絮刺",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1221021",
            Element.ELECTRIC,
        ),
    ),
    data_quality_notes=(
        "The raw source exposes Daze and anomaly buildup curves, but the current "
        "calculation result does not output those quantities or replay the stance "
        "and energy timeline.",
    ),
)


__all__ = [
    "ASSIST_STRIKE_FLYING_THISTLE_MOVE_ID",
    "BASIC_LOWER_MOVE_ID",
    "BASIC_UPPER_MOVE_ID",
    "CHAIN_STAR_AND_MOON_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOONLIT_FLOW_MOVE_ID",
    "QUICK_ASSIST_FLOWER_SLASH_MOVE_ID",
    "SPECIAL_FLOWING_TURN_MOVE_ID",
    "ULTIMATE_THUNDER_SHADOW_MOVE_ID",
    "POLARITY_TARGET_HAS_ACTIVE_ANOMALY",
    "YANAGI_ELECTRIC_ANOMALY_RECORD_ID",
    "YANAGI_ID",
    "YANAGI_REVIEWED_MAPPING",
]
