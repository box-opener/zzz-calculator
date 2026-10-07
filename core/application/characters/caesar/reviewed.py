"""Reviewed Nanoka 3.2 move identities for Caesar (character:1071)."""

from __future__ import annotations

from core.types import (
    AnomalyRecordId,
    CharacterId,
    DamageTag,
    Element,
    MoveId,
    SkillGroup,
)

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


CAESAR_ID = CharacterId("character:1071")
CAESAR_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:character:1071:physical-assault"
)

CAESAR_SHIELD_ACTIVE = ScenarioConditionId("condition:caesar:glory-shield-active")
CAESAR_SHIELD_ATTACK_BUFF_ACTIVE = ScenarioConditionId(
    "condition:caesar:shield-holder-attack-buff-active"
)
CAESAR_CINEMA1_RESISTANCE_DEBUFF_ACTIVE = ScenarioConditionId(
    "condition:caesar:cinema1-target-resistance-debuff-active"
)
CAESAR_EXTRA_ABILITY_DEBUFF_ACTIVE = ScenarioConditionId(
    "condition:caesar:extra-ability-target-damage-debuff-active"
)
CAESAR_IMPACT_BUFF_ACTIVE = ScenarioConditionId(
    "condition:caesar:impact-buff-active"
)
CAESAR_CINEMA6_SELF_CRIT_BUFF_ACTIVE = ScenarioConditionId(
    "condition:caesar:cinema6-self-crit-buff-active"
)
PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:caesar:physical-disorder-remaining-seconds"
)

