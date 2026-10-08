"""Reviewed live Nanoka 3.2 move mapping for Burnice (character:1171)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


BURNICE_ID = CharacterId("character:1171")
BURNICE_FIRE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1171:fire-burn")
BURNICE_FIRE_ANOMALY_MOVE_ID = MoveId("move:burnice:fire-burn")
BURNICE_FIRE_DISORDER_MOVE_ID = MoveId("move:burnice:fire-disorder")

BURN_ACTIVE = ScenarioConditionId("condition:burnice:target-is-burning")
SCORCHED_ACTIVE = ScenarioConditionId("condition:burnice:target-is-scorched")
DOUBLE_EX_STATE_ACTIVE = ScenarioConditionId("condition:burnice:double-ex-state-active")
BURN_THROUGH_STACKS = ScenarioParameterId("parameter:burnice:burn-through-stacks")
FIRE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:burnice:fire-disorder-remaining-seconds"
)

BASIC_MOVE_ID = MoveId("move:burnice:basic-blazing-tune")
BLENDER_MOVE_ID = MoveId("move:burnice:basic-blazing-blender")
DASH_MOVE_ID = MoveId("move:burnice:dash-dangerous-fermentation")
DODGE_COUNTER_MOVE_ID = MoveId("move:burnice:dodge-counter-swaying-flash")
SPECIAL_MOVE_ID = MoveId("move:burnice:special-hot-matured-method")
EX_SPECIAL_MOVE_ID = MoveId("move:burnice:ex-special-hot-sway-method")
EX_SPECIAL_DOUBLE_MOVE_ID = MoveId("move:burnice:ex-special-hot-sway-double")
SPECIAL_THROW_MOVE_ID = MoveId("move:burnice:special-throw-method")
CHAIN_MOVE_ID = MoveId("move:burnice:chain-oil-furnace-flame")
ULTIMATE_MOVE_ID = MoveId("move:burnice:ultimate-enjoy-flame")
QUICK_ASSIST_MOVE_ID = MoveId("move:burnice:quick-assist-refreshing-drink")
ASSIST_STRIKE_MOVE_ID = MoveId("move:burnice:assist-strike-blazing-manna")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULT = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    curve: str,
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
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
                source_skill_id=curve,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


def reviewed_mapping(*, potential_level: int = 0) -> NanokaReviewedMapping:
    blender_tags = _BASIC | (_ASSIST if potential_level >= 1 else frozenset())
    moves: list[NanokaMoveSpec] = [
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：炽焰直调式（{('一', '二', '三', '四', '五')[stage - 1]}段）",
                source="普通攻击：炽焰直调式",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                curve=f"117100{stage}",
                element=Element.PHYSICAL if stage <= 2 else Element.FIRE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "blender-spray",
            move_id=BLENDER_MOVE_ID,
            label="普通攻击：炽焰搅拌式（持续喷射）",
            source="普通攻击：炽焰搅拌式",
            group=SkillGroup.BASIC_ATTACK,
            tags=blender_tags,
            parameter="持续喷射伤害倍率",
            curve="1171006",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "blender-finisher",
            move_id=BLENDER_MOVE_ID,
            label="普通攻击：炽焰搅拌式（终结一击）",
            source="普通攻击：炽焰搅拌式",
            group=SkillGroup.BASIC_ATTACK,
            tags=blender_tags,
            parameter="终结一击伤害倍率",
            curve="1171007",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：危险发酵式",
            source="冲刺攻击：危险发酵式",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1171014",
            element=Element.FIRE,
        ),
        _move(
            "dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：摇荡闪",
            source="闪避反击：摇荡闪",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1171015",
            element=Element.FIRE,
        ),
        _move(
            "special-tap",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：灼热熟成法（点按）",
            source="特殊技：灼热熟成法",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            curve="1171008",
            element=Element.FIRE,
        ),
        _move(
            "special-charge",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：灼热熟成法（蓄力）",
            source="特殊技：灼热熟成法",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="蓄力伤害倍率",
            curve="1171009",
            element=Element.FIRE,
        ),
        _move(
            "ex-single-spray",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：灼热摇荡法（持续喷射）",
            source="强化特殊技：灼热摇荡法",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter="持续喷射伤害倍率",
            curve="1171010",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "ex-single-impact",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：灼热摇荡法（火焰冲击）",
            source="强化特殊技：灼热摇荡法",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter="火焰冲击伤害倍率",
            curve="1171011",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "ex-double-spray",
            move_id=EX_SPECIAL_DOUBLE_MOVE_ID,
            label="强化特殊技：灼热摇荡法·双份（持续喷射）",
            source="强化特殊技：灼热摇荡法·双份",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter="持续喷射伤害倍率",
            curve="1171012",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "ex-double-impact",
            move_id=EX_SPECIAL_DOUBLE_MOVE_ID,
            label="强化特殊技：灼热摇荡法·双份（火焰冲击）",
            source="强化特殊技：灼热摇荡法·双份",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter="火焰冲击伤害倍率",
            curve="1171013",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "chain-attack",
            move_id=CHAIN_MOVE_ID,
            label="连携技：燃油熔焰",
            source="连携技：燃油熔焰",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1171016",
            element=Element.FIRE,
        ),
        _move(
            "ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：纵享盛焰（最大倍率）",
            source="终结技：纵享盛焰",
            group=SkillGroup.ULTIMATE,
            tags=_ULT,
            parameter="最大伤害倍率",
            curve="1171017",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：提神特饮",
            source="快速支援：提神特饮",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1171018",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：灼焰甘露",
            source="支援突击：灼焰甘露",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1171022",
            element=Element.FIRE,
        ),
    ]
    if potential_level >= 1:
        moves.append(
            _move(
                "special-throw",
                move_id=MoveId("move:burnice:ex-special-blazing-throw"),
                label="强化特殊技：灼热抛接法（本体倍率）",
                source="强化特殊技：灼热抛接法",
                group=SkillGroup.SPECIAL_ATTACK,
                tags=_EX,
                parameter="伤害倍率",
                curve="1171026",
                element=Element.FIRE,
            )
        )
    return NanokaReviewedMapping(moves=tuple(moves))


BURNICE_REVIEWED_MAPPING = reviewed_mapping()


__all__ = [
    "BURNICE_ID",
    "BURNICE_FIRE_ANOMALY_RECORD_ID",
    "BURNICE_FIRE_ANOMALY_MOVE_ID",
    "BURNICE_FIRE_DISORDER_MOVE_ID",
    "BURN_ACTIVE",
    "SCORCHED_ACTIVE",
    "DOUBLE_EX_STATE_ACTIVE",
    "BURN_THROUGH_STACKS",
    "FIRE_DISORDER_REMAINING_SECONDS",
    "BURNICE_REVIEWED_MAPPING",
    "reviewed_mapping",
]
