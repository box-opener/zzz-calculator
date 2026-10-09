from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.application import (
    CalculationDiagnostic,
    CalculationRuleItem,
    CalculationScenario,
    ConditionResolution,
    CritDisplayMode,
    DamageEventCalculationOutput,
    DamageEventTemplateRef,
    DamageEventSemanticId,
    DerivedDamageEventTemplateRef,
    DiagnosticId,
    DiagnosticKind,
    EventCalculationStatus,
    MoveCalculationEntry,
    MoveCalculationOutput,
    MoveEntryId,
    MultiplierRelation,
    MultiplierVariant,
    MultiplierVariantId,
    RuleEligibility,
    RuleItemId,
    ScenarioCondition,
    ScenarioConditionId,
    ScenarioIntegerParameter,
    ScenarioParameterId,
    ParameterResolution,
)
from core.calculation import CalculationResult
from core.types import (
    BattleEventKind,
    CharacterId,
    CalculationNode,
    DamageTag,
    DamageType,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    EventTemplateId,
    FixedMultiplier,
    MoveId,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SnapshotRule,
)


def _source() -> RuleSource:
    return RuleSource(
        source_id=RuleSourceId("source:test"),
        source_type=EffectSourceType.SKILL,
        label="test source",
        raw_text="test source text",
    )


def _modifier_effect(owner: CharacterId) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:test"),
            source=_source(),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.2),
        ),
    )


def _diagnostic(
    diagnostic_id: str,
    *,
    blocking: bool,
    kind: DiagnosticKind = DiagnosticKind.AMBIGUOUS_SEMANTICS,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(diagnostic_id),
        kind=kind,
        message="test diagnostic",
        blocking=blocking,
        original_text="test text",
        candidates=("a", "b"),
    )


def _event_ref(
    semantic_id: str,
    *,
    label: str = "main damage",
    tag: DamageTag | None = None,
) -> DamageEventTemplateRef:
    group = (
        SkillGroup.DODGE
        if tag in (DamageTag.DASH_ATTACK, DamageTag.DODGE_COUNTER)
        else SkillGroup.BASIC_ATTACK
    )
    return DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:{semantic_id}"),
        semantic_id=DamageEventSemanticId(semantic_id),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=frozenset() if tag is None else frozenset({tag}),
    )


def _derived_event_ref(
    semantic_id: str,
    *,
    label: str = "derived damage",
    multiplier: float = 1.0,
) -> DerivedDamageEventTemplateRef:
    return DerivedDamageEventTemplateRef(
        template=_event_ref(semantic_id, label=label),
        multiplier=FixedMultiplier(Resolved(multiplier)),
    )


def _variant(
    variant_id: str,
    *,
    multiplier: float = 1.0,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
    repeat_count: int | None = None,
    repeat_count_parameter_id: ScenarioParameterId | None = None,
) -> MultiplierVariant:
    return MultiplierVariant(
        variant_id=MultiplierVariantId(variant_id),
        label=variant_id,
        parameter_name=f"parameter:{variant_id}",
        multiplier=FixedMultiplier(Resolved(multiplier)),
        condition_ids=condition_ids,
        repeat_count=repeat_count,
        repeat_count_parameter_id=repeat_count_parameter_id,
    )


def _move(
    relation: MultiplierRelation,
    variants: tuple[MultiplierVariant, ...],
    *,
    diagnostics: tuple[CalculationDiagnostic, ...] = (),
    stage_index: int | None = None,
    derived: tuple[DerivedDamageEventTemplateRef, ...] = (),
) -> MoveCalculationEntry:
    return MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:test"),
        character_id=CharacterId("character:test"),
        move_id=MoveId("move:test"),
        display_name="Test move",
        original_text="Test move text",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        multiplier_relation=relation,
        multiplier_variants=variants,
        main_damage_event=_event_ref(
            "event:main",
            tag=DamageTag.BASIC_ATTACK,
        ),
        derived_damage_events=derived,
        stage_index=stage_index,
        diagnostics=diagnostics,
    )


