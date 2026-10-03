"""Reviewed Qingyi (1251) identities and direct-source mapping."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


QINGYI_ID = CharacterId("character:1251")

FLASHOVER_ACTIVE = ScenarioConditionId("condition:qingyi:flashover-active")
C1_TARGET_DEBUFF_ACTIVE = ScenarioConditionId("condition:qingyi:c1-target-debuff-active")
C6_ALL_RESISTANCE_ACTIVE = ScenarioConditionId("condition:qingyi:c6-all-resistance-active")
SUBJUGATION_STACKS = ScenarioParameterId("parameter:qingyi:subjugation-stacks")
FLASHOVER_EXCESS_PERCENT = ScenarioParameterId(
    "parameter:qingyi:flashover-excess-percent"
)
ELECTRIC_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:qingyi:electric-disorder-remaining-seconds"
)

BASIC_YISHA_MOVE_ID = MoveId("move:qingyi:basic-yisha")
BASIC_DRUNKEN_CLOUD_MOVE_ID = MoveId("move:qingyi:basic-drunken-cloud")
BASIC_MOON_TURN_MOVE_ID = MoveId("move:qingyi:basic-drunken-flower-moon-turn")
DASH_ATTACK_MOVE_ID = MoveId("move:qingyi:dash-entry")
DODGE_COUNTER_MOVE_ID = MoveId("move:qingyi:dodge-counter-intention")
SPECIAL_MOVE_ID = MoveId("move:qingyi:special-day-brocade-hall")
EX_SPECIAL_MOVE_ID = MoveId("move:qingyi:ex-special-moon-over-sea-begonia")
CHAIN_MOVE_ID = MoveId("move:qingyi:chain-peaceful-order")
ULTIMATE_MOVE_ID = MoveId("move:qingyi:ultimate-eight-sounds-ganzhou")
QUICK_ASSIST_MOVE_ID = MoveId("move:qingyi:quick-assist-pine-wind")
SUPPORT_FOLLOWUP_MOVE_ID = MoveId("move:qingyi:support-followup-clear-river-song")
ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:qingyi:electric-current")
ELECTRIC_ANOMALY_MOVE_ID = MoveId("move:qingyi:electric-anomaly")
ELECTRIC_DISORDER_MOVE_ID = MoveId("move:qingyi:electric-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOWUP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _parameter(key: str, name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    skill_group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    conditions: tuple = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=skill_group,
        damage_tags=tags,
        parameters=(_parameter(f"{key}-damage", parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


# These entries have one explicitly identified damage attribute in Nanoka's
# move prose. Basic: 一煞 and its stage curves are compiled separately because
# the prose says the move deals both Physical and Electric damage but does not
# assign the raw curves to either attribute.
QINGYI_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-drunken-cloud",
            BASIC_DRUNKEN_CLOUD_MOVE_ID,
            "普通攻击：醉花云",
            "普通攻击：醉花云",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1251007",
            Element.ELECTRIC,
        ),
        _move(
            "dash-entry",
            DASH_ATTACK_MOVE_ID,
            "冲刺攻击：入破",
            "冲刺攻击：入破",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1251012",
            Element.PHYSICAL,
        ),
        _move(
            "dodge-counter-intention",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：意不尽",
            "闪避反击：意不尽",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1251013",
            Element.ELECTRIC,
        ),
        _move(
            "special-day-brocade-hall",
            SPECIAL_MOVE_ID,
            "特殊技：昼锦堂",
            "特殊技：昼锦堂",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1251010",
            Element.ELECTRIC,
        ),
        _move(
            "chain-peaceful-order",
            CHAIN_MOVE_ID,
            "连携技：太平令",
            "连携技：太平令",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1251014",
            Element.ELECTRIC,
        ),
        _move(
            "ultimate-eight-sounds-ganzhou",
            ULTIMATE_MOVE_ID,
            "终结技：八声甘州",
            "终结技：八声甘州",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1251015",
            Element.ELECTRIC,
        ),
        _move(
            "quick-assist-pine-wind",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：风入松",
            "快速支援：风入松",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1251016",
            Element.ELECTRIC,
        ),
        _move(
            "support-followup-clear-river-song",
            SUPPORT_FOLLOWUP_MOVE_ID,
            "支援突击：清江引",
            "支援突击：清江引",
            SkillGroup.ASSIST,
            _FOLLOWUP,
            "伤害倍率",
            "1251020",
            Element.ELECTRIC,
        ),
    )
)


__all__ = [
    "BASIC_DRUNKEN_CLOUD_MOVE_ID",
    "BASIC_MOON_TURN_MOVE_ID",
    "BASIC_YISHA_MOVE_ID",
    "C1_TARGET_DEBUFF_ACTIVE",
    "C6_ALL_RESISTANCE_ACTIVE",
    "CHAIN_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ELECTRIC_ANOMALY_MOVE_ID",
    "ELECTRIC_ANOMALY_RECORD_ID",
    "ELECTRIC_DISORDER_MOVE_ID",
    "ELECTRIC_DISORDER_REMAINING_SECONDS",
    "EX_SPECIAL_MOVE_ID",
    "FLASHOVER_ACTIVE",
    "FLASHOVER_EXCESS_PERCENT",
    "QINGYI_ID",
    "QINGYI_REVIEWED_MAPPING",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "SUBJUGATION_STACKS",
    "SUPPORT_FOLLOWUP_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
