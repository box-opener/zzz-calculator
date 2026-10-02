"""Reviewed Vivian (1331) move identities and Nanoka curve mappings."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


VIVIAN_ID = CharacterId("character:1331")
PROPHECY_ACTIVE = ScenarioConditionId("condition:vivian:prophecy-active")
MIND4_ATTACK_BUFF_ACTIVE = ScenarioConditionId("condition:vivian:mind4-attack-buff-active")
TARGET_HAS_ANOMALY = ScenarioConditionId("condition:vivian:target-has-anomaly")
HAS_PROTECTIVE_FEATHER = ScenarioConditionId("condition:vivian:protective-feather-available")
MUTATION_TRIGGERED = ScenarioConditionId("condition:vivian:mutation-triggered")
C6_MAX_FEATHER_MUTATION = ScenarioConditionId("condition:vivian:c6-max-feather-mutation")
C6_PARTIAL_FEATHER_MUTATION = ScenarioConditionId("condition:vivian:c6-partial-feather-mutation")
PROPHECY_TICK_COUNT = ScenarioParameterId("parameter:vivian:prophecy-tick-count")

BASIC_FLURRY_MOVE_ID = MoveId("move:vivian:basic-feather-flurry")
BASIC_DANCE_MOVE_ID = MoveId("move:vivian:basic-lady-dance")
BASIC_FALL_MOVE_ID = MoveId("move:vivian:basic-skirt-float-fall")
BASIC_BLOSSOMS_MOVE_ID = MoveId("move:vivian:basic-feathering-blossoms")
DASH_MOVE_ID = MoveId("move:vivian:dash-silver-thorn")
DODGE_COUNTER_MOVE_ID = MoveId("move:vivian:dodge-feather-blade-counter")
SPECIAL_MOVE_ID = MoveId("move:vivian:special-silver-aria")
EX_SPECIAL_MOVE_ID = MoveId("move:vivian:ex-special-violet-elegy")
CHAIN_MOVE_ID = MoveId("move:vivian:chain-star-harmony")
ULTIMATE_MOVE_ID = MoveId("move:vivian:ultimate-birdsong")
QUICK_ASSIST_MOVE_ID = MoveId("move:vivian:quick-assist-feather-guard")
SUPPORT_FOLLOWUP_MOVE_ID = MoveId("move:vivian:support-judgment-feather")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _p(key: str, parameter_name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=parameter_name,
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
    )


_STAGES = ("一", "二", "三", "四")
VIVIAN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-feather-flurry-{stage}",
                BASIC_FLURRY_MOVE_ID,
                f"普通攻击：翎羽拂击（{_STAGES[stage - 1]}段）",
                "普通攻击：翎羽拂击",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_STAGES[stage - 1]}段伤害倍率",
                f"133100{stage}",
                Element.ETHER,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move("basic-lady-dance", BASIC_DANCE_MOVE_ID, "普通攻击：淑女礼仪·舞步", "普通攻击：淑女礼仪·舞步", SkillGroup.BASIC_ATTACK, _BASIC, "伤害倍率", "1331005", Element.ETHER),
        _move("basic-skirt-float-fall", BASIC_FALL_MOVE_ID, "普通攻击：裙裾浮游·悬落", "普通攻击：裙裾浮游·悬落", SkillGroup.BASIC_ATTACK, _BASIC, "伤害倍率", "1331006", Element.ETHER),
        _move("basic-feathering-blossoms", BASIC_BLOSSOMS_MOVE_ID, "普通攻击：落羽生花", "普通攻击：落羽生花", SkillGroup.BASIC_ATTACK, _BASIC, "伤害倍率", "1331008", Element.ETHER),
        _move("dash-silver-thorn", DASH_MOVE_ID, "冲刺攻击：银刺舞曲", "冲刺攻击：银刺舞曲", SkillGroup.DODGE, _DASH, "伤害倍率", "1331011", Element.PHYSICAL),
        _move("dodge-feather-blade-counter", DODGE_COUNTER_MOVE_ID, "闪避反击：羽刃反振", "闪避反击：羽刃反振", SkillGroup.DODGE, _COUNTER, "伤害倍率", "1331012", Element.ETHER),
        _move("special-silver-aria", SPECIAL_MOVE_ID, "特殊技：银羽咏叹", "特殊技：银羽咏叹", SkillGroup.SPECIAL_ATTACK, _SPECIAL, "伤害倍率", "1331009", Element.ETHER),
        _move("ex-special-violet-elegy", EX_SPECIAL_MOVE_ID, "强化特殊技：堇花悼亡", "强化特殊技：堇花悼亡", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, "伤害倍率", "1331010", Element.ETHER),
        _move("chain-star-harmony", CHAIN_MOVE_ID, "连携技：星羽和声", "连携技：星羽和声", SkillGroup.CHAIN_ATTACK, _CHAIN, "伤害倍率", "1331013", Element.ETHER),
        _move("ultimate-birdsong", ULTIMATE_MOVE_ID, "终结技：飞鸟鸣颂", "终结技：飞鸟鸣颂", SkillGroup.ULTIMATE, _ULTIMATE, "伤害倍率", "1331014", Element.ETHER),
        _move("quick-assist-feather-guard", QUICK_ASSIST_MOVE_ID, "快速支援：凛羽之护", "快速支援：凛羽之护", SkillGroup.ASSIST, _ASSIST, "伤害倍率", "1331015", Element.ETHER),
        _move("support-judgment-feather", SUPPORT_FOLLOWUP_MOVE_ID, "支援突击：裁决羽刃", "支援突击：裁决羽刃", SkillGroup.ASSIST, _FOLLOW_UP, "伤害倍率", "1331019", Element.ETHER),
    )
)

MIXED_ELEMENT_MOVE_IDS = frozenset(
    {BASIC_FLURRY_MOVE_ID, DODGE_COUNTER_MOVE_ID, SPECIAL_MOVE_ID, QUICK_ASSIST_MOVE_ID}
)

__all__ = [
    "BASIC_BLOSSOMS_MOVE_ID", "BASIC_DANCE_MOVE_ID", "BASIC_FALL_MOVE_ID",
    "BASIC_FLURRY_MOVE_ID", "C6_MAX_FEATHER_MUTATION", "C6_PARTIAL_FEATHER_MUTATION",
    "DASH_MOVE_ID", "DODGE_COUNTER_MOVE_ID", "EX_SPECIAL_MOVE_ID", "HAS_PROTECTIVE_FEATHER",
    "MIXED_ELEMENT_MOVE_IDS", "MUTATION_TRIGGERED", "MIND4_ATTACK_BUFF_ACTIVE", "PROPHECY_ACTIVE", "PROPHECY_TICK_COUNT",
    "QUICK_ASSIST_MOVE_ID", "SPECIAL_MOVE_ID", "SUPPORT_FOLLOWUP_MOVE_ID", "TARGET_HAS_ANOMALY",
    "ULTIMATE_MOVE_ID", "VIVIAN_ID", "VIVIAN_REVIEWED_MAPPING",
]
