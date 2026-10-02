"""Reviewed Anby (1011) source identities and direct move mappings."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup, StateId

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ANBY_ID = CharacterId("character:1011")
AFTER_BASIC_THIRD_ACTIVE = ScenarioConditionId(
    "condition:anby:after-basic-third-active"
)
ANBY_ENEMY_STUNNED_STATE_ID = StateId("state:enemy:stunned")
CINEMA1_ENERGY_EFFICIENCY_ACTIVE = ScenarioConditionId(
    "condition:anby:cinema1-energy-efficiency-active"
)
ANBY_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:anby:electric-current")
ANBY_ELECTRIC_ANOMALY_MOVE_ID = MoveId("move:anby:electric-anomaly")
ANBY_ELECTRIC_DISORDER_MOVE_ID = MoveId("move:anby:electric-disorder")

BASIC_VOLT_MOVE_ID = MoveId("move:anby:basic-volt-assault")
BASIC_FALLING_THUNDER_MOVE_ID = MoveId("move:anby:basic-falling-thunder")
DASH_ARC_SLASH_MOVE_ID = MoveId("move:anby:dash-arc-slash")
DODGE_COUNTER_THUNDER_MOVE_ID = MoveId("move:anby:dodge-counter-thunderclap")
SPECIAL_ELECTRIC_SLASH_MOVE_ID = MoveId("move:anby:special-electric-slash")
EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID = MoveId("move:anby:ex-special-cobalt-lightning")
CHAIN_ELECTROMAGNETIC_ENGINE_MOVE_ID = MoveId("move:anby:chain-electromagnetic-engine")
ULTIMATE_OVERLOAD_ENGINE_MOVE_ID = MoveId("move:anby:ultimate-overload-engine")
ASSIST_DESCENDING_THUNDER_MOVE_ID = MoveId("move:anby:assist-descending-thunder")
ASSIST_SPINNING_LIGHTNING_MOVE_ID = MoveId("move:anby:assist-spinning-lightning")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_ASSIST_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _parameter(key: str, name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
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
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(_parameter(f"{key}-damage", parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


ANBY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-volt-assault-{stage}",
                BASIC_VOLT_MOVE_ID,
                f"普通攻击：伏特速攻（{stage}段）",
                "普通攻击：伏特速攻",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                f"101100{stage}",
                Element.PHYSICAL if stage < 4 else Element.ELECTRIC,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-falling-thunder",
            BASIC_FALLING_THUNDER_MOVE_ID,
            "普通攻击：落雷",
            "普通攻击：落雷",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1011005",
            Element.ELECTRIC,
        ),
        _move(
            "dash-arc-slash",
            DASH_ARC_SLASH_MOVE_ID,
            "冲刺攻击：电弧斩",
            "冲刺攻击：电弧斩",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1011008",
            Element.PHYSICAL,
        ),
        _move(
            "dodge-counter-thunderclap",
            DODGE_COUNTER_THUNDER_MOVE_ID,
            "闪避反击：迅雷",
            "闪避反击：迅雷",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1011009",
            Element.ELECTRIC,
        ),
        _move(
            "special-electric-slash",
            SPECIAL_ELECTRIC_SLASH_MOVE_ID,
            "特殊技：电光挥击",
            "特殊技：电光挥击",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1011006",
            Element.ELECTRIC,
        ),
        _move(
            "ex-special-cobalt-lightning",
            EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID,
            "强化特殊技：苍雷斩",
            "强化特殊技：苍雷斩",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1011007",
            Element.ELECTRIC,
        ),
        _move(
            "chain-electromagnetic-engine",
            CHAIN_ELECTROMAGNETIC_ENGINE_MOVE_ID,
            "连携技：电磁引擎",
            "连携技：电磁引擎",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1011010",
            Element.ELECTRIC,
        ),
        _move(
            "ultimate-overload-engine",
            ULTIMATE_OVERLOAD_ENGINE_MOVE_ID,
            "终结技：过载引擎",
            "终结技：过载引擎",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1011011",
            Element.ELECTRIC,
        ),
        _move(
            "assist-descending-thunder",
            ASSIST_DESCENDING_THUNDER_MOVE_ID,
            "快速支援：降雷",
            "快速支援：降雷",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1011012",
            Element.ELECTRIC,
        ),
        _move(
            "assist-spinning-lightning",
            ASSIST_SPINNING_LIGHTNING_MOVE_ID,
            "支援突击：回旋闪电",
            "支援突击：回旋闪电",
            SkillGroup.ASSIST,
            _ASSIST_FOLLOW_UP,
            "伤害倍率",
            "1011016",
            Element.ELECTRIC,
        ),
    ),
    data_quality_notes=(
        "Separate source `失衡倍率` curves are retained in the raw detail. The current "
        "damage request has no Daze result; the reviewed mapping selects only `伤害倍率` "
        "for Direct entries.",
    ),
)


__all__ = [
    "AFTER_BASIC_THIRD_ACTIVE",
    "ANBY_ELECTRIC_ANOMALY_MOVE_ID",
    "ANBY_ELECTRIC_ANOMALY_RECORD_ID",
    "ANBY_ELECTRIC_DISORDER_MOVE_ID",
    "ANBY_ID",
    "ANBY_REVIEWED_MAPPING",
    "ASSIST_DESCENDING_THUNDER_MOVE_ID",
    "ASSIST_SPINNING_LIGHTNING_MOVE_ID",
    "BASIC_FALLING_THUNDER_MOVE_ID",
    "BASIC_VOLT_MOVE_ID",
    "CINEMA1_ENERGY_EFFICIENCY_ACTIVE",
    "DASH_ARC_SLASH_MOVE_ID",
    "DODGE_COUNTER_THUNDER_MOVE_ID",
    "ANBY_ENEMY_STUNNED_STATE_ID",
    "EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID",
    "SPECIAL_ELECTRIC_SLASH_MOVE_ID",
    "ULTIMATE_OVERLOAD_ENGINE_MOVE_ID",
    "CHAIN_ELECTROMAGNETIC_ENGINE_MOVE_ID",
]
