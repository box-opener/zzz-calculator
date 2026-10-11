"""Reviewed move identities and Nanoka 3.2 curves for Sigrid."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import SIGRID_ID


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

_BASIC_MOVE = MoveId("move:sigrid:basic-fierce-spear")
_CHARGED_MOVE = MoveId("move:sigrid:basic-lance-form")
_DASH_MOVE = MoveId("move:sigrid:dash-chasing-wind")
_COUNTER_MOVE = MoveId("move:sigrid:dodge-counter-returning-spear")
_SPECIAL_MOVE = MoveId("move:sigrid:special-ice-flower")
_EX_RANQIONG_MOVE = MoveId("move:sigrid:ex-ranqiong")
_EX_SUIYU_MOVE = MoveId("move:sigrid:ex-suiyu")
_CHAIN_MOVE = MoveId("move:sigrid:chain-ice-curtain")
_ULTIMATE_MOVE = MoveId("move:sigrid:ultimate-frost-sky")
_QUICK_ASSIST_MOVE = MoveId("move:sigrid:quick-assist-sky-patrol")
_ASSIST_STRIKE_MOVE = MoveId("move:sigrid:assist-strike-ice-feast")


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element = Element.ICE,
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
                variant_key="damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


_BASIC_SOURCE = "普通攻击：凛冽枪尖"
_CHARGED_SOURCE = "普通攻击：敛枪式"

SIGRID_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-fierce-spear-stage-{stage}",
                move_id=_BASIC_MOVE,
                label=f"普通攻击：凛冽枪尖（{('一', '二', '三', '四')[stage - 1]}段）",
                source_name=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                source_skill_id=f"159100{(1, 2, 4, 5)[stage - 1]}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        *tuple(
            _move(
                f"basic-lance-form-stage-{stage}",
                move_id=_CHARGED_MOVE,
                label=f"普通攻击：敛枪式（第{('一', '二', '三')[stage - 1]}段）",
                source_name=f"{_CHARGED_SOURCE} 第{('一', '二', '三')[stage - 1]}段",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name="伤害倍率",
                source_skill_id=("1591007", "1591008", "1591022")[stage - 1],
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            "dash-chasing-wind",
            move_id=_DASH_MOVE,
            label="冲刺攻击：逐风",
            source_name="冲刺攻击：逐风",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1591013",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter-returning-spear",
            move_id=_COUNTER_MOVE,
            label="闪避反击：回马枪",
            source_name="闪避反击：回马枪",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1591014",
        ),
        _move(
            "special-ice-flower",
            move_id=_SPECIAL_MOVE,
            label="特殊技：冰花",
            source_name="特殊技：冰花",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1591010",
        ),
        _move(
            "ex-ranqiong",
            move_id=_EX_RANQIONG_MOVE,
            label="强化特殊技：乱琼",
            source_name="强化特殊技：乱琼",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1591011",
        ),
        _move(
            "ex-suiyu",
            move_id=_EX_SUIYU_MOVE,
            label="强化特殊技：碎玉",
            source_name="强化特殊技：碎玉",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1591012",
        ),
        _move(
            "chain-ice-curtain",
            move_id=_CHAIN_MOVE,
            label="连携技：冰凌卷地",
            source_name="连携技：冰凌卷地",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1591015",
        ),
        _move(
            "ultimate-frost-sky",
            move_id=_ULTIMATE_MOVE,
            label="终结技：霜天",
            source_name="终结技：霜天",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1591016",
        ),
        _move(
            "quick-assist-sky-patrol",
            move_id=_QUICK_ASSIST_MOVE,
            label="快速支援：巡戍铁卫",
            source_name="快速支援：巡戍铁卫",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1591017",
        ),
        _move(
            "assist-strike-ice-feast",
            move_id=_ASSIST_STRIKE_MOVE,
            label="支援突击：冰饕",
            source_name="支援突击：冰饕",
            group=SkillGroup.ASSIST,
            tags=_FOLLOW_UP,
            parameter_name="伤害倍率",
            source_skill_id="1591021",
        ),
    ),
    data_quality_notes=(
        "The raw source supplies damage curves for 16 entries: four Basic stages, three Lance Form stages, Dodge Attack, Dodge Counter, Special, two EX Specials, Chain, Ultimate, Quick Assist, and Assist Strike. Parry Assist's three parameters are Daze-only and are not damage events.",
        "The source explicitly classifies Basic stage four, both EX Specials, Assist Strike, Chain, Ultimate, and Dodge Counter as [出枪式]; ordinary Basic stages one through three are not included in that source-defined term.",
        "All 16 authored damage entries are Ice except Dash Attack: 逐风, whose move description explicitly says Physical damage.",
        "Chain grants a 50-second current-state +20% damage effect to later 敛枪式 attacks. The static calculator represents that as a user-selected current condition and does not infer activation from the Chain entry or simulate duration.",
        "No self Anomaly or Disorder result is authored for this non-Anomaly Attack agent.",
    ),
)


__all__ = ["SIGRID_ID", "SIGRID_REVIEWED_MAPPING"]
