"""Reviewed Nanoka 3.2 source mappings for Harumasa (character:1201)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


HARUMASA_ID = CharacterId("character:1201")
HARUMASA_JULEI_TAG_SCOPE_MECHANISM = "harumasa-julei-tag-scope-unresolved"
HARUMASA_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1201:electric-shock")
HARUMASA_TEN_CROSS_ACTIVE = ScenarioConditionId("condition:harumasa:target-ten-cross-marked")
HARUMASA_POTENTIAL_ATK_BUFF_ACTIVE = ScenarioConditionId("condition:harumasa:potential-attack-buff-active")
HARUMASA_EXTRA_ABILITY_ANOMALY_ACTIVE = ScenarioConditionId("condition:harumasa:target-attribute-anomaly-active")
HARUMASA_C6_ELECTRIC_RESISTANCE_IGNORE_ACTIVE = ScenarioConditionId("condition:harumasa:cinema6-electric-resistance-ignore-active")
HARUMASA_C6_ELECTROMAGNETIC_EXPLOSION_READY = ScenarioConditionId("condition:harumasa:cinema6-electromagnetic-explosion-ready")

HARUMASA_BASIC_MOVE_ID = MoveId("move:harumasa:basic-cloud-piercer")
HARUMASA_SHIFT_MOVE_ID = MoveId("move:harumasa:basic-cloud-piercer-shift")
HARUMASA_FEATHER_MOVE_ID = MoveId("move:harumasa:basic-fallen-feather")
HARUMASA_ARROW_MOVE_ID = MoveId("move:harumasa:basic-jia-yi-arrow")
HARUMASA_DASH_MOVE_ID = MoveId("move:harumasa:dash-flying-string")
HARUMASA_COUNTER_MOVE_ID = MoveId("move:harumasa:dodge-counter-hidden-edge")
HARUMASA_DASH_SLASH_MOVE_ID = MoveId("move:harumasa:dash-flying-string-slash")
HARUMASA_JULEI_MOVE_ID = MoveId("move:harumasa:julei")
HARUMASA_SPECIAL_MOVE_ID = MoveId("move:harumasa:special-heaven-net")
HARUMASA_EX_MOVE_ID = MoveId("move:harumasa:ex-ground-net")
HARUMASA_EX_PATROL_MOVE_ID = MoveId("move:harumasa:ex-ground-net-patrol")
HARUMASA_CHAIN_MOVE_ID = MoveId("move:harumasa:chain-hui-li")
HARUMASA_ULTIMATE_MOVE_ID = MoveId("move:harumasa:ultimate-remorse")
HARUMASA_ULTIMATE_SCATTER_MOVE_ID = MoveId("move:harumasa:ultimate-scatter")
HARUMASA_QUICK_ASSIST_MOVE_ID = MoveId("move:harumasa:quick-assist-string-pierce")
HARUMASA_ASSIST_STRIKE_MOVE_ID = MoveId("move:harumasa:assist-strike-structure-slash")

HARUMASA_ELECTRIC_DISORDER_REMAINING_SECONDS = "parameter:harumasa:electric-disorder-remaining-seconds"
HARUMASA_CURRENT_ELECTRIC_BLADE_STACKS = "parameter:harumasa:current-electric-blade-stacks"
HARUMASA_CURRENT_FENGMANG_STACKS = "parameter:harumasa:current-fengmang-stacks"

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
    group: SkillGroup | None,
    tags: frozenset[DamageTag],
    parameter: str,
    curve: str,
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
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


_BASE_MOVES = (
    *tuple(
        _move(
            f"basic-stage-{stage}",
            move_id=HARUMASA_BASIC_MOVE_ID,
            label=f"普通攻击：穿云（第{('一', '二', '三', '四', '五')[stage - 1]}段）",
            source="普通攻击：穿云",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
            curve=f"120100{stage}",
            element=Element.PHYSICAL if stage <= 3 else Element.ELECTRIC,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
        for stage in range(1, 6)
    ),
    _move("basic-shift", move_id=HARUMASA_SHIFT_MOVE_ID, label="普通攻击：穿云·移形", source="普通攻击：穿云·移形", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="伤害倍率", curve="1201006", element=Element.PHYSICAL),
    _move("basic-feather", move_id=HARUMASA_FEATHER_MOVE_ID, label="普通攻击：落羽", source="普通攻击：落羽", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="伤害倍率", curve="1201007", element=Element.ELECTRIC),
    _move("basic-arrow", move_id=HARUMASA_ARROW_MOVE_ID, label="普通攻击：甲乙矢", source="普通攻击：甲乙矢", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="伤害倍率", curve="1201008", element=Element.ELECTRIC),
    _move("dash-physical", move_id=HARUMASA_DASH_MOVE_ID, label="冲刺攻击：飞弦", source="冲刺攻击：飞弦", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1201011", element=Element.PHYSICAL),
    _move("dodge-counter-electric", move_id=HARUMASA_COUNTER_MOVE_ID, label="闪避反击：藏锋", source="闪避反击：藏锋", group=SkillGroup.DODGE, tags=_COUNTER, parameter="伤害倍率", curve="1201012", element=Element.ELECTRIC),
    _move("special-electric", move_id=HARUMASA_SPECIAL_MOVE_ID, label="特殊技：天罗", source="特殊技：天罗", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1201009", element=Element.ELECTRIC),
    _move("ex-electric", move_id=HARUMASA_EX_MOVE_ID, label="强化特殊技：地网", source="强化特殊技：地网", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1201010", element=Element.ELECTRIC),
    _move("chain-electric", move_id=HARUMASA_CHAIN_MOVE_ID, label="连携技：会·离", source="连携技：会·离", group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter="伤害倍率", curve="1201013", element=Element.ELECTRIC),
    _move("ultimate-electric", move_id=HARUMASA_ULTIMATE_MOVE_ID, label="终结技：残心", source="终结技：残心", group=SkillGroup.ULTIMATE, tags=_ULT, parameter="伤害倍率", curve="1201014", element=Element.ELECTRIC),
    _move("quick-assist-electric", move_id=HARUMASA_QUICK_ASSIST_MOVE_ID, label="快速支援：穿弦", source="快速支援：穿弦", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1201015", element=Element.ELECTRIC),
    _move("assist-strike-electric", move_id=HARUMASA_ASSIST_STRIKE_MOVE_ID, label="支援突击：构身·斩", source="支援突击：构身·斩", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1201019", element=Element.ELECTRIC),
    *tuple(
        _move(
            f"dash-slash-{stage}",
            move_id=HARUMASA_DASH_SLASH_MOVE_ID,
            label=f"冲刺攻击：飞弦·斩（第{('一', '二', '三')[stage - 1]}段）",
            source="冲刺攻击：飞弦·斩",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
            curve=f"120102{stage - 1}",
            element=Element.ELECTRIC,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
            condition_ids=(HARUMASA_TEN_CROSS_ACTIVE,),
        )
        for stage in (1, 2, 3)
    ),
    _move("potential1-julei", move_id=HARUMASA_JULEI_MOVE_ID, label="潜能1：逐雷（单次来源倍率）", source="逐雷", group=SkillGroup.DODGE, tags=frozenset(), parameter="额外伤害倍率", curve="1201025", element=Element.ELECTRIC),
    _move("potential1-ex-patrol", move_id=HARUMASA_EX_PATROL_MOVE_ID, label="潜能1：强化特殊技·地网·巡弋", source="强化特殊技：地网·巡弋", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1201023", element=Element.ELECTRIC),
)


HARUMASA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=_BASE_MOVES,
    data_quality_notes=(
        "The user confirmed Basic stages 1–3 as Physical and stages 4–5 as Electric, resolving the source's combined Physical/Electric description without inferring from attribute-infliction values.",
        "Potential 1 Julei is exposed as its single source coefficient, without assuming its attack tag or automatic trigger count.",
    ),
)


def reviewed_mapping(*, potential_level: int = 0) -> NanokaReviewedMapping:
    if not 0 <= potential_level <= 6:
        raise ValueError("Harumasa potential level must be between 0 and 6")
    return NanokaReviewedMapping(
        moves=tuple(
            item
            for item in HARUMASA_REVIEWED_MAPPING.moves
            if not item.entry_key.startswith("potential1-") or potential_level >= 1
        ),
        data_quality_notes=HARUMASA_REVIEWED_MAPPING.data_quality_notes,
    )


__all__ = [name for name in globals() if name.isupper()] + ["HARUMASA_REVIEWED_MAPPING", "reviewed_mapping"]
