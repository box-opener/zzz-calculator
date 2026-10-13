"""Reviewed Soldier 0 - Anby (1381) Nanoka skill identities and curves."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, EventTemplateId, MoveId, SkillGroup, StateId

from ...ids import RuleItemId, ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


SOLDIER0_ANBY_ID = CharacterId("character:1381")

SOLDIER0_ANBY_CORE_RULE_ID = RuleItemId("rule:character:1381:core:marked-target")
SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID = RuleItemId("rule:character:1381:extra-ability:polarization")
SOLDIER0_ANBY_CINEMA1_RULE_ID = RuleItemId("rule:character:1381:cinema1:ex-white-thunder")
SOLDIER0_ANBY_CINEMA2_RULE_ID = RuleItemId("rule:character:1381:cinema2:crit-rate")
SOLDIER0_ANBY_CINEMA3_RULE_ID = RuleItemId("rule:character:1381:cinema3:skill-levels")
SOLDIER0_ANBY_CINEMA4_RULE_ID = RuleItemId("rule:character:1381:cinema4:electric-resistance-ignore")
SOLDIER0_ANBY_CINEMA5_RULE_ID = RuleItemId("rule:character:1381:cinema5:skill-levels")
SOLDIER0_ANBY_CINEMA6_RULE_ID = RuleItemId("rule:character:1381:cinema6:electromagnetic-vortex")
SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID = RuleItemId("rule:character:1381:potential:critical-cangguang")
SOLDIER0_ANBY_CANGGUANG_THUNDERCLAP_RULE_ID = RuleItemId("rule:character:1381:skill:cangguang-thunderclap")

SOLDIER0_ANBY_SILVER_STAR_ACTIVE = ScenarioConditionId("condition:soldier0-anby:silver-star-active")
SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE = ScenarioConditionId("condition:soldier0-anby:white-thunder-active")
SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED = ScenarioConditionId("condition:soldier0-anby:cinema6-vortex-triggered")
SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER = ScenarioConditionId("condition:soldier0-anby:cangguang-third-white-thunder")
SOLDIER0_ANBY_SILVER_STAR_STATE = StateId("state:enemy:soldier0-anby:silver-star")
SOLDIER0_ANBY_WHITE_THUNDER_STATE = StateId("state:enemy:soldier0-anby:white-thunder")

SOLDIER0_ANBY_EX_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:ex-special-lightsplitter:main")
SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:cinema1:white-thunder")
SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:cinema1:thunderclap")
SOLDIER0_ANBY_CRITICAL_CANGGUANG_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:potential:critical-cangguang")
SOLDIER0_ANBY_CINEMA6_VORTEX_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:cinema6:electromagnetic-vortex")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_FOLLOW_UP = frozenset({DamageTag.FOLLOW_UP_ATTACK})
_SPECIAL_FOLLOW_UP = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})

BASIC_MOVE_ID = MoveId("move:soldier0-anby:basic-electric-pierce")
BASIC_FINISHER_MOVE_ID = MoveId("move:soldier0-anby:basic-electric-pierce-finisher")
DASH_MOVE_ID = MoveId("move:soldier0-anby:dash-current")
DODGE_COUNTER_MOVE_ID = MoveId("move:soldier0-anby:dodge-counter-ground-flash")
SPECIAL_MOVE_ID = MoveId("move:soldier0-anby:special-star-thunder")
CANGGUANG_MOVE_ID = MoveId("move:soldier0-anby:special-cangguang")
WHITE_THUNDER_MOVE_ID = MoveId("move:soldier0-anby:white-thunder")
THUNDERCLAP_MOVE_ID = MoveId("move:soldier0-anby:special-thunderclap")
CRITICAL_CANGGUANG_MOVE_ID = MoveId("move:soldier0-anby:special-cangguang-critical")
EX_SPECIAL_MOVE_ID = MoveId("move:soldier0-anby:ex-special-lightsplitter")
CHAIN_MOVE_ID = MoveId("move:soldier0-anby:chain-thunder-leap")
ULTIMATE_MOVE_ID = MoveId("move:soldier0-anby:ultimate-sky-sunder")
QUICK_ASSIST_MOVE_ID = MoveId("move:soldier0-anby:assist-cloud-flash")
ASSIST_STRIKE_MOVE_ID = MoveId("move:soldier0-anby:assist-director")


def _move(
    key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    *,
    element: Element = Element.ELECTRIC,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
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
        element=element,
        stage_index=stage,
    )


SOLDIER0_ANBY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-stage-1", BASIC_MOVE_ID, "普通攻击：电击穿（一段）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "一段伤害倍率", "1381001",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=1,
        ),
        _move(
            "basic-stage-2", BASIC_MOVE_ID, "普通攻击：电击穿（二段）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "二段伤害倍率", "1381002",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=2,
        ),
        _move(
            "basic-stage-3", BASIC_MOVE_ID, "普通攻击：电击穿（三段）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "三段伤害倍率", "1381003",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=3,
        ),
        _move(
            "basic-stage-3-finisher", BASIC_FINISHER_MOVE_ID, "普通攻击：电击穿（三段终结）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "三段终结伤害倍率", "1381004",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=3,
        ),
        _move(
            "basic-stage-4", BASIC_MOVE_ID, "普通攻击：电击穿（四段）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "四段伤害倍率", "1381005",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=4,
        ),
        _move(
            "basic-stage-5", BASIC_MOVE_ID, "普通攻击：电击穿（五段）", "普通攻击：电击穿",
            SkillGroup.BASIC_ATTACK, _BASIC, "五段伤害倍率", "1381006",
            relation=MultiplierRelation.SEQUENTIAL_STAGE, stage=5,
        ),
        _move(
            "dash-current", DASH_MOVE_ID, "冲刺攻击：奔流", "冲刺攻击：奔流",
            SkillGroup.DODGE, _DASH, "伤害倍率", "1381012",
        ),
        _move(
            "dodge-counter", DODGE_COUNTER_MOVE_ID, "闪避反击：地闪回击", "闪避反击：地闪回击",
            SkillGroup.DODGE, _COUNTER, "伤害倍率", "1381013",
        ),
        _move(
            "special-star-thunder", SPECIAL_MOVE_ID, "特殊技：星雷", "特殊技：星雷",
            SkillGroup.SPECIAL_ATTACK, _SPECIAL, "伤害倍率", "1381010",
        ),
        _move(
            "special-cangguang-main", CANGGUANG_MOVE_ID, "特殊技：苍光", "特殊技：苍光",
            SkillGroup.SPECIAL_ATTACK, _SPECIAL, "伤害倍率", "1381009",
        ),
        _move(
            "white-thunder", WHITE_THUNDER_MOVE_ID, "白雷（追加伤害单包）", "特殊技：苍光",
            SkillGroup.SPECIAL_ATTACK, _FOLLOW_UP, "[白雷]伤害倍率", "1381007",
        ),
        _move(
            "special-thunderclap", THUNDERCLAP_MOVE_ID, "特殊技：雷殛", "特殊技：雷殛",
            SkillGroup.SPECIAL_ATTACK, _SPECIAL_FOLLOW_UP, "[雷殛]伤害倍率", "1381008",
        ),
        _move(
            "special-cangguang-critical", CRITICAL_CANGGUANG_MOVE_ID, "特殊技：苍光·临界", "特殊技：苍光·临界",
            SkillGroup.SPECIAL_ATTACK, _SPECIAL_FOLLOW_UP, "伤害倍率", "1381023",
        ),
        _move(
            "ex-special-lightsplitter", EX_SPECIAL_MOVE_ID, "强化特殊技：极雷断空", "强化特殊技：极雷断空",
            SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, "伤害倍率", "1381011",
        ),
        _move(
            "chain-thunder-leap", CHAIN_MOVE_ID, "连携技：疾跃落雷", "连携技：疾跃落雷",
            SkillGroup.CHAIN_ATTACK, _CHAIN, "伤害倍率", "1381014",
        ),
        _move(
            "ultimate-sky-sunder", ULTIMATE_MOVE_ID, "终结技：斩空掠电", "终结技：斩空掠电",
            SkillGroup.ULTIMATE, _ULTIMATE, "伤害倍率", "1381015",
        ),
        _move(
            "quick-assist-cloud-flash", QUICK_ASSIST_MOVE_ID, "快速支援：云闪", "快速支援：云闪",
            SkillGroup.ASSIST, _ASSIST, "伤害倍率", "1381016",
        ),
        _move(
            "assist-director", ASSIST_STRIKE_MOVE_ID, "支援突击：直击先导", "支援突击：直击先导",
            SkillGroup.ASSIST, _ASSIST, "伤害倍率", "1381020",
        ),
    ),
    data_quality_notes=(
        "Potential-filtered skill parameters are resolved before Nanoka raw loading: Basic III uses curve 1381003 at Potential 0 and 1381022 at Potential 1-6; the separately named finisher remains curve 1381004.",
        "White Thunder's separately selectable one-packet query uses the [白雷] damage parameter on the Cangguang source record, with curve 1381007, and a neutral SkillGroup/MoveId plus Follow-up-only identity. EX Special uses EX_SPECIAL_ATTACK only; 雷殛 and 苍光·临界 have only source-explicit Special Attack plus Follow-up tags.",
        "No Daze, energy, or timeline values are mapped as Direct damage.",
    ),
)


__all__ = [
    "SOLDIER0_ANBY_CORE_RULE_ID",
    "SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID",
    "SOLDIER0_ANBY_CINEMA1_RULE_ID",
    "SOLDIER0_ANBY_CINEMA2_RULE_ID",
    "SOLDIER0_ANBY_CINEMA3_RULE_ID",
    "SOLDIER0_ANBY_CINEMA4_RULE_ID",
    "SOLDIER0_ANBY_CINEMA5_RULE_ID",
    "SOLDIER0_ANBY_CINEMA6_RULE_ID",
    "SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID",
    "SOLDIER0_ANBY_CANGGUANG_THUNDERCLAP_RULE_ID",
    "SOLDIER0_ANBY_SILVER_STAR_ACTIVE",
    "SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE",
    "SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED",
    "SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER",
    "SOLDIER0_ANBY_SILVER_STAR_STATE",
    "SOLDIER0_ANBY_WHITE_THUNDER_STATE",
    "SOLDIER0_ANBY_EX_TEMPLATE_ID",
    "SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID",
    "SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID",
    "SOLDIER0_ANBY_CRITICAL_CANGGUANG_TEMPLATE_ID",
    "SOLDIER0_ANBY_CINEMA6_VORTEX_TEMPLATE_ID",
    "BASIC_FINISHER_MOVE_ID",
    "BASIC_MOVE_ID",
    "CANGGUANG_MOVE_ID",
    "CHAIN_MOVE_ID",
    "CRITICAL_CANGGUANG_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SOLDIER0_ANBY_ID",
    "SOLDIER0_ANBY_REVIEWED_MAPPING",
    "SPECIAL_MOVE_ID",
    "THUNDERCLAP_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "WHITE_THUNDER_MOVE_ID",
]
