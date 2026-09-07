"""Manually reviewed Alice skill taxonomy.

Only stable source names, damage tags, and multiplier relationships live here;
all numeric values and original text are read from the Nanoka raw record.
"""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ALICE_ID = CharacterId("character:1401")
STAR_DANCE_1_CONDITION_ID = ScenarioConditionId("condition:alice:star-dance-charge-1")
STAR_DANCE_2_CONDITION_ID = ScenarioConditionId("condition:alice:star-dance-charge-2")
STAR_DANCE_3_CONDITION_ID = ScenarioConditionId("condition:alice:star-dance-charge-3")
POLAR_ASSAULT_CONDITION_ID = ScenarioConditionId("condition:alice:polar-assault-active")
PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID = ScenarioConditionId("condition:alice:physical-anomaly-active")
VICTORY_STATE_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:alice:victory-state-active"
)
ALICE_REMAINING_DURATION_PARAMETER_ID = ScenarioParameterId(
    "parameter:alice:physical-anomaly-remaining-seconds"
)
ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID = ScenarioParameterId(
    "parameter:alice:periodic-extra-tick-count"
)
ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID = ScenarioParameterId(
    "parameter:alice:victory-extra-attack-count"
)
ALICE_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:alice:physical-current"
)


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DODGE = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _p(key: str, name: str, *condition_ids: object) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(key, name, tuple(condition_ids))


def _move(
    key: str,
    move_id: str,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    params: tuple[NanokaDamageParameterSpec, ...],
    relation: MultiplierRelation,
    element: Element = Element.PHYSICAL,
    stage: int | None = None,
    conditions: tuple[object, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=MoveId(move_id),
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=params,
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


ALICE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-star-opera-{stage}",
                "move:alice:star-opera",
                f"普通攻击：星仪序曲（{stage}段）",
                "普通攻击：星仪序曲",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                (_p(f"stage-{stage}", f"{('一','二','三','四','五')[stage - 1]}段伤害倍率"),),
                MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-star-opera-5-enhanced",
            "move:alice:star-opera",
            "普通攻击：星仪序曲（五段·强化）",
            "普通攻击：星仪序曲",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (_p("enhanced-stage-5", "五段（强化）伤害倍率"),),
            MultiplierRelation.SEQUENTIAL_STAGE,
            stage=5,
        ),
        _move(
            "basic-star-dance",
            "move:alice:star-dance",
            "普通攻击：星芒圆舞曲",
            "普通攻击：星芒圆舞曲",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (
                _p("charge-1", "一段蓄力伤害倍率", STAR_DANCE_1_CONDITION_ID),
                _p("charge-2", "二段蓄力伤害倍率", STAR_DANCE_2_CONDITION_ID),
                _p("charge-3", "三段蓄力伤害倍率", STAR_DANCE_3_CONDITION_ID),
            ),
            MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        ),
        _move("dodge-dash", "move:alice:dodge-dash", "冲刺攻击：剑舞之风", "冲刺攻击：剑舞之风", SkillGroup.DODGE, _DODGE, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("dodge-counter", "move:alice:dodge-counter", "闪避反击：剑闪之仪", "闪避反击：剑闪之仪", SkillGroup.DODGE, _COUNTER, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-break-dawn", "move:alice:break-dawn", "特殊技：破晓突刺", "特殊技：破晓突刺", SkillGroup.SPECIAL_ATTACK, _SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-north-cross", "move:alice:north-cross", "强化特殊技：极光突刺·北十字", "强化特殊技：极光突刺·北十字", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-south-cross", "move:alice:south-cross", "强化特殊技：极光突刺·南十字", "强化特殊技：极光突刺·南十字", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("chain-star-interlude", "move:alice:star-interlude", "连携技：星落间章", "连携技：星落间章", SkillGroup.CHAIN_ATTACK, _CHAIN, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("ultimate-star-finale", "move:alice:star-finale", "终结技：星芒终章", "终结技：星芒终章", SkillGroup.ULTIMATE, _ULTIMATE, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-quick-pierce", "move:alice:quick-pierce", "快速支援：交替穿刺", "快速支援：交替穿刺", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-cross-counter", "move:alice:cross-counter", "支援突击：交叉还击", "支援突击：交叉还击", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
    )
)


__all__ = [
    "ALICE_ID",
    "ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID",
    "ALICE_PHYSICAL_ANOMALY_RECORD_ID",
    "ALICE_REMAINING_DURATION_PARAMETER_ID",
    "ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID",
    "ALICE_REVIEWED_MAPPING",
    "PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID",
    "POLAR_ASSAULT_CONDITION_ID",
    "VICTORY_STATE_ACTIVE_CONDITION_ID",
    "STAR_DANCE_1_CONDITION_ID",
    "STAR_DANCE_2_CONDITION_ID",
    "STAR_DANCE_3_CONDITION_ID",
]
