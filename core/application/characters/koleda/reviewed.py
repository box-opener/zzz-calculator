"""Reviewed live Nanoka 3.2 move identities for Koleda (character:1101)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


KOLEDA_ID = CharacterId("character:1101")
BEN_ID = CharacterId("character:1121")

BEN_ENHANCED_FOLLOWUP_ACTIVE = ScenarioConditionId(
    "condition:koleda:ben-coordinated-quick-followup-active"
)
BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH = ScenarioConditionId(
    "condition:koleda:ben-enhanced-basic-first-stage-no-switch"
)
POTENTIAL1_TEAM_DAMAGE_ACTIVE = ScenarioConditionId(
    "condition:koleda:potential1-team-damage-active"
)
EXTRA_ABILITY_TARGET_MARK_ACTIVE = ScenarioConditionId(
    "condition:koleda:extra-ability-target-mark-active"
)

POTENTIAL1_ENHANCED_BASIC_LAYERS = ScenarioParameterId(
    "parameter:koleda:potential1-enhanced-basic-consumed-furnace-layers"
)
CINEMA4_CURRENT_FURNACE_LAYERS = ScenarioParameterId(
    "parameter:koleda:cinema4-current-furnace-layers"
)
FIRE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:koleda:fire-disorder-remaining-seconds"
)

BASIC_MOVE_ID = MoveId("move:koleda:basic-aegis-smash")
ENHANCED_BASIC_MOVE_ID = MoveId("move:koleda:enhanced-basic-furnace-smash")
DASH_MOVE_ID = MoveId("move:koleda:dash-shudder")
DODGE_COUNTER_MOVE_ID = MoveId("move:koleda:dodge-counter-dont-underestimate-me")
SPECIAL_MOVE_ID = MoveId("move:koleda:special-hammer-time")
EX_SPECIAL_MOVE_ID = MoveId("move:koleda:ex-special-boiling-furnace")
CHAIN_ATTACK_MOVE_ID = MoveId("move:koleda:chain-heaven-earth-crash")
ULTIMATE_MOVE_ID = MoveId("move:koleda:ultimate-hammer-to-the-core")
QUICK_ASSIST_MOVE_ID = MoveId("move:koleda:quick-assist-here-i-come")
ASSIST_STRIKE_MOVE_ID = MoveId("move:koleda:assist-strike-hammer-bell")
FIRE_ANOMALY_MOVE_ID = MoveId("move:koleda:fire-burn")
FIRE_DISORDER_MOVE_ID = MoveId("move:koleda:fire-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    *,
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
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
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


_BASIC_STAGES = ("一", "二", "三", "四")


def reviewed_mapping(*, ben_in_team: bool, potential_level: int = 0) -> NanokaReviewedMapping:
    moves: list[NanokaMoveSpec] = [
        *tuple(
            _move(
                key=f"basic-physical-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：砸扁，粉碎（{_BASIC_STAGES[stage - 1]}段）",
                source_name="普通攻击：砸扁，粉碎",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{_BASIC_STAGES[stage - 1]}段伤害倍率",
                source_skill_id=f"110100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            key="enhanced-basic-stage1",
            move_id=ENHANCED_BASIC_MOVE_ID,
            label="强化普通攻击：熔炉升温（第一段）",
            source_name="普通攻击：砸扁，粉碎",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="强化普攻一段伤害倍率",
            source_skill_id="1101005",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            key="enhanced-basic-stage2",
            move_id=ENHANCED_BASIC_MOVE_ID,
            label=(
                "强化普通攻击：熔炉升温（第二段·本协同）"
                if ben_in_team and potential_level == 0
                else "强化普通攻击：熔炉升温（第二段）"
            ),
            source_name="普通攻击：砸扁，粉碎",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name=(
                "强化普攻二段伤害倍率（协同）"
                if ben_in_team and potential_level == 0
                else "强化普攻二段伤害倍率"
            ),
            source_skill_id=(
                "1101007" if ben_in_team and potential_level == 0 else "1101006"
            ),
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            key="dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：给我颤抖",
            source_name="冲刺攻击：给我颤抖",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1101201",
            element=Element.PHYSICAL,
        ),
        _move(
            key="dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：别小看我",
            source_name="闪避反击：别小看我",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1101202",
            element=Element.FIRE,
        ),
        _move(
            key="special-impact",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：爆破！铁锤时间（打击）",
            source_name="特殊技：爆破！铁锤时间",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="打击伤害倍率",
            source_skill_id="1101101",
            element=Element.FIRE,
        ),
        _move(
            key="special-explosion",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：爆破！铁锤时间（引爆）",
            source_name="特殊技：爆破！铁锤时间",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="引爆伤害倍率",
            source_skill_id="1101102",
            element=Element.FIRE,
        ),
        _move(
            key="ex-special-impact",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：沸腾熔炉（打击）",
            source_name="强化特殊技：沸腾熔炉",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="打击伤害倍率",
            source_skill_id="1101104",
            element=Element.FIRE,
        ),
        _move(
            key="ex-special-explosion",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：沸腾熔炉（引爆）",
            source_name="强化特殊技：沸腾熔炉",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="引爆伤害倍率",
            source_skill_id="1101105",
            element=Element.FIRE,
        ),
        _move(
            key="chain-attack",
            move_id=CHAIN_ATTACK_MOVE_ID,
            label="连携技：天崩-地裂",
            source_name="连携技：天崩-地裂",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1101301",
            element=Element.FIRE,
        ),
        _move(
            key="ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：锤进地心（本协同）" if ben_in_team else "终结技：锤进地心",
            source_name="终结技：锤进地心",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率（协同）" if ben_in_team else "伤害倍率",
            source_skill_id="1101402" if ben_in_team else "1101401",
            element=Element.FIRE,
        ),
        _move(
            key="quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：让我来",
            source_name="快速支援：让我来",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1101501",
            element=Element.FIRE,
        ),
        _move(
            key="assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：锤钟",
            source_name="支援突击：锤钟",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1101505",
            element=Element.FIRE,
        ),
    ]

    if ben_in_team:
        if potential_level >= 1:
            moves.append(
                _move(
                    key="enhanced-basic-stage2-ben-coordinated",
                    move_id=ENHANCED_BASIC_MOVE_ID,
                    label="强化普通攻击：熔炉升温（第二段·本协同）",
                    source_name="普通攻击：砸扁，粉碎",
                    group=SkillGroup.BASIC_ATTACK,
                    tags=_BASIC,
                    parameter_name="强化普攻二段伤害倍率（协同）",
                    source_skill_id="1101007",
                    element=Element.FIRE,
                    relation=MultiplierRelation.SEQUENTIAL_STAGE,
                    stage=2,
                    condition_ids=(BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,),
                )
            )
        moves.extend(
            (
                _move(
                    key="special-ben-coordinated-explosion",
                    move_id=SPECIAL_MOVE_ID,
                    label="特殊技：爆破！铁锤时间（本协同引爆）",
                    source_name="特殊技：爆破！铁锤时间",
                    group=SkillGroup.SPECIAL_ATTACK,
                    tags=_SPECIAL,
                    parameter_name="引爆伤害倍率（协同）",
                    source_skill_id="1101103",
                    element=Element.FIRE,
                    condition_ids=(BEN_ENHANCED_FOLLOWUP_ACTIVE,),
                ),
                _move(
                    key="ex-special-ben-coordinated-explosion",
                    move_id=EX_SPECIAL_MOVE_ID,
                    label="强化特殊技：沸腾熔炉（本协同引爆）",
                    source_name="强化特殊技：沸腾熔炉",
                    group=SkillGroup.SPECIAL_ATTACK,
                    tags=_EX_SPECIAL,
                    parameter_name="引爆伤害倍率（协同）",
                    source_skill_id="1101106",
                    element=Element.FIRE,
                    condition_ids=(BEN_ENHANCED_FOLLOWUP_ACTIVE,),
                ),
            )
        )

    return NanokaReviewedMapping(
        moves=tuple(moves),
        data_quality_notes=(
            "Koleda and Ben coordinated parameters are selected from their exact source curves only when Ben is in the team; quick Special/EX cooperation also needs the explicit enhanced-Basic follow-up state.",
            "Potential I adds source-described current states and move access; its empty ability-list description does not justify an invented additional damage multiplier.",
            "Potential I describes a stronger first-stage chase effect without a separate numeric curve; no extra hit or multiplier is inferred.",
            "The source's class-7 [锋御] / 锐暴 potential branch remains outside the registered role model; the non-[锋御] team Crit Damage branch is modeled for current registered roles.",
            "Disorder, Energy, Daze, Support Point, furnace-generation, and timing/resource transitions are not replayed.",
        ),
    )


KOLEDA_REVIEWED_MAPPING = reviewed_mapping(ben_in_team=False)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BEN_ENHANCED_FOLLOWUP_ACTIVE",
    "BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH",
    "BEN_ID",
    "BASIC_MOVE_ID",
    "CINEMA4_CURRENT_FURNACE_LAYERS",
    "CHAIN_ATTACK_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ENHANCED_BASIC_MOVE_ID",
    "EXTRA_ABILITY_TARGET_MARK_ACTIVE",
    "EX_SPECIAL_MOVE_ID",
    "FIRE_ANOMALY_MOVE_ID",
    "FIRE_DISORDER_MOVE_ID",
    "FIRE_DISORDER_REMAINING_SECONDS",
    "KOLEDA_ID",
    "KOLEDA_REVIEWED_MAPPING",
    "POTENTIAL1_ENHANCED_BASIC_LAYERS",
    "POTENTIAL1_TEAM_DAMAGE_ACTIVE",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "reviewed_mapping",
]
