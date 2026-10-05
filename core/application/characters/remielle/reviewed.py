"""Reviewed Remielle (1581) raw direct-damage identities."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


REMIELLE_ID = CharacterId("character:1581")
# Retained only as a legacy request key. Selected source slots now define whether
# a static Flare source exists, so the compiler no longer exposes this toggle.
VIRTUAL_LIGHTS_AVAILABLE = ScenarioConditionId(
    "condition:remielle:virtual-lights-available"
)
REFLECTION_STATE_ACTIVE = ScenarioConditionId(
    "condition:remielle:reflection-state-active"
)
PHASE_SHIFT_ACTIVE = ScenarioConditionId("condition:remielle:phase-shift-active")
ENEMY_PRISM_ACTIVE = ScenarioConditionId("condition:remielle:enemy-prism-active")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})

BASIC_DANCE_MOVE_ID = MoveId("move:remielle:basic-flutter")
BASIC_SOLO_MOVE_ID = MoveId("move:remielle:basic-solo-dance")
BASIC_VERTICAL_RAINBOW_MOVE_ID = MoveId("move:remielle:basic-vertical-rainbow")
BASIC_SURPRISE_MOVE_ID = MoveId("move:remielle:basic-surprise")
DASH_MOVE_ID = MoveId("move:remielle:dash-sharp-glint")
DODGE_COUNTER_MOVE_ID = MoveId("move:remielle:dodge-counter-shadow")
SPECIAL_MOVE_ID = MoveId("move:remielle:special-dawn")
SPECIAL_TRANSITION_MOVE_ID = MoveId("move:remielle:special-dawn-transition")
EX_SPECIAL_MOVE_ID = MoveId("move:remielle:ex-special-hymn-of-dawn")
CHAIN_MOVE_ID = MoveId("move:remielle:chain-overlapping-steps")
ULTIMATE_MOVE_ID = MoveId("move:remielle:ultimate-chaotic-finale")
QUICK_ASSIST_MOVE_ID = MoveId("move:remielle:quick-assist-new-feather")
ASSIST_STRIKE_MOVE_ID = MoveId("move:remielle:assist-strike-sleepless-dawn")
SPECIAL_ASSIST_MOVE_ID = MoveId("move:remielle:special-assist-feather-dance")


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str | None = None,
    *,
    source_skill_components: tuple[tuple[str, float], ...] = (),
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    conditions: tuple[ScenarioConditionId, ...] = (),
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
                source_skill_components=source_skill_components,
                condition_ids=conditions,
            ),
        ),
        multiplier_relation=relation,
        element=Element.LUMINANCE,
        stage_index=stage,
        condition_ids=conditions,
    )


_BASIC_STAGE_NAMES = ("一", "二", "三", "四")
REMIELLE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-flutter-{stage}",
                BASIC_DANCE_MOVE_ID,
                f"普通攻击：蹁跹（{_BASIC_STAGE_NAMES[stage - 1]}段）",
                "普通攻击：蹁跹",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_BASIC_STAGE_NAMES[stage - 1]}段伤害倍率",
                f"158100{stage + 1}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-solo-dance",
            BASIC_SOLO_MOVE_ID,
            "普通攻击：独舞",
            "普通攻击：独舞",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1581006",
        ),
        _move(
            "basic-vertical-rainbow",
            BASIC_VERTICAL_RAINBOW_MOVE_ID,
            "普通攻击：垂虹",
            "普通攻击：垂虹",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1581007",
        ),
        _move(
            "basic-surprise",
            BASIC_SURPRISE_MOVE_ID,
            "普通攻击：惊鸿",
            "普通攻击：惊鸿",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1581008",
            conditions=(REFLECTION_STATE_ACTIVE,),
        ),
        _move(
            "dash-sharp-glint",
            DASH_MOVE_ID,
            "冲刺攻击：锐芒",
            "冲刺攻击：锐芒",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1581012",
        ),
        _move(
            "dodge-counter-shadow",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：对影",
            "闪避反击：对影",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1581013",
        ),
        _move(
            "special-dawn",
            SPECIAL_MOVE_ID,
            "特殊技：薄明",
            "特殊技：薄明",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1581009",
        ),
        _move(
            "special-dawn-transition",
            SPECIAL_TRANSITION_MOVE_ID,
            "特殊技：曙色颂·转辉",
            "特殊技：曙色颂·转辉",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1581010",
        ),
        _move(
            "ex-special-hymn-of-dawn",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：曙色颂",
            "强化特殊技：曙色颂",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1581011",
        ),
        _move(
            "chain-overlapping-steps",
            CHAIN_MOVE_ID,
            "连携技：交叠舞步",
            "连携技：交叠舞步",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1581014",
        ),
        _move(
            "ultimate-chaotic-finale",
            ULTIMATE_MOVE_ID,
            "终结技：缭乱终幕",
            "终结技：缭乱终幕",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1581016",
        ),
        _move(
            "quick-assist-new-feather",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：片羽新生",
            "快速支援：片羽新生",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1581017",
        ),
        _move(
            "assist-strike-sleepless-dawn",
            ASSIST_STRIKE_MOVE_ID,
            "支援突击：眠醒残明",
            "支援突击：眠醒残明",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1581021",
        ),
        _move(
            "special-assist-feather-dance",
            SPECIAL_ASSIST_MOVE_ID,
            "支援技：花羽轮舞",
            "支援技：花羽轮舞",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1581015",
        ),
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_DANCE_MOVE_ID",
    "BASIC_SOLO_MOVE_ID",
    "BASIC_SURPRISE_MOVE_ID",
    "BASIC_VERTICAL_RAINBOW_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ENEMY_PRISM_ACTIVE",
    "EX_SPECIAL_MOVE_ID",
    "PHASE_SHIFT_ACTIVE",
    "QUICK_ASSIST_MOVE_ID",
    "REFLECTION_STATE_ACTIVE",
    "REMIELLE_ID",
    "REMIELLE_REVIEWED_MAPPING",
    "SPECIAL_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "SPECIAL_TRANSITION_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "VIRTUAL_LIGHTS_AVAILABLE",
]
