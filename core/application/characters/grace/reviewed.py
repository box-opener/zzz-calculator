"""Reviewed Nanoka 3.2 move identities for Grace (character:1181)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


GRACE_ID = CharacterId("character:1181")
GRACE_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1181:electric-shock")
GRACE_ELECTRIC_ANOMALY_MOVE_ID = MoveId("move:grace:electric-shock")
GRACE_ELECTRIC_DISORDER_MOVE_ID = MoveId("move:grace:electric-disorder")

ELECTRIC_ENERGY_EMPOWERED = ScenarioConditionId("condition:grace:electric-energy-empowered")
TARGET_ELECTRICALLY_BREACHED = ScenarioConditionId("condition:grace:target-electrically-breached")
PULSE_GRENADE_READY = ScenarioConditionId("condition:grace:pulse-grenade-ready")
PULSE_STATE_ACTIVE = ScenarioConditionId("condition:grace:pulse-state-active")
POTENTIAL1_VORTEX_ACTIVE = ScenarioConditionId("condition:grace:potential1-vortex-active")
EXTRA_GRENADE_C6_ACTIVE = ScenarioConditionId("condition:grace:cinema6-energy-consumed")
ELECTRIC_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:grace:electric-disorder-remaining-seconds"
)

BASIC_MOVE_ID = MoveId("move:grace:basic-high-pressure-nail")
DASH_ATTACK_MOVE_ID = MoveId("move:grace:dash-inspection")
DODGE_COUNTER_MOVE_ID = MoveId("move:grace:dodge-counter-violation")
SPECIAL_MOVE_ID = MoveId("move:grace:special-engineering-clearance")
EX_SPECIAL_MOVE_ID = MoveId("move:grace:ex-special-overstandard-clearance")
SPECIAL_CYCLE_MOVE_ID = MoveId("move:grace:special-engineering-clearance-cycle")
VORTEX_GRENADE_MOVE_ID = MoveId("move:grace:vortex-cluster-grenade")
PULSE_GRENADE_MOVE_ID = MoveId("move:grace:pulse-grenade")
CHAIN_MOVE_ID = MoveId("move:grace:chain-cooperative-construction")
ULTIMATE_MOVE_ID = MoveId("move:grace:ultimate-demolition")
QUICK_ASSIST_MOVE_ID = MoveId("move:grace:quick-assist-incident-response")
ASSIST_STRIKE_MOVE_ID = MoveId("move:grace:assist-strike-electric-needle")

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
    curve: str | None = None,
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


GRACE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：高压射钉（第{('一', '二', '三', '四')[stage - 1]}段）",
                source="普通攻击：高压射钉",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                curve=f"118100{stage}",
                element=Element.PHYSICAL if stage <= 3 else Element.ELECTRIC,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move("dash-attack", move_id=DASH_ATTACK_MOVE_ID, label="冲刺攻击：突击检查", source="冲刺攻击：突击检查", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1181007", element=Element.PHYSICAL),
        _move("basic-step-shot", move_id=BASIC_MOVE_ID, label="普通攻击：高压射钉（垫步射击）", source="普通攻击：高压射钉", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="垫步射击伤害倍率", curve="1181015", element=Element.PHYSICAL),
        _move("dodge-counter", move_id=DODGE_COUNTER_MOVE_ID, label="闪避反击：违章处罚", source="闪避反击：违章处罚", group=SkillGroup.DODGE, tags=_COUNTER, parameter="伤害倍率", curve="1181008", element=Element.ELECTRIC),
        _move("special-tap", move_id=SPECIAL_MOVE_ID, label="特殊技：工程清障", source="特殊技：工程清障", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1181005", element=Element.ELECTRIC),
        _move("ex-special-two-grenades", move_id=EX_SPECIAL_MOVE_ID, label="强化特殊技：超规工程清障（两颗手雷）", source="强化特殊技：超规工程清障", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", components=(("1181006", 2.0),), element=Element.ELECTRIC),
        _move("potential1-cycle-single-throw", move_id=SPECIAL_CYCLE_MOVE_ID, label="潜能1：特殊技·循环（单次投掷）", source="特殊技：工程清障·循环", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", components=(("1181018", 1.0 / 29.0),), element=Element.ELECTRIC, condition_ids=(PULSE_STATE_ACTIVE,)),
        _move("potential1-vortex-grenade", move_id=VORTEX_GRENADE_MOVE_ID, label="潜能1：涡流集束手雷（单次）", source="涡流集束手雷基础倍率", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1181020", element=Element.ELECTRIC, condition_ids=(POTENTIAL1_VORTEX_ACTIVE,)),
        _move("potential1-pulse-grenade", move_id=PULSE_GRENADE_MOVE_ID, label="潜能1：脉冲手雷（单次）", source="脉冲手雷倍率", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1181019", element=Element.ELECTRIC, condition_ids=(PULSE_GRENADE_READY,)),
        _move("chain-attack", move_id=CHAIN_MOVE_ID, label="连携技：协作施工", source="连携技：协作施工", group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter="伤害倍率", curve="1181009", element=Element.ELECTRIC),
        _move("ultimate", move_id=ULTIMATE_MOVE_ID, label="终结技：工程爆破请勿接近", source="终结技：工程爆破请勿接近", group=SkillGroup.ULTIMATE, tags=_ULT, parameter="伤害倍率", curve="1181010", element=Element.ELECTRIC),
        _move("quick-assist", move_id=QUICK_ASSIST_MOVE_ID, label="快速支援：事故解决方案", source="快速支援：事故解决方案", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1181011", element=Element.ELECTRIC),
        _move("assist-strike", move_id=ASSIST_STRIKE_MOVE_ID, label="支援突击：反击电针", source="支援突击：反击电针", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1181012", element=Element.ELECTRIC),
    ),
    data_quality_notes=(
        "Potential 1 Special Cycle reports one damage curve divided by 29; the picker exposes one grenade at that single-throw ratio without simulating its duration or number of throws.",
        "Potential 1 pulse-grenade Discharge uses the source's per-element coefficient and one selected active teammate anomaly record; DoT sources use one anomaly tick as the Discharge base.",
    ),
)


__all__ = [name for name in globals() if name.isupper()] + ["GRACE_REVIEWED_MAPPING"]
