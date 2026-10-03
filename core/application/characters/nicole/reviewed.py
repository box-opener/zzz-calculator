"""Reviewed Nicole (1031) identities and source-curve selections."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


NICOLE_ID = CharacterId("character:1031")

ENHANCED_AMMO_ACTIVE = ScenarioConditionId("condition:nicole:enhanced-ammo-active")
CORE_DEFENSE_DOWN_ACTIVE = ScenarioConditionId(
    "condition:nicole:core-defense-down-active"
)
CINEMA6_TARGET_CRIT_ACTIVE = ScenarioConditionId(
    "condition:nicole:cinema6-target-crit-active"
)

BASIC_RABBIT_COMBO_MOVE_ID = MoveId("move:nicole:basic-rabbit-combo")
DASH_SURPRISE_BOX_MOVE_ID = MoveId("move:nicole:dash-surprise-box")
DODGE_COUNTER_PINNING_SHOT_MOVE_ID = MoveId("move:nicole:dodge-counter-pinning-shot")
SPECIAL_CANDY_BULLET_MOVE_ID = MoveId("move:nicole:special-candy-bullet")
EX_SPECIAL_CANDY_BULLET_MOVE_ID = MoveId("move:nicole:ex-special-candy-bullet")
CHAIN_EXPENSIVE_ETHER_BOMB_MOVE_ID = MoveId("move:nicole:chain-expensive-ether-bomb")
ULTIMATE_CUSTOM_ETHER_GRENADE_MOVE_ID = MoveId("move:nicole:ultimate-custom-ether-grenade")
QUICK_ASSIST_EMERGENCY_SHELLING_MOVE_ID = MoveId("move:nicole:quick-assist-emergency-shelling")
SUPPORT_FOLLOWUP_TAKE_ADVANTAGE_MOVE_ID = MoveId("move:nicole:support-followup-take-advantage")
ETHER_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:nicole:ether-corrosion")
ETHER_ANOMALY_MOVE_ID = MoveId("move:nicole:ether-corrosion")
ETHER_DISORDER_MOVE_ID = MoveId("move:nicole:ether-corrosion-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _parameter(
    key: str,
    name: str,
    *,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
    condition_ids=(),
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        condition_ids=tuple(condition_ids),
        source_skill_id=source_skill_id,
        source_skill_components=source_skill_components,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    *,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids=(),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            _parameter(
                f"{key}-damage",
                parameter_name,
                source_skill_id=source_skill_id,
                source_skill_components=source_skill_components,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=tuple(condition_ids),
    )


NICOLE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-rabbit-combo-1",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：狡兔连打（一段）",
            "普通攻击：狡兔连打",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "一段伤害倍率",
            source_skill_components=(("1031001", 1.0), ("1031002", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "basic-rabbit-combo-2",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：狡兔连打（二段）",
            "普通攻击：狡兔连打",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "二段伤害倍率",
            source_skill_components=(("1031004", 1.0), ("1031005", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "basic-rabbit-combo-3",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：狡兔连打（三段）",
            "普通攻击：狡兔连打",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "三段伤害倍率",
            source_skill_components=(("1031007", 1.0), ("1031008", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=3,
        ),
        _move(
            "basic-enhanced-cunning-shot-1",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：为所欲为（一段强化弹）",
            "普通攻击：为所欲为",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "一段伤害倍率",
            source_skill_components=(("1031001", 1.0), ("1031003", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
            condition_ids=(ENHANCED_AMMO_ACTIVE,),
        ),
        _move(
            "basic-enhanced-cunning-shot-2",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：为所欲为（二段强化弹）",
            "普通攻击：为所欲为",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "二段伤害倍率",
            source_skill_components=(("1031004", 1.0), ("1031006", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
            condition_ids=(ENHANCED_AMMO_ACTIVE,),
        ),
        _move(
            "basic-enhanced-cunning-shot-3",
            BASIC_RABBIT_COMBO_MOVE_ID,
            "普通攻击：为所欲为（三段强化弹）",
            "普通攻击：为所欲为",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "三段伤害倍率",
            source_skill_components=(("1031007", 1.0), ("1031009", 1.0)),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=3,
            condition_ids=(ENHANCED_AMMO_ACTIVE,),
        ),
        _move(
            "dash-surprise-box-front",
            DASH_SURPRISE_BOX_MOVE_ID,
            "冲刺攻击：惊喜开箱（前闪）",
            "冲刺攻击：惊喜开箱",
            SkillGroup.DODGE,
            _DASH,
            "前闪攻击伤害倍率",
            source_skill_components=(("1031201", 1.0), ("1031202", 1.0)),
            element=Element.PHYSICAL,
        ),
        _move(
            "dash-surprise-box-back",
            DASH_SURPRISE_BOX_MOVE_ID,
            "冲刺攻击：惊喜开箱（后闪）",
            "冲刺攻击：惊喜开箱",
            SkillGroup.DODGE,
            _DASH,
            "后闪攻击伤害倍率",
            source_skill_id="1031204",
            element=Element.PHYSICAL,
        ),
        _move(
            "dash-surprise-box-front-enhanced",
            DASH_SURPRISE_BOX_MOVE_ID,
            "冲刺攻击：为所欲为（前闪强化弹）",
            "冲刺攻击：为所欲为",
            SkillGroup.DODGE,
            _DASH,
            "前闪攻击伤害倍率",
            source_skill_components=(("1031201", 1.0), ("1031203", 1.0)),
            element=Element.PHYSICAL,
            condition_ids=(ENHANCED_AMMO_ACTIVE,),
        ),
        _move(
            "dodge-counter-pinning-shot",
            DODGE_COUNTER_PINNING_SHOT_MOVE_ID,
            "闪避反击：牵制炮击",
            "闪避反击：牵制炮击",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            source_skill_components=(("1031205", 1.0), ("1031206", 1.0)),
            element=Element.ETHER,
        ),
        _move(
            "special-candy-bullet",
            SPECIAL_CANDY_BULLET_MOVE_ID,
            "特殊技：糖衣炮弹",
            "特殊技：糖衣炮弹",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            source_skill_components=(("1031101", 1.0), ("1031102", 1.0)),
            element=Element.ETHER,
        ),
        _move(
            "ex-special-candy-bullet-shelling",
            EX_SPECIAL_CANDY_BULLET_MOVE_ID,
            "强化特殊技：夹心糖衣炮弹（炮击）",
            "强化特殊技：夹心糖衣炮弹",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "炮击伤害倍率",
            source_skill_components=(("1031104", 1.0), ("1031105", 1.0)),
            element=Element.ETHER,
        ),
        _move(
            "chain-expensive-ether-bomb-shelling",
            CHAIN_EXPENSIVE_ETHER_BOMB_MOVE_ID,
            "连携技：高价以太爆弹（炮击）",
            "连携技：高价以太爆弹",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "炮击伤害倍率",
            source_skill_components=(("1031301", 1.0), ("1031302", 1.0)),
            element=Element.ETHER,
        ),
        _move(
            "ultimate-custom-ether-grenade-shelling",
            ULTIMATE_CUSTOM_ETHER_GRENADE_MOVE_ID,
            "终结技：特制以太榴弹（炮击）",
            "终结技：特制以太榴弹",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "炮击伤害倍率",
            source_skill_id="1031304",
            element=Element.ETHER,
        ),
        _move(
            "quick-assist-emergency-shelling",
            QUICK_ASSIST_EMERGENCY_SHELLING_MOVE_ID,
            "快速支援：救急炮击",
            "快速支援：救急炮击",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            source_skill_components=(("1031401", 1.0), ("1031402", 1.0)),
            element=Element.ETHER,
        ),
        _move(
            "support-followup-take-advantage",
            SUPPORT_FOLLOWUP_TAKE_ADVANTAGE_MOVE_ID,
            "支援突击：趁虚而入",
            "支援突击：趁虚而入",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            source_skill_id="1031501",
            element=Element.ETHER,
        ),
    ),
    data_quality_notes=(
        "The base Physical Basic/Dash entries and Ether Dodge Counter/Special/Chain/Ultimate/Assist entries follow the exact Nanoka prose and skill_list element IDs.",
        "Nicole's source supplies distinct Basic/Dash normal and enhanced-ammo curves. The enhanced entries share one current-state selection; mapping the 0–8 reload counter to a hit position/count is not inferred.",
        "For the explicit source formulas `A + {B/3}*3`, `A + {B/4}*4`, and `A + {B/20}*20`, the reviewed component weights sum the corresponding curves once each; the divisors and repeats cancel and are not multiplied a second time.",
        "EX Special, Chain, and Ultimate entries include each raw cannon and Energy Field total curve once. The EX charged entry is a separate selectable total that adds the charge curve once; no hit count, duration, or field range scales these totals.",
    ),
)


__all__ = [
    "BASIC_RABBIT_COMBO_MOVE_ID",
    "CHAIN_EXPENSIVE_ETHER_BOMB_MOVE_ID",
    "CINEMA6_TARGET_CRIT_ACTIVE",
    "CORE_DEFENSE_DOWN_ACTIVE",
    "DASH_SURPRISE_BOX_MOVE_ID",
    "DODGE_COUNTER_PINNING_SHOT_MOVE_ID",
    "ENHANCED_AMMO_ACTIVE",
    "ETHER_ANOMALY_MOVE_ID",
    "ETHER_ANOMALY_RECORD_ID",
    "ETHER_DISORDER_MOVE_ID",
    "EX_SPECIAL_CANDY_BULLET_MOVE_ID",
    "NICOLE_ID",
    "NICOLE_REVIEWED_MAPPING",
    "QUICK_ASSIST_EMERGENCY_SHELLING_MOVE_ID",
    "SPECIAL_CANDY_BULLET_MOVE_ID",
    "SUPPORT_FOLLOWUP_TAKE_ADVANTAGE_MOVE_ID",
    "ULTIMATE_CUSTOM_ETHER_GRENADE_MOVE_ID",
]
