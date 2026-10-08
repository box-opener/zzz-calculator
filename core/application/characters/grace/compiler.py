"""Compile Grace's reviewed Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
)

from ...ids import DamageEventSemanticId, MoveEntryId, MultiplierVariantId, RuleItemId
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import GraceCompileConfig
from .reviewed import (
    ELECTRIC_DISORDER_REMAINING_SECONDS,
    ELECTRIC_ENERGY_EMPOWERED,
    EXTRA_GRENADE_C6_ACTIVE,
    GRACE_ELECTRIC_ANOMALY_MOVE_ID,
    GRACE_ELECTRIC_ANOMALY_RECORD_ID,
    GRACE_ELECTRIC_DISORDER_MOVE_ID,
    GRACE_ID,
    GRACE_REVIEWED_MAPPING,
    POTENTIAL1_VORTEX_ACTIVE,
    PULSE_GRENADE_READY,
    PULSE_STATE_ACTIVE,
    PULSE_GRENADE_MOVE_ID,
    TARGET_ELECTRICALLY_BREACHED,
)


_SHOCK_TEMPLATE_ID = EventTemplateId("template:character:1181:electric-shock")
_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1181:electric-disorder")
_C6_SPECIAL_CHILD_ID = EventTemplateId("template:character:1181:cinema6:extra-special-grenade")
_C6_EX_CHILD_ID = EventTemplateId("template:character:1181:cinema6:extra-ex-grenade")
_C6_CYCLE_CHILD_ID = EventTemplateId("template:character:1181:cinema6:extra-cycle-grenade")
_PULSE_DISCHARGE_ID = EventTemplateId("template:character:1181:potential1:pulse-discharge")
_CYCLE_DISCHARGE_ID = EventTemplateId("template:character:1181:potential1:cycle-discharge")
_CYCLE_PULSE_GRENADE_ID = EventTemplateId("template:character:1181:potential1:cycle-pulse-grenade")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    found = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(found) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(found)}")
    return float(found[0].group("value"))


def _condition(condition_id, label: str, text: str, value: bool = False) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1181:{key}"),
        owner=GRACE_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1181:{key}"),
            source=source,
            owner=GRACE_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(modifier_path=node, operation=operation, value=value),
    )


def _event_creation(
    key: str,
    source: RuleSource,
    child_template_id: EventTemplateId,
    parent_template_ids: tuple[EventTemplateId, ...],
) -> EventCreationEffect:
    template_filter = (
        EventTemplateIdFilter(parent_template_ids[0])
        if len(parent_template_ids) == 1
        else AnyFilter(tuple(EventTemplateIdFilter(item) for item in parent_template_ids))
    )
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1181:{key}"),
            source=source,
            owner=GRACE_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(DamageTypeFilter(DamageType.DIRECT), DamageDealerFilter(GRACE_ID), template_filter),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=child_template_id,
            unique_per_source_event=True,
        ),
    )


def load_raw_record(
    data: Mapping[str, object],
    *,
    potential_level: int = 0,
) -> NanokaRawRecord:
    if not 0 <= potential_level <= 6:
        raise ValueError("Grace potential_level must be between 0 and 6")
    view = deepcopy(dict(data))
    passive = view.get("passive")
    levels = passive.get("level") if isinstance(passive, dict) else None
    if not isinstance(levels, dict):
        raise ValueError("Grace source is missing passive level data")
    first_id, last_id = (1181501, 1181507) if potential_level == 0 else (1181508, 1181514)
    passive["level"] = {
        key: item
        for key, item in levels.items()
        if isinstance(item, Mapping)
        and isinstance(item.get("id"), int)
        and first_id <= int(item["id"]) <= last_id
    }
    raw = load_nanoka_raw_record(view, expected_character_id=str(GRACE_ID))
    if potential_level and not any(item.level == potential_level for item in raw.potential_details):
        raise ValueError(f"Grace source is missing Potential {potential_level}")
    return raw


def _validate_raw(raw: NanokaRawRecord, config: GraceCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Grace raw record and compile config IDs must match")
    if raw.name != "格莉丝" or raw.code_name != "Grace":
        raise ValueError("unexpected Grace identity")
    if raw.specialty != "异常" or raw.element != "电属性" or raw.rarity != 4:
        raise ValueError("unexpected Grace role, element, or rank")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Grace source must include seven cores and six mindscapes")
    if config.potential_level and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError(f"Grace source is missing Potential {config.potential_level}")


def _static_electric_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_SHOCK_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1181:electric-shock"),
        label="属性异常：感电（单跳125%，10秒10跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=GRACE_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=GRACE_ID,
        history_record_source=GRACE_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=GRACE_ELECTRIC_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1181:electric-shock"),
        character_id=GRACE_ID,
        move_id=GRACE_ELECTRIC_ANOMALY_MOVE_ID,
        display_name="属性异常：感电（单跳125%，10秒10跳）",
        original_text="静态单人100%电属性异常记录；感电每跳125%，持续10秒，共10跳；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1181:electric-shock-tick"),
                label="感电单跳125% × 10",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1181:electric-disorder"),
        label="紊乱：感电（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=GRACE_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=GRACE_ID,
        history_record_source=GRACE_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=GRACE_ELECTRIC_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1181:electric-disorder"),
        character_id=GRACE_ID,
        move_id=GRACE_ELECTRIC_DISORDER_MOVE_ID,
        display_name="紊乱：感电（当前剩余时间）",
        original_text="感电紊乱倍率按规范为450% + floor(t)×125%；剩余时间是当前输入，不推演时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1181:electric-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="感电紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ELECTRIC_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.25,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=ELECTRIC_DISORDER_REMAINING_SECONDS,
        label="当前目标感电剩余时间（秒）",
        original_text="使用当前剩余时间，范围0–10秒；不模拟感电时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_grace(
    config: GraceCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    mapping = NanokaReviewedMapping(
        moves=tuple(
            item for item in GRACE_REVIEWED_MAPPING.moves
            if not item.entry_key.startswith("potential1-") or config.potential_level >= 1
        ),
        data_quality_notes=GRACE_REVIEWED_MAPPING.data_quality_notes,
    )
    direct_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=GRACE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1181",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    conditions = []
    if config.potential_level >= 2:
        detail = next(item for item in raw_record.potential_details if item.level == config.potential_level)
        conditions.append(
            _condition(
                ELECTRIC_ENERGY_EMPOWERED,
                "当前处于电能强化状态",
                detail.description,
            )
        )
    if config.cinema_level >= 2:
        conditions.append(
            _condition(
                TARGET_ELECTRICALLY_BREACHED,
                "目标当前处于电致击穿状态",
                raw_record.mindscapes[1].description,
            )
        )
    if config.potential_level >= 1:
        conditions.extend((
            _condition(PULSE_GRENADE_READY, "当前可投掷脉冲手雷", "表示当前的脉冲手雷已就绪；不模拟资源历史。"),
            _condition(PULSE_STATE_ACTIVE, "当前处于脉冲状态", "表示潜能1循环特殊技已解锁；不模拟脉冲资源数量。"),
            _condition(POTENTIAL1_VORTEX_ACTIVE, "本次强化特殊技已额外投掷涡流集束手雷", "当前招式额外投掷状态；不模拟电能积累过程。"),
        ))
    if config.cinema_level >= 6:
        conditions.append(
            _condition(
                EXTRA_GRENADE_C6_ACTIVE,
                "本次特殊技或强化特殊技消耗全部电能",
                raw_record.mindscapes[5].description,
            )
        )
    rules: list[CalculationRuleItem] = []
    parameters: list[ScenarioIntegerParameter] = []
    static_entries, static_templates, disorder_seconds = _static_electric_entries(raw_record)
    entries.extend(static_entries)
    templates.extend(static_templates)
    parameters.append(disorder_seconds)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(GRACE_ID, "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = source_for(GRACE_ID, "extra-ability", EffectSourceType.ADDITIONAL_ABILITY, raw_record.extra_ability_name, raw_record.extra_ability_description)
    c1_source = source_for(GRACE_ID, "cinema1", EffectSourceType.CINEMA, raw_record.mindscapes[0].name, raw_record.mindscapes[0].description)
    c2_source = source_for(GRACE_ID, "cinema2", EffectSourceType.CINEMA, raw_record.mindscapes[1].name, raw_record.mindscapes[1].description)

    # Core resource and buildup behavior is recorded as source-only because the
    # calculation result contract does not simulate energy or buildup meters.
    rules.append(_rule("core:energy-buildup-source-only", core_source, "核心被动：电能与异常积蓄", core.description, RuleEligibility.ELIGIBLE))
    rules.append(_rule("cinema1:energy-source-only", c1_source, "1影：电能回复（资源状态）", raw_record.mindscapes[0].description, RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE))
    rules.append(_rule("cinema4:energy-efficiency-source-only", source_for(GRACE_ID, "cinema4", EffectSourceType.CINEMA, raw_record.mindscapes[3].name, raw_record.mindscapes[3].description), "4影：能量效率（资源状态）", raw_record.mindscapes[3].description, RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE))

    if config.additional_ability_eligible:
        extra_text = raw_record.extra_ability_description
        rules.append(_rule(
            "extra-ability:shock-record-anomaly-bonus",
            extra_source,
            "额外能力：当前感电异常增伤+18%/层（最多2层）",
            extra_text,
            RuleEligibility.ELIGIBLE,
            stack_count=2,
            stack_min=0,
            stack_max=2,
            effects=(
                _modifier(
                    "extra-ability:shock-record-anomaly-bonus",
                    extra_source,
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    Resolved(0.18),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        ElementFilter(Element.ELECTRIC),
                    ),
                ),
            ),
        ))
    else:
        rules.append(_rule(
            "extra-ability:shock-record-anomaly-bonus",
            extra_source,
            "额外能力：感电伤害提升18%（队伍条件未满足）",
            raw_record.extra_ability_description,
            RuleEligibility.INELIGIBLE,
        ))

    if config.cinema_level >= 2:
        c2_resistance = _number(raw_record.mindscapes[1].description, r"电属性伤害抗性降低(?P<value>[\d.]+)%", "Grace C2 Electric resistance reduction") / 100.0
        rules.append(_rule(
            "cinema2:electric-resistance-debuff",
            c2_source,
            f"2影：目标当前电抗降低{c2_resistance * 100:g}%（异常积蓄抗性不计入伤害结果）",
            raw_record.mindscapes[1].description,
            RuleEligibility.ELIGIBLE,
            conditions=(TARGET_ELECTRICALLY_BREACHED,),
            effects=(
                _modifier("cinema2:electric-resistance-reduction", c2_source, CalculationNode.ENEMY_RESISTANCE_REDUCTION, Resolved(c2_resistance), target=EffectTarget.ENEMY, filters=(ElementFilter(Element.ELECTRIC),)),
            ),
        ))

    if config.potential_level >= 2:
        detail = next(item for item in raw_record.potential_details if item.level == config.potential_level)
        damage_bonus = _number(detail.description, r"电属性伤害提升(?P<value>[\d.]+)%", "Grace Potential Electric damage increase") / 100.0
        potential_source = source_for(GRACE_ID, f"potential{config.potential_level}", EffectSourceType.SPECIAL_MECHANISM, detail.level_show_name, detail.description)
        rules.append(_rule(
            f"potential{config.potential_level}:electric-damage-bonus",
            potential_source,
            f"潜能{config.potential_level}：电能强化，电伤+{damage_bonus * 100:g}%",
            detail.description,
            RuleEligibility.ELIGIBLE,
            conditions=(ELECTRIC_ENERGY_EMPOWERED,),
            effects=(_modifier(
                f"potential{config.potential_level}:electric-damage-bonus",
                potential_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(damage_bonus),
                target=EffectTarget.TEAM,
                filters=(DamageDealerFilter(GRACE_ID), ElementFilter(Element.ELECTRIC)),
            ),),
        ))

    if config.cinema_level >= 3 or config.cinema_level >= 5:
        for level in (3, 5):
            if config.cinema_level < level:
                continue
            mindscape = raw_record.mindscapes[level - 1]
            source = source_for(GRACE_ID, f"cinema{level}", EffectSourceType.CINEMA, mindscape.name, mindscape.description)
            rules.append(_rule(f"cinema{level}:skill-levels", source, f"{level}影：技能等级+2", mindscape.description, RuleEligibility.ELIGIBLE))

    # Potential 1's next-grenade Discharge is an independent event. Its source
    # is resolved from one selected active actor's current panel record by the
    # execution layer, never by replacing the current operator.
    if config.potential_level >= 1:
        pulse_source_text = next((item.description for item in raw_record.moves if item.name == "脉冲"), raw_record.potential_details[0].description)
        multipliers = tuple((element, value) for element, value in (
            (Element.ETHER, 5.60), (Element.XUANMO, 5.60),
            (Element.ELECTRIC, 2.80), (Element.FIRE, 7.00),
            (Element.PHYSICAL, 0.50), (Element.LINREN, 0.50),
            (Element.ICE, 0.70), (Element.LIESHUANG, 0.70),
            (Element.WIND, 0.28),
        ))
        discharge_rule_id = RuleItemId("rule:character:1181:potential1:pulse-discharge")
        def _discharge_template(template_id: EventTemplateId, suffix: str):
            ref = DamageEventTemplateRef(
                template_id=template_id,
                semantic_id=DamageEventSemanticId(f"event:character:1181:potential1:{suffix}-discharge"),
                label="潜能1：脉冲手雷异放（所选异常记录）",
                damage_type=DamageType.ANOMALY,
                damage_subtype=DamageSubtype.DISCHARGE,
                element=Element.ELECTRIC,
                source_rule_item_id=discharge_rule_id,
            )
            return ref, DischargeDamageEventTemplate(
                ref=ref,
                damage_dealer=GRACE_ID,
                element=Element.ELECTRIC,
                discharge_triggerer=GRACE_ID,
                history_record_source=None,
                crit_rule=NoCritRule(),
                move_id=None,
                multiplier_from_source_event=False,
                source_multiplier_by_element=multipliers,
            )

        pulse_discharge_ref, pulse_discharge_template = _discharge_template(_PULSE_DISCHARGE_ID, "pulse")
        cycle_discharge_ref, cycle_discharge_template = _discharge_template(_CYCLE_DISCHARGE_ID, "cycle")
        templates.extend((pulse_discharge_template, cycle_discharge_template))
        pulse_grenade_template = next(
            template
            for template in direct_templates
            if template.move_id == PULSE_GRENADE_MOVE_ID
        )
        cycle_pulse_rule_id = RuleItemId("rule:character:1181:potential1:cycle-pulse-grenade")
        cycle_pulse_ref = replace(
            pulse_grenade_template.ref,
            template_id=_CYCLE_PULSE_GRENADE_ID,
            semantic_id=DamageEventSemanticId("event:character:1181:potential1:cycle-pulse-grenade"),
            label="循环特殊技：额外脉冲手雷",
            source_rule_item_id=cycle_pulse_rule_id,
        )
        templates.append(replace(pulse_grenade_template, ref=cycle_pulse_ref, move_id=None))
        cycle_entry_index = next(
            i for i, entry in enumerate(entries)
            if entry.entry_id == MoveEntryId("move-entry:character:1181:potential1-cycle-single-throw")
        )
        pulse_entry = next(
            entry for entry in entries
            if entry.entry_id == MoveEntryId("move-entry:character:1181:potential1-pulse-grenade")
        )
        entries[cycle_entry_index] = replace(
            entries[cycle_entry_index],
            derived_damage_events=(
                *entries[cycle_entry_index].derived_damage_events,
                DerivedDamageEventTemplateRef(
                    template=cycle_pulse_ref,
                    multiplier=FixedMultiplier(Resolved(_compiled_ratio(pulse_entry))),
                ),
            ),
        )
        pulse_entry_index = next((i for i, entry in enumerate(entries) if entry.entry_id == MoveEntryId("move-entry:character:1181:potential1-pulse-grenade")), None)
        if pulse_entry_index is not None:
            entries[pulse_entry_index] = replace(
                entries[pulse_entry_index],
                derived_damage_events=(*entries[pulse_entry_index].derived_damage_events, DerivedDamageEventTemplateRef(template=pulse_discharge_ref, multiplier=FixedMultiplier(Resolved(1.0)))),
            )
        cycle_entry_index = next((i for i, entry in enumerate(entries) if entry.entry_id == MoveEntryId("move-entry:character:1181:potential1-cycle-single-throw")), None)
        if cycle_entry_index is not None:
            entries[cycle_entry_index] = replace(
                entries[cycle_entry_index],
                derived_damage_events=(*entries[cycle_entry_index].derived_damage_events, DerivedDamageEventTemplateRef(template=cycle_discharge_ref, multiplier=FixedMultiplier(Resolved(1.0)))),
            )
        potential_source = source_for(GRACE_ID, "potential1:pulse-discharge", EffectSourceType.SPECIAL_MECHANISM, "潜能1：脉冲", pulse_source_text)
        cycle_template_id = EventTemplateId("template:character:1181:potential1-cycle-single-throw:main")
        rules.append(_rule(
            "potential1:cycle-pulse-grenade",
            potential_source,
            "潜能1：循环特殊技满足脉冲条件时额外投掷一颗脉冲手雷",
            pulse_source_text,
            RuleEligibility.ELIGIBLE,
            conditions=(PULSE_GRENADE_READY,),
            effects=(_event_creation("potential1:cycle-pulse-grenade", potential_source, _CYCLE_PULSE_GRENADE_ID, (cycle_template_id,)),),
        ))
        pulse_template_id = pulse_grenade_template.ref.template_id
        rules.append(_rule(
            "potential1:pulse-discharge",
            potential_source,
            "潜能1：脉冲手雷命中异常目标时结算一次异放",
            pulse_source_text,
            RuleEligibility.ELIGIBLE,
            conditions=(PULSE_GRENADE_READY,),
            effects=(
                _event_creation("potential1:pulse-discharge", potential_source, _PULSE_DISCHARGE_ID, (pulse_template_id,)),
                _event_creation("potential1:cycle-discharge", potential_source, _CYCLE_DISCHARGE_ID, (_CYCLE_PULSE_GRENADE_ID,)),
            ),
        ))

    # C6 doubles every main Special/EX grenade and adds one additional main
    # grenade. Potential 1's separately named Vortex and Pulse grenades do not
    # receive this C6 multiplier or extra grenade.
    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        c6_source = source_for(GRACE_ID, "cinema6:grenades", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
        child_specs = [
            ("special", "special-tap", _C6_SPECIAL_CHILD_ID),
            ("ex", "ex-special-two-grenades", _C6_EX_CHILD_ID),
        ]
        if config.potential_level >= 1:
            child_specs.append(
                ("cycle", "potential1-cycle-single-throw", _C6_CYCLE_CHILD_ID)
            )
        c6_effects = []
        for key, entry_key, child_id in child_specs:
            parent_entry = next(item for item in entries if str(item.entry_id).endswith(entry_key))
            parent_template = next(
                template for template in direct_templates
                if template.move_id == parent_entry.move_id and template.ref.element is Element.ELECTRIC
            )
            parent_ref = parent_template.ref
            child_ref = replace(
                parent_ref,
                template_id=child_id,
                semantic_id=DamageEventSemanticId(f"event:character:1181:cinema6:extra-{key}-grenade"),
                label=f"6影：额外{ {'special': '特殊技', 'ex': '强化特殊技', 'cycle': '循环特殊技'}[key] }手雷",
                source_rule_item_id=RuleItemId("rule:character:1181:cinema6:grenade-double-and-extra"),
            )
            templates.append(replace(parent_template, ref=child_ref, move_id=None))
            # One EX curve already represents two grenades; the additional
            # grenade uses one half of that total curve, and every grenade is
            # multiplied by the source-confirmed 200% under C6.
            ratio = _compiled_ratio(parent_entry)
            single_ratio = ratio / 2.0 if key == "ex" else ratio
            entries[entries.index(parent_entry)] = replace(
                parent_entry,
                derived_damage_events=(
                    *parent_entry.derived_damage_events,
                    DerivedDamageEventTemplateRef(
                        template=child_ref,
                        multiplier=FixedMultiplier(Resolved(single_ratio * 2.0)),
                    ),
                ),
            )
            c6_effects.extend((
                _modifier(
                    f"cinema6:{key}-grenade-double",
                    c6_source,
                    CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                    Resolved(2.0),
                    target=EffectTarget.TEAM,
                    filters=(DamageDealerFilter(GRACE_ID), EventTemplateIdFilter(parent_ref.template_id)),
                    operation=EffectOperation.MULTIPLY,
                ),
                _event_creation(
                    f"cinema6:extra-{key}-grenade",
                    c6_source,
                    child_id,
                    (parent_ref.template_id,),
                ),
            ))
        rules.append(_rule(
            "cinema6:grenade-double-and-extra",
            c6_source,
            "6影：消耗全部电能时，每颗手雷伤害提升至200%并额外投掷一颗",
            cinema6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(EXTRA_GRENADE_C6_ACTIVE,),
            effects=tuple(c6_effects),
        ))
    else:
        c6_source = source_for(GRACE_ID, "cinema6:grenades", EffectSourceType.CINEMA, raw_record.mindscapes[5].name, raw_record.mindscapes[5].description)
        rules.append(_rule("cinema6:grenade-double-and-extra", c6_source, "6影：额外投掷手雷", raw_record.mindscapes[5].description, RuleEligibility.INELIGIBLE))

    diagnostics = list(diagnostics)
    return build_definition(
        character_id=GRACE_ID,
        role=CharacterRole.ANOMALY,
        element=Element.ELECTRIC,
        source=source_for(GRACE_ID, "nanoka-3.2", EffectSourceType.SPECIAL_MECHANISM, "Nanoka 3.2", raw_record.source_url),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def _compiled_ratio(entry: MoveCalculationEntry) -> float:
    multiplier = entry.multiplier_variants[0].multiplier
    if not isinstance(multiplier, FixedMultiplier) or not isinstance(multiplier.value, Resolved):
        raise ValueError(f"Grace multiplier is unresolved for {entry.entry_id}")
    return multiplier.value.value


__all__ = ["compile_grace", "load_raw_record"]
