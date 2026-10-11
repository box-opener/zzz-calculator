"""Reviewed move identities for Nangong Yu's Nanoka live 3.2 source."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import NANGONGYU_ID


NANGONGYU_ETHER_ANOMALY_RECORD_ID = "anomaly:character:1511:ether-corruption"

METEOR_DANCE_MOVE_ID = MoveId("move:nangongyu:meteor-dance")
CHARGE_STRIKE_MOVE_ID = MoveId("move:nangongyu:charge-strike")
DASH_ATTACK_MOVE_ID = MoveId("move:nangongyu:dash-attack")
DODGE_COUNTER_MOVE_ID = MoveId("move:nangongyu:dodge-counter")
SPECIAL_ATTACK_MOVE_ID = MoveId("move:nangongyu:special-attack")
EX_SPECIAL_MOVE_ID = MoveId("move:nangongyu:ex-special")
CHAIN_ATTACK_MOVE_ID = MoveId("move:nangongyu:chain-attack")
ULTIMATE_MOVE_ID = MoveId("move:nangongyu:ultimate")
QUICK_ASSIST_MOVE_ID = MoveId("move:nangongyu:quick-assist")
ASSIST_STRIKE_MOVE_ID = MoveId("move:nangongyu:assist-strike")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _parameter(
    key: str,
    parameter_name: str,
    *,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=parameter_name,
        source_skill_id=source_skill_id,
        source_skill_components=source_skill_components,
    )


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    parameter: NanokaDamageParameterSpec,
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
        parameters=(parameter,),
        multiplier_relation=relation,
        element=Element.ETHER,
        stage_index=stage_index,
    )


_moves: list[NanokaMoveSpec] = []
for stage, parameter_name, source_skill_id, label in (
    (1, "一段伤害倍率", "1511001", "普通攻击：流星舞步（一段）"),
    (2, "二段伤害倍率", "1511002", "普通攻击：流星舞步（二段）"),
    (3, "三段伤害倍率", "1511003", "普通攻击：流星舞步（三段）"),
):
    _moves.append(
        _move(
            f"basic-meteor-dance-{stage}",
            move_id=METEOR_DANCE_MOVE_ID,
            label=label,
            source_name="普通攻击：流星舞步",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter=_parameter(f"stage-{stage}", parameter_name, source_skill_id=source_skill_id),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=stage,
        )
    )

for stage, parameter_name, source_skill_id in (
    (1, "一段伤害倍率", "1511004"),
    (2, "二段伤害倍率", "1511005"),
    (3, "三段伤害倍率", "1511006"),
):
    _moves.append(
        _move(
            f"basic-charge-strike-{stage}",
            move_id=CHARGE_STRIKE_MOVE_ID,
            label=f"普通攻击：可爱地雷飞天撞（{('一', '二', '三')[stage - 1]}段）",
            source_name="普通攻击：可爱地雷飞天撞",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter=_parameter(f"stage-{stage}", parameter_name, source_skill_id=source_skill_id),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=stage,
        )
    )

# Nanoka publishes the cooperative third-stage curve as the sum of two
# separate source-skill curves. Keep it as its own explicitly named entry.
_moves.append(
    _move(
        "basic-charge-strike-3-cooperative",
        move_id=CHARGE_STRIKE_MOVE_ID,
        label="普通攻击：可爱地雷飞天撞（第三段协同）",
        source_name="普通攻击：可爱地雷飞天撞",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        parameter=_parameter(
            "stage-3-cooperative",
            "三段伤害倍率（协同）",
            source_skill_components=(("1511006", 1.0), ("1511018", 1.0)),
        ),
    )
)

for key, move_id, label, source_name, group, tags, parameter_name, source_id in (
    (
        "dash-attack",
        DASH_ATTACK_MOVE_ID,
        "冲刺攻击：回转流星",
        "冲刺攻击：回转流星",
        SkillGroup.DODGE,
        _DASH,
        "伤害倍率",
        "1511009",
    ),
    (
        "dodge-counter",
        DODGE_COUNTER_MOVE_ID,
        "闪避反击：流星华尔兹",
        "闪避反击：流星华尔兹",
        SkillGroup.DODGE,
        _COUNTER,
        "伤害倍率",
        "1511010",
    ),
    (
        "special-attack",
        SPECIAL_ATTACK_MOVE_ID,
        "特殊技：有点沉重的爱意",
        "特殊技：有点沉重的爱意",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        "伤害倍率",
        "1511007",
    ),
    (
        "ex-special",
        EX_SPECIAL_MOVE_ID,
        "强化特殊技：相当沉重的爱意",
        "强化特殊技：相当沉重的爱意",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        "伤害倍率",
        "1511008",
    ),
    (
        "chain-attack",
        CHAIN_ATTACK_MOVE_ID,
        "连携技：慧星引力",
        "连携技：慧星引力",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        "伤害倍率",
        "1511011",
    ),
    (
        "ultimate",
        ULTIMATE_MOVE_ID,
        "终结技：流落星群",
        "终结技：流落星群",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        "伤害倍率",
        "1511012",
    ),
    (
        "quick-assist",
        QUICK_ASSIST_MOVE_ID,
        "快速支援：救场技巧",
        "快速支援：救场技巧",
        SkillGroup.ASSIST,
        _ASSIST,
        "伤害倍率",
        "1511013",
    ),
    (
        "assist-strike",
        ASSIST_STRIKE_MOVE_ID,
        "支援突击：即兴演出",
        "支援突击：即兴演出",
        SkillGroup.ASSIST,
        _ASSIST,
        "伤害倍率",
        "1511017",
    ),
):
    _moves.append(
        _move(
            key,
            move_id=move_id,
            label=label,
            source_name=source_name,
            skill_group=group,
            damage_tags=tags,
            parameter=_parameter("damage", parameter_name, source_skill_id=source_id),
        )
    )


NANGONGYU_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=tuple(_moves),
    data_quality_notes=(
        "The source provides separate Daze and attribute-buildup curves for these moves; "
        "this calculator version does not output Daze or buildup totals.",
        "The cooperative charged-Basic third-stage entry uses Nanoka's explicit summed "
        "source-skill curves as one reviewed multiplier; no additional move tags are inferred.",
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "CHAIN_ATTACK_MOVE_ID",
    "CHARGE_STRIKE_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "METEOR_DANCE_MOVE_ID",
    "NANGONGYU_ETHER_ANOMALY_RECORD_ID",
    "NANGONGYU_ID",
    "NANGONGYU_REVIEWED_MAPPING",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_ATTACK_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
