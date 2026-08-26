from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

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
    Element,
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
        event_kind=BattleEventKind.DAMAGE,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=frozenset() if tag is None else frozenset({tag}),
        multiplier=FixedMultiplier(Resolved(1.0)),
    )


def _variant(
    variant_id: str,
    *,
    multiplier: float = 1.0,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
    repeat_count: int | None = None,
    repeat_count_condition_id: ScenarioConditionId | None = None,
) -> MultiplierVariant:
    return MultiplierVariant(
        variant_id=MultiplierVariantId(variant_id),
        label=variant_id,
        parameter_name=f"parameter:{variant_id}",
        multiplier=FixedMultiplier(Resolved(multiplier)),
        condition_ids=condition_ids,
        repeat_count=repeat_count,
        repeat_count_condition_id=repeat_count_condition_id,
    )


def _move(
    relation: MultiplierRelation,
    variants: tuple[MultiplierVariant, ...],
    *,
    diagnostics: tuple[CalculationDiagnostic, ...] = (),
    stage_index: int | None = None,
    derived: tuple[DamageEventTemplateRef, ...] = (),
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
        enabled=True,
        effects=(effect,),
        stack_count=2,
        stack_min=0,
        stack_max=3,
    )

    assert item.active_effects == (effect,)
    disabled = replace(item, enabled=False)
    assert disabled.active_effects == ()

    with pytest.raises(ValueError, match="ineligible"):
        CalculationRuleItem(
            rule_id=RuleItemId("rule:invalid"),
            owner=owner,
            source=_source(),
            display_name="Invalid rule",
            original_text="Invalid rule text",
            eligibility=RuleEligibility.INELIGIBLE,
            enabled=True,
        )

    with pytest.raises(ValueError, match="within its legal bounds"):
        CalculationRuleItem(
            rule_id=RuleItemId("rule:invalid-stack"),
            owner=owner,
            source=_source(),
            display_name="Invalid stack",
            original_text="Invalid stack text",
            eligibility=RuleEligibility.ELIGIBLE,
            enabled=True,
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
        (_variant("per-projectile", repeat_count=3),),
    )

    assert (
        isinstance(complete.multiplier_variants[0].multiplier, FixedMultiplier)
    )
    assert isinstance(complete.multiplier_variants[0].multiplier.value, Resolved)
    assert complete.multiplier_variants[0].multiplier.value.value == 1.0
    assert stage.stage_index == 2
    assert len(variants.multiplier_variants) == 2
    assert repeat.multiplier_variants[0].repeat_count == 3


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
        derived=(_event_ref("event:derived", label="extra damage"),),
    )

    assert move.main_damage_event.event_kind is BattleEventKind.DAMAGE
    assert move.derived_damage_events[0].label == "extra damage"

    with pytest.raises(ValueError, match="semantic IDs"):
        _move(
            MultiplierRelation.COMPLETE,
            (_variant("duplicate"),),
            derived=(_event_ref("event:main"),),
        )


def test_move_output_distinguishes_complete_and_known_partial_totals() -> None:
    complete_event = DamageEventCalculationOutput(
        semantic_id=DamageEventSemanticId("event:main"),
        label="main",
        damage_type=DamageType.DIRECT,
        damage_subtype=None,
        status=EventCalculationStatus.CALCULATED,
        result=CalculationResult(value=100.0, breakdown=()),
    )
    complete = MoveCalculationOutput(
        move_entry_id=MoveEntryId("move-entry:test"),
        crit_display_mode=CritDisplayMode.EXPECTED,
        events=(complete_event,),
        known_total=100.0,
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
        known_total=100.0,
        complete=False,
        diagnostics=(_diagnostic("diagnostic:partial", blocking=True),),
    )

    assert complete.complete is True
    assert complete.known_total == 100.0
    assert partial.complete is False
    assert partial.known_total == 100.0
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
