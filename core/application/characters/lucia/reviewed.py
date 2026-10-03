"""Reviewed move identities and source-curve mappings for Lucia (1451)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


LUCIA_ID = CharacterId("character:1451")

DREAM_ACTIVE = ScenarioConditionId("condition:lucia:dream-active")
DREAM_INACTIVE = ScenarioConditionId("condition:lucia:dream-inactive")
ANY_ETHER_CURTAIN_ACTIVE = ScenarioConditionId("condition:lucia:any-ether-curtain-active")
SPRING_CURTAIN_ACTIVE = ScenarioConditionId("condition:lucia:spring-curtain-active")
DREAM_SONG_ACTIVE = ScenarioConditionId("condition:lucia:dream-song-active")
BREAK_DARK_ACTIVE = ScenarioConditionId("condition:lucia:break-dark-active")
ADDITIONAL_ATTACK_READY = ScenarioConditionId("condition:lucia:additional-attack-ready")

LUCIA_ETHER_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:lucia:ether-current")

BASIC_MOVE_ID = MoveId("move:lucia:basic-star-rail-combo")
BASIC_WHIM_MOVE_ID = MoveId("move:lucia:basic-whim")
BASIC_CHORUS_MOVE_ID = MoveId("move:lucia:basic-chorus")
DASH_MOVE_ID = MoveId("move:lucia:dash-refraction")
DODGE_COUNTER_WHIM_MOVE_ID = MoveId("move:lucia:dodge-counter-whim")
DODGE_COUNTER_CHORUS_MOVE_ID = MoveId("move:lucia:dodge-counter-chorus")
SPECIAL_WHIM_MOVE_ID = MoveId("move:lucia:special-death-concerto-storm-whim")
SPECIAL_CHORUS_MOVE_ID = MoveId("move:lucia:special-death-concerto-storm-chorus")
EX_SPECIAL_CHORUS_MOVE_ID = MoveId("move:lucia:ex-death-concerto-dawn-chorus")
CHAIN_CHORUS_MOVE_ID = MoveId("move:lucia:chain-gleaming-theater-chorus")
ULTIMATE_CHORUS_MOVE_ID = MoveId("move:lucia:ultimate-charge-armor-chorus")
QUICK_ASSIST_WHIM_MOVE_ID = MoveId("move:lucia:quick-assist-fog-strike-whim")
QUICK_ASSIST_CHORUS_MOVE_ID = MoveId("move:lucia:quick-assist-fog-strike-chorus")
SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID = MoveId("move:lucia:support-follow-up-dream-chorus")
ULTIMATE_RUSH_HIT_MOVE_ID = ULTIMATE_CHORUS_MOVE_ID
EX_CHORUS_HP_COMPONENT_MOVE_ID = EX_SPECIAL_CHORUS_MOVE_ID
CORE_ADDITIONAL_ATTACK_EFFECT_ID = "effect:character:1451:core:additional-attack"
LUCIA_ADDITIONAL_ATTACK_CURVES = (
    ("普通攻击：星轨连击", "1451007"),
    ("特殊技：死神协奏曲·风暴", "1451010"),
    ("快速支援：迷雾重击", "1451015"),
)


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

LUCIA_CHORUS_MOVE_IDS = (
    BASIC_CHORUS_MOVE_ID,
    DODGE_COUNTER_CHORUS_MOVE_ID,
    SPECIAL_CHORUS_MOVE_ID,
    EX_SPECIAL_CHORUS_MOVE_ID,
    CHAIN_CHORUS_MOVE_ID,
    ULTIMATE_CHORUS_MOVE_ID,
    QUICK_ASSIST_CHORUS_MOVE_ID,
    SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID,
)


def _p(key: str, name: str, source_skill_id: str, *conditions):
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        condition_ids=tuple(conditions),
        source_skill_id=source_skill_id,
    )


def _move(
    entry_key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    skill_group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition: ScenarioConditionId | None = None,
):
    return NanokaMoveSpec(
        entry_key=entry_key,
        move_id=move_id,
        display_name=display_name,
        source_name=source_name,
        skill_group=skill_group,
        damage_tags=tags,
        parameters=(
            _p(
                f"{entry_key}-damage",
                parameter_name,
                source_skill_id,
                *(() if condition is None else (condition,)),
            ),
        ),
        multiplier_relation=relation,
        element=Element.ETHER,
        stage_index=stage,
        condition_ids=(() if condition is None else (condition,)),
    )


LUCIA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-star-rail-{stage}",
                BASIC_MOVE_ID,
                f"普通攻击：星轨连击（{stage}段）",
                "普通攻击：星轨连击",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{'一二三四'[stage - 1]}段伤害倍率",
                f"145100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-whim-fifth",
            BASIC_WHIM_MOVE_ID,
            "普通攻击：星轨连击（五段·随想）",
            "普通攻击：星轨连击",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "随想伤害倍率",
            "1451005",
            condition=DREAM_INACTIVE,
        ),
        _move(
            "basic-chorus-fifth",
            BASIC_CHORUS_MOVE_ID,
            "普通攻击：星轨连击（五段·合唱）",
            "普通攻击：星轨连击",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "合唱伤害倍率",
            "1451006",
            condition=DREAM_ACTIVE,
        ),
        _move(
            "dodge-dash-refraction",
            DASH_MOVE_ID,
            "冲刺攻击：折光",
            "冲刺攻击：折光",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1451012",
        ),
        _move(
            "dodge-counter-whim",
            DODGE_COUNTER_WHIM_MOVE_ID,
            "闪避反击：星尘回响（随想）",
            "闪避反击：星尘回响",
            SkillGroup.DODGE,
            _COUNTER,
            "随想伤害倍率",
            "1451013",
            condition=DREAM_INACTIVE,
        ),
        _move(
            "dodge-counter-chorus",
            DODGE_COUNTER_CHORUS_MOVE_ID,
            "闪避反击：星尘回响（合唱）",
            "闪避反击：星尘回响",
            SkillGroup.DODGE,
            _COUNTER,
            "合唱伤害倍率",
            "1451014",
            condition=DREAM_ACTIVE,
        ),
        _move(
            "special-whim-storm",
            SPECIAL_WHIM_MOVE_ID,
            "特殊技：死神协奏曲·风暴（随想）",
            "特殊技：死神协奏曲·风暴",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "随想伤害倍率",
            "1451008",
            condition=DREAM_INACTIVE,
        ),
        _move(
            "special-chorus-storm",
            SPECIAL_CHORUS_MOVE_ID,
            "特殊技：死神协奏曲·风暴（合唱）",
            "特殊技：死神协奏曲·风暴",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "合唱伤害倍率",
            "1451009",
            condition=DREAM_ACTIVE,
        ),
        _move(
            "ex-special-dawn-chorus",
            EX_SPECIAL_CHORUS_MOVE_ID,
            "强化特殊技：死神协奏曲·破晓（合唱）",
            "强化特殊技：死神协奏曲·破晓",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1451011",
        ),
        _move(
            "chain-gleaming-theater-chorus",
            CHAIN_CHORUS_MOVE_ID,
            "连携技：璀色剧场（合唱）",
            "连携技：璀色剧场",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1451016",
        ),
        _move(
            "ultimate-charge-armor-finisher",
            ULTIMATE_CHORUS_MOVE_ID,
            "终结技：进击，大铠甲！（终结技瞬发伤害）",
            "终结技：进击，大铠甲！",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "终结技伤害倍率",
            "1451017",
        ),
        _move(
            "quick-assist-whim",
            QUICK_ASSIST_WHIM_MOVE_ID,
            "快速支援：迷雾重击（随想）",
            "快速支援：迷雾重击",
            SkillGroup.ASSIST,
            _ASSIST,
            "随想伤害倍率",
            "1451018",
            condition=DREAM_INACTIVE,
        ),
        _move(
            "quick-assist-chorus",
            QUICK_ASSIST_CHORUS_MOVE_ID,
            "快速支援：迷雾重击（合唱）",
            "快速支援：迷雾重击",
            SkillGroup.ASSIST,
            _ASSIST,
            "合唱伤害倍率",
            "1451023",
            condition=DREAM_ACTIVE,
        ),
        _move(
            "assist-follow-up-chorus",
            SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID,
            "支援突击：绘梦和声（合唱）",
            "支援突击：绘梦和声",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            "1451022",
        ),
    )
)


__all__ = [
    "ADDITIONAL_ATTACK_READY",
    "ANY_ETHER_CURTAIN_ACTIVE",
    "BASIC_CHORUS_MOVE_ID",
    "BASIC_MOVE_ID",
    "BASIC_WHIM_MOVE_ID",
    "BREAK_DARK_ACTIVE",
    "CHAIN_CHORUS_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_CHORUS_MOVE_ID",
    "DODGE_COUNTER_WHIM_MOVE_ID",
    "DREAM_ACTIVE",
    "DREAM_INACTIVE",
    "DREAM_SONG_ACTIVE",
    "EX_CHORUS_HP_COMPONENT_MOVE_ID",
    "EX_SPECIAL_CHORUS_MOVE_ID",
    "LUCIA_CHORUS_MOVE_IDS",
    "LUCIA_ETHER_ANOMALY_RECORD_ID",
    "LUCIA_ADDITIONAL_ATTACK_CURVES",
    "LUCIA_ID",
    "LUCIA_REVIEWED_MAPPING",
    "QUICK_ASSIST_CHORUS_MOVE_ID",
    "QUICK_ASSIST_WHIM_MOVE_ID",
    "SPRING_CURTAIN_ACTIVE",
    "SPECIAL_CHORUS_MOVE_ID",
    "SPECIAL_WHIM_MOVE_ID",
    "SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID",
    "ULTIMATE_CHORUS_MOVE_ID",
    "ULTIMATE_RUSH_HIT_MOVE_ID",
    "CORE_ADDITIONAL_ATTACK_EFFECT_ID",
]
