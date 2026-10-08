"""Reviewed Nanoka 3.2 move identities for Ellen (character:1191)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ELLEN_ID = CharacterId("character:1191")
ELLEN_ICE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1191:ice-freeze")

ELLEN_ICE_MODE_ACTIVE = ScenarioConditionId("condition:ellen:ice-mode-active")
ELLEN_ICE_BLADE_WAVE_READY = ScenarioConditionId("condition:ellen:ice-blade-wave-ready")
ELLEN_C6_PENETRATION_ACTIVE = ScenarioConditionId("condition:ellen:cinema6-penetration-active")

ELLEN_DASH_QUICK_MOVE_ID = MoveId("move:ellen:dash-ice-fast-shear")
ELLEN_DASH_CHARGED_MOVE_ID = MoveId("move:ellen:dash-ice-charged-shear")
ELLEN_FROST_EDGE_MOVE_ID = MoveId("move:ellen:potential1-frost-edge")
ELLEN_ICE_ANOMALY_MOVE_ID = MoveId("move:ellen:ice-shatter")
ELLEN_ICE_DISORDER_MOVE_ID = MoveId("move:ellen:ice-disorder")

ELLEN_ICE_DISORDER_REMAINING_SECONDS = "parameter:ellen:ice-disorder-remaining-seconds"
ELLEN_CHILL_CHARGES_FOR_EX = "parameter:ellen:current-chill-charges-for-ex"
ELLEN_EXTRA_ABILITY_ICE_STACKS = "parameter:ellen:extra-ability-ice-stacks"
ELLEN_FROST_EDGE_TARGET_SIZE = "parameter:ellen:frost-edge-target-size"
ELLEN_C6_FEAST_STACKS = "parameter:ellen:cinema6-feast-stacks"

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
    curve: str | None,
    components: tuple[tuple[str, float], ...] = (),
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
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
                source_skill_components=components,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


ELLEN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-physical-{stage}",
                move_id=MoveId("move:ellen:basic-physical"),
                label=f"普通攻击：利齿修剪法（第{('一', '二', '三')[stage - 1]}段）",
                source="普通攻击：利齿修剪法",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                curve=f"119100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        *tuple(
            _move(
                f"basic-ice-{stage}",
                move_id=MoveId("move:ellen:basic-ice"),
                label=f"普通攻击：急冻修剪法（第{('一', '二', '三')[stage - 1]}段）",
                source="普通攻击：急冻修剪法",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                curve=f"119100{stage + 3}",
                element=Element.ICE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
                condition_ids=(ELLEN_ICE_MODE_ACTIVE,),
            )
            for stage in range(1, 4)
        ),
        _move("dash-physical", move_id=MoveId("move:ellen:dash-physical"), label="冲刺攻击：骇浪", source="冲刺攻击：骇浪", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1191013", element=Element.PHYSICAL),
        _move("dash-ice", move_id=MoveId("move:ellen:dash-ice-surge"), label="冲刺攻击：寒潮（急冻）", source="冲刺攻击：寒潮", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1191014", element=Element.ICE, condition_ids=(ELLEN_ICE_MODE_ACTIVE,)),
        _move("dash-ice-spin", move_id=MoveId("move:ellen:dash-ice-spin"), label="冲刺攻击：冰渊潜袭（回旋斩击）", source="冲刺攻击：冰渊潜袭", group=SkillGroup.DODGE, tags=_DASH, parameter="回旋斩击伤害倍率", curve="1191007", element=Element.ICE),
        _move("dash-ice-quick-shear", move_id=ELLEN_DASH_QUICK_MOVE_ID, label="冲刺攻击：冰渊潜袭（快速剪击）", source="冲刺攻击：冰渊潜袭", group=SkillGroup.DODGE, tags=_DASH, parameter="快速剪击伤害倍率", curve="1191008", element=Element.ICE),
        _move("dash-ice-charged-shear", move_id=ELLEN_DASH_CHARGED_MOVE_ID, label="冲刺攻击：冰渊潜袭（蓄力剪击）", source="冲刺攻击：冰渊潜袭", group=SkillGroup.DODGE, tags=_DASH, parameter="蓄力剪击伤害倍率", curve="1191009", element=Element.ICE),
        _move("dodge-counter", move_id=MoveId("move:ellen:dodge-counter-reef"), label="闪避反击：暗礁", source="闪避反击：暗礁", group=SkillGroup.DODGE, tags=_COUNTER, parameter="伤害倍率", curve="1191015", element=Element.ICE),
        _move("special-tail-swipe", move_id=MoveId("move:ellen:special-tail-swipe"), label="特殊技：摆尾", source="特殊技：摆尾", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1191010", element=Element.ICE),
        _move("ex-sweep", move_id=MoveId("move:ellen:ex-sweep"), label="强化特殊技：横扫", source="强化特殊技：横扫", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1191011", element=Element.ICE),
        _move("ex-whirlwind", move_id=MoveId("move:ellen:ex-sharknado"), label="强化特殊技：鲨卷风", source="强化特殊技：鲨卷风", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1191012", element=Element.ICE),
        _move("chain-avalanche", move_id=MoveId("move:ellen:chain-avalanche"), label="连携技：雪崩", source="连携技：雪崩", group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter="伤害倍率", curve="1191016", element=Element.ICE),
        _move("ultimate-endless-winter", move_id=MoveId("move:ellen:ultimate-endless-winter"), label="终结技：永冬狂宴", source="终结技：永冬狂宴", group=SkillGroup.ULTIMATE, tags=_ULT, parameter="伤害倍率", curve="1191017", element=Element.ICE),
        _move("quick-assist-escort-shark", move_id=MoveId("move:ellen:quick-assist-escort-shark"), label="快速支援：护卫鲛", source="快速支援：护卫鲛", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1191018", element=Element.ICE),
        _move("assist-strike-cruising-shark", move_id=MoveId("move:ellen:assist-strike-cruising-shark"), label="支援突击：巡洋鲨", source="支援突击：巡洋鲨", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1191022", element=Element.ICE),
        *tuple(
            _move(
                f"potential1-ice-blade-wave-{stage}",
                move_id=MoveId("move:ellen:potential1-ice-blade-wave"),
                label=f"潜能1：普通攻击·冰刃浪（第{('一', '二')[stage - 1]}段）",
                source="普通攻击：冰刃浪",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二')[stage - 1]}段伤害倍率",
                curve=f"11910{28 + stage}",
                element=Element.ICE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
                condition_ids=(ELLEN_ICE_BLADE_WAVE_READY,),
            )
            for stage in range(1, 3)
        ),
        *tuple(
            _move(
                f"potential1-frost-edge-{size}",
                move_id=ELLEN_FROST_EDGE_MOVE_ID,
                label=f"潜能1：普通攻击·霜锋（{size_label}）",
                source="普通攻击：霜锋",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"对{size_label}敌人伤害倍率",
                curve=None,
                components=(
                    (("1191027", 3.0),)
                    if size == "small"
                    else (("1191027", 3.0), ("1191028", 3.0))
                    if size == "medium"
                    else (("1191027", 3.0), ("1191028", 6.0))
                ),
                element=Element.ICE,
            )
            for size, size_label in (
                ("small", "小体型"),
                ("medium", "中体型"),
                ("large", "大体型"),
            )
        ),
    ),
    data_quality_notes=(
        "The three Potential 1 Frost Edge entries use the source's explicit small/medium/large enemy-size formulas; target-size selection for automatic P1 follow-ups is a current input, not inferred from history.",
        "Static Ice Anomaly and Disorder entries use the shared 100%-buildup, NoCrit source model; no resource or time history is replayed.",
    ),
)


def reviewed_mapping(*, potential_level: int = 0) -> NanokaReviewedMapping:
    if not 0 <= potential_level <= 6:
        raise ValueError("Ellen potential_level must be between 0 and 6")
    return NanokaReviewedMapping(
        moves=tuple(
            item
            for item in ELLEN_REVIEWED_MAPPING.moves
            if not item.entry_key.startswith("potential1-") or potential_level >= 1
        ),
        data_quality_notes=ELLEN_REVIEWED_MAPPING.data_quality_notes,
    )


__all__ = [name for name in globals() if name.isupper()] + ["ELLEN_REVIEWED_MAPPING", "reviewed_mapping"]
