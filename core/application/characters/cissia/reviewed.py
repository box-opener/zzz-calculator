"""Reviewed Nanoka 3.2 move identities for Cissia (character:1521)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import CISSIA_ID

CISSIA_TOXIN_ACTIVE = ScenarioConditionId("condition:cissia:toxin-active-or-recent")
CISSIA_SNAKE_SHADOW_AVAILABLE = ScenarioConditionId(
    "condition:cissia:snake-shadow-available"
)
CISSIA_CINEMA6_MARK_PROC_ACTIVE = ScenarioConditionId(
    "condition:cissia:cinema6-mark-proc-active"
)
CISSIA_EX_EXTRA_HIT_COUNT = ScenarioParameterId(
    "parameter:cissia:ex-special-extra-hit-count"
)
CISSIA_CINEMA4_AWARENESS_STACKS = ScenarioParameterId(
    "parameter:cissia:cinema4-awareness-stacks"
)

SNAKE_TONGUE_MOVE_ID = MoveId("move:cissia:basic-snake-tongue")
SNAKE_KISS_MOVE_ID = MoveId("move:cissia:basic-snake-kiss")
DASH_ATTACK_MOVE_ID = MoveId("move:cissia:dash-bite-mark")
DODGE_COUNTER_MOVE_ID = MoveId("move:cissia:dodge-counter-bite-back")
SPECIAL_MOVE_ID = MoveId("move:cissia:special-fang")
EX_SPECIAL_MOVE_ID = MoveId("move:cissia:ex-special-venom-fang")
CHAIN_ATTACK_MOVE_ID = MoveId("move:cissia:chain-gang-crime")
ULTIMATE_MOVE_ID = MoveId("move:cissia:ultimate-crawling-dread")
QUICK_ASSIST_MOVE_ID = MoveId("move:cissia:quick-assist-alarm")
ASSIST_STRIKE_MOVE_ID = MoveId("move:cissia:assist-strike-accomplice")

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
    conditions: tuple = (),
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
        element=Element.ELECTRIC,
        stage_index=stage,
        condition_ids=conditions,
    )


CISSIA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=SNAKE_TONGUE_MOVE_ID,
                label=f"普通攻击：吐信（第{stage}段）",
                source_name="普通攻击：吐信",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                curve=f"152100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-snake-kiss",
            move_id=SNAKE_KISS_MOVE_ID,
            label="普通攻击：蛇吻",
            source_name="普通攻击：蛇吻",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            curve="1521006",
            conditions=(CISSIA_SNAKE_SHADOW_AVAILABLE,),
        ),
        _move(
            "dash-attack",
            move_id=DASH_ATTACK_MOVE_ID,
            label="冲刺攻击：齿痕",
            source_name="冲刺攻击：齿痕",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            curve="1521010",
        ),
        _move(
            "dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：反咬一口",
            source_name="闪避反击：反咬一口",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            curve="1521011",
        ),
        _move(
            "special",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：獠齿",
            source_name="特殊技：獠齿",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            curve="1521007",
        ),
        _move(
            "ex-special",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：毒牙",
            source_name="强化特殊技：毒牙",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            curve="1521008",
        ),
        _move(
            "chain-attack",
            move_id=CHAIN_ATTACK_MOVE_ID,
            label="连携技：团伙作案",
            source_name="连携技：团伙作案",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            curve="1521012",
        ),
        _move(
            "ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：爬行恐惧",
            source_name="终结技：爬行恐惧",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            curve="1521013",
        ),
        _move(
            "quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：报警装置",
            source_name="快速支援：报警装置",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1521014",
        ),
        _move(
            "assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：共犯情谊",
            source_name="支援突击：共犯情谊",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1521018",
        ),
    ),
    data_quality_notes=(
        "Cissia is an Electric Attack agent. The source includes no ordinary Anomaly or Disorder damage entry, and none is synthesized.",
        "The EX Special source explicitly separates its base 1521008 ratio from the extra-strike 1521009 ratio; the latter is exposed as a 0–3 current repeat count.",
        "Bone Erosion is a neutral Electric Direct child with current Attack and no inherited MoveId, SkillGroup, or DamageTag. Its ratio is the raw 1521019 curve plus the Core-sourced extra Attack ratio.",
        "Parry support has only Daze multipliers and is not exposed as a damage move. Poison resources, periodic timing, and three-second history are not replayed.",
    ),
)


__all__ = [
    "CISSIA_ID",
    "CISSIA_REVIEWED_MAPPING",
    "CISSIA_TOXIN_ACTIVE",
    "CISSIA_SNAKE_SHADOW_AVAILABLE",
    "CISSIA_CINEMA6_MARK_PROC_ACTIVE",
    "CISSIA_EX_EXTRA_HIT_COUNT",
    "CISSIA_CINEMA4_AWARENESS_STACKS",
    "SNAKE_KISS_MOVE_ID",
]
