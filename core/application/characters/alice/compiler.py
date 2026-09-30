"""Compile the Nanoka Alice record into application contracts."""

from __future__ import annotations

from core.types import (
    AnyFilter,
    CharacterId,
    CharacterRole,
    CalculationNode,
    DamageTag,
    DamageTagFilter,
    DamageSubtypeFilter,
    DamageTypeFilter,
    DamageDealerFilter,
    CharacterFilter,
    CreatedByEffectFilter,
    Element,
    ElementFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    CurrentAnomalyEffectStrengthValueSource,
    CurrentAnomalyProficiencyValueSource,
    DamageEventId,
    FixedMultiplier,
    NoCritRule,
    StandardCritRule,
    DamageSubtype,
    DamageType,
    MoveId,
    EventCreationEffect,
    EventCreationResult,
    EventSelector,
    BattleEventKind,
    ModifierEffect,
    ModifierResult,
    MoveIdFilter,
    NotFilter,
    ScenarioParameterDerivedValue,
    SettledDamageValueSource,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    Resolved,
    Unresolved,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import RuleItemId
from ...ids import DamageEventSemanticId, MoveEntryId, MultiplierVariantId
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierVariant,
    MultiplierRelation,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    CurrentAttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
    SettledAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
)
from .config import AliceCompileConfig
from .reviewed import (
    ALICE_ID,
    ALICE_REVIEWED_MAPPING,
    PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID,
    POLAR_ASSAULT_CONDITION_ID,
    STAR_DANCE_1_CONDITION_ID,
    STAR_DANCE_2_CONDITION_ID,
    STAR_DANCE_3_CONDITION_ID,
    ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID,
    ALICE_PHYSICAL_ANOMALY_RECORD_ID,
    ALICE_REMAINING_DURATION_PARAMETER_ID,
    ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID,
    VICTORY_STATE_ACTIVE_CONDITION_ID,
)
from ...scenario import ParameterResolution, ScenarioIntegerParameter


PHYSICAL_ANOMALY_BUILDUP_EFFICIENCY = (
    0.125,
    0.146,
    0.167,
    0.188,
    0.208,
    0.229,
    0.250,
)


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )


