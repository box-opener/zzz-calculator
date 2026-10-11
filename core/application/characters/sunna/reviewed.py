"""Reviewed move identities and Nanoka 3.2 curves for Sunna (1491)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import SUNNA_ID

ANGEL_CHORUS_ACTIVE = ScenarioConditionId("condition:sunna:angel-chorus-active")
ETHER_VEIL_ACTIVE = ScenarioConditionId("condition:sunna:ether-veil-active")
BAD_CAT_ACTIVE = ScenarioConditionId("condition:sunna:bad-cat-active")
CINEMA6_CREATING_ACTIVE = ScenarioConditionId("condition:sunna:cinema6-creating-active")
SUNNA_ETHER_VEIL_ACTIVE = ScenarioConditionId("condition:sunna:sunna-ether-veil-active")
EXTRA_STUN_VULNERABILITY_ACTIVE = ScenarioConditionId(
    "condition:sunna:extra-stun-vulnerability-active"
)
COOPERATIVE_PHOTO_EXTRA = ScenarioParameterId("parameter:sunna:cooperative-photo-extra")

SUNNA_BASIC_MOVE_ID = MoveId("move:sunna:wandering-meteor-hammer")
SUNNA_BAD_CAT_MOVE_ID = MoveId("move:sunna:bad-cat-automatic-attack")
SUNNA_DASH_MOVE_ID = MoveId("move:sunna:skyward-hammer")
SUNNA_DODGE_COUNTER_MOVE_ID = MoveId("move:sunna:daydream-triple-strike")
SUNNA_SPECIAL_MOVE_ID = MoveId("move:sunna:star-shot")
SUNNA_EX_BOMB_MOVE_ID = MoveId("move:sunna:bubblegum-bombardment")
SUNNA_EX_PHOTO_MOVE_ID = MoveId("move:sunna:special-photo-technique")
SUNNA_CHAIN_MOVE_ID = MoveId("move:sunna:keep-away-from-cat")
SUNNA_ULTIMATE_MOVE_ID = MoveId("move:sunna:smash-everything")
SUNNA_QUICK_ASSIST_MOVE_ID = MoveId("move:sunna:rapid-fire-strikes")
SUNNA_ASSIST_STRIKE_MOVE_ID = MoveId("move:sunna:bouncing-practice")

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
    label: str,
    source_id: str | None = None,
    *,
    components: tuple[tuple[str, float], ...] = (),
    conditions: tuple[ScenarioConditionId, ...] = (),
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=label,
        source_skill_id=source_id,
        source_skill_components=components,
        condition_ids=conditions,
    )


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    curve: str | None,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    components: tuple[tuple[str, float], ...] = (),
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
            _parameter(
                f"{key}-damage",
                parameter_name,
                curve,
                components=components,
                conditions=condition_ids,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
        condition_ids=condition_ids,
    )


_STAGE_LABELS = ("一", "二", "三", "四")
SUNNA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=SUNNA_BASIC_MOVE_ID,
                label=f"普通攻击：鬼马流星锤（{_STAGE_LABELS[stage - 1]}段）",
                source_name="普通攻击：鬼马流星锤",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{_STAGE_LABELS[stage - 1]}段伤害倍率",
                curve=f"149100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "bad-cat",
            move_id=SUNNA_BAD_CAT_MOVE_ID,
            label="普通攻击：坏猫出没（自动攻击）",
            source_name="普通攻击：坏猫出没",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            curve="1491005",
            condition_ids=(BAD_CAT_ACTIVE,),
        ),
        _move(
            "dash-attack",
            move_id=SUNNA_DASH_MOVE_ID,
            label="冲刺攻击：冲天锤",
            source_name="冲刺攻击：冲天锤",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            curve="1491009",
        ),
        _move(
            "dodge-counter",
            move_id=SUNNA_DODGE_COUNTER_MOVE_ID,
            label="闪避反击：妄想三振",
            source_name="闪避反击：妄想三振",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            curve="1491010",
        ),
        _move(
            "special",
            move_id=SUNNA_SPECIAL_MOVE_ID,
            label="特殊技：星星发射",
            source_name="特殊技：星星发射",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            curve="1491006",
        ),
        _move(
            "ex-special-bubblegum-bombardment",
            move_id=SUNNA_EX_BOMB_MOVE_ID,
            label="强化特殊技：泡泡糖轰炸",
            source_name="强化特殊技：泡泡糖轰炸",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="泡泡糖轰炸伤害倍率",
            curve=None,
            components=(("1491007", 1.0), ("1491018", 1.0)),
        ),
        _move(
            "ex-special-photo-technique",
            move_id=SUNNA_EX_PHOTO_MOVE_ID,
            label="强化特殊技：特别拍照技巧",
            source_name="强化特殊技：特别拍照技巧",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            curve="1491008",
            condition_ids=(ANGEL_CHORUS_ACTIVE,),
        ),
        _move(
            "chain-attack",
            move_id=SUNNA_CHAIN_MOVE_ID,
            label="连携技：别惹猫咪",
            source_name="连携技：别惹猫咪",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            curve="1491011",
        ),
        _move(
            "ultimate",
            move_id=SUNNA_ULTIMATE_MOVE_ID,
            label="终结技：通通砸碎！",
            source_name="终结技：通通砸碎！",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            curve="1491012",
        ),
        _move(
            "quick-assist",
            move_id=SUNNA_QUICK_ASSIST_MOVE_ID,
            label="快速支援：狂音连打",
            source_name="快速支援：狂音连打",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1491013",
        ),
        _move(
            "assist-strike",
            move_id=SUNNA_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：弹跳练习",
            source_name="支援突击：弹跳练习",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            curve="1491017",
        ),
    ),
    data_quality_notes=(
        "Sunna is a non-Anomaly Support agent. No self Anomaly or Disorder damage entry is synthesized.",
        "The Basic Bad Cat automatic attack is Physical and uses 1491005 with Sunna's Initial ATK. Its current activation condition combines backline presence, no marked enemy, and an available clawing tool; resource and battle timelines are not simulated, so the exact current activation is user selected.",
        "Special Photo Technique has a separate coordinated damage parameter in source (1491008 + 1491019). Its activation depends on the Angel Chorus state; it is retained for explicit state mapping rather than merged into the unconditional move curve.",
        "Core Cat's Gaze damage is attributed to the triggering agent and uses that agent's element and stats. A generated child event has no inherited move, skill-group, or damage-tag identity.",
        "Cinema 6 damage bonus is limited to Cat's Gaze child events; current Angel Chorus, Ether Veil, and Cinema 6 states are static user-selected inputs, not a replay of duration or resource timelines.",
    ),
)


__all__ = [
    "SUNNA_ID",
    "SUNNA_REVIEWED_MAPPING",
    "SUNNA_BASIC_MOVE_ID",
    "SUNNA_BAD_CAT_MOVE_ID",
    "SUNNA_DASH_MOVE_ID",
    "SUNNA_DODGE_COUNTER_MOVE_ID",
    "SUNNA_SPECIAL_MOVE_ID",
    "SUNNA_EX_BOMB_MOVE_ID",
    "SUNNA_EX_PHOTO_MOVE_ID",
    "SUNNA_CHAIN_MOVE_ID",
    "SUNNA_ULTIMATE_MOVE_ID",
    "SUNNA_QUICK_ASSIST_MOVE_ID",
    "SUNNA_ASSIST_STRIKE_MOVE_ID",
    "ANGEL_CHORUS_ACTIVE",
    "BAD_CAT_ACTIVE",
    "ETHER_VEIL_ACTIVE",
    "CINEMA6_CREATING_ACTIVE",
    "SUNNA_ETHER_VEIL_ACTIVE",
    "EXTRA_STUN_VULNERABILITY_ACTIVE",
    "COOPERATIVE_PHOTO_EXTRA",
]
