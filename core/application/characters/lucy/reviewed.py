"""Reviewed live Nanoka 3.2 source mapping for Lucy (character:1151)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


LUCY_ID = CharacterId("character:1151")
CHEER_ON_ACTIVE = ScenarioConditionId("condition:lucy:cheer-on-active")
PIGS_ACTIVE = ScenarioConditionId("condition:lucy:bodyguard-pigs-active")

FIRE_ANOMALY_RECORD_ID = "anomaly:character:1151:fire-burn"
FIRE_ANOMALY_MOVE_ID = MoveId("move:lucy:fire-burn")
FIRE_DISORDER_MOVE_ID = MoveId("move:lucy:fire-disorder")

BASIC_MOVE_ID = MoveId("move:lucy:basic-ladys-bat")
DASH_MOVE_ID = MoveId("move:lucy:dash-brave-boar")
DODGE_COUNTER_MOVE_ID = MoveId("move:lucy:dodge-counter-fang-turn")
SPECIAL_STRAIGHT_MOVE_ID = MoveId("move:lucy:special-hit-straight-ball")
SPECIAL_FLY_MOVE_ID = MoveId("move:lucy:special-hit-fly-ball")
EX_STRAIGHT_MOVE_ID = MoveId("move:lucy:ex-home-run-straight-ball")
EX_FLY_MOVE_ID = MoveId("move:lucy:ex-home-run-fly-ball")
CHAIN_MOVE_ID = MoveId("move:lucy:chain-grand-slam")
ULTIMATE_MOVE_ID = MoveId("move:lucy:ultimate-goodbye-home-run")
QUICK_ASSIST_MOVE_ID = MoveId("move:lucy:quick-assist-hit-by-pitch")
ASSIST_STRIKE_MOVE_ID = MoveId("move:lucy:assist-strike-home-plate")

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
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    source_skill_id: str,
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
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


LUCY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-1",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：淑女的球棍（一段）",
            source="普通攻击：淑女的球棍",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="一段伤害倍率",
            source_skill_id="1151001",
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "basic-2",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：淑女的球棍（二段）",
            source="普通攻击：淑女的球棍",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="二段伤害倍率",
            source_skill_id="1151002",
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "basic-3",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：淑女的球棍（三段）",
            source="普通攻击：淑女的球棍",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="三段伤害倍率",
            source_skill_id="1151004",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=3,
        ),
        # The compiler blocks this entry before creating an event because the
        # raw source doesn't map the derived curve to Physical or Fire. The
        # required enum value here is only a non-emitted template placeholder.
        _move(
            "basic-3-derived",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：淑女的球棍（三段派生）",
            source="普通攻击：淑女的球棍",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="三段（派生）伤害倍率",
            source_skill_id="1151003",
            element=Element.PHYSICAL,
        ),
        _move(
            "basic-4",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：淑女的球棍（四段）",
            source="普通攻击：淑女的球棍",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="四段伤害倍率",
            source_skill_id="1151005",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=4,
        ),
        _move(
            "dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：豪勇猪突！",
            source="冲刺攻击：豪勇猪突！",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1151014",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：獠牙折转！",
            source="闪避反击：獠牙折转！",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1151015",
            element=Element.FIRE,
        ),
        _move(
            "special-straight-ball",
            move_id=SPECIAL_STRAIGHT_MOVE_ID,
            label="特殊技：安打！（平直球）",
            source="特殊技：安打！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="平直球伤害倍率",
            source_skill_id="1151008",
            element=Element.FIRE,
        ),
        _move(
            "special-fly-ball",
            move_id=SPECIAL_FLY_MOVE_ID,
            label="特殊技：安打！（高飞球）",
            source="特殊技：安打！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="高飞球伤害倍率",
            source_skill_id="1151009",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-straight-ball",
            move_id=EX_STRAIGHT_MOVE_ID,
            label="强化特殊技：全垒打！（平直球）",
            source="强化特殊技：全垒打！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="平直球伤害倍率",
            source_skill_id="1151012",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-fly-ball",
            move_id=EX_FLY_MOVE_ID,
            label="强化特殊技：全垒打！（高飞球）",
            source="强化特殊技：全垒打！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="高飞球伤害倍率",
            source_skill_id="1151013",
            element=Element.FIRE,
        ),
        _move(
            "chain-attack",
            move_id=CHAIN_MOVE_ID,
            label="连携技：大满贯！",
            source="连携技：大满贯！",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1151016",
            element=Element.FIRE,
        ),
        _move(
            "ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：再见全垒打！",
            source="终结技：再见全垒打！",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1151017",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：触身球！",
            source="快速支援：触身球！",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1151018",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：触垒得分！",
            source="支援突击：触垒得分！",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1151022",
            element=Element.FIRE,
        ),
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_MOVE_ID",
    "CHEER_ON_ACTIVE",
    "CHAIN_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_FLY_MOVE_ID",
    "EX_STRAIGHT_MOVE_ID",
    "FIRE_ANOMALY_MOVE_ID",
    "FIRE_ANOMALY_RECORD_ID",
    "FIRE_DISORDER_MOVE_ID",
    "LUCY_ID",
    "LUCY_REVIEWED_MAPPING",
    "PIGS_ACTIVE",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_FLY_MOVE_ID",
    "SPECIAL_STRAIGHT_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
