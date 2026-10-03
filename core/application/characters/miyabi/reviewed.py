"""Reviewed move taxonomy for Hoshimi Miyabi (character:1091)."""

from __future__ import annotations

from dataclasses import dataclass

from core.application.diagnostics import CalculationDiagnostic
from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


MIYABI_ID = CharacterId("character:1091")

FROSTMOON_CHARGE_1 = ScenarioConditionId("condition:miyabi:frostmoon-charge-1")
FROSTMOON_CHARGE_2 = ScenarioConditionId("condition:miyabi:frostmoon-charge-2")
FROSTMOON_CHARGE_3 = ScenarioConditionId("condition:miyabi:frostmoon-charge-3")
ICEFIRE_ACTIVE = ScenarioConditionId("condition:miyabi:icefire-active")
FROSTBURN_BREAK_READY = ScenarioConditionId(
    "condition:miyabi:frostburn-break-ready"
)
FROSTSCORCH_ACTIVE = ScenarioConditionId("condition:miyabi:frostscorch-active")
FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE = ScenarioConditionId(
    "condition:miyabi:c1-team-buildup-buff-active"
)
NEXT_FROSTMOON_AFTER_DISORDER = ScenarioConditionId(
    "condition:miyabi:next-frostmoon-after-disorder"
)
ULTIMATE_ICE_BONUS_ACTIVE = ScenarioConditionId(
    "condition:miyabi:ultimate-ice-bonus-active"
)

KAZAHANA_MOVE_ID = MoveId("move:miyabi:kazahana")
FROSTMOON_MOVE_ID = MoveId("move:miyabi:frostmoon")
DASH_MOVE_ID = MoveId("move:miyabi:winter-bee")
DODGE_COUNTER_MOVE_ID = MoveId("move:miyabi:cold-sparrow")
SPECIAL_MOVE_ID = MoveId("move:miyabi:deep-snow")
ULTIMATE_MOVE_ID = MoveId("move:miyabi:lingering-snow")
QUICK_ASSIST_MOVE_ID = MoveId("move:miyabi:petal-wind")
ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:miyabi:petal-adieu")


