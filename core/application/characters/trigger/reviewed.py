"""Manually reviewed Trigger skill taxonomy and conditions."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


TRIGGER_ID = CharacterId("character:1361")
SNIPER_STANCE_CONDITION_ID = ScenarioConditionId(
    "condition:trigger:sniper-stance-active"
)
HUNTER_EYE_CONDITION_ID = ScenarioConditionId(
    "condition:trigger:hunter-eye-active"
)
FOLLOW_UP_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:trigger:follow-up-active"
)


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_FOLLOW_UP = frozenset({DamageTag.BASIC_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
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
    *,
    element: Element = Element.ELECTRIC,
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


TRIGGER_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-cold-chamber-{stage}",
                "move:trigger:cold-chamber",
                f"普通攻击：冷膛射击（{stage}段）",
                "普通攻击：冷膛射击",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                (_p(f"stage-{stage}", f"{('一','二','三','四')[stage - 1]}段伤害倍率"),),
                MultiplierRelation.SEQUENTIAL_STAGE,
                element=Element.PHYSICAL if stage < 4 else Element.ELECTRIC,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        *tuple(
            _move(
                f"basic-silent-sniping-{stage}",
                "move:trigger:silent-sniping",
                f"普通攻击：无音狙杀（{label}）",
                "普通攻击：无音狙杀",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                (_p(key, param, SNIPER_STANCE_CONDITION_ID),),
                MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage, label, key, param in (
                (1, "连续射击", "shoot", "射击伤害倍率"),
                (2, "蓄力反击", "counter", "反击伤害倍率"),
                (3, "终结一击", "finisher", "终结伤害倍率"),
            )
        ),
        _move(
            "basic-concerto-sniping",
            "move:trigger:concerto-sniping",
            "普通攻击：协奏狙杀",
            "普通攻击：协奏狙杀",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("complete", "连射伤害倍率", FOLLOW_UP_ACTIVE_CONDITION_ID),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "basic-concerto-sniping-hell-shoot",
            "move:trigger:concerto-sniping-hell",
            "普通攻击：协奏狙杀·冥狱（连射）",
            "普通攻击：协奏狙杀·冥狱",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("shoot", "连射伤害倍率", FOLLOW_UP_ACTIVE_CONDITION_ID),),
            MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "basic-concerto-sniping-hell-finisher",
            "move:trigger:concerto-sniping-hell",
            "普通攻击：协奏狙杀·冥狱（终结）",
            "普通攻击：协奏狙杀·冥狱",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("finisher", "终结伤害倍率", FOLLOW_UP_ACTIVE_CONDITION_ID),),
            MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move("dodge-dash", "move:trigger:dodge-dash", "冲刺攻击：怨魂返", "冲刺攻击：怨魂返", SkillGroup.DODGE, _DASH, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE, element=Element.PHYSICAL),
        _move("dodge-counter", "move:trigger:dodge-counter", "闪避反击：极魂罚", "闪避反击：极魂罚", SkillGroup.DODGE, _COUNTER, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-ghost-flash", "move:trigger:ghost-flash", "特殊技：幽闪", "特殊技：幽闪", SkillGroup.SPECIAL_ATTACK, _SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-ghost-bloom", "move:trigger:ghost-bloom", "强化特殊技：幽闪花葬", "强化特殊技：幽闪花葬", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("chain-styx", "move:trigger:styx", "连携技：冥河之引", "连携技：冥河之引", SkillGroup.CHAIN_ATTACK, _CHAIN, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("ultimate-anthem", "move:trigger:underworld-anthem", "终结技：冥府挽歌", "终结技：冥府挽歌", SkillGroup.ULTIMATE, _ULTIMATE, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-quick-cover", "move:trigger:quick-cover", "快速支援：冷枪援护", "快速支援：冷枪援护", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-thunder-pierce", "move:trigger:thunder-pierce", "支援突击：殛雷穿心", "支援突击：殛雷穿心", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
    )
)


__all__ = [
    "FOLLOW_UP_ACTIVE_CONDITION_ID",
    "HUNTER_EYE_CONDITION_ID",
    "SNIPER_STANCE_CONDITION_ID",
    "TRIGGER_ID",
    "TRIGGER_REVIEWED_MAPPING",
]
