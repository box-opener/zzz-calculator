"""Reviewed Nanoka 3.2 move identities for Seed (character:1461)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import SEED_ID

SEED_BASIC_MOVE_ID = MoveId("move:seed:frost-petal-dance")
SEED_HEAVY_STRIKE_MOVE_ID = MoveId("move:seed:falling-flower-heavy-strike")
SEED_FALLING_CRASH_MOVE_ID = MoveId("move:seed:falling-flower-crash")
SEED_DASH_MOVE_ID = MoveId("move:seed:magnetic-wheel-dance")
SEED_DODGE_COUNTER_MOVE_ID = MoveId("move:seed:petal-fracture-counter")
SEED_SPECIAL_MOVE_ID = MoveId("move:seed:frost-shards")
SEED_EX_SPECIAL_MOVE_ID = MoveId("move:seed:iron-calyx-rain")
SEED_EX_RELEASE_MOVE_ID = MoveId("move:seed:iron-calyx-release")
SEED_CHAIN_MOVE_ID = MoveId("move:seed:snowstorm")
SEED_ULTIMATE_MOVE_ID = MoveId("move:seed:mecha-garden-bloom")
SEED_QUICK_ASSIST_MOVE_ID = MoveId("move:seed:flower-volley")
SEED_ASSIST_STRIKE_MOVE_ID = MoveId("move:seed:crimson-core-barrage")

PARTNER_EX_BUFF_ACTIVE = ScenarioConditionId(
    "condition:seed:partner-ex-buff-active-on-seed"
)
SEED_EX_BUFF_ACTIVE = ScenarioConditionId("condition:seed:seed-ex-buff-active-on-partner")
SEED_SURROUND_HUNT_ACTIVE = ScenarioConditionId("condition:seed:seed-surround-hunt-active")
PARTNER_SURROUND_HUNT_ACTIVE = ScenarioConditionId(
    "condition:seed:partner-surround-hunt-active"
)
CINEMA6_LASER_PROC_ACTIVE = ScenarioConditionId(
    "condition:seed:cinema6-laser-proc-active"
)
CINEMA2_ENERGY_INTERVALS_SPENT = ScenarioParameterId(
    "parameter:seed:cinema2-energy-intervals-spent"
)

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    curve: str,
    element: Element,
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
                source_skill_id=curve,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


SEED_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=SEED_BASIC_MOVE_ID,
                label=f"普通攻击：霜蕊轮舞（第{stage}段）",
                source_name="普通攻击：霜蕊轮舞",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                curve=f"146100{stage}",
                element=Element.PHYSICAL if stage <= 2 else Element.ELECTRIC,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "heavy-strike",
            move_id=SEED_HEAVY_STRIKE_MOVE_ID,
            label="普通攻击：落华·重戮",
            source_name="普通攻击：落华·重戮",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            curve="1461006",
            element=Element.ELECTRIC,
        ),
        *tuple(
            _move(
                f"falling-crash-{stage}",
                move_id=SEED_FALLING_CRASH_MOVE_ID,
                label=f"普通攻击：落华·崩坠（第{stage}式）",
                source_name=f"普通攻击：落华·崩坠{('一', '二')[stage - 1]}式",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name="伤害倍率",
                curve=f"146100{stage + 6}",
                element=Element.ELECTRIC,
            )
            for stage in (1, 2)
        ),
        _move(
            "dash-attack",
            move_id=SEED_DASH_MOVE_ID,
            label="冲刺攻击：磁陨轮舞",
            source_name="冲刺攻击：磁陨轮舞",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            curve="1461012",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            move_id=SEED_DODGE_COUNTER_MOVE_ID,
            label="闪避反击：裂萼纷华",
            source_name="闪避反击：裂萼纷华",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            curve="1461013",
            element=Element.ELECTRIC,
        ),
        _move(
            "special",
            move_id=SEED_SPECIAL_MOVE_ID,
            label="特殊技：苍霜零落",
            source_name="特殊技：苍霜零落",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            curve="1461005",
            element=Element.ELECTRIC,
        ),
        _move(
            "ex-special-rain",
            move_id=SEED_EX_SPECIAL_MOVE_ID,
            label="强化特殊技：铁萼雨幕",
            source_name="强化特殊技：铁萼雨幕",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            curve="1461009",
            element=Element.ELECTRIC,
        ),
        _move(
            "ex-special-release",
            move_id=SEED_EX_RELEASE_MOVE_ID,
            label="强化特殊技：铁萼雨幕·离",
            source_name="强化特殊技：铁萼雨幕·离",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            curve="1461022",
            element=Element.ELECTRIC,
        ),
        _move(
            "chain-attack",
            move_id=SEED_CHAIN_MOVE_ID,
            label="连携技：落霰风暴",
            source_name="连携技：落霰风暴",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            curve="1461014",
            element=Element.ELECTRIC,
        ),
        _move(
            "ultimate",
            move_id=SEED_ULTIMATE_MOVE_ID,
            label="终结技：机芯花园·绽放！",
            source_name="终结技：机芯花园·绽放！",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            curve="1461015",
            element=Element.ELECTRIC,
        ),
        _move(
            "quick-assist",
            move_id=SEED_QUICK_ASSIST_MOVE_ID,
            label="快速支援：花雨齐射",
            source_name="快速支援：花雨齐射",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1461016",
            element=Element.ELECTRIC,
        ),
        _move(
            "assist-strike",
            move_id=SEED_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：绯芯爆裂",
            source_name="支援突击：绯芯爆裂",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1461020",
            element=Element.ELECTRIC,
        ),
    ),
    data_quality_notes=(
        "Seed is a non-Anomaly Attack agent; the source provides no authored Anomaly or Disorder move, so none is synthesized.",
        "Basic stages 1–2 are Physical and stages 3–4 Electric per their description; Falling Flower, dash, and dodge-counter entries retain their source-described elements.",
        "The C6 source identifies a Heavy Strike trigger and three 165% ATK lasers; the user confirmed these are Electric Basic Direct child events.",
        "Steel Energy, Energy, Decibel, Daze, and timing/cooldown are not modeled as standalone damage results. Core and cinema current states are user-selected static inputs; the implementation does not replay entry, switching, or durations.",
    ),
)


__all__ = [
    "SEED_ID",
    "SEED_REVIEWED_MAPPING",
    "SEED_BASIC_MOVE_ID",
    "SEED_HEAVY_STRIKE_MOVE_ID",
    "SEED_FALLING_CRASH_MOVE_ID",
    "SEED_DASH_MOVE_ID",
    "SEED_DODGE_COUNTER_MOVE_ID",
    "SEED_SPECIAL_MOVE_ID",
    "SEED_EX_SPECIAL_MOVE_ID",
    "SEED_EX_RELEASE_MOVE_ID",
    "SEED_CHAIN_MOVE_ID",
    "SEED_ULTIMATE_MOVE_ID",
    "SEED_QUICK_ASSIST_MOVE_ID",
    "SEED_ASSIST_STRIKE_MOVE_ID",
    "PARTNER_EX_BUFF_ACTIVE",
    "SEED_EX_BUFF_ACTIVE",
    "SEED_SURROUND_HUNT_ACTIVE",
    "PARTNER_SURROUND_HUNT_ACTIVE",
    "CINEMA6_LASER_PROC_ACTIVE",
    "CINEMA2_ENERGY_INTERVALS_SPENT",
]