@dataclass(frozen=True, slots=True)
class UnresolvedMultiplierSpec:
    """Reviewed source curves for entries that need explicit compilation."""

    entry_key: str
    move_id: MoveId
    display_name: str
    source_name: str
    parameter_name: str
    source_skill_ids: tuple[str, ...]
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]
    element: Element
    explanation: str
    source_curves_are_additive: bool = False


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_DODGE_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _parameter(
    key: str,
    name: str,
    source_skill_id: str,
    *condition_ids: ScenarioConditionId,
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        condition_ids=tuple(condition_ids),
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameters: tuple[NanokaDamageParameterSpec, ...],
    relation: MultiplierRelation,
    element: Element,
    *,
    stage: int | None = None,
    conditions: tuple[ScenarioConditionId, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=parameters,
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


MIYABI_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=tuple(
        _move(
            f"kazahana-{stage}",
            KAZAHANA_MOVE_ID,
            f"普通攻击：风花（{stage}段）",
            "普通攻击：风花",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (
                _parameter(
                    f"stage-{stage}",
                    f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                    f"109100{stage}",
                ),
            ),
            MultiplierRelation.SEQUENTIAL_STAGE,
            Element.PHYSICAL if stage <= 2 else Element.LIESHUANG,
            stage=stage,
        )
        for stage in range(1, 6)
    )
    + (
        _move(
            "frostmoon-charge",
            FROSTMOON_MOVE_ID,
            "普通攻击：霜月",
            "普通攻击：霜月",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (
                _parameter("charge-1", "一段蓄力斩击伤害倍率", "1091027", FROSTMOON_CHARGE_1),
                _parameter("charge-2", "二段蓄力斩击伤害倍率", "1091028", FROSTMOON_CHARGE_2),
                _parameter("charge-3", "三段蓄力斩击伤害倍率", "1091029", FROSTMOON_CHARGE_3),
            ),
            MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
            Element.LIESHUANG,
        ),
        _move(
            "dash-attack",
            DASH_MOVE_ID,
            "冲刺攻击：冬蜂",
            "冲刺攻击：冬蜂",
            SkillGroup.DODGE,
            _DASH,
            (_parameter("complete", "伤害倍率", "1091013"),),
            MultiplierRelation.COMPLETE,
            Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：寒雀",
            "闪避反击：寒雀",
            SkillGroup.DODGE,
            _DODGE_COUNTER,
            (_parameter("complete", "伤害倍率", "1091014"),),
            MultiplierRelation.COMPLETE,
            Element.LIESHUANG,
        ),
        _move(
            "special-deep-snow",
            SPECIAL_MOVE_ID,
            "特殊技：深雪",
            "特殊技：深雪",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            (_parameter("complete", "伤害倍率", "1091008"),),
            MultiplierRelation.COMPLETE,
            Element.LIESHUANG,
        ),
        _move(
            "ultimate-lingering-snow",
            ULTIMATE_MOVE_ID,
            "终结技：名残雪",
            "终结技：名残雪",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            (_parameter("complete", "伤害倍率", "1091018"),),
            MultiplierRelation.COMPLETE,
            Element.LIESHUANG,
        ),
        _move(
            "quick-assist-petal-wind",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：花信风",
            "快速支援：花信风",
            SkillGroup.ASSIST,
            _ASSIST,
            (_parameter("complete", "伤害倍率", "1091021"),),
            MultiplierRelation.COMPLETE,
            Element.LIESHUANG,
        ),
        _move(
            "assist-follow-up-petal-adieu",
            ASSIST_FOLLOW_UP_MOVE_ID,
            "支援突击：花辞",
            "支援突击：花辞",
            SkillGroup.ASSIST,
            _ASSIST,
            (_parameter("complete", "伤害倍率", "1091025"),),
            MultiplierRelation.COMPLETE,
            Element.LIESHUANG,
        ),
    )
)


MIYABI_UNRESOLVED_MULTIPLIERS = (
    UnresolvedMultiplierSpec(
        entry_key="ex-special-strike",
        move_id=MoveId("move:miyabi:flying-snow-strike"),
        display_name="强化特殊技：飞雪·斩击",
        source_name="强化特殊技：飞雪",
        parameter_name="斩击伤害倍率",
        source_skill_ids=("1091009", "1091010"),
        source_curves_are_additive=True,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=_EX_SPECIAL,
        element=Element.LIESHUANG,
        explanation="原始参数表达式明确相加1091009与1091010两条斩击曲线。",
    ),
    UnresolvedMultiplierSpec(
        entry_key="ex-special-follow-up",
        move_id=MoveId("move:miyabi:flying-snow-follow-up"),
        display_name="强化特殊技：飞雪·追击",
        source_name="强化特殊技：飞雪",
        parameter_name="追击伤害倍率",
        source_skill_ids=("1091011", "1091012"),
        source_curves_are_additive=True,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=_EX_SPECIAL,
        element=Element.LIESHUANG,
        explanation="原始参数表达式明确相加1091011与1091012两条追击曲线。",
    ),
    UnresolvedMultiplierSpec(
        entry_key="chain-spring-call",
        move_id=MoveId("move:miyabi:spring-call"),
        display_name="连携技：春临",
        source_name="连携技：春临",
        parameter_name="伤害倍率",
        source_skill_ids=("1091015", "1091016", "1091017"),
        source_curves_are_additive=True,
        skill_group=SkillGroup.CHAIN_ATTACK,
        damage_tags=_CHAIN,
        element=Element.LIESHUANG,
        explanation="原始参数表达式明确相加1091015、1091016与1091017三条曲线。",
    ),
)


__all__ = [
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ASSIST_FOLLOW_UP_MOVE_ID",
    "FROSTBURN_BREAK_READY",
    "FROSTMOON_CHARGE_1",
    "FROSTMOON_CHARGE_2",
    "FROSTMOON_CHARGE_3",
    "FROSTMOON_MOVE_ID",
    "ICEFIRE_ACTIVE",
    "KAZAHANA_MOVE_ID",
    "MIYABI_ID",
    "MIYABI_REVIEWED_MAPPING",
    "MIYABI_UNRESOLVED_MULTIPLIERS",
    "NEXT_FROSTMOON_AFTER_DISORDER",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_ICE_BONUS_ACTIVE",
    "ULTIMATE_MOVE_ID",
    "FROSTSCORCH_ACTIVE",
    "FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE",
    "UnresolvedMultiplierSpec",
]