BASIC_SLASH_MOVE_ID = MoveId("move:caesar:basic-aegis-slice")
BASIC_SHIELD_THROW_MOVE_ID = MoveId("move:caesar:basic-this-road-is-closed")
DASH_ATTACK_MOVE_ID = MoveId("move:caesar:dash-drift")
DODGE_COUNTER_MOVE_ID = MoveId("move:caesar:dodge-counter-tooth-for-tooth")
SPECIAL_SHIELD_CRASH_MOVE_ID = MoveId("move:caesar:special-shield-crash")
SPECIAL_THRUST_MOVE_ID = MoveId("move:caesar:special-clamor-thrust")
EX_COUNTERATTACK_MOVE_ID = MoveId("move:caesar:ex-parry-counterattack")
EX_SHIELD_BASH_MOVE_ID = MoveId("move:caesar:ex-super-strong-shield-bash")
EX_DEFENSIVE_COUNTER_MOVE_ID = MoveId(
    "move:caesar:ex-super-strong-shield-bash-defensive-counter"
)
CHAIN_ATTACK_MOVE_ID = MoveId("move:caesar:chain-rage-road-shock")
ULTIMATE_MOVE_ID = MoveId("move:caesar:ultimate-tyrant-blow")
QUICK_ASSIST_MOVE_ID = MoveId("move:caesar:quick-assist-lane-change")
ASSIST_STRIKE_MOVE_ID = MoveId("move:caesar:assist-strike-support-edge")
PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:caesar:physical-assault")
PHYSICAL_DISORDER_MOVE_ID = MoveId("move:caesar:physical-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _stage(stage: int, source_skill_id: str) -> NanokaMoveSpec:
    names = ("一", "二", "三", "四", "五", "六")
    name = names[stage - 1]
    return NanokaMoveSpec(
        entry_key=f"basic-slash-{stage}",
        move_id=BASIC_SLASH_MOVE_ID,
        display_name=f"普通攻击：横行斩打（{name}段）",
        source_name="普通攻击：横行斩打",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"basic-slash-{stage}-damage",
                parameter_name=f"{name}段伤害倍率",
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=MultiplierRelation.SEQUENTIAL_STAGE,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


def _move(
    *,
    key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=display_name,
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
        element=Element.PHYSICAL,
    )


CAESAR_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(_stage(stage, f"107100{stage}") for stage in range(1, 7)),
        _move(
            key="basic-slash-stage3-derived",
            move_id=BASIC_SLASH_MOVE_ID,
            display_name="普通攻击：横行斩打（三段派生）",
            source_name="普通攻击：横行斩打",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="三段（派生）伤害倍率",
            source_skill_id="1071008",
        ),
        _move(
            key="basic-shield-throw",
            move_id=BASIC_SHIELD_THROW_MOVE_ID,
            display_name="普通攻击：此路不通！",
            source_name="普通攻击：此路不通！",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            source_skill_id="1071007",
        ),
        _move(
            key="dash-attack",
            move_id=DASH_ATTACK_MOVE_ID,
            display_name="冲刺攻击：猪突猛进",
            source_name="冲刺攻击：猪突猛进",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1071016",
        ),
        _move(
            key="dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            display_name="闪避反击：以牙还牙",
            source_name="闪避反击：以牙还牙",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1071017",
        ),
        _move(
            key="special-shield-crash",
            move_id=SPECIAL_SHIELD_CRASH_MOVE_ID,
            display_name="特殊技：震荡盾击",
            source_name="特殊技：震荡盾击",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1071009",
        ),
        _move(
            key="special-clamor-thrust",
            move_id=SPECIAL_THRUST_MOVE_ID,
            display_name="特殊技：喧嚣直刺",
            source_name="特殊技：喧嚣直刺",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1071010",
        ),
        _move(
            key="ex-parry-counterattack",
            move_id=EX_COUNTERATTACK_MOVE_ID,
            display_name="强化特殊技：招架反击",
            source_name="强化特殊技：招架反击",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1071011",
        ),
        _move(
            key="ex-precision-guard-counter",
            move_id=EX_COUNTERATTACK_MOVE_ID,
            display_name="强化特殊技：招架反击（精准格挡反击）",
            source_name="强化特殊技：招架反击",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="[精准格挡]反击伤害倍率",
            source_skill_id="1071012",
        ),
        _move(
            key="ex-super-strong-shield-bash",
            move_id=EX_SHIELD_BASH_MOVE_ID,
            display_name="强化特殊技：超强力盾击",
            source_name="强化特殊技：超强力盾击",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1071013",
        ),
        _move(
            key="ex-defensive-counter-shield-bash",
            move_id=EX_DEFENSIVE_COUNTER_MOVE_ID,
            display_name="强化特殊技：超强力盾击（防御反击）",
            source_name="强化特殊技：超强力盾击",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1071013",
        ),
        _move(
            key="chain-road-rage",
            move_id=CHAIN_ATTACK_MOVE_ID,
            display_name="连携技：路怒震打",
            source_name="连携技：路怒震打",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1071018",
        ),
        _move(
            key="ultimate-tyrant-blow",
            move_id=ULTIMATE_MOVE_ID,
            display_name="终结技：暴君猛击",
            source_name="终结技：暴君猛击",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1071019",
        ),
        _move(
            key="quick-assist-lane-change",
            move_id=QUICK_ASSIST_MOVE_ID,
            display_name="快速支援：变道支援",
            source_name="快速支援：变道支援",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1071020",
        ),
        _move(
            key="assist-strike-support-edge",
            move_id=ASSIST_STRIKE_MOVE_ID,
            display_name="支援突击：支援之锋",
            source_name="支援突击：支援之锋",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1071024",
        ),
    ),
    data_quality_notes=(
        "The third Basic stage and its raw `三段（派生）伤害倍率` are shown as separate source-linked entries. The source does not state whether this curve is an additional hit or an alternative, so no combined stage total is inferred.",
        "Core Shield value, damage absorption, and timed shield state, Parry Support Daze, Energy/Support Point resource changes, and incoming damage are retained as source text because those results are outside the current contract. Current shield-holder attack buff and current enemy debuffs are modeled as explicit states.",
        "Raw damage values use Nanoka parameter IDs, while MoveIds come from the separate skill_list action records. EX entries only have the EX tag; Special and EX are not combined as tags.",
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_SHIELD_THROW_MOVE_ID",
    "BASIC_SLASH_MOVE_ID",
    "CAESAR_ID",
    "CAESAR_PHYSICAL_ANOMALY_RECORD_ID",
    "CAESAR_REVIEWED_MAPPING",
    "CAESAR_IMPACT_BUFF_ACTIVE",
    "CAESAR_CINEMA6_SELF_CRIT_BUFF_ACTIVE",
    "CAESAR_SHIELD_ATTACK_BUFF_ACTIVE",
    "CAESAR_SHIELD_ACTIVE",
    "CAESAR_EXTRA_ABILITY_DEBUFF_ACTIVE",
    "CAESAR_CINEMA1_RESISTANCE_DEBUFF_ACTIVE",
    "CHAIN_ATTACK_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_COUNTERATTACK_MOVE_ID",
    "EX_DEFENSIVE_COUNTER_MOVE_ID",
    "EX_SHIELD_BASH_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_SHIELD_CRASH_MOVE_ID",
    "SPECIAL_THRUST_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "PHYSICAL_ANOMALY_MOVE_ID",
    "PHYSICAL_DISORDER_MOVE_ID",
    "PHYSICAL_DISORDER_REMAINING_SECONDS",
]
