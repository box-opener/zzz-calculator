"""Reviewed Nanoka 3.2 damage identities for Promeia (character:1541)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import PROMEIA_ID

PROMEIA_ICE_ANOMALY_MOVE_ID = MoveId("move:promeia:ice-anomaly")
PROMEIA_ICE_DISORDER_MOVE_ID = MoveId("move:promeia:ice-disorder")


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _parameter(key: str, name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage_index: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=skill_group,
        damage_tags=damage_tags,
        parameters=(_parameter(key, parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=Element.ICE,
        stage_index=stage_index,
    )


_moves: list[NanokaMoveSpec] = []
_basic_id = MoveId("move:promeia:basic-bias")
for stage, label, parameter_name, source_id in (
    (1, "一段", "一段伤害倍率", "1541001"),
    (2, "二段", "二段伤害倍率", "1541002"),
    (3, "三段", "三段伤害倍率", "1541003"),
    (4, "四段", "四段伤害倍率", "1541004"),
    (5, "五段", "五段伤害倍率", "1541005"),
):
    _moves.append(
        _move(
            f"basic-bias-{stage}",
            move_id=_basic_id,
            label=f"普通攻击：偏锋（{label}）",
            source_name="普通攻击：偏锋",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter_name=parameter_name,
            source_skill_id=source_id,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=stage,
        )
    )

_moves.extend(
    (
        _move(
            "basic-spin-blade",
            move_id=MoveId("move:promeia:basic-spin-blade"),
            label="普通攻击：旋刃",
            source_name="普通攻击：旋刃",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter_name="一段伤害倍率",
            source_skill_id="1541006",
        ),
        _move(
            "dash-slay",
            move_id=MoveId("move:promeia:dash-slay"),
            label="冲刺攻击：掠命",
            source_name="冲刺攻击：掠命",
            skill_group=SkillGroup.DODGE,
            damage_tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1541015",
        ),
        _move(
            "dodge-counter-bat-leap",
            move_id=MoveId("move:promeia:dodge-counter-bat-leap"),
            label="闪避反击：蝠跃",
            source_name="闪避反击：蝠跃",
            skill_group=SkillGroup.DODGE,
            damage_tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1541016",
        ),
        _move(
            "special-cold-glint",
            move_id=MoveId("move:promeia:special-cold-glint"),
            label="特殊技：处刑式·寒芒乍现",
            source_name="特殊技：处刑式·寒芒乍现",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1541007",
        ),
        _move(
            "ex-throat-frost-path",
            move_id=MoveId("move:promeia:ex-throat-frost-path"),
            label="强化特殊技：处刑式·封喉霜径",
            source_name="强化特殊技：处刑式·封喉霜径",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=_EX_SPECIAL,
            parameter_name="飞镖射击总伤害倍率",
            source_skill_id="1541009",
        ),
        _move(
            "special-frost-fall",
            move_id=MoveId("move:promeia:special-frost-fall"),
            label="特殊技：处刑式·坠霜",
            source_name="特殊技：处刑式·坠霜",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1541010",
        ),
        _move(
            "special-heavy-frost",
            move_id=MoveId("move:promeia:special-heavy-frost"),
            label="特殊技：处刑式·重霜",
            source_name="特殊技：处刑式·重霜",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1541011",
        ),
        _move(
            "ex-judgment",
            move_id=MoveId("move:promeia:ex-judgment"),
            label="强化特殊技：处刑式·绝裁",
            source_name="强化特殊技：处刑式·绝裁",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1541014",
        ),
        _move(
            "chain-hanging-reckoning",
            move_id=MoveId("move:promeia:chain-hanging-reckoning"),
            label="连携技：倒悬清算",
            source_name="连携技：倒悬清算",
            skill_group=SkillGroup.CHAIN_ATTACK,
            damage_tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1541017",
        ),
        _move(
            "ultimate-bone-punishment",
            move_id=MoveId("move:promeia:ultimate-bone-punishment"),
            label="终结技：彻骨磔罚",
            source_name="终结技：彻骨磔罚",
            skill_group=SkillGroup.ULTIMATE,
            damage_tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1541018",
        ),
        _move(
            "quick-assist-folding-strike",
            move_id=MoveId("move:promeia:quick-assist-folding-strike"),
            label="快速支援：折袭",
            source_name="快速支援：折袭",
            skill_group=SkillGroup.ASSIST,
            damage_tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1541019",
        ),
        _move(
            "assist-strike-weapons-severed",
            move_id=MoveId("move:promeia:assist-strike-weapons-severed"),
            label="支援突击：截兵",
            source_name="支援突击：截兵",
            skill_group=SkillGroup.ASSIST,
            damage_tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1541023",
        ),
    )
)


PROMEIA_REVIEWED_MAPPING = NanokaReviewedMapping(moves=tuple(_moves))


__all__ = [
    "PROMEIA_ICE_ANOMALY_MOVE_ID",
    "PROMEIA_ICE_DISORDER_MOVE_ID",
    "PROMEIA_ID",
    "PROMEIA_REVIEWED_MAPPING",
]
