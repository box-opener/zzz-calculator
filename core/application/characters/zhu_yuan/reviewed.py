"""Reviewed Nanoka 3.2 move identities for Zhu Yuan (character:1241)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ZHU_YUAN_ID = CharacterId("character:1241")
ZHU_SUPPRESSION_MODE_ACTIVE = ScenarioConditionId("condition:zhu-yuan:suppression-mode-active")
ZHU_ENHANCED_SHELL_CONSUMED = ScenarioConditionId("condition:zhu-yuan:enhanced-shell-consumed")
ZHU_ADDITIONAL_CRIT_ACTIVE = ScenarioConditionId("condition:zhu-yuan:additional-ability-crit-active")
ZHU_C6_ETHER_AFTERGLOW_ACTIVE = ScenarioConditionId("condition:zhu-yuan:cinema6-ether-afterglow-active")
ZHU_C1_QUICK_RELOAD_ACTIVE = ScenarioConditionId("condition:zhu-yuan:cinema1-quick-reload-active")
ZHU_CURRENT_SPECIAL_SHOT_COUNT = ScenarioParameterId("parameter:zhu-yuan:current-special-shot-count")

ZHU_ASSAULT_BASIC_MOVE_ID = MoveId("move:zhu-yuan:basic-arrest-mode")
ZHU_SUPPRESSION_BASIC_MOVE_ID = MoveId("move:zhu-yuan:basic-suppression-mode")
ZHU_ASSAULT_DASH_MOVE_ID = MoveId("move:zhu-yuan:dash-firepower-raid")
ZHU_SUPPRESSION_DASH_MOVE_ID = MoveId("move:zhu-yuan:dash-firepower-suppression")
ZHU_COUNTER_MOVE_ID = MoveId("move:zhu-yuan:dodge-counter-firepower-shock")
ZHU_SPECIAL_MOVE_ID = MoveId("move:zhu-yuan:special-deer-shot")
ZHU_EX_MOVE_ID = MoveId("move:zhu-yuan:ex-full-salvo")
ZHU_CHAIN_MOVE_ID = MoveId("move:zhu-yuan:chain-annihilation-mode")
ZHU_ULTIMATE_MOVE_ID = MoveId("move:zhu-yuan:ultimate-annihilation-mode-max")
ZHU_QUICK_ASSIST_MOVE_ID = MoveId("move:zhu-yuan:quick-assist-covering-fire")
ZHU_ASSIST_STRIKE_MOVE_ID = MoveId("move:zhu-yuan:assist-strike-self-defense-counter")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULT = frozenset({DamageTag.ULTIMATE})
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
    curve: str,
    element: Element,
    conditions: tuple[ScenarioConditionId, ...] = (),
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
                source_skill_id=curve,
                condition_ids=conditions,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


_KNOWN_MOVES = (
    _move("dash-firepower-raid", move_id=ZHU_ASSAULT_DASH_MOVE_ID, label="冲刺攻击：火力奇袭", source="冲刺攻击：火力奇袭", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1241017", element=Element.ETHER),
    *tuple(
        _move(
            f"pressure-basic-physical-{stage}",
            move_id=ZHU_SUPPRESSION_BASIC_MOVE_ID,
            label=f"普通攻击：请勿抵抗（第{('一', '二', '三')[stage - 1]}段·物理分项）",
            source="普通攻击：请勿抵抗",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率（物理）",
            curve=f"124100{5 + stage}",
            element=Element.PHYSICAL,
            conditions=(ZHU_SUPPRESSION_MODE_ACTIVE,),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
        for stage in range(1, 4)
    ),
    *tuple(
        _move(
            f"pressure-basic-ether-{stage}",
            move_id=ZHU_SUPPRESSION_BASIC_MOVE_ID,
            label=f"普通攻击：请勿抵抗（第{('一', '二', '三')[stage - 1]}段·以太鹿弹分项）",
            source="普通攻击：请勿抵抗",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率（以太）",
            curve=f"12410{9 + stage}",
            element=Element.ETHER,
            conditions=(ZHU_SUPPRESSION_MODE_ACTIVE, ZHU_ENHANCED_SHELL_CONSUMED),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
        for stage in range(1, 4)
    ),
    _move("pressure-dash-physical", move_id=ZHU_SUPPRESSION_DASH_MOVE_ID, label="冲刺攻击：火力压制（物理分项）", source="冲刺攻击：火力压制", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率（物理）", curve="1241018", element=Element.PHYSICAL, conditions=(ZHU_SUPPRESSION_MODE_ACTIVE,)),
    _move("pressure-dash-ether", move_id=ZHU_SUPPRESSION_DASH_MOVE_ID, label="冲刺攻击：火力压制（以太鹿弹分项）", source="冲刺攻击：火力压制", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率（以太）", curve="1241019", element=Element.ETHER, conditions=(ZHU_SUPPRESSION_MODE_ACTIVE, ZHU_ENHANCED_SHELL_CONSUMED)),
    _move("dodge-counter-ether", move_id=ZHU_COUNTER_MOVE_ID, label="闪避反击：火力震爆", source="闪避反击：火力震爆", group=SkillGroup.DODGE, tags=_COUNTER, parameter="伤害倍率", curve="1241020", element=Element.ETHER),
    _move("special-ether-single-shot", move_id=ZHU_SPECIAL_MOVE_ID, label="特殊技：鹿弹射击（单次）", source="特殊技：鹿弹射击", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1241015", element=Element.ETHER),
    _move("ex-ether", move_id=ZHU_EX_MOVE_ID, label="强化特殊技：全弹连射", source="强化特殊技：全弹连射", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1241016", element=Element.ETHER),
    _move("chain-ether", move_id=ZHU_CHAIN_MOVE_ID, label="连携技：歼灭模式", source="连携技：歼灭模式", group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter="伤害倍率", curve="1241022", element=Element.ETHER),
    _move("ultimate-ether", move_id=ZHU_ULTIMATE_MOVE_ID, label="终结技：歼灭模式MAX", source="终结技：歼灭模式MAX ", group=SkillGroup.ULTIMATE, tags=_ULT, parameter="伤害倍率", curve="1241023", element=Element.ETHER),
    _move("quick-assist-ether", move_id=ZHU_QUICK_ASSIST_MOVE_ID, label="快速支援：掩护射击", source="快速支援：掩护射击", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1241024", element=Element.ETHER),
)

ZHU_YUAN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=_KNOWN_MOVES,
    data_quality_notes=(
        "The five Assault-mode Basic ratios are preserved as source-linked partial entries because their per-stage Physical/Ether mapping is unresolved.",
        "Suppression-mode Physical and Ether component curves remain separate; the relation between the Ether curves and shell-consuming Physical shots is not inferred.",
        "The Assist Strike has one mixed Physical/Ether source curve and remains a local partial entry until its packet split is known.",
        "Cinema 6's four extra Ether bullets have a known 880% ATK total but unresolved event identity; no synthetic Direct child is emitted.",
    ),
)


__all__ = [name for name in globals() if name.isupper()] + ["ZHU_YUAN_REVIEWED_MAPPING"]
