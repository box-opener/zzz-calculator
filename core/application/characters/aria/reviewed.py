"""Reviewed Nanoka 3.2 move identities for Aria (character:1501)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import ARIA_ID


ARIA_DELUSION_ACTIVE = ScenarioConditionId("condition:aria:delusion-active")
ARIA_THIRD_CHARGE_ANOMALY_HIT = ScenarioConditionId(
    "condition:aria:third-charge-anomaly-hit"
)
ARIA_ETHER_ANOMALY_RECORD_ID = "anomaly:character:1501:ether-corruption"

ARIA_BASIC_HEARTBEAT_MOVE_ID = MoveId("move:aria:basic-sweet-heartbeat")
ARIA_BASIC_PITCH_MOVE_ID = MoveId("move:aria:basic-absolute-pitch")
ARIA_DASH_MOVE_ID = MoveId("move:aria:dash-smooth-combo")
ARIA_COUNTER_MOVE_ID = MoveId("move:aria:dodge-counter-sliding-variation")
ARIA_SPECIAL_MOVE_ID = MoveId("move:aria:special-full-sugar")
ARIA_SPECIAL_NO_ICE_MOVE_ID = MoveId("move:aria:special-full-sugar-no-ice")
ARIA_EX_SPECIAL_FALL_MOVE_ID = MoveId("move:aria:ex-special-delusion")
ARIA_EX_SPECIAL_LIGHTSPEED_MOVE_ID = MoveId("move:aria:ex-special-lightspeed")
ARIA_CHAIN_MOVE_ID = MoveId("move:aria:chain-fantasy-collab")
ARIA_ULTIMATE_MOVE_ID = MoveId("move:aria:ultimate-energy-full")
ARIA_QUICK_ASSIST_MOVE_ID = MoveId("move:aria:quick-assist-shattered-dream")
ARIA_SUPPORT_ASSAULT_MOVE_ID = MoveId("move:aria:support-assault-encore")

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
    name: str,
    *,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
    condition_ids: tuple[ScenarioConditionId, ...] = (),
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        condition_ids=condition_ids,
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
    condition_ids: tuple[ScenarioConditionId, ...] = (),
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
        condition_ids=condition_ids,
    )


_moves: list[NanokaMoveSpec] = []
for stage, parameter_name, skill_id in (
    (1, "一段伤害倍率", "1501001"),
    (2, "二段伤害倍率", "1501002"),
    (3, "三段伤害倍率", "1501003"),
    (4, "四段伤害倍率", "1501004"),
):
    _moves.append(
        _move(
            f"basic-sweet-heartbeat-{stage}",
            move_id=ARIA_BASIC_HEARTBEAT_MOVE_ID,
            label=f"普通攻击：甜心律动（{('一','二','三','四')[stage - 1]}段）",
            source_name="普通攻击：甜心律动",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter=_parameter(
                f"stage-{stage}", parameter_name, source_skill_id=skill_id
            ),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=stage,
        )
    )

for charge, parameter_name, skill_id, components in (
    (1, "一段蓄力攻击伤害倍率", "1501005", ()),
    (2, "二段蓄力攻击伤害倍率", "1501006", ()),
    (3, "三段蓄力攻击伤害倍率", "1501007", ()),
    (
        3,
        "三段蓄力攻击伤害倍率（协同）",
        None,
        (("1501007", 1.0), ("1501022", 1.0)),
    ),
):
    cooperative = bool(components)
    _moves.append(
        _move(
            "basic-absolute-pitch-charge-3-cooperative"
            if cooperative
            else f"basic-absolute-pitch-charge-{charge}",
            move_id=ARIA_BASIC_PITCH_MOVE_ID,
            label=(
                f"普通攻击：绝对音准（{('一','二','三')[charge - 1]}段蓄力"
                f"{'协同' if cooperative else ''}）"
            ),
            source_name="普通攻击：绝对音准",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=_BASIC,
            parameter=_parameter(
                f"charge-{charge}{'-cooperative' if cooperative else ''}",
                parameter_name,
                source_skill_id=skill_id,
                source_skill_components=components,
            ),
        )
    )

_moves.append(
    _move(
        "basic-absolute-pitch-enhanced",
        move_id=ARIA_BASIC_PITCH_MOVE_ID,
        label="普通攻击：绝对音准（强化蓄力）",
        source_name="普通攻击：绝对音准",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        parameter=_parameter(
            "enhanced-charge-3-cooperative",
            "强化蓄力攻击伤害倍率（协同）",
            source_skill_components=(("1501008", 1.0), ("1501022", 1.0)),
            condition_ids=(ARIA_DELUSION_ACTIVE,),
        ),
        condition_ids=(ARIA_DELUSION_ACTIVE,),
    )
)

for key, move_id, label, source_name, group, tags, param_name, skill_id in (
    (
        "dodge-dash",
        ARIA_DASH_MOVE_ID,
        "冲刺攻击：丝滑小连招",
        "冲刺攻击：丝滑小连招",
        SkillGroup.DODGE,
        _DASH,
        "伤害倍率",
        "1501013",
    ),
    (
        "dodge-counter",
        ARIA_COUNTER_MOVE_ID,
        "闪避反击：滑动变奏",
        "闪避反击：滑动变奏",
        SkillGroup.DODGE,
        _COUNTER,
        "伤害倍率",
        "1501014",
    ),
    (
        "special-full-sugar",
        ARIA_SPECIAL_MOVE_ID,
        "特殊技：全糖电音",
        "特殊技：全糖电音",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        "伤害倍率",
        "1501009",
    ),
    (
        "special-full-sugar-no-ice",
        ARIA_SPECIAL_NO_ICE_MOVE_ID,
        "特殊技：全糖电音·不加冰",
        "特殊技：全糖电音·不加冰",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
        "伤害倍率",
        "1501010",
    ),
    (
        "ex-special-delusion",
        ARIA_EX_SPECIAL_FALL_MOVE_ID,
        "强化特殊技：坠入妄想",
        "强化特殊技：坠入妄想",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        "伤害倍率",
        "1501011",
    ),
    (
        "ex-special-lightspeed",
        ARIA_EX_SPECIAL_LIGHTSPEED_MOVE_ID,
        "强化特殊技：光速入坑",
        "强化特殊技：光速入坑",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
        "伤害倍率",
        "1501012",
    ),
    (
        "chain-fantasy-collab",
        ARIA_CHAIN_MOVE_ID,
        "连携技：梦幻联动",
        "连携技：梦幻联动",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
        "伤害倍率",
        "1501015",
    ),
    (
        "ultimate-energy-full",
        ARIA_ULTIMATE_MOVE_ID,
        "终结技：元气百分百",
        "终结技：元气百分百",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
        "伤害倍率",
        "1501016",
    ),
    (
        "assist-quick",
        ARIA_QUICK_ASSIST_MOVE_ID,
        "快速支援：破碎幻梦",
        "快速支援：破碎幻梦",
        SkillGroup.ASSIST,
        _ASSIST,
        "伤害倍率",
        "1501017",
    ),
    (
        "assist-assault",
        ARIA_SUPPORT_ASSAULT_MOVE_ID,
        "支援突击：安可曲目",
        "支援突击：安可曲目",
        SkillGroup.ASSIST,
        _ASSIST,
        "伤害倍率",
        "1501021",
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
            parameter=_parameter("complete", param_name, source_skill_id=skill_id),
        )
    )


ARIA_REVIEWED_MAPPING = NanokaReviewedMapping(moves=tuple(_moves))


__all__ = [
    "ARIA_BASIC_HEARTBEAT_MOVE_ID",
    "ARIA_BASIC_PITCH_MOVE_ID",
    "ARIA_CHAIN_MOVE_ID",
    "ARIA_COUNTER_MOVE_ID",
    "ARIA_DELUSION_ACTIVE",
    "ARIA_DASH_MOVE_ID",
    "ARIA_ETHER_ANOMALY_RECORD_ID",
    "ARIA_EX_SPECIAL_FALL_MOVE_ID",
    "ARIA_EX_SPECIAL_LIGHTSPEED_MOVE_ID",
    "ARIA_REVIEWED_MAPPING",
    "ARIA_QUICK_ASSIST_MOVE_ID",
    "ARIA_SPECIAL_MOVE_ID",
    "ARIA_SPECIAL_NO_ICE_MOVE_ID",
    "ARIA_SUPPORT_ASSAULT_MOVE_ID",
    "ARIA_THIRD_CHARGE_ANOMALY_HIT",
    "ARIA_ULTIMATE_MOVE_ID",
]
