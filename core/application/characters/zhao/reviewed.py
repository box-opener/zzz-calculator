"""Reviewed Zhao (1341) move identities and Nanoka damage curves."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ZHAO_ID = CharacterId("character:1341")

SPRING_CURTAIN_ACTIVE = ScenarioConditionId("condition:zhao:spring-curtain-active")
ANY_ETHER_CURTAIN_ACTIVE = ScenarioConditionId("condition:zhao:any-ether-curtain-active")
SPRING_CURTAIN_ATTACK_BUFF_ACTIVE = ScenarioConditionId("condition:zhao:spring-curtain-attack-buff-active")
ZHAO_C1_RESISTANCE_IGNORE_ACTIVE = ScenarioConditionId("condition:zhao:c1-resistance-ignore-active")
ZHAO_C2_ATTACK_BUFF_ACTIVE = ScenarioConditionId("condition:zhao:c2-heal-attack-buff-active")
FROSTBITE_FULL = ScenarioConditionId("condition:zhao:frostbite-full")
IN_COMBAT = ScenarioConditionId("condition:zhao:in-combat")
CHARGE_SECONDS = ScenarioParameterId("parameter:zhao:final-judgment-charge-seconds")
ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId("parameter:zhao:ice-disorder-remaining-seconds")

BASIC_JUDGMENT_MOVE_ID = MoveId("move:zhao:basic-cold-judgment")
BASIC_FINAL_JUDGMENT_MOVE_ID = MoveId("move:zhao:basic-final-judgment")
DASH_BOUNCING_SPRINT_MOVE_ID = MoveId("move:zhao:dash-bouncing-sprint")
DODGE_COUNTER_SUDDEN_FLASH_MOVE_ID = MoveId("move:zhao:dodge-counter-sudden-flash")
SPECIAL_ICE_SPILL_MOVE_ID = MoveId("move:zhao:special-ice-spill")
EX_SPECIAL_FROSTED_LAND_MOVE_ID = MoveId("move:zhao:ex-special-frosted-land")
CHAIN_TEMPORARY_COOPERATION_MOVE_ID = MoveId("move:zhao:chain-temporary-cooperation")
ULTIMATE_RABBIT_SLASH_MOVE_ID = MoveId("move:zhao:ultimate-rabbit-slash")
ENTRY_FROSTBURST_MOVE_ID = MoveId("move:zhao:entry-frostburst")
QUICK_ASSIST_PATCHING_MOVE_ID = MoveId("move:zhao:quick-assist-patching-gaps")
SUPPORT_FOLLOWUP_AFTERGLOW_MOVE_ID = MoveId("move:zhao:support-afterglow")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _p(key: str, name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=(_p(f"{key}-damage", parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


ZHAO_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move("basic-cold-judgment-1", BASIC_JUDGMENT_MOVE_ID, "普通攻击：凛冽裁决（一段）", "普通攻击：凛冽裁决", SkillGroup.BASIC_ATTACK, _BASIC, "一段伤害倍率", "1341001", Element.PHYSICAL, relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=1),
        _move("basic-cold-judgment-2", BASIC_JUDGMENT_MOVE_ID, "普通攻击：凛冽裁决（二段）", "普通攻击：凛冽裁决", SkillGroup.BASIC_ATTACK, _BASIC, "二段伤害倍率", "1341002", Element.ICE, relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=2),
        _move("basic-cold-judgment-3", BASIC_JUDGMENT_MOVE_ID, "普通攻击：凛冽裁决（三段）", "普通攻击：凛冽裁决", SkillGroup.BASIC_ATTACK, _BASIC, "三段伤害倍率", "1341003", Element.ICE, relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=3),
        _move("basic-cold-judgment-4", BASIC_JUDGMENT_MOVE_ID, "普通攻击：凛冽裁决（四段）", "普通攻击：凛冽裁决", SkillGroup.BASIC_ATTACK, _BASIC, "四段伤害倍率", "1341004", Element.ICE, relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=4),
        _move("basic-final-judgment", BASIC_FINAL_JUDGMENT_MOVE_ID, "普通攻击：最终裁决", "普通攻击：最终裁决", SkillGroup.BASIC_ATTACK, _BASIC, "伤害倍率", "1341008", Element.ICE),
        _move("dash-bouncing-sprint", DASH_BOUNCING_SPRINT_MOVE_ID, "冲刺攻击：弹跳冲刺", "冲刺攻击：弹跳冲刺", SkillGroup.DODGE, _DASH, "伤害倍率", "1341011", Element.ICE),
        _move("dodge-counter-sudden-flash", DODGE_COUNTER_SUDDEN_FLASH_MOVE_ID, "闪避反击：倏忽闪", "闪避反击：倏忽闪", SkillGroup.DODGE, _COUNTER, "伤害倍率", "1341012", Element.ICE),
        _move("special-ice-spill", SPECIAL_ICE_SPILL_MOVE_ID, "特殊技：碎冰溢寒", "特殊技：碎冰溢寒", SkillGroup.SPECIAL_ATTACK, _SPECIAL, "伤害倍率", "1341009", Element.ICE),
        _move("ex-special-frosted-land", EX_SPECIAL_FROSTED_LAND_MOVE_ID, "强化特殊技：流霜冻土", "强化特殊技：流霜冻土", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, "伤害倍率", "1341010", Element.ICE),
        _move("chain-temporary-cooperation", CHAIN_TEMPORARY_COOPERATION_MOVE_ID, "连携技：临时合作", "连携技：临时合作", SkillGroup.CHAIN_ATTACK, _CHAIN, "伤害倍率", "1341013", Element.ICE),
        _move("entry-frostburst", ENTRY_FROSTBURST_MOVE_ID, "登场技：霜迸", "登场技：霜迸", SkillGroup.ASSIST, _ASSIST, "伤害倍率", "1341015", Element.ICE, condition_ids=(FROSTBITE_FULL, IN_COMBAT)),
        _move("quick-assist-patching-gaps", QUICK_ASSIST_PATCHING_MOVE_ID, "快速支援：查漏补缺", "快速支援：查漏补缺", SkillGroup.ASSIST, _ASSIST, "伤害倍率", "1341016", Element.ICE),
        _move("support-afterglow", SUPPORT_FOLLOWUP_AFTERGLOW_MOVE_ID, "支援突击：凛光返照", "支援突击：凛光返照", SkillGroup.ASSIST, _FOLLOW_UP, "伤害倍率", "1341020", Element.ICE),
    )
)

MIXED_ELEMENT_MOVE_IDS = frozenset({DASH_BOUNCING_SPRINT_MOVE_ID})

__all__ = [
    "ANY_ETHER_CURTAIN_ACTIVE", "BASIC_FINAL_JUDGMENT_MOVE_ID", "BASIC_JUDGMENT_MOVE_ID",
    "CHAIN_TEMPORARY_COOPERATION_MOVE_ID", "CHARGE_SECONDS", "DASH_BOUNCING_SPRINT_MOVE_ID",
    "DODGE_COUNTER_SUDDEN_FLASH_MOVE_ID", "ENTRY_FROSTBURST_MOVE_ID", "EX_SPECIAL_FROSTED_LAND_MOVE_ID",
    "FROSTBITE_FULL", "IN_COMBAT", "MIXED_ELEMENT_MOVE_IDS", "QUICK_ASSIST_PATCHING_MOVE_ID",
    "ICE_DISORDER_REMAINING_SECONDS", "SPECIAL_ICE_SPILL_MOVE_ID", "SPRING_CURTAIN_ACTIVE", "SPRING_CURTAIN_ATTACK_BUFF_ACTIVE",
    "SUPPORT_FOLLOWUP_AFTERGLOW_MOVE_ID", "ULTIMATE_RABBIT_SLASH_MOVE_ID", "ZHAO_C1_RESISTANCE_IGNORE_ACTIVE",
    "ZHAO_C2_ATTACK_BUFF_ACTIVE", "ZHAO_ID", "ZHAO_REVIEWED_MAPPING",
]