def test_static_and_user_scenario_conditions_are_distinct() -> None:
    static = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:static"),
        label="static condition",
        original_text="always active",
        resolution=ConditionResolution.STATIC,
        value=True,
    )
    user = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:user"),
        label="user condition",
        original_text="current state",
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )
    scenario = CalculationScenario(
        scenario_id="scenario:test",
        current_operator=CharacterId("character:test"),
        conditions=(static, user),
        enabled_rule_item_ids=frozenset({RuleItemId("rule:test")}),
    )

    assert static.value is True
    assert user.value is None
    assert scenario.current_operator == CharacterId("character:test")

    with pytest.raises(ValueError, match="static conditions"):
        ScenarioCondition(
            condition_id=ScenarioConditionId("condition:invalid"),
            label="invalid",
            original_text="invalid",
            resolution=ConditionResolution.STATIC,
            value=None,
        )


def test_integer_scenario_parameter_supports_user_selected_repeat_count() -> None:
    parameter = ScenarioIntegerParameter(
        parameter_id=ScenarioParameterId("parameter:sword-count"),
        label="剑气次数",
        original_text="每道剑气",
        resolution=ParameterResolution.USER_SELECTED,
        value=5,
        minimum=0,
        maximum=8,
    )
    scenario = CalculationScenario(
        scenario_id="scenario:repeat-count",
        current_operator=CharacterId("character:test"),
        parameters=(parameter,),
    )

    assert scenario.parameters[0].value == 5
    with pytest.raises(ValueError, match="within its legal bounds"):
        ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId("parameter:invalid"),
            label="invalid",
            original_text="invalid",
            resolution=ParameterResolution.USER_SELECTED,
            value=9,
            minimum=0,
            maximum=8,
        )


def test_selectable_event_without_move_id_keeps_reviewed_group_and_tags() -> None:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:passive-tremolo"),
        semantic_id=DamageEventSemanticId("event:passive-tremolo"),
        label="终曲追加震音",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset(
            {
                DamageTag.SPECIAL_ATTACK,
                DamageTag.EX_SPECIAL_ATTACK,
                DamageTag.TREMOLO,
            }
        ),
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:passive-tremolo"),
        character_id=CharacterId("character:astra"),
        move_id=None,
        display_name="终曲追加震音",
        original_text="明确标注震音，未给独立招式ID",
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=ref.damage_tags,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(_variant("passive-tremolo", multiplier=1.25),),
        main_damage_event=ref,
    )

    assert entry.move_id is None
    assert entry.skill_group is SkillGroup.SPECIAL_ATTACK
    assert entry.damage_tags == ref.damage_tags


def test_rule_item_disables_all_results_together_and_validates_stacks() -> None:
    owner = CharacterId("character:owner")
    effect = _modifier_effect(owner)
    item = CalculationRuleItem(
        rule_id=RuleItemId("rule:test"),
        owner=owner,
        source=_source(),
        display_name="Test rule",
        original_text="Test rule text",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
        stack_count=2,
        stack_min=0,
        stack_max=3,
    )

    enabled_scenario = CalculationScenario(
        scenario_id="scenario:enabled",
        current_operator=owner,
        enabled_rule_item_ids=frozenset({item.rule_id}),
    )
    disabled_scenario = CalculationScenario(
        scenario_id="scenario:disabled",
        current_operator=owner,
    )
    assert item.effects == (effect,)
    assert item.rule_id in enabled_scenario.enabled_rule_item_ids
    assert item.rule_id not in disabled_scenario.enabled_rule_item_ids
    assert not hasattr(item, "enabled")

    with pytest.raises(ValueError, match="within its legal bounds"):
        CalculationRuleItem(
            rule_id=RuleItemId("rule:invalid-stack"),
            owner=owner,
            source=_source(),
            display_name="Invalid stack",
            original_text="Invalid stack text",
            eligibility=RuleEligibility.ELIGIBLE,
            stack_count=4,
            stack_min=0,
            stack_max=3,
        )


def test_multiplier_relations_preserve_stages_variants_and_unit_counts() -> None:
    complete = _move(
        MultiplierRelation.COMPLETE,
        (_variant("complete"),),
    )
    stage = _move(
        MultiplierRelation.SEQUENTIAL_STAGE,
        (_variant("stage-2"),),
        stage_index=2,
    )
    variants = _move(
        MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        (_variant("with-resource"), _variant("without-resource")),
    )
    repeat = _move(
        MultiplierRelation.UNIT_REPEAT,
        (
            _variant(
                "per-projectile",
                repeat_count_parameter_id=ScenarioParameterId("parameter:count"),
            ),
        ),
    )

    assert isinstance(complete.multiplier_variants[0].multiplier, FixedMultiplier)
    assert isinstance(complete.multiplier_variants[0].multiplier.value, Resolved)
    assert complete.multiplier_variants[0].multiplier.value.value == 1.0
    assert stage.stage_index == 2
    assert len(variants.multiplier_variants) == 2
    assert repeat.multiplier_variants[
        0
    ].repeat_count_parameter_id == ScenarioParameterId("parameter:count")