def _rule(
    rule_id: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    effects=(),
    *,
    condition_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(rule_id),
        owner=ALICE_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    effect_key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1401:{effect_key}"),
            source=source,
            owner=ALICE_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("raw Alice record must contain all seven core levels") from exc


def _raw_talent(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Alice record is missing cinema {level}") from exc


def _special_entry(
    *,
    entry_id: str,
    move_id: MoveId,
    label: str,
    ref: DamageEventTemplateRef,
    variant: MultiplierVariant,
    condition_ids=(),
) -> MoveCalculationEntry:
    return MoveCalculationEntry(
        entry_id=MoveEntryId(entry_id),
        character_id=ALICE_ID,
        move_id=move_id,
        display_name=label,
        original_text=label,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(variant,),
        main_damage_event=ref,
        condition_ids=tuple(condition_ids),
    )


def _history_anomaly_pair(
    source_rule_id: RuleItemId | None = None,
) -> tuple[AttributeAnomalyDamageEventTemplate, DamageEventTemplateRef]:
    move_id = MoveId("move:alice:physical-anomaly")
    ref = DamageEventTemplateRef(
        template_id="template:alice:1401:physical-anomaly",
        semantic_id="event:alice:1401:physical-anomaly",
        label="属性异常：强击",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_id,
    )
    template = AttributeAnomalyDamageEventTemplate(
        ref=ref,
        damage_dealer=ALICE_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=ALICE_ID,
        history_record_source=ALICE_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=move_id,
    )
    return template, ref


def _polar_pair() -> tuple[CurrentAttributeAnomalyDamageEventTemplate, DamageEventTemplateRef]:
    move_id = MoveId("move:alice:polar-assault")
    ref = DamageEventTemplateRef(
        template_id="template:alice:1401:polar-assault",
        semantic_id="event:alice:1401:polar-assault",
        label="极性强击",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
    )
    template = CurrentAttributeAnomalyDamageEventTemplate(
        ref=ref,
        damage_dealer=ALICE_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=ALICE_ID,
        base_source=CurrentAnomalyEffectStrengthValueSource(ALICE_ID),
        crit_rule=NoCritRule(),
        move_id=move_id,
    )
    return template, ref


def _disorder_pair() -> tuple[DisorderDamageEventTemplate, DamageEventTemplateRef]:
    move_id = MoveId("move:alice:disorder")
    ref = DamageEventTemplateRef(
        template_id="template:alice:1401:disorder",
        semantic_id="event:alice:1401:disorder",
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        damage_subtype=None,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
    )
    template = DisorderDamageEventTemplate(
        ref=ref,
        damage_dealer=ALICE_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=ALICE_ID,
        history_record_source=ALICE_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=move_id,
    )
    return template, ref


def _c6_pair(
    source_rule_id: RuleItemId,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    ref = DamageEventTemplateRef(
        template_id="template:alice:1401:cinema6:decisive-extra-attack",
        semantic_id="event:alice:1401:cinema6:decisive-extra-attack",
        label="6影：决胜状态额外攻击",
        damage_type=DamageType.DIRECT,
        damage_subtype=None,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(33.0)),
        repeat_count=1,
        repeat_count_parameter_id=ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ALICE_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAnomalyProficiencyValueSource(ALICE_ID),
        crit_rule=StandardCritRule(ALICE_ID, guaranteed=True),
        move_id=None,
    )
    return derived, typed


def compile_alice(
    config: AliceCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = ALICE_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=ALICE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="alice:1401",
    )
    physical_template, physical_ref = _history_anomaly_pair()
    polar_template, polar_ref = _polar_pair()
    disorder_template, disorder_ref = _disorder_pair()
    physical_move_id = MoveId("move:alice:physical-anomaly")
    polar_move_id = MoveId("move:alice:polar-assault")
    disorder_move_id = MoveId("move:alice:disorder")
    entries = (
        *entries,
        _special_entry(
            entry_id="move-entry:alice:1401:physical-anomaly",
            move_id=physical_move_id,
            label="属性异常：强击",
            ref=physical_ref,
            variant=MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:alice:1401:physical-anomaly"
                ),
                label="强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        _special_entry(
            entry_id="move-entry:alice:1401:polar-assault",
            move_id=polar_move_id,
            label="极性强击",
            ref=polar_ref,
            variant=MultiplierVariant(
                variant_id=MultiplierVariantId("variant:alice:1401:polar-assault"),
                label="原本强击效果100%",
                parameter_name="极性强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
            condition_ids=(POLAR_ASSAULT_CONDITION_ID,),
        ),
        _special_entry(
            entry_id="move-entry:alice:1401:disorder",
            move_id=disorder_move_id,
            label="紊乱：物理异常",
            ref=disorder_ref,
            variant=MultiplierVariant(
                variant_id=MultiplierVariantId("variant:alice:1401:disorder"),
                label="基础紊乱倍率+剩余时间补偿",
                parameter_name="物理异常紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ALICE_REMAINING_DURATION_PARAMETER_ID,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
    )
    templates = (*templates, physical_template, polar_template, disorder_template)
    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        ALICE_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    star_conditions = (
        _condition(STAR_DANCE_1_CONDITION_ID, "星芒圆舞曲：一段蓄力", "一段蓄力"),
        _condition(STAR_DANCE_2_CONDITION_ID, "星芒圆舞曲：二段蓄力", "二段蓄力"),
        _condition(STAR_DANCE_3_CONDITION_ID, "星芒圆舞曲：三段蓄力", "三段蓄力"),
        _condition(
            PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID,
            "目标处于物理异常状态",
            "物理异常状态持续期间",
        ),
        _condition(
            POLAR_ASSAULT_CONDITION_ID,
            "本次攻击触发极性强击",
            "三段蓄力终结一击触发极性强击",
        ),
        _condition(
            VICTORY_STATE_ACTIVE_CONDITION_ID,
            "当前处于决胜状态",
            "[决胜状态]持续期间",
        ),
    )

    core_rule_id = RuleItemId("rule:alice:1401:core-passive")
    periodic_ref = DamageEventTemplateRef(
        template_id="template:alice:1401:core-periodic-extra",
        semantic_id="event:alice:1401:core-periodic-extra",
        label="核心被动：物理异常额外伤害",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
        source_rule_item_id=core_rule_id,
    )
    periodic_template = SettledAnomalyDamageEventTemplate(
        ref=periodic_ref,
        damage_dealer=ALICE_ID,
        element=Element.PHYSICAL,
        base_source=SettledDamageValueSource(
            DamageEventId("event:alice:1401:periodic-source")
        ),
        crit_rule=NoCritRule(),
        move_id=None,
    )
    periodic_derived = DerivedDamageEventTemplateRef(
        template=periodic_ref,
        multiplier=FixedMultiplier(Resolved(0.025)),
        repeat_count=1,
        repeat_count_parameter_id=ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID,
    )
    periodic_effect_id = EffectId("effect:character:1401:core:periodic-extra")
    periodic_creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=periodic_effect_id,
            source=core_source,
            owner=ALICE_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.ANOMALY),
                ElementFilter(Element.PHYSICAL),
                NotFilter(CreatedByEffectFilter(periodic_effect_id)),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=periodic_ref.template_id,
        ),
    )
    disorder_extra = _modifier(
        "core:disorder-extra-multiplier",
        core_source,
        CalculationNode.DISORDER_EXTRA_MULTIPLIER,
        ScenarioParameterDerivedValue(
            parameter_id=str(ALICE_REMAINING_DURATION_PARAMETER_ID),
            coefficient=Resolved(0.18),
            base=Resolved(0.0),
            cap_max=Resolved(1.80),
        ),
        target=EffectTarget.TEAM,
        filters=(
            DamageTypeFilter(DamageType.DISORDER),
            ElementFilter(Element.PHYSICAL),
        ),
    )
    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            str(core_rule_id),
            core_source,
            core.name,
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:physical-buildup-efficiency",
                    core_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    Resolved(PHYSICAL_ANOMALY_BUILDUP_EFFICIENCY[config.core_level - 1]),
                    target=EffectTarget.SELF,
                    condition=None,
                ),
                disorder_extra,
                periodic_creation,
            ),
        )
    )

    extra_name = raw_record.extra_ability_name
    extra_text = raw_record.extra_ability_description
    extra_source = source_for(
        ALICE_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        extra_name,
        extra_text,
    )
    rules.append(
        _rule(
            "rule:alice:1401:extra-ability",
            extra_source,
            extra_name,
            extra_text,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
        )
    )

    c1 = _raw_talent(raw_record, 1)
    c1_source = source_for(
        ALICE_ID,
        "cinema-1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    # C1's defense reduction is tied to Alice's Strong Attack, which is an
    # anomaly event.  The damage tag keeps this Effect from leaking onto all
    # ordinary sword hits while the anomaly event lane is being integrated.
    rules.append(
        _rule(
            "rule:alice:1401:cinema1",
            c1_source,
            f"1影：{c1.name}",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:enemy-defense",
                    c1_source,
                    CalculationNode.ENEMY_DEFENSE_REDUCTION,
                    Resolved(0.20),
                    target=EffectTarget.ENEMY,
                    filters=(DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),),
                ),
            ),
        )
    )

    c2 = _raw_talent(raw_record, 2)
    c2_source = source_for(
        ALICE_ID,
        "cinema-2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    rules.append(
        _rule(
            "rule:alice:1401:cinema2",
            c2_source,
            f"2影：{c2.name}",
            c2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:anomaly-damage",
                    c2_source,
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "cinema2:disorder-damage",
                    c2_source,
                    CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    c3 = _raw_talent(raw_record, 3)
    c3_source = source_for(
        ALICE_ID,
        "cinema-3",
        EffectSourceType.CINEMA,
        f"3影：{c3.name}",
        c3.description,
    )
    rules.append(
        _rule(
            "rule:alice:1401:cinema3",
            c3_source,
            f"3影：{c3.name}",
            c3.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 3
            else RuleEligibility.INELIGIBLE,
        )
    )

    c4 = _raw_talent(raw_record, 4)
    c4_source = source_for(
        ALICE_ID,
        "cinema-4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    rules.append(
        _rule(
            "rule:alice:1401:cinema4",
            c4_source,
            f"4影：{c4.name}",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:physical-resistance-ignore",
                    c4_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(0.10),
                    target=EffectTarget.ENEMY,
                    filters=(
                        DamageDealerFilter(ALICE_ID),
                        AnyFilter(
                            (
                                DamageTypeFilter(DamageType.DIRECT),
                                DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                            )
                        ),
                        AnyFilter(
                            (
                                ElementFilter(Element.PHYSICAL),
                                ElementFilter(Element.LINREN),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    c5 = _raw_talent(raw_record, 5)
    c5_source = source_for(
        ALICE_ID,
        "cinema-5",
        EffectSourceType.CINEMA,
        f"5影：{c5.name}",
        c5.description,
    )
    rules.append(
        _rule(
            "rule:alice:1401:cinema5",
            c5_source,
            f"5影：{c5.name}",
            c5.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 5
            else RuleEligibility.INELIGIBLE,
        )
    )

    c6 = _raw_talent(raw_record, 6)
    c6_source = source_for(
        ALICE_ID,
        "cinema-6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_rule_id = RuleItemId("rule:alice:1401:cinema6")
    c6_derived, c6_template = _c6_pair(c6_rule_id)
    templates = (*templates, periodic_template, c6_template)
    rules.append(
        _rule(
            str(c6_rule_id),
            c6_source,
            f"6影：{c6.name}",
            c6.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1401:cinema6:decisive-extra-attack"
                        ),
                        source=c6_source,
                        owner=ALICE_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            CharacterFilter(ALICE_ID),
                            AnyFilter(
                                (
                                    MoveIdFilter(MoveId("move:alice:star-dance")),
                                    MoveIdFilter(MoveId("move:alice:star-finale")),
                                )
                            ),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=c6_derived.template.template_id,
                    ),
                ),
            ),
            condition_ids=(VICTORY_STATE_ACTIVE_CONDITION_ID,),
        )
    )

    return build_definition(
        character_id=ALICE_ID,
        role=CharacterRole.ANOMALY,
        element=Element.PHYSICAL,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=star_conditions,
        parameters=(
            ScenarioIntegerParameter(
                parameter_id=ALICE_REMAINING_DURATION_PARAMETER_ID,
                label="被结算物理异常剩余时间",
                original_text="默认按物理异常最大剩余时间10秒结算",
                resolution=ParameterResolution.USER_SELECTED,
                value=10,
                minimum=0,
                maximum=10,
            ),
            ScenarioIntegerParameter(
                parameter_id=ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID,
                label="物理异常额外伤害触发次数",
                original_text="每0.95秒触发一次（静态展示次数）",
                resolution=ParameterResolution.USER_SELECTED,
                value=1,
                minimum=1,
                maximum=32,
            ),
            ScenarioIntegerParameter(
                parameter_id=ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID,
                label="决胜状态额外攻击次数",
                original_text="最多触发6次",
                resolution=ParameterResolution.USER_SELECTED,
                value=6,
                minimum=0,
                maximum=6,
            ),
        ),
        independent_derived_damage_events=(periodic_derived, c6_derived),
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: AliceCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "爱丽丝":
        raise ValueError("unexpected character name in raw Alice record")
    if raw.code_name != "Alice":
        raise ValueError("unexpected Alice code name in raw record")
    if raw.specialty != "异常":
        raise ValueError("unexpected Alice specialty in raw record")
    if raw.element != "物理":
        raise ValueError("unexpected Alice element in raw record")
    if len(raw.core_levels) != 7:
        raise ValueError("raw Alice record must contain all seven core levels")
    if len(raw.mindscapes) != 6:
        raise ValueError("raw Alice record must contain all six mindscapes")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(ALICE_ID))


__all__ = [
    "ALICE_ID",
    "PHYSICAL_ANOMALY_BUILDUP_EFFICIENCY",
    "PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID",
    "POLAR_ASSAULT_CONDITION_ID",
    "compile_alice",
    "load_raw_record",
]
