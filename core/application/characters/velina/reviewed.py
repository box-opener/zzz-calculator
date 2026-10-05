"""Reviewed source identities and curve mappings for Velina (1561)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


VELINA_ID = CharacterId("character:1561")
VELINA_WIND_RECORD_ID = AnomalyRecordId("anomaly:character:1561:wind-weathering")

CINEMA4_ATTACK_ACTIVE = ScenarioConditionId("condition:velina:cinema4-attack-active")
ENEMY_WIND_WEATHERED = ScenarioConditionId("condition:velina:enemy-wind-weathered")
MICRO_CYCLONE_DISSIPATING = ScenarioConditionId(
    "condition:velina:micro-cyclone-dissipating"
)
BROAD_CYCLONE_DISSIPATING = ScenarioConditionId(
    "condition:velina:broad-cyclone-dissipating"
)
WIND_EROSION_STACKS = ScenarioParameterId("parameter:velina:wind-erosion-stacks")
WIND_WEATHERING_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:velina:wind-weathering-remaining-seconds"
)

BASIC_DANCE_MOVE_ID = MoveId("move:velina:basic-fan-dance")
DASH_ATTACK_MOVE_ID = MoveId("move:velina:dash-step-the-wind")
DODGE_COUNTER_MOVE_ID = MoveId("move:velina:counter-broken-clouds")
SPECIAL_MOVE_ID = MoveId("move:velina:special-wind-shear")
EX_SPECIAL_MOVE_ID = MoveId("move:velina:ex-wind-shear-clear")
EX_SPECIAL_FINALE_MOVE_ID = MoveId("move:velina:ex-wind-shear-finale")
EX_SPECIAL_STORM_EYE_MOVE_ID = MoveId("move:velina:ex-storm-eye")
BROAD_CYCLONE_MOVE_ID = MoveId("move:velina:broad-cyclone")
MICRO_CYCLONE_MOVE_ID = MoveId("move:velina:micro-cyclone")
CHAIN_ATTACK_MOVE_ID = MoveId("move:velina:chain-whirling-chapter")
ULTIMATE_MOVE_ID = MoveId("move:velina:ultimate-hear-the-wind")
QUICK_ASSIST_MOVE_ID = MoveId("move:velina:quick-assist-emergency-plan")
ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:velina:assist-negotiation")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
# The source calls these EX Special Attacks. Special skill group and the EX tag
# are separate dimensions; the EX event therefore carries only the EX tag.
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    skill_id: str,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    repeat: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter,
                source_skill_id=skill_id,
                repeat_count=repeat,
            ),
        ),
        multiplier_relation=relation,
        element=Element.WIND,
        stage_index=stage,
    )


_BASIC_STAGE = ("一", "二", "三", "四", "五")

VELINA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-fan-dance-{stage}",
                BASIC_DANCE_MOVE_ID,
                f"普通攻击：扇舞（{_BASIC_STAGE[stage - 1]}段）",
                "普通攻击：扇舞",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_BASIC_STAGE[stage - 1]}段伤害倍率",
                f"156100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "dash-step-the-wind",
            DASH_ATTACK_MOVE_ID,
            "冲刺攻击：踏风",
            "冲刺攻击：踏风",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1561011",
        ),
        _move(
            "counter-broken-clouds",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：折云",
            "闪避反击：折云",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1561012",
        ),
        _move(
            "special-wind-shear",
            SPECIAL_MOVE_ID,
            "特殊技：风切变·激浊",
            "特殊技：风切变·激浊",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1561008",
        ),
        _move(
            "ex-wind-shear-clear",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：风切变·扬清",
            "强化特殊技：风切变·扬清",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1561009",
        ),
        _move(
            "ex-wind-shear-finale",
            EX_SPECIAL_FINALE_MOVE_ID,
            "强化特殊技：风切变·三重绝息",
            "强化特殊技：风切变·三重绝息",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1561010",
        ),
        _move(
            "ex-storm-eye",
            EX_SPECIAL_STORM_EYE_MOVE_ID,
            "强化特殊技：风切变·风暴眼",
            "强化特殊技：风切变·风暴眼",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1561006",
        ),
        _move(
            "micro-cyclone",
            MICRO_CYCLONE_MOVE_ID,
            "微域气旋（强化特殊技伤害）",
            "微域气旋",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1561021",
        ),
        _move(
            "broad-cyclone-wind",
            BROAD_CYCLONE_MOVE_ID,
            "广域气旋（风属性单次攻击 × 10）",
            "广域气旋",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "[广域气旋]风属性单次攻击伤害倍率",
            "1561007",
            relation=MultiplierRelation.UNIT_REPEAT,
            repeat=10,
        ),
        _move(
            "chain-whirling-chapter",
            CHAIN_ATTACK_MOVE_ID,
            "连携技：旋舞华章",
            "连携技：旋舞华章",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1561013",
        ),
        _move(
            "ultimate-hear-the-wind",
            ULTIMATE_MOVE_ID,
            "终结技：聆听呼啸",
            "终结技：聆听呼啸",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1561014",
        ),
        _move(
            "quick-assist-emergency-plan",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：紧急预案",
            "快速支援：紧急预案",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1561015",
        ),
        _move(
            "assist-negotiation",
            ASSIST_FOLLOW_UP_MOVE_ID,
            "支援突击：谈判技巧",
            "支援突击：谈判技巧",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1561019",
        ),
    ),
    data_quality_notes=(
        "The source keeps separate Daze and buildup curves. They are retained as "
        "source data and are not substituted for damage multipliers because the "
        "current result contract does not calculate those results.",
        "Cyclone ticks and their Wind/infused elements are compiled as separate "
        "single-element outputs; Wind and infused damage are not added together.",
    ),
)


__all__ = [
    "ASSIST_FOLLOW_UP_MOVE_ID",
    "BASIC_DANCE_MOVE_ID",
    "BROAD_CYCLONE_DISSIPATING",
    "BROAD_CYCLONE_MOVE_ID",
    "CINEMA4_ATTACK_ACTIVE",
    "CHAIN_ATTACK_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ENEMY_WIND_WEATHERED",
    "EX_SPECIAL_FINALE_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "EX_SPECIAL_STORM_EYE_MOVE_ID",
    "MICRO_CYCLONE_DISSIPATING",
    "MICRO_CYCLONE_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "VELINA_ID",
    "VELINA_REVIEWED_MAPPING",
    "VELINA_WIND_RECORD_ID",
    "WIND_EROSION_STACKS",
    "WIND_WEATHERING_REMAINING_SECONDS",
]
