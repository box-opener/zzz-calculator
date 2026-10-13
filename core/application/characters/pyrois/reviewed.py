"""Reviewed move identities for Pyrois's Nanoka live 3.2 source."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from ...ids import ScenarioConditionId
from .config import PYROIS_ID


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH_TAGS = frozenset({DamageTag.DASH_ATTACK})
_COUNTER_TAGS = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL_TAGS = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_TAGS = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN_TAGS = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

_BASIC_DUSK = MoveId("move:pyrois:basic-afterglow")
_BASIC_DAYLIGHT = MoveId("move:pyrois:basic-daylight")
_DASH = MoveId("move:pyrois:dash-sunrise")
_COUNTER = MoveId("move:pyrois:dodge-counter-morning-glow")
_SPECIAL = MoveId("move:pyrois:special-residual-light")
_EX = MoveId("move:pyrois:ex-sunflower")
_CHAIN = MoveId("move:pyrois:chain-march-parade")
_ULTIMATE_UP = MoveId("move:pyrois:ultimate-military-execution")
_ULTIMATE_DOWN = MoveId("move:pyrois:ultimate-victory-road")
_ULTIMATE_LEFT = MoveId("move:pyrois:ultimate-unbound-sword")
_ULTIMATE_RIGHT = MoveId("move:pyrois:ultimate-eternal-prison")
_QUICK_ASSIST = MoveId("move:pyrois:quick-assist-dusk-guard")
_SUPPORT_STRIKE = MoveId("move:pyrois:assist-strike-see-daylight")
PYROIS_ASSIST_ORDER_MOVE_ID = MoveId("move:pyrois:special-battle-order")

PYROIS_SUNFLAME_ACTIVE = ScenarioConditionId(
    "condition:character:1551:sunflame-state-active"
)
PYROIS_SUNFLARE_ACTIVE = ScenarioConditionId(
    "condition:character:1551:sunflare-state-active"
)
PYROIS_LEFT_CORE_EXTRA_ACTIVE = ScenarioConditionId(
    "condition:character:1551:left-core-extra-trigger-active"
)
PYROIS_RIGHT_CORE_EXTRA_ACTIVE = ScenarioConditionId(
    "condition:character:1551:right-core-extra-trigger-active"
)
PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE = ScenarioConditionId(
    "condition:character:1551:ex-assist-order-proc-active"
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
    source_skill_id: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
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
                variant_key="damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=Element.ETHER,
        stage_index=stage,
    )


def _basic_stages(
    source_name: str,
    move_id: MoveId,
    stage_count: int,
    first_skill_id: int,
    display_prefix: str,
) -> tuple[NanokaMoveSpec, ...]:
    numerals = "一二三四"
    return tuple(
        _move(
            f"{display_prefix}-stage-{stage}",
            move_id=move_id,
            label=f"{source_name}（{numerals[stage - 1]}段）",
            source_name=source_name,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name=f"{numerals[stage - 1]}段伤害倍率",
            source_skill_id=str(first_skill_id + stage - 1),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
        for stage in range(1, stage_count + 1)
    )


PYROIS_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *_basic_stages("普通攻击：余晖", _BASIC_DUSK, 3, 1551001, "basic-afterglow"),
        *_basic_stages("普通攻击：天光", _BASIC_DAYLIGHT, 4, 1551004, "basic-daylight"),
        _move(
            "dash-sunrise",
            move_id=_DASH,
            label="冲刺攻击：旭日",
            source_name="冲刺攻击：旭日",
            group=SkillGroup.DODGE,
            tags=_DASH_TAGS,
            parameter_name="伤害倍率",
            source_skill_id="1551010",
        ),
        _move(
            "dodge-counter-morning-glow",
            move_id=_COUNTER,
            label="闪避反击：朝晖",
            source_name="闪避反击：朝晖",
            group=SkillGroup.DODGE,
            tags=_COUNTER_TAGS,
            parameter_name="伤害倍率",
            source_skill_id="1551011",
        ),
        _move(
            "special-residual-light",
            move_id=_SPECIAL,
            label="特殊技：残照",
            source_name="特殊技：残照",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL_TAGS,
            parameter_name="伤害倍率",
            source_skill_id="1551008",
        ),
        _move(
            "ex-sunflower",
            move_id=_EX,
            label="强化特殊技：日华",
            source_name="强化特殊技：日华",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_TAGS,
            parameter_name="伤害倍率",
            source_skill_id="1551009",
        ),
        _move(
            "chain-march-parade",
            move_id=_CHAIN,
            label="连携技：行军仪仗",
            source_name="连携技：行军仪仗",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN_TAGS,
            parameter_name="伤害倍率",
            source_skill_id="1551012",
        ),
        _move(
            "ultimate-military-execution",
            move_id=_ULTIMATE_UP,
            label="终结技：万军诛绝（上分支）",
            source_name="终结技：万军诛绝",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1551015",
        ),
        _move(
            "ultimate-victory-road",
            move_id=_ULTIMATE_DOWN,
            label="终结技：凯旋坦途（下分支）",
            source_name="终结技：凯旋坦途",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1551014",
        ),
        _move(
            "ultimate-unbound-sword",
            move_id=_ULTIMATE_LEFT,
            label="终结技：无拘剑势（左分支）",
            source_name="终结技：无拘剑势",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1551013",
        ),
        _move(
            "ultimate-eternal-prison",
            move_id=_ULTIMATE_RIGHT,
            label="终结技：永陷幽囚（右分支）",
            source_name="终结技：永陷幽囚",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1551016",
        ),
        _move(
            "quick-assist-dusk-guard",
            move_id=_QUICK_ASSIST,
            label="快速支援：黄昏禁卫",
            source_name="快速支援：黄昏禁卫",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1551017",
        ),
        _move(
            "assist-strike-see-daylight",
            move_id=_SUPPORT_STRIKE,
            label="支援突击：重睹天日",
            source_name="支援突击：重睹天日",
            group=SkillGroup.ASSIST,
            tags=_FOLLOW_UP,
            parameter_name="伤害倍率",
            source_skill_id="1551021",
        ),
    ),
    data_quality_notes=(
        "All 18 reviewed selectable move entries map to source Ether damage curves. The three Parry Assist parameters are Daze-only and intentionally do not create damage entries.",
        "The four Ultimate branches use their own curves: upper 1551015, lower 1551014, left 1551013, and right 1551016.",
        "Special: Battle Order 1551022 is a separate source-named Ether Special attack created by EX Special or Ultimate and uses Pyrois's current panel; it is not added to a parent multiplier.",
        "The Core's left/right branch extra ATK damage uses typed Ether Ultimate Direct children and retains its source multiplier and trigger.",
    ),
)


__all__ = [
    "PYROIS_ASSIST_ORDER_MOVE_ID",
    "PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE",
    "PYROIS_LEFT_CORE_EXTRA_ACTIVE",
    "PYROIS_REVIEWED_MAPPING",
    "PYROIS_RIGHT_CORE_EXTRA_ACTIVE",
    "PYROIS_SUNFLAME_ACTIVE",
    "PYROIS_SUNFLARE_ACTIVE",
]