def test_unresolved_multiplier_relation_requires_blocking_diagnostic() -> None:
    with pytest.raises(ValueError, match="blocking diagnostic"):
        _move(
            MultiplierRelation.UNRESOLVED_RELATION,
            (_variant("unknown"),),
        )

    with pytest.raises(ValueError, match="multiple variants"):
        _move(
            MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
            (_variant("only-one"),),
        )

    with pytest.raises(ValueError, match="repeat count"):
        _move(
            MultiplierRelation.UNIT_REPEAT,
            (_variant("missing-count"),),
        )

    move = _move(
        MultiplierRelation.UNRESOLVED_RELATION,
        (_variant("unknown"),),
        diagnostics=(_diagnostic("diagnostic:multiplier", blocking=True),),
    )
    assert move.diagnostics[0].blocking is True


def test_move_event_semantic_ids_are_unique_and_derived_events_are_explicit() -> None:
    move = _move(
        MultiplierRelation.COMPLETE,
        (_variant("main"),),
        derived=(_derived_event_ref("event:derived", label="extra damage"),),
    )

    assert move.main_damage_event.event_kind is BattleEventKind.DAMAGE
    assert move.derived_damage_events[0].template.label == "extra damage"
    assert move.derived_damage_events[0].multiplier is not None
    assert move.derived_damage_events[0].required is False

    with pytest.raises(ValueError, match="semantic IDs"):
        _move(
            MultiplierRelation.COMPLETE,
            (_variant("duplicate"),),
            derived=(_derived_event_ref("event:main"),),
        )


def test_damage_event_template_ref_is_always_a_damage_event() -> None:
    template = _event_ref("event:typed")

    assert template.event_kind is BattleEventKind.DAMAGE
    assert template.damage_type is DamageType.DIRECT
    assert not hasattr(template, "multiplier")

    with pytest.raises(TypeError):
        DamageEventTemplateRef(
            template_id=EventTemplateId("template:state"),
            semantic_id=DamageEventSemanticId("event:state"),
            label="invalid state template",
            damage_type=DamageType.DIRECT,
            event_kind=BattleEventKind.STATE_CHANGE,  # type: ignore[call-arg]
        )


def test_move_output_distinguishes_complete_and_known_partial_totals() -> None:
    complete_event = DamageEventCalculationOutput(
        semantic_id=DamageEventSemanticId("event:main"),
        label="main",
        damage_type=DamageType.DIRECT,
        damage_subtype=None,
        status=EventCalculationStatus.CALCULATED,
        result=CalculationResult(value=100.0, breakdown=()),
        repeat_count=3,
    )
    complete = MoveCalculationOutput(
        move_entry_id=MoveEntryId("move-entry:test"),
        crit_display_mode=CritDisplayMode.EXPECTED,
        events=(complete_event,),
        known_total=300.0,
        complete=True,
    )
    incomplete_event = DamageEventCalculationOutput(
        semantic_id=DamageEventSemanticId("event:unsupported"),
        label="unsupported derived damage",
        damage_type=DamageType.SHARP_EXPLOSION,
        damage_subtype=None,
        status=EventCalculationStatus.UNSUPPORTED_CALCULATOR,
        diagnostics=(
            _diagnostic(
                "diagnostic:unsupported",
                blocking=True,
                kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            ),
        ),
    )
    partial = MoveCalculationOutput(
        move_entry_id=MoveEntryId("move-entry:test"),
        crit_display_mode=CritDisplayMode.EXPECTED,
        events=(complete_event, incomplete_event),
        known_total=300.0,
        complete=False,
        diagnostics=(_diagnostic("diagnostic:partial", blocking=True),),
    )

    assert complete.complete is True
    assert complete.known_total == 300.0
    assert complete_event.known_value == 300.0
    assert partial.complete is False
    assert partial.known_total == 300.0
    assert partial.events[1].status is EventCalculationStatus.UNSUPPORTED_CALCULATOR


def test_application_contracts_are_frozen() -> None:
    condition = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:frozen"),
        label="frozen",
        original_text="frozen",
        resolution=ConditionResolution.STATIC,
        value=True,
    )

    with pytest.raises(FrozenInstanceError):
        condition.value = False  # type: ignore[misc]
