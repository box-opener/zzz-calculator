"""Direct move application service for the static calculation pipeline."""

from __future__ import annotations

from dataclasses import replace
from math import floor

from core.types import (
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AnomalyRecord,
    AnomalySourceChoice,
    ANOMALY_ELEMENTS,
    AttributeAnomalyDamageEvent,
    anomaly_source_record_id,
    BattleEventKind,
    CalculationContext,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    DamageEvent,
    DamageEventId,
    DamageEventMetadata,
    DischargeDamageEvent,
    DamageSubtype,
    DamageMultiplier,
    DamageType,
    CurrentPenetrationForceValueSource,
    DirectDamageEvent,
    DisorderDamageEvent,
    PolarDisorderDamageEvent,
    PenetrationDamageEvent,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectTarget,
    FixedMultiplier,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    Element,
    IndependentAnomalyCrit,
    IndependentAnomalyCritRule,
    NoAnomalyCrit,
    ModifierEffect,
    NoCritRule,
    LuminanceSourceChoice,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    LuminanceSourceKind,
    LuminanceSpecialSourceId,
    LuminanceSpecialSourceSnapshot,
    RecordedAnomalyCritRule,
    Resolved,
    StandardCritRule,
    SnapshotRule,
    TurbulenceDamageEvent,
    Unresolved,
    UnresolvedReason,
)

from ..matching import (
    EffectMatchStatus,
    EffectMatchContext,
    EffectMatcher,
    RuleItemMatchResult,
)

from ..characters.definition import CharacterCalculationDefinition
from ..characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
    DirectDamageEventTemplate,
    DischargeDamageEventTemplate,
    LuminanceFlareDamageEventTemplate,
    DisorderDamageEventTemplate,
    TurbulenceDamageEventTemplate,
    PolarDisorderDamageEventTemplate,
)
from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DamageEventSemanticId, DiagnosticId, MoveEntryId
from ..moves import DerivedDamageEventTemplateRef, MoveCalculationEntry
from ..scenario import ScenarioRuleStack
from ..rules import CalculationRuleItem, RuleEligibility
from ..output import (
    CritCapability,
    CritDisplayMode,
    DamageEventCalculationOutput,
    EventCalculationStatus,
    MoveCalculationOutput,
)
from .contracts import (
    DamageEventExecutionTrace,
    EventStatModifier,
    HistoryRecordMode,
    InstantiatedDamageEvent,
    MoveCalculationExecution,
    MoveCalculationRequest,
)
from .event_factory import instantiate_damage_event
from .modifiers import (
    MatchedEffectApplication,
    ModifierApplicationResult,
    apply_global_panel_effects,
    apply_matched_modifiers,
)
from .multiplier import (
    MultiplierResolutionStatus,
    resolve_move_multiplier,
)
from .router import CalculationRouter, CalculatorExecutionResult
from .static_records import (
    static_anomaly_effect_strength_source,
    static_attribute_anomaly_record,
)


def _anomaly_tick_multiplier(
    instantiated: InstantiatedDamageEvent,
) -> DamageMultiplier:
    """Carry one source damage tick into a Discharge child.

    The source event's repeat count describes its total periodic damage. A
    Discharge hit inherits the per-tick multiplier, never the source duration's
    accumulated total.
    """

    return instantiated.event.multiplier


def _turbulence_multiplier_for_history(record: AnomalyRecord) -> float | None:
    """Use the selected static record's full remaining duration for Turbulence.

    Static single-character records carry the maximum current duration. The
    service does not replay duration or anomaly timing; explicit callers may
    provide a record whose duration represents the duration available at the
    trigger.
    """

    duration = record.duration
    if not isinstance(duration, Resolved):
        return None
    seconds = max(float(duration.value), 0.0)
    element = record.element
    if element in {Element.PHYSICAL, Element.LINREN}:
        return 8.0 + floor(seconds + 1e-9) * 0.075
    if element is Element.ICE:
        return 13.0 + floor(seconds + 1e-9) * 0.075
    if element is Element.LIESHUANG:
        return floor(seconds + 1e-9) * 0.75
    if element is Element.FIRE:
        return 9.0 + floor(seconds / 0.5 + 1e-9) * 0.50
    if element is Element.ELECTRIC:
        return 6.5 + floor(seconds + 1e-9) * 1.25
    if element in {Element.ETHER, Element.XUANMO}:
        return 6.5 + floor(seconds / 0.5 + 1e-9) * 0.625
    return None


class DirectMoveApplicationService:
    """Apply matched direct-damage rules and invoke the pure calculator."""

    def __init__(
        self,
        matcher: EffectMatcher | None = None,
        router: CalculationRouter | None = None,
    ) -> None:
        self._matcher = matcher or EffectMatcher()
        self._router = router or CalculationRouter()

    def calculate(self, request: MoveCalculationRequest) -> MoveCalculationExecution:
        entry = _find_entry(request.definition, request.move_entry_id)
        if entry is None:
            diagnostic = _diagnostic(
                str(request.move_entry_id),
                "missing-move-entry",
                DiagnosticKind.MISSING_DATA,
                "requested MoveEntryId is not present in the definition",
            )
            return _execution_without_events(request, diagnostic)

        definitions = _all_definitions(request)
        rule_items = _all_rule_items(request)
        request = replace(
            request,
            scenario=_materialize_rule_stack_defaults(request.scenario, rule_items),
        )

        multiplier = resolve_move_multiplier(entry, request.scenario)
        if multiplier.status is not MultiplierResolutionStatus.RESOLVED:
            return _execution_without_events(
                request,
                *multiplier.diagnostics,
            )
        assert multiplier.multiplier is not None

        main_template = _find_template(request, entry.main_damage_event.template_id)
        if main_template is None:
            diagnostic = _diagnostic(
                str(entry.main_damage_event.template_id),
                "missing-template",
                DiagnosticKind.MISSING_DATA,
                "main MoveEntry template is not present in the definition",
            )
            return _execution_without_events(request, diagnostic)

        main_repeat_count = multiplier.repeat_count
        if isinstance(main_template, LuminanceFlareDamageEventTemplate):
            repeat_rule_id = main_template.repeat_count_rule_item_id
            repeat_rule = next(
                (item for item in rule_items if item.rule_id == repeat_rule_id),
                None,
            ) if repeat_rule_id is not None else None
            if (
                repeat_rule is not None
                and repeat_rule.eligibility is not RuleEligibility.INELIGIBLE
                and repeat_rule.rule_id in request.scenario.enabled_rule_item_ids
            ):
                main_repeat_count = 2

        global_panel_application = apply_global_panel_effects(
            request.base_character_snapshots,
            request.initial_character_snapshots,
            rule_items,
            request.scenario,
            frozenset(profile.character_id for profile in request.team_profiles),
        )
        source_diagnostics: tuple[CalculationDiagnostic, ...] = ()
        special_source = None
        if isinstance(main_template, LuminanceFlareDamageEventTemplate):
            if request.luminance_source_choice is None:
                return MoveCalculationExecution(
                    output=MoveCalculationOutput(
                        move_entry_id=entry.entry_id,
                        crit_display_mode=request.crit_display_mode,
                        events=(),
                        known_total=0.0,
                        complete=True,
                        diagnostics=(),
                    ),
                    resolved_character_snapshots=global_panel_application.character_snapshots,
                    event_traces=(),
                    panel_traces=global_panel_application.panel_traces,
                )
            request, special_source, source_diagnostics = _prepare_remielle_flare_source(
                request,
                main_template,
                global_panel_application.character_snapshots,
                rule_items,
                self._matcher,
                global_panel_application.applied_panel_effect_ids,
            )
        if request.burnice_anomaly_source_choice is not None:
            has_reviewed_burnice_discharge = any(
                isinstance(template, DischargeDamageEventTemplate)
                and template.source_multiplier_by_element
                for definition in _all_definitions(request)
                for template in definition.damage_event_templates
            )
            if not has_reviewed_burnice_discharge:
                return _execution_without_events(
                    request,
                    _diagnostic(
                        str(request.move_entry_id),
                        "burnice-source-on-non-discharge",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "A selected Burnice anomaly source is valid only for the Potential 1 Special Throw Discharge entry.",
                    ),
                )
            request, burnice_source_diagnostics = _prepare_burnice_anomaly_source(
                request,
                global_panel_application.character_snapshots,
                rule_items,
                self._matcher,
                global_panel_application.applied_panel_effect_ids,
            )
            source_diagnostics = (*source_diagnostics, *burnice_source_diagnostics)
        if request.grace_anomaly_source_choice is not None:
            has_grace_source_discharge = any(
                isinstance(template, DischargeDamageEventTemplate)
                and template.source_multiplier_by_element
                for definition in _all_definitions(request)
                if definition.character_id == CharacterId("character:1181")
                for template in definition.damage_event_templates
            )
            if request.definition.character_id != CharacterId("character:1181") or not has_grace_source_discharge:
                return _execution_without_events(
                    request,
                    _diagnostic(
                        str(request.move_entry_id),
                        "grace-source-on-non-discharge",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "A selected Grace anomaly source is valid only for the Potential 1 Pulse Grenade Discharge entry.",
                    ),
                )
            request, grace_source_diagnostics = _prepare_grace_anomaly_source(
                request,
                global_panel_application.character_snapshots,
                rule_items,
                self._matcher,
                global_panel_application.applied_panel_effect_ids,
            )
            source_diagnostics = (*source_diagnostics, *grace_source_diagnostics)
        main_event = instantiate_damage_event(
            main_template,
            multiplier.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            repeat_count=main_repeat_count,
            luminance_source_choice=request.luminance_source_choice,
            luminance_special_source=special_source,
            burnice_anomaly_source_choice=request.burnice_anomaly_source_choice,
            grace_anomaly_source_choice=request.grace_anomaly_source_choice,
        )
        # Static browser requests need an identity-only record before matching
        # (ANOMALY_CONTRIBUTORS can be a filter).  This is deliberately gated
        # by an explicit request mode; normal application callers must provide
        # their own history records.
        identity_history, identity_diagnostics = _history_records_for_event(
            request,
            main_event.event,
            global_panel_application.character_snapshots,
            (),
            matcher=self._matcher,
            rule_items=rule_items,
            applied_panel_effect_ids=global_panel_application.applied_panel_effect_ids,
        )
        identity_diagnostics = (*source_diagnostics, *identity_diagnostics)
        identity_request = replace(request, history_records=identity_history)
        main_context = _match_context(
            identity_request,
            main_event.event,
            global_panel_application.character_snapshots,
            request.base_calculation_modifiers,
            current_template_id=main_event.template_id,
        )
        main_matches = self._matcher.match_rule_items(rule_items, main_context)
        non_stacking_event_diagnostics: list[CalculationDiagnostic] = []
        matched_effects = _matched_effects(
            main_matches,
            rule_items,
            request.scenario,
            diagnostics=non_stacking_event_diagnostics,
        )
        panel_application = apply_matched_modifiers(
            global_panel_application.character_snapshots,
            request.base_calculation_modifiers,
            matched_effects,
            request.scenario.current_operator,
            initial_character_snapshots=request.initial_character_snapshots,
            scenario=request.scenario,
            event=main_event.event,
            apply_panel=False,
            applied_panel_effect_ids=global_panel_application.applied_panel_effect_ids,
        )
        if non_stacking_event_diagnostics:
            panel_application = replace(
                panel_application,
                diagnostics=(
                    *panel_application.diagnostics,
                    *non_stacking_event_diagnostics,
                ),
            )
        panel_application = _merge_modifier_applications(
            global_panel_application,
            panel_application,
        )
        # Event-level normal/anomaly bonuses belong to the completed record,
        # while defense/resistance/vulnerability remain calculator regions.
        # Build the final record once from the same settlement snapshots used
        # by the calculator and make it available to derived events too.
        final_history, final_diagnostics = _history_records_for_event(
            request,
            main_event.event,
            panel_application.character_snapshots,
            panel_application.event_modifiers,
            matcher=self._matcher,
            rule_items=rule_items,
            applied_panel_effect_ids=panel_application.applied_panel_effect_ids,
        )
        request = replace(request, history_records=final_history)
        if request.history_record_mode is HistoryRecordMode.STATIC_SINGLE_CHARACTER:
            main_event = _bind_static_anomaly_crit(main_event, final_history)
        if identity_diagnostics or final_diagnostics:
            panel_application = replace(
                panel_application,
                diagnostics=(
                    *panel_application.diagnostics,
                    *identity_diagnostics,
                    *final_diagnostics,
                ),
            )

        event_outputs: list[DamageEventCalculationOutput] = []
        traces: list[DamageEventExecutionTrace] = []
        move_diagnostics: list[CalculationDiagnostic] = [
            *multiplier.diagnostics,
            *(
                diagnostic
                for rule in rule_items
                if rule.rule_id in request.scenario.enabled_rule_item_ids
                and rule.eligibility is not RuleEligibility.INELIGIBLE
                for diagnostic in rule.diagnostics
            ),
        ]
        queue: list[
            tuple[
                InstantiatedDamageEvent,
                tuple[EventTemplateId, ...],
                tuple[RuleItemMatchResult, ...],
                ModifierApplicationResult,
            ]
        ] = [(main_event, (main_event.template_id,), main_matches, panel_application)]
        seen_semantics = {main_event.semantic_id}
        settled_damage_values = {}
        replace_disorder_with_turbulence = False
        turbulence_lineage: dict[DamageEventSemanticId, DamageEventSemanticId] = {}
        while queue:
            instantiated, ancestry, matches, application = queue.pop(0)
            event_diagnostics = list(application.diagnostics)
            event_diagnostics.extend(_match_diagnostics(matches))
            calculation = self._calculate_event(
                request,
                instantiated,
                application,
                event_diagnostics,
                settled_damage_values,
            )
            event_outputs.append(calculation[0])
            traces.append(
                DamageEventExecutionTrace(
                    semantic_id=instantiated.semantic_id,
                    rule_matches=matches,
                    applied_modifiers=application.event_modifiers,
                    event_stat_modifiers=application.event_stat_modifiers,
                    event_multiplier_modifiers=application.event_multiplier_modifiers,
                    guaranteed_crit_effect_ids=(
                        application.event_crit_guarantee_effect_ids
                    ),
                    created_by_effect_id=instantiated.created_by_effect_id,
                    diagnostics=calculation[2],
                    base_source_character_id=getattr(
                        getattr(
                            instantiated.event,
                            "base_settlement_data_source",
                            getattr(instantiated.event, "source_snapshot", None),
                        ),
                        "character_id",
                        getattr(
                            getattr(instantiated.event, "source_snapshot", None),
                            "source_character_id",
                            None,
                        ),
                    ),
                    base_source_effect_ids=tuple(
                        getattr(
                            getattr(instantiated.event, "base_settlement_data_source", None),
                            "source_effect_ids",
                            (),
                        )
                    ),
                )
            )
            move_diagnostics.extend(calculation[2])
            if calculation[0].result is not None and calculation[0].result.value is not None:
                settled_damage_values[instantiated.event.metadata.event_id] = Resolved(
                    calculation[0].result.value
                )

            event_creation_applications = list(
                _matched_event_creations(matches, rule_items, request.scenario)
            )
            if instantiated.template_id == main_event.template_id:
                event_creation_applications.extend(
                    _required_event_creation_applications(
                        entry,
                        request.definition,
                    )
                )
            for effect_application in event_creation_applications:
                if effect_application.stack_count != 1:
                    move_diagnostics.append(
                        _diagnostic(
                            str(effect_application.effect.rule.effect_id),
                            "stack-event-creation",
                            DiagnosticKind.AMBIGUOUS_SEMANTICS,
                            "stacked EventCreation effects are unsupported",
                        )
                    )
                    continue
                if not isinstance(effect_application.effect, EventCreationEffect):
                    continue
                child_template = (
                    _find_template(
                        request,
                        effect_application.effect.result.event_template_id,
                    )
                    if effect_application.effect.result.event_template_id is not None
                    else None
                )
                if (
                    isinstance(instantiated.event, DisorderDamageEvent)
                    and isinstance(child_template, TurbulenceDamageEventTemplate)
                ):
                    # Winded targets receive the legal Wind-triggered
                    # Turbulence settlement in place of ordinary Disorder.
                    replace_disorder_with_turbulence = True
                turbulence_parent = (
                    instantiated.semantic_id
                    if isinstance(instantiated.event, TurbulenceDamageEvent)
                    else turbulence_lineage.get(instantiated.semantic_id)
                )
                created = self._create_derived_event(
                    request,
                    effect_application.effect,
                    ancestry,
                    seen_semantics,
                    current_character_snapshots=application.character_snapshots,
                    source_event_id=instantiated.event.metadata.event_id,
                    source_history_record_id=(
                        instantiated.event.history_record_source
                        if isinstance(
                            instantiated.event,
                            (AttributeAnomalyDamageEvent, DisorderDamageEvent),
                        )
                        else None
                    ),
                    source_anomaly_multiplier=(
                        _anomaly_tick_multiplier(instantiated)
                        if isinstance(instantiated.event, AttributeAnomalyDamageEvent)
                        else None
                    ),
                    required_component=effect_application.rule_item_id is None,
                )
                if isinstance(created, CalculationDiagnostic):
                    move_diagnostics.append(created)
                    continue
                if created is None:
                    continue
                child, child_ancestry = created
                if turbulence_parent is not None:
                    turbulence_lineage[child.semantic_id] = turbulence_parent
                if isinstance(child.event, PolarDisorderDamageEvent):
                    request, polar_source_diagnostics = _prepare_polar_anomaly_source(
                        request,
                        application.character_snapshots,
                        rule_items,
                        self._matcher,
                        application.applied_panel_effect_ids,
                    )
                    move_diagnostics.extend(polar_source_diagnostics)
                child_history, child_history_diagnostics = _history_records_for_event(
                    request,
                    child.event,
                    application.character_snapshots,
                    (),
                    matcher=self._matcher,
                    rule_items=rule_items,
                    applied_panel_effect_ids=application.applied_panel_effect_ids,
                )
                request = replace(request, history_records=child_history)
                if request.history_record_mode is HistoryRecordMode.STATIC_SINGLE_CHARACTER:
                    child = _bind_static_anomaly_crit(child, child_history)
                move_diagnostics.extend(child_history_diagnostics)
                seen_semantics.add(child.semantic_id)
                child_context = _match_context(
                    request,
                    child.event,
                    application.character_snapshots,
                    request.base_calculation_modifiers,
                    created_by_effect_id=child.created_by_effect_id,
                    current_template_id=child.template_id,
                )
                child_matches = self._matcher.match_rule_items(
                    rule_items, child_context
                )
                child_non_stacking_diagnostics: list[CalculationDiagnostic] = []
                child_application = apply_matched_modifiers(
                    application.character_snapshots,
                    request.base_calculation_modifiers,
                    _matched_effects(
                        child_matches,
                        rule_items,
                        request.scenario,
                        diagnostics=child_non_stacking_diagnostics,
                    ),
                    request.scenario.current_operator,
                    initial_character_snapshots=request.initial_character_snapshots,
                    scenario=request.scenario,
                    event=child.event,
                    apply_panel=False,
                    applied_panel_effect_ids=panel_application.applied_panel_effect_ids,
                )
                if child_non_stacking_diagnostics:
                    child_application = replace(
                        child_application,
                        diagnostics=(
                            *child_application.diagnostics,
                            *child_non_stacking_diagnostics,
                        ),
                    )
                queue.append((child, child_ancestry, child_matches, child_application))

        if replace_disorder_with_turbulence:
            turbulence_outputs = [
                item
                for item in event_outputs
                if item.damage_subtype is DamageSubtype.TURBULENCE
            ]
            non_turbulence_outputs = [
                item
                for item in event_outputs
                if item.damage_subtype is not DamageSubtype.TURBULENCE
                and item.damage_type is not DamageType.DISORDER
                and item.semantic_id not in turbulence_lineage
            ]
            selected_turbulence = None
            if turbulence_outputs:
                calculated_turbulence = [
                    item
                    for item in turbulence_outputs
                    if item.status is EventCalculationStatus.CALCULATED
                    and item.known_value is not None
                ]
                if calculated_turbulence:
                    selected_turbulence = max(
                        calculated_turbulence,
                        key=lambda item: (item.known_value, str(item.semantic_id)),
                    )
                if len(calculated_turbulence) != len(turbulence_outputs):
                    move_diagnostics.append(
                        _diagnostic(
                            str(entry.entry_id),
                            "turbulence-candidate-maximum",
                            DiagnosticKind.MISSING_DATA,
                            "One or more legal Wind Turbulence candidates are unresolved, "
                            "so the maximum candidate cannot be confirmed.",
                        )
                    )
            if selected_turbulence is None:
                event_outputs = non_turbulence_outputs
            else:
                selected_candidate_id = selected_turbulence.semantic_id
                event_outputs = [
                    *non_turbulence_outputs,
                    *(
                        item
                        for item in turbulence_outputs
                        if item.semantic_id == selected_candidate_id
                    ),
                    *(
                        item
                        for item in event_outputs
                        if turbulence_lineage.get(item.semantic_id)
                        == selected_candidate_id
                    ),
                ]
            visible_semantics = {item.semantic_id for item in event_outputs}
            traces = [
                trace
                for trace in traces
                if trace.semantic_id in visible_semantics
            ]

        known_values = [
            item.known_value
            for item in event_outputs
            if item.status is EventCalculationStatus.CALCULATED
            and item.known_value is not None
        ]
        known_total = sum(known_values) if known_values else None
        complete = (
            bool(event_outputs)
            and all(
                item.status is EventCalculationStatus.CALCULATED
                for item in event_outputs
            )
            and not any(item.blocking for item in move_diagnostics)
        )
        output = MoveCalculationOutput(
            move_entry_id=entry.entry_id,
            crit_display_mode=request.crit_display_mode,
            events=tuple(event_outputs),
            known_total=known_total,
            complete=complete,
            diagnostics=tuple(move_diagnostics),
        )
        return MoveCalculationExecution(
            output=output,
            resolved_character_snapshots=panel_application.character_snapshots,
            event_traces=tuple(traces),
            panel_traces=panel_application.panel_traces,
        )

    def _calculate_event(
        self,
        request: MoveCalculationRequest,
        instantiated: InstantiatedDamageEvent,
        application: ModifierApplicationResult,
        event_diagnostics: list[CalculationDiagnostic],
        settled_damage_values,
    ) -> tuple[
        DamageEventCalculationOutput,
        CalculatorExecutionResult,
        tuple[CalculationDiagnostic, ...],
    ]:
        diagnostics_list = list(event_diagnostics)
        calculation_event = _apply_guaranteed_crit_effects(
            instantiated.event,
            application.event_crit_guarantee_effect_ids,
            diagnostics_list,
        )
        calculation_event = _apply_event_multiplier_modifiers(
            calculation_event,
            application.event_multiplier_modifiers,
            diagnostics_list,
        )
        event_stat_snapshots = _apply_event_stat_modifiers(
            application.character_snapshots,
            application.event_stat_modifiers,
            diagnostics_list,
        )
        diagnostics = tuple(diagnostics_list)
        if any(item.blocking for item in diagnostics):
            output = DamageEventCalculationOutput(
                semantic_id=instantiated.semantic_id,
                label=instantiated.label,
                damage_type=calculation_event.damage_type,
                damage_subtype=calculation_event.damage_subtype,
                element=calculation_event.metadata.element,
                status=EventCalculationStatus.BLOCKED,
                diagnostics=diagnostics,
                repeat_count=instantiated.repeat_count,
                crit_capability=_crit_capability(calculation_event),
            )
            return (
                output,
                CalculatorExecutionResult(EventCalculationStatus.BLOCKED),
                diagnostics,
            )

        display_snapshots = _display_snapshots(
            event_stat_snapshots,
            calculation_event,
            request.crit_display_mode,
        )
        context = CalculationContext(
            event=calculation_event,
            battle_state_id=request.battle_state_id,
            character_snapshots=display_snapshots,
            target_snapshot=request.target_snapshot,
            modifiers=(
                (*application.event_modifiers, *application.event_multiplier_modifiers)
                if isinstance(
                    calculation_event,
                    (LuminanceDamageEvent, SpecialLuminanceDamageEvent),
                )
                else application.event_modifiers
            ),
            history_records=request.history_records,
            vulnerability_policy=application.vulnerability_policy,
            settled_damage_values=settled_damage_values,
        )
        calculation = self._router.calculate(calculation_event, context)
        all_diagnostics = diagnostics + calculation.diagnostics
        output = DamageEventCalculationOutput(
            semantic_id=instantiated.semantic_id,
            label=instantiated.label,
            damage_type=calculation_event.damage_type,
            damage_subtype=calculation_event.damage_subtype,
            element=calculation_event.metadata.element,
            status=calculation.status,
            result=calculation.result,
            diagnostics=all_diagnostics,
            repeat_count=instantiated.repeat_count,
            crit_capability=_crit_capability(calculation_event),
        )
        return output, calculation, all_diagnostics

    def _create_derived_event(
        self,
        request: MoveCalculationRequest,
        effect: EventCreationEffect,
        ancestry: tuple[EventTemplateId, ...],
        seen_semantics,
        *,
        current_character_snapshots: tuple[CharacterSnapshot, ...] = (),
        source_event_id: DamageEventId | None = None,
        source_history_record_id: AnomalyRecordId | None = None,
        source_anomaly_multiplier: DamageMultiplier | None = None,
        required_component: bool = False,
    ) -> (
        tuple[InstantiatedDamageEvent, tuple[EventTemplateId, ...]]
        | CalculationDiagnostic
        | None
    ):
        if effect.result.event_kind is not BattleEventKind.DAMAGE:
            return _diagnostic(
                str(effect.rule.effect_id),
                "unsupported-event-kind",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "Stage-015 only instantiates damage EventCreation results",
            )
        template_id = effect.result.event_template_id
        if template_id is None:
            unresolved = effect.result.unresolved_template
            unresolved_reason = unresolved.reason if unresolved is not None else None
            diagnostic_kind = (
                DiagnosticKind.AMBIGUOUS_SEMANTICS
                if unresolved_reason
                in {
                    UnresolvedReason.AMBIGUOUS_TEXT,
                    UnresolvedReason.AMBIGUOUS_IDENTITY,
                    UnresolvedReason.AMBIGUOUS_ORDERING,
                }
                else DiagnosticKind.UNSUPPORTED_CALCULATOR
                if unresolved_reason
                in {
                    UnresolvedReason.MISSING_SPEC_RULE,
                    UnresolvedReason.NOT_IMPLEMENTED_IN_SPEC,
                }
                else DiagnosticKind.MISSING_DATA
            )
            return _diagnostic(
                str(effect.rule.effect_id),
                "unresolved-template",
                diagnostic_kind,
                (
                    unresolved.notes
                    if unresolved is not None
                    else "event template is unresolved"
                ),
                original_text=(
                    unresolved.original_text if unresolved is not None else None
                ),
                candidates=(
                    unresolved.candidates if unresolved is not None else ()
                ),
            )
        if template_id in ancestry:
            return _diagnostic(
                str(effect.rule.effect_id),
                "event-cycle",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "EventCreation re-entered a template in its ancestry",
            )
        definitions = _all_definitions(request)
        derived_ref = _find_derived_ref(request, template_id)
        if derived_ref is None:
            return _diagnostic(
                str(template_id),
                "missing-derived-reference",
                DiagnosticKind.MISSING_DATA,
                "EventCreation template has no DerivedDamageEventTemplateRef",
            )
        template = _find_template(request, template_id)
        if template is None:
            return _diagnostic(
                str(template_id),
                "missing-template",
                DiagnosticKind.MISSING_DATA,
                "EventCreation template is not registered",
            )
        if (
            isinstance(template, PolarDisorderDamageEventTemplate)
            and request.polarity_anomaly_source_choice is None
        ):
            return _diagnostic(
                str(effect.rule.effect_id),
                "polar-source-choice",
                DiagnosticKind.MISSING_DATA,
                "Select one active ordinary anomaly source for Polar Disorder.",
            )
        if (
            isinstance(template, DirectDamageEventTemplate)
            and template.allow_external_base_source
            and isinstance(template.base_source, CurrentPenetrationForceValueSource)
        ):
            template = self._resolve_external_penetration_force_source(
                request,
                template,
                current_character_snapshots,
            )
        repeat_count = derived_ref.repeat_count
        if derived_ref.repeat_count_parameter_id is not None:
            parameter = next(
                (
                    item
                    for item in request.scenario.parameters
                    if item.parameter_id == derived_ref.repeat_count_parameter_id
                ),
                None,
            )
            if parameter is None or parameter.value is None:
                return _diagnostic(
                    str(derived_ref.repeat_count_parameter_id),
                    "repeat-count-unresolved",
                    DiagnosticKind.MISSING_DATA,
                    "derived event repeat-count parameter is unresolved",
                )
            repeat_count = parameter.value
        if repeat_count == 0 and derived_ref.skip_when_repeat_count_zero:
            return None
        instance_semantic_id = derived_ref.semantic_id
        if effect.result.unique_per_source_event:
            if source_event_id is None:
                return _diagnostic(
                    str(effect.rule.effect_id),
                    "source-event-identity",
                    DiagnosticKind.MISSING_DATA,
                    "this EventCreation requires a source-event identity for its generated instance",
                )
            instance_semantic_id = DamageEventSemanticId(
                f"{derived_ref.semantic_id}:source:{source_event_id}"
            )
        if instance_semantic_id in seen_semantics:
            return _diagnostic(
                str(instance_semantic_id),
                "duplicate-semantic-event",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "the same semantic event was created more than once",
            )
        instance_template = (
            replace(
                template,
                ref=replace(template.ref, semantic_id=instance_semantic_id),
            )
            if instance_semantic_id != template.ref.semantic_id
            else template
        )
        instance_multiplier = derived_ref.multiplier
        turbulence_crit_rule = None
        turbulence_element = None
        if isinstance(instance_template, TurbulenceDamageEventTemplate):
            record_id = (
                instance_template.history_record_source
                or source_history_record_id
            )
            if record_id is None:
                return _diagnostic(
                    str(effect.rule.effect_id),
                    "turbulence-source-record",
                    DiagnosticKind.MISSING_DATA,
                    "Turbulence requires a typed non-Wind AnomalyRecord source.",
                )
            source_records = tuple(
                item for item in request.history_records if item.record_id == record_id
            )
            if len(source_records) != 1:
                return _diagnostic(
                    str(record_id),
                    "turbulence-source-record",
                    DiagnosticKind.MISSING_DATA,
                    "Turbulence requires exactly one matching non-Wind AnomalyRecord.",
                )
            source_record = source_records[0]
            turbulence_element = source_record.element
            if source_record.element is Element.WIND:
                return _diagnostic(
                    str(record_id),
                    "turbulence-wind-source",
                    DiagnosticKind.MISSING_DATA,
                    "Turbulence cannot use a Wind Weathering record as its source.",
                )
            turbulence_multiplier = _turbulence_multiplier_for_history(source_record)
            if turbulence_multiplier is None:
                return _diagnostic(
                    str(record_id),
                    "turbulence-source-duration",
                    DiagnosticKind.MISSING_DATA,
                    "The source AnomalyRecord duration is unresolved, so the "
                    "Turbulence remaining-time multiplier cannot be calculated.",
                )
            stack_parameter_id = instance_template.wind_erosion_stack_parameter_id
            if stack_parameter_id is not None:
                stack_parameter = next(
                    (
                        item
                        for item in request.scenario.parameters
                        if item.parameter_id == stack_parameter_id
                    ),
                    None,
                )
                if stack_parameter is None or stack_parameter.value is None:
                    return _diagnostic(
                        str(stack_parameter_id),
                        "turbulence-wind-erosion-stacks",
                        DiagnosticKind.MISSING_DATA,
                        "Current Wind Erosion stacks are required for Velina's "
                        "conditional Turbulence multiplier.",
                    )
                if stack_parameter.value >= instance_template.enhanced_at_stack_count:
                    turbulence_multiplier += instance_template.core_turbulence_bonus
            instance_multiplier = FixedMultiplier(Resolved(turbulence_multiplier))
            capability = source_record.crit_capability
            if isinstance(capability, IndependentAnomalyCrit) and (
                DamageSubtype.TURBULENCE in capability.inherited_by
            ):
                turbulence_crit_rule = RecordedAnomalyCritRule(
                    record_id=source_record.record_id,
                    capability=capability,
                )
            else:
                turbulence_crit_rule = NoCritRule()
        child = instantiate_damage_event(
            instance_template,
            instance_multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            source_rule_item_id=template.ref.source_rule_item_id,
            created_by_effect_id=(
                None if required_component else effect.rule.effect_id
            ),
            repeat_count=repeat_count,
            source_event_id=source_event_id,
            source_history_record_id=source_history_record_id,
            source_anomaly_multiplier=source_anomaly_multiplier,
            turbulence_crit_rule=turbulence_crit_rule,
            turbulence_element=turbulence_element,
            polarity_anomaly_source_choice=request.polarity_anomaly_source_choice,
            burnice_anomaly_source_choice=request.burnice_anomaly_source_choice,
            grace_anomaly_source_choice=request.grace_anomaly_source_choice,
        )
        return child, (*ancestry, template_id)

    def _resolve_external_penetration_force_source(
        self,
        request: MoveCalculationRequest,
        template: DirectDamageEventTemplate,
        current_character_snapshots: tuple[CharacterSnapshot, ...],
    ) -> DirectDamageEventTemplate:
        """Read the previous teammate's current Force without changing the dealer.

        Penetration Force bonuses are matched against a typed, identity-only
        Penetration context for that source owner. The resulting bonus is folded
        into the Direct child event's base Force source; its damage dealer,
        element, crit owner, and ordinary damage regions remain Dialyn's.
        """

        base_source = template.base_source
        assert isinstance(base_source, CurrentPenetrationForceValueSource)
        definitions = _all_definitions(request)
        source_definition = next(
            (
                item for item in definitions
                if item.character_id == base_source.character_id
            ),
            None,
        )
        if source_definition is None:
            return replace(
                template,
                base_source=replace(
                    base_source,
                    additional_force=Unresolved(
                        reason=UnresolvedReason.MISSING_DATA,
                        notes=(
                            "The previous teammate's compiled definition is required "
                            "to resolve current Penetration Force bonuses."
                        ),
                    ),
                ),
            )

        synthetic_source_event = PenetrationDamageEvent(
            metadata=DamageEventMetadata(
                event_id=DamageEventId(
                    f"event:{request.battle_state_id}:source-force:{base_source.character_id}"
                ),
                battle_state_id=request.battle_state_id,
                damage_dealer=base_source.character_id,
                target_enemy=request.target_snapshot.enemy_id,
                element=source_definition.base_element,
                created_at=request.battle_time,
            ),
            base_settlement_data_source=CurrentPenetrationForceValueSource(
                base_source.character_id
            ),
            multiplier=FixedMultiplier(Resolved(1.0)),
            crit_rule=StandardCritRule(base_source.character_id),
        )
        rule_items = _all_rule_items(request)
        source_context = _match_context(
            request,
            synthetic_source_event,
            current_character_snapshots,
            request.base_calculation_modifiers,
        )
        matches = self._matcher.match_rule_items(rule_items, source_context)
        source_force_rule_ids = {
            rule.rule_id
            for rule in rule_items
            if any(
                isinstance(effect, ModifierEffect)
                and effect.result.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS
                for effect in rule.effects
            )
        }
        source_force_effects = tuple(
            application
            for application in _matched_effects(matches, rule_items, request.scenario)
            if isinstance(application.effect, ModifierEffect)
            and application.effect.result.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS
        )
        source_force_effect_ids = tuple(
            application.effect.rule.effect_id
            for application in source_force_effects
        )
        source_application = apply_matched_modifiers(
            current_character_snapshots,
            request.base_calculation_modifiers,
            source_force_effects,
            request.scenario.current_operator,
            initial_character_snapshots=request.initial_character_snapshots,
            scenario=request.scenario,
            event=synthetic_source_event,
            apply_panel=False,
        )
        blocked_force_diagnostics = tuple(
            diagnostic
            for match in matches
            if match.rule_id in source_force_rule_ids
            and match.status is EffectMatchStatus.BLOCKED
            for diagnostic in match.diagnostics
        )
        relevant_value_diagnostics = tuple(
            diagnostic
            for diagnostic in source_application.diagnostics
            if any(
                str(effect_id) in str(diagnostic.diagnostic_id)
                for effect_id in source_force_effect_ids
            )
        )
        unresolved_force = (*blocked_force_diagnostics, *relevant_value_diagnostics)
        force_values = tuple(
            modifier.value
            for modifier in source_application.event_modifiers
            if modifier.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS
        )
        if unresolved_force or any(not isinstance(value, Resolved) for value in force_values):
            additional_force = Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=(
                    "The previous teammate's current Penetration Force bonus could not "
                    "be completely resolved from active source-owner effects."
                ),
                original_text="上一位命破队友当前贯穿力及其生效的贯穿力加成",
            )
        else:
            additional_force = Resolved(
                sum(value.value for value in force_values if isinstance(value, Resolved))
            )
        return replace(
            template,
            base_source=replace(
                base_source,
                additional_force=additional_force,
                source_effect_ids=tuple(str(item) for item in source_force_effect_ids),
            ),
        )


def calculate_move(request: MoveCalculationRequest) -> MoveCalculationExecution:
    return DirectMoveApplicationService().calculate(request)


def _find_entry(
    definition: CharacterCalculationDefinition,
    entry_id: MoveEntryId,
) -> MoveCalculationEntry | None:
    return next(
        (item for item in definition.move_entries if item.entry_id == entry_id),
        None,
    )


def _find_template(
    request: MoveCalculationRequest,
    template_id: EventTemplateId,
) -> DamageEventTemplate | None:
    templates = tuple(
        template
        for definition in _all_definitions(request)
        for template in definition.damage_event_templates
    ) + request.additional_damage_event_templates
    return next(
        (
            item
            for item in templates
            if item.ref.template_id == template_id
        ),
        None,
    )


def _find_derived_ref(
    request: MoveCalculationRequest,
    template_id: EventTemplateId,
) -> DerivedDamageEventTemplateRef | None:
    definitions = _all_definitions(request)
    return next(
        (
            item
            for definition in definitions
            for item in definition.independent_derived_damage_events
            if item.template.template_id == template_id
        ),
        None,
    ) or next(
        (
            item
            for definition in definitions
            for entry in definition.move_entries
            for item in entry.derived_damage_events
            if item.template.template_id == template_id
        ),
        None,
    ) or next(
        (
            item
            for item in request.additional_derived_damage_events
            if item.template.template_id == template_id
        ),
        None,
    )


def _matched_effects(
    matches: tuple[RuleItemMatchResult, ...],
    rule_items: tuple,
    scenario,
    *,
    diagnostics: list[CalculationDiagnostic] | None = None,
) -> tuple[MatchedEffectApplication, ...]:
    rules = {item.rule_id: item for item in rule_items}
    applications: list[MatchedEffectApplication] = []
    for item in matches:
        rule = rules[item.rule_id]
        applications.extend(
            MatchedEffectApplication(
                effect=effect,
                rule_item_id=item.rule_id,
                stack_count=_resolved_stack_count(rule, scenario),
                non_stacking_group_id=rule.non_stacking_group_id,
            )
            for effect in item.matched_effects
        )
    return tuple(applications)


def _matched_event_creations(
    matches: tuple[RuleItemMatchResult, ...],
    rule_items: tuple,
    scenario,
) -> tuple[MatchedEffectApplication, ...]:
    return tuple(
        application
        for application in _matched_effects(matches, rule_items, scenario)
        if isinstance(application.effect, EventCreationEffect)
    )


def _required_event_creation_applications(
    entry: MoveCalculationEntry,
    definition: CharacterCalculationDefinition,
) -> tuple[MatchedEffectApplication, ...]:
    """Expose required source components through the normal derived-event path.

    These components are part of the selected move's authored damage packet,
    rather than optional scenario effects. The synthetic effect wrapper keeps
    the ordinary event-instantiation and calculation pipeline while making no
    RuleItem that a caller could disable.
    """

    applications: list[MatchedEffectApplication] = []
    for derived in entry.derived_damage_events:
        if not derived.required:
            continue
        effect_id = EffectId(
            f"effect:required-component:{derived.template.template_id}"
        )
        effect = EventCreationEffect(
            rule=EffectRule(
                effect_id=effect_id,
                source=definition.source,
                owner=definition.character_id,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=derived.template.template_id,
            ),
        )
        applications.append(MatchedEffectApplication(effect=effect))
    return tuple(applications)


def _all_definitions(
    request: MoveCalculationRequest,
) -> tuple[CharacterCalculationDefinition, ...]:
    return (request.definition, *request.supporting_definitions)


def _all_rule_items(
    request: MoveCalculationRequest,
) -> tuple:
    definitions = _all_definitions(request)
    return tuple(
        rule for definition in definitions for rule in definition.rule_items
    ) + tuple(request.additional_rule_items)


def _materialize_rule_stack_defaults(
    scenario,
    rule_items: tuple[CalculationRuleItem, ...],
):
    """Make compiled defaults explicit before matcher predicates run."""

    selected = {item.rule_item_id for item in scenario.rule_stack_counts}
    defaults = tuple(
        ScenarioRuleStack(rule.rule_id, rule.stack_count)
        for rule in rule_items
        if rule.stack_count is not None and rule.rule_id not in selected
    )
    if not defaults:
        return scenario
    return replace(
        scenario,
        rule_stack_counts=(*scenario.rule_stack_counts, *defaults),
    )


def _merge_modifier_applications(
    global_panel: ModifierApplicationResult,
    event_application: ModifierApplicationResult,
) -> ModifierApplicationResult:
    return ModifierApplicationResult(
        character_snapshots=event_application.character_snapshots,
        event_modifiers=event_application.event_modifiers,
        event_stat_modifiers=event_application.event_stat_modifiers,
        event_multiplier_modifiers=event_application.event_multiplier_modifiers,
        event_crit_guarantee_effect_ids=(
            *global_panel.event_crit_guarantee_effect_ids,
            *event_application.event_crit_guarantee_effect_ids,
        ),
        vulnerability_policy=event_application.vulnerability_policy,
        applied_panel_effect_ids=(
            global_panel.applied_panel_effect_ids
            | event_application.applied_panel_effect_ids
        ),
        panel_traces=global_panel.panel_traces + event_application.panel_traces,
        diagnostics=global_panel.diagnostics + event_application.diagnostics,
    )


def _resolved_stack_count(rule_item, scenario) -> int:
    if rule_item.stack_count is None:
        return 1
    selected = scenario.selected_stack(rule_item.rule_id)
    return rule_item.stack_count if selected is None else selected


def _match_diagnostics(
    matches: tuple[RuleItemMatchResult, ...],
) -> tuple[CalculationDiagnostic, ...]:
    return tuple(item for match in matches for item in match.diagnostics)


def _match_context(
    request: MoveCalculationRequest,
    event: DamageEvent,
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers,
    *,
    created_by_effect_id: EffectId | None = None,
    current_template_id: EventTemplateId | None = None,
) -> EffectMatchContext:
    context = CalculationContext(
        event=event,
        battle_state_id=request.battle_state_id,
        character_snapshots=snapshots,
        target_snapshot=request.target_snapshot,
        modifiers=tuple(modifiers),
        history_records=request.history_records,
    )
    return EffectMatchContext(
        current_event=event,
        calculation_context=context,
        scenario=request.scenario,
        team=request.team_profiles,
        target=request.target_profile,
        initial_character_snapshots=request.initial_character_snapshots,
        created_by_effect_id=created_by_effect_id,
        current_template_id=current_template_id,
    )


def _history_records_for_event(
    request: MoveCalculationRequest,
    event: DamageEvent,
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers,
    *,
    matcher: EffectMatcher | None = None,
    rule_items: tuple[CalculationRuleItem, ...] = (),
    applied_panel_effect_ids: frozenset[EffectId] = frozenset(),
):
    """Resolve explicit history first, then the opt-in static adapter.

    The typed attribute-anomaly path and a narrowly declared disorder path are
    eligible for the v1 single-character assumption.  Unknown history IDs and
    other anomaly mechanisms remain missing-data cases until their caller
    supplies a real record.
    """

    if request.history_record_mode != HistoryRecordMode.STATIC_SINGLE_CHARACTER:
        return request.history_records, ()
    if isinstance(event, AttributeAnomalyDamageEvent) and any(
        record.record_id == event.history_record_source
        for record in request.history_records
    ):
        # An explicit caller-owned record is authoritative.  Do not even
        # inspect panel fields for a synthetic replacement (or derive a
        # second set of diagnostics) in this branch.
        return request.history_records, ()
    if isinstance(event, DisorderDamageEvent) and any(
        record.record_id == event.history_record_source
        for record in request.history_records
    ):
        return request.history_records, ()
    if isinstance(event, DischargeDamageEvent) and any(
        record.record_id == event.history_record_source
        for record in request.history_records
    ):
        return request.history_records, ()
    if isinstance(event, DisorderDamageEvent) and not _declared_static_disorder_source(
        request,
        event,
    ):
        # A static disorder record is permitted only when the active
        # definition explicitly declares the source record and its triggerer.
        # This keeps the adapter from guessing an owner or numeric record from
        # an arbitrary history-record ID.
        return request.history_records, ()
    if isinstance(event, DischargeDamageEvent):
        source_template = next(
            (
                template
                for definition in _all_definitions(request)
                for template in definition.damage_event_templates
                if isinstance(template, AttributeAnomalyDamageEventTemplate)
                and template.history_record_source == event.history_record_source
                and template.damage_dealer == event.discharge_triggerer
                and template.element is event.metadata.element
            ),
            None,
        )
        if source_template is not None and matcher is not None:
            generation_event = AttributeAnomalyDamageEvent(
                metadata=DamageEventMetadata(
                    event_id=DamageEventId(
                        f"event:{request.battle_state_id}:static-record:{source_template.history_record_source}"
                    ),
                    battle_state_id=request.battle_state_id,
                    damage_dealer=source_template.damage_dealer,
                    target_enemy=event.metadata.target_enemy,
                    element=source_template.element,
                    created_at=request.battle_time,
                    skill_group=None,
                    move_id=source_template.move_id,
                    damage_tags=frozenset(),
                ),
                anomaly_triggerer=source_template.anomaly_triggerer,
                base_settlement_data_source=AnomalyRecordValueSource(
                    source_template.history_record_source
                ),
                history_record_source=source_template.history_record_source,
                multiplier=FixedMultiplier(Resolved(1.0)),
                crit_rule=source_template.crit_rule,
            )
            generation_context = _match_context(
                request,
                generation_event,
                snapshots,
                request.base_calculation_modifiers,
                current_template_id=source_template.ref.template_id,
            )
            generation_matches = matcher.match_rule_items(rule_items, generation_context)
            generation_application = apply_matched_modifiers(
                snapshots,
                request.base_calculation_modifiers,
                _matched_effects(
                    generation_matches,
                    rule_items,
                    request.scenario,
                ),
                request.scenario.current_operator,
                initial_character_snapshots=request.initial_character_snapshots,
                scenario=request.scenario,
                event=generation_event,
                apply_panel=False,
                applied_panel_effect_ids=applied_panel_effect_ids,
            )
            assembly = static_attribute_anomaly_record(
                generation_event,
                generation_application.character_snapshots,
                generation_application.event_modifiers,
                modifier_sources=_modifier_sources(request),
            )
            if assembly is not None and assembly.record is not None:
                return (
                    (*request.history_records, assembly.record),
                    (
                        *_match_diagnostics(generation_matches),
                        *generation_application.diagnostics,
                        *assembly.diagnostics,
                    ),
                )
            if assembly is not None:
                return request.history_records, assembly.diagnostics
    assembly = static_attribute_anomaly_record(
        event,
        snapshots,
        modifiers,
        modifier_sources=_modifier_sources(request),
    )
    if assembly is None:
        return request.history_records, ()
    source_id = assembly.record.record_id if assembly.record is not None else None
    if source_id is None:
        return request.history_records, assembly.diagnostics
    return (*request.history_records, assembly.record), assembly.diagnostics


def _bind_static_anomaly_crit(
    instantiated: InstantiatedDamageEvent,
    records: tuple[AnomalyRecord, ...],
) -> InstantiatedDamageEvent:
    """Bind anomaly and inheriting Discharge events to the recorded crit capability."""

    event = instantiated.event
    if not isinstance(event, (AttributeAnomalyDamageEvent, DischargeDamageEvent)):
        return instantiated
    record = next(
        (item for item in records if item.record_id == event.history_record_source),
        None,
    )
    if record is None:
        return instantiated
    if isinstance(record.crit_capability, IndependentAnomalyCrit):
        if (
            isinstance(event, DischargeDamageEvent)
            and DamageSubtype.DISCHARGE not in record.crit_capability.inherited_by
        ):
            return instantiated
        crit_rule = RecordedAnomalyCritRule(record.record_id, record.crit_capability)
    elif isinstance(record.crit_capability, NoAnomalyCrit):
        crit_rule = NoCritRule()
    else:
        crit_rule = RecordedAnomalyCritRule(record.record_id, record.crit_capability)
    return replace(instantiated, event=replace(event, crit_rule=crit_rule))


def _prepare_remielle_flare_source(
    request: MoveCalculationRequest,
    template: LuminanceFlareDamageEventTemplate,
    snapshots: tuple[CharacterSnapshot, ...],
    rule_items: tuple[CalculationRuleItem, ...],
    matcher: EffectMatcher,
    applied_panel_effect_ids: frozenset[EffectId],
):
    """Create one selected source snapshot without inventing Flare history.

    Ordinary slots use the existing static AnomalyRecord builder. Special
    virtual voids use a separate source snapshot and never enter the ordinary
    AnomalyRecord collection.
    """

    choice = request.luminance_source_choice
    if choice is None:
        raise ValueError("Remielle Flare requires a selected source slot")
    source_event_id = DamageEventId(
        f"event:{request.battle_state_id}:luminance-source-generation:{choice.slot_id}"
    )
    record_id = AnomalyRecordId(f"anomaly:remielle:source-slot:{choice.slot_id}")
    source_event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=source_event_id,
            battle_state_id=request.battle_state_id,
            damage_dealer=choice.source_character_id,
            target_enemy=request.target_snapshot.enemy_id,
            element=choice.element,
            created_at=request.battle_time,
        ),
        anomaly_triggerer=choice.source_character_id,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    source_scenario = replace(
        request.scenario,
        current_operator=choice.source_character_id,
    )
    source_request = replace(request, scenario=source_scenario)

    identity_record = None
    if choice.kind is LuminanceSourceKind.ORDINARY_ANOMALY:
        identity_assembly = static_attribute_anomaly_record(source_event, snapshots, ())
        identity_record = identity_assembly.record
        if identity_record is None:
            return request, None, identity_assembly.diagnostics
    source_history = request.history_records + (
        (identity_record,) if identity_record is not None else ()
    )
    match_request = replace(source_request, history_records=source_history)
    source_context = _match_context(
        match_request,
        source_event,
        snapshots,
        request.base_calculation_modifiers,
    )
    matches = matcher.match_rule_items(rule_items, source_context)
    source_effects = _matched_effects(matches, rule_items, source_scenario)
    source_application = apply_matched_modifiers(
        snapshots,
        request.base_calculation_modifiers,
        source_effects,
        source_scenario.current_operator,
        initial_character_snapshots=request.initial_character_snapshots,
        scenario=source_scenario,
        event=source_event,
        apply_panel=False,
        applied_panel_effect_ids=applied_panel_effect_ids,
    )
    source_diagnostics = (
        *_match_diagnostics(matches),
        *source_application.diagnostics,
    )
    modifier_sources = _modifier_sources(request)

    if choice.kind is LuminanceSourceKind.ORDINARY_ANOMALY:
        assembly = static_attribute_anomaly_record(
            source_event,
            source_application.character_snapshots,
            source_application.event_modifiers,
            modifier_sources=modifier_sources,
        )
        if assembly is None or assembly.record is None:
            diagnostics = (
                *source_diagnostics,
                *(assembly.diagnostics if assembly is not None else ()),
            )
            return request, None, diagnostics
        updated_request = replace(
            request,
            history_records=(*request.history_records, assembly.record),
        )
        return (
            updated_request,
            None,
            (*source_diagnostics, *assembly.diagnostics),
        )

    strength = static_anomaly_effect_strength_source(
        source_event,
        source_application.character_snapshots,
        source_application.event_modifiers,
        modifier_sources=modifier_sources,
    )
    rem_snapshot = next(
        (
            item for item in source_application.character_snapshots
            if item.character_id == choice.source_character_id
        ),
        None,
    )
    if rem_snapshot is None:
        return request, None, (
            *source_diagnostics,
            *strength.diagnostics,
        )
    source_factor = 0.25 if choice.kind is LuminanceSourceKind.SPECIAL_BASIC4 else 1.0
    special_source = LuminanceSpecialSourceSnapshot(
        source_id=LuminanceSpecialSourceId(
            f"luminance-special:remielle:{choice.slot_id}"
        ),
        slot_id=choice.slot_id,
        source_character_id=choice.source_character_id,
        element=choice.element,
        weighted_anomaly_effect_strength=strength.effect_strength,
        penetration_rate=strength.penetration_rate,
        penetration_flat=strength.penetration_flat,
        source_multiplier=Resolved(
            2.5 * rem_snapshot.level / 60.0 * source_factor
        ),
        source_kind=choice.kind,
        level=rem_snapshot.level,
        anomaly_effect_strength_trace=strength.trace,
    )
    return request, special_source, (*source_diagnostics, *strength.diagnostics)


def _prepare_polar_anomaly_source(
    request: MoveCalculationRequest,
    snapshots: tuple[CharacterSnapshot, ...],
    rule_items: tuple[CalculationRuleItem, ...],
    matcher: EffectMatcher,
    applied_panel_effect_ids: frozenset[EffectId],
):
    """Resolve exactly one selected current anomaly source for Polar Disorder."""

    choice = request.polarity_anomaly_source_choice
    if choice is None:
        return request, (
            _diagnostic(
                "character:1221:polar-source",
                "polar-source-choice",
                DiagnosticKind.MISSING_DATA,
                "Select one active ordinary anomaly source for Polar Disorder.",
            ),
        )
    record_id = anomaly_source_record_id(choice)
    existing = next(
        (item for item in request.history_records if item.record_id == record_id),
        None,
    )
    if existing is not None:
        if (
            existing.target_enemy != request.target_snapshot.enemy_id
            or existing.element is not choice.element
            or existing.anomaly_triggerer != choice.source_character_id
            or choice.source_character_id not in existing.contributors
        ):
            return request, (
                _diagnostic(
                    str(record_id),
                    "polar-source-record-mismatch",
                    DiagnosticKind.MISSING_DATA,
                    "The selected Polar anomaly record does not match its target or element.",
                ),
            )
        return request, ()
    if request.history_record_mode is not HistoryRecordMode.STATIC_SINGLE_CHARACTER:
        return request, (
            _diagnostic(
                str(record_id),
                "polar-source-record-missing",
                DiagnosticKind.MISSING_DATA,
                "The selected Polar anomaly source record must be supplied by explicit history.",
            ),
        )

    source_definition = next(
        (
            item for item in _all_definitions(request)
            if item.character_id == choice.source_character_id
        ),
        None,
    )
    if source_definition is None:
        return request, (
            _diagnostic(
                str(choice.source_character_id),
                "polar-source-definition-missing",
                DiagnosticKind.MISSING_DATA,
                "The selected Polar source actor has no active compiled definition.",
            ),
        )

    source_template_id = next(
        (
            template.ref.template_id
            for template in source_definition.damage_event_templates
            if isinstance(template, AttributeAnomalyDamageEventTemplate)
            and template.element is choice.element
        ),
        EventTemplateId(
            "template:static-anomaly-source:"
            f"{choice.source_character_id}:"
            f"{choice.element.value.replace(':', '-')}"
        ),
    )

    source_event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId(
                f"event:{request.battle_state_id}:polar-source:{choice.source_character_id}:{choice.element.value.replace(':', '-')}"
            ),
            battle_state_id=request.battle_state_id,
            damage_dealer=choice.source_character_id,
            target_enemy=request.target_snapshot.enemy_id,
            element=choice.element,
            created_at=request.battle_time,
        ),
        anomaly_triggerer=choice.source_character_id,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    identity_assembly = static_attribute_anomaly_record(source_event, snapshots, ())
    if identity_assembly is None or identity_assembly.record is None:
        return request, (
            *(
                identity_assembly.diagnostics
                if identity_assembly is not None
                else ()
            ),
            _diagnostic(
                str(record_id),
                "polar-source-identity",
                DiagnosticKind.MISSING_DATA,
                "The selected Polar source cannot produce an ordinary anomaly record.",
            ),
        )

    source_scenario = replace(
        request.scenario,
        current_operator=choice.source_character_id,
    )
    match_request = replace(
        request,
        scenario=source_scenario,
        history_records=(*request.history_records, identity_assembly.record),
    )
    source_context = _match_context(
        match_request,
        source_event,
        snapshots,
        request.base_calculation_modifiers,
        current_template_id=source_template_id,
    )
    matches = matcher.match_rule_items(rule_items, source_context)
    source_application = apply_matched_modifiers(
        snapshots,
        request.base_calculation_modifiers,
        _matched_effects(matches, rule_items, source_scenario),
        source_scenario.current_operator,
        initial_character_snapshots=request.initial_character_snapshots,
        scenario=source_scenario,
        event=source_event,
        apply_panel=False,
        applied_panel_effect_ids=applied_panel_effect_ids,
    )
    assembly = static_attribute_anomaly_record(
        source_event,
        source_application.character_snapshots,
        source_application.event_modifiers,
        modifier_sources=_modifier_sources(request),
    )
    if assembly is None or assembly.record is None:
        return request, (
            *_match_diagnostics(matches),
            *source_application.diagnostics,
            *(assembly.diagnostics if assembly is not None else ()),
            _diagnostic(
                str(record_id),
                "polar-source-record-unresolved",
                DiagnosticKind.MISSING_DATA,
                "The selected Polar anomaly source record could not be assembled.",
            ),
        )
    return (
        replace(request, history_records=(*request.history_records, assembly.record)),
        (
            *_match_diagnostics(matches),
            *source_application.diagnostics,
            *assembly.diagnostics,
        ),
    )


def _prepare_burnice_anomaly_source(
    request: MoveCalculationRequest,
    snapshots: tuple[CharacterSnapshot, ...],
    rule_items: tuple[CalculationRuleItem, ...],
    matcher: EffectMatcher,
    applied_panel_effect_ids: frozenset[EffectId],
):
    """Capture one selected active actor's current-panel anomaly record.

    The calculation operator and formation remain those of the submitted
    scene. The selected source actor is represented only as the typed source
    event's dealer and anomaly triggerer.
    """

    choice = request.burnice_anomaly_source_choice
    if choice is None:
        return request, ()
    record_id = anomaly_source_record_id(choice)
    existing = next(
        (item for item in request.history_records if item.record_id == record_id),
        None,
    )
    if existing is not None:
        if (
            existing.target_enemy != request.target_snapshot.enemy_id
            or existing.element is not choice.element
            or existing.anomaly_triggerer != choice.source_character_id
            or choice.source_character_id not in existing.contributors
        ):
            return request, (
                _diagnostic(
                    str(record_id),
                    "burnice-source-record-mismatch",
                    DiagnosticKind.MISSING_DATA,
                    "The selected anomaly record does not match the selected actor, element, or target.",
                ),
            )
        return request, ()
    if request.history_record_mode is not HistoryRecordMode.STATIC_SINGLE_CHARACTER:
        return request, (
            _diagnostic(
                str(record_id),
                "burnice-source-record-missing",
                DiagnosticKind.MISSING_DATA,
                "An explicit anomaly record is required for the selected Burnice Discharge source.",
            ),
        )

    source_definition = next(
        (
            item
            for item in _all_definitions(request)
            if item.character_id == choice.source_character_id
        ),
        None,
    )
    if source_definition is None:
        return request, (
            _diagnostic(
                str(choice.source_character_id),
                "burnice-source-definition-missing",
                DiagnosticKind.MISSING_DATA,
                "The selected anomaly source actor has no active compiled definition.",
            ),
        )
    source_template = next(
        (
            item
            for item in source_definition.damage_event_templates
            if isinstance(item, AttributeAnomalyDamageEventTemplate)
            and item.element is choice.element
            and item.element in ANOMALY_ELEMENTS
        ),
        None,
    )
    if source_template is None:
        return request, (
            _diagnostic(
                str(record_id),
                "burnice-source-template-missing",
                DiagnosticKind.MISSING_DATA,
                "The selected actor has no reviewed ordinary anomaly template for this element.",
            ),
        )

    source_event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId(
                f"event:{request.battle_state_id}:burnice-source:{choice.source_character_id}:{choice.element.value.replace(':', '-') }"
            ),
            battle_state_id=request.battle_state_id,
            damage_dealer=choice.source_character_id,
            target_enemy=request.target_snapshot.enemy_id,
            element=choice.element,
            created_at=request.battle_time,
            skill_group=None,
            move_id=source_template.move_id,
            damage_tags=frozenset(),
        ),
        anomaly_triggerer=choice.source_character_id,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    identity_assembly = static_attribute_anomaly_record(source_event, snapshots, ())
    if identity_assembly is None or identity_assembly.record is None:
        diagnostics = (
            *(identity_assembly.diagnostics if identity_assembly is not None else ()),
            _diagnostic(
                str(record_id),
                "burnice-source-identity-unresolved",
                DiagnosticKind.MISSING_DATA,
                "The selected source actor cannot produce a resolved ordinary anomaly record from the current panel.",
            ),
        )
        return request, diagnostics

    match_request = replace(
        request,
        history_records=(*request.history_records, identity_assembly.record),
    )
    source_context = _match_context(
        match_request,
        source_event,
        snapshots,
        request.base_calculation_modifiers,
        current_template_id=source_template.ref.template_id,
    )
    matches = matcher.match_rule_items(rule_items, source_context)
    source_application = apply_matched_modifiers(
        snapshots,
        request.base_calculation_modifiers,
        _matched_effects(matches, rule_items, request.scenario),
        request.scenario.current_operator,
        initial_character_snapshots=request.initial_character_snapshots,
        scenario=request.scenario,
        event=source_event,
        apply_panel=False,
        applied_panel_effect_ids=applied_panel_effect_ids,
    )
    assembly = static_attribute_anomaly_record(
        source_event,
        source_application.character_snapshots,
        source_application.event_modifiers,
        modifier_sources=_modifier_sources(request),
    )
    if assembly is None or assembly.record is None:
        return request, (
            *_match_diagnostics(matches),
            *source_application.diagnostics,
            *(assembly.diagnostics if assembly is not None else ()),
            _diagnostic(
                str(record_id),
                "burnice-source-record-unresolved",
                DiagnosticKind.MISSING_DATA,
                "The selected anomaly source record could not be resolved from its active panel effects.",
            ),
        )
    return (
        replace(request, history_records=(*request.history_records, assembly.record)),
        (
            *_match_diagnostics(matches),
            *source_application.diagnostics,
            *assembly.diagnostics,
        ),
    )


def _prepare_grace_anomaly_source(
    request: MoveCalculationRequest,
    snapshots: tuple[CharacterSnapshot, ...],
    rule_items: tuple[CalculationRuleItem, ...],
    matcher: EffectMatcher,
    applied_panel_effect_ids: frozenset[EffectId],
):
    """Capture the selected active actor's current-panel Shock source record."""

    choice = request.grace_anomaly_source_choice
    if choice is None:
        return request, ()
    record_id = anomaly_source_record_id(choice)
    existing = next(
        (item for item in request.history_records if item.record_id == record_id),
        None,
    )
    if existing is not None:
        if (
            existing.target_enemy != request.target_snapshot.enemy_id
            or existing.element is not choice.element
            or existing.anomaly_triggerer != choice.source_character_id
            or choice.source_character_id not in existing.contributors
        ):
            return request, (_diagnostic(
                str(record_id),
                "grace-source-record-mismatch",
                DiagnosticKind.MISSING_DATA,
                "The selected anomaly record does not match its selected actor, element, or target.",
            ),)
        return request, ()
    if request.history_record_mode is not HistoryRecordMode.STATIC_SINGLE_CHARACTER:
        return request, (_diagnostic(
            str(record_id),
            "grace-source-record-missing",
            DiagnosticKind.MISSING_DATA,
            "An explicit anomaly record is required for the selected Grace Discharge source.",
        ),)

    source_definition = next(
        (item for item in _all_definitions(request) if item.character_id == choice.source_character_id),
        None,
    )
    if source_definition is None:
        return request, (_diagnostic(
            str(choice.source_character_id),
            "grace-source-definition-missing",
            DiagnosticKind.MISSING_DATA,
            "The selected anomaly source actor has no active compiled definition.",
        ),)
    source_template = next(
        (
            item for item in source_definition.damage_event_templates
            if isinstance(item, AttributeAnomalyDamageEventTemplate)
            and item.element is choice.element
            and item.element in ANOMALY_ELEMENTS
        ),
        None,
    )
    if source_template is None:
        return request, (_diagnostic(
            str(record_id),
            "grace-source-template-missing",
            DiagnosticKind.MISSING_DATA,
            "The selected actor has no reviewed ordinary anomaly template for this element.",
        ),)

    source_event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId(
                f"event:{request.battle_state_id}:grace-source:{choice.source_character_id}:{choice.element.value.replace(':', '-') }"
            ),
            battle_state_id=request.battle_state_id,
            damage_dealer=choice.source_character_id,
            target_enemy=request.target_snapshot.enemy_id,
            element=choice.element,
            created_at=request.battle_time,
            skill_group=None,
            move_id=source_template.move_id,
            damage_tags=frozenset(),
        ),
        anomaly_triggerer=choice.source_character_id,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    identity_assembly = static_attribute_anomaly_record(source_event, snapshots, ())
    if identity_assembly is None or identity_assembly.record is None:
        return request, (
            *(identity_assembly.diagnostics if identity_assembly is not None else ()),
            _diagnostic(
                str(record_id),
                "grace-source-identity-unresolved",
                DiagnosticKind.MISSING_DATA,
                "The selected source actor cannot produce a resolved ordinary anomaly record from the current panel.",
            ),
        )

    match_request = replace(request, history_records=(*request.history_records, identity_assembly.record))
    source_context = _match_context(
        match_request,
        source_event,
        snapshots,
        request.base_calculation_modifiers,
        current_template_id=source_template.ref.template_id,
    )
    matches = matcher.match_rule_items(rule_items, source_context)
    source_application = apply_matched_modifiers(
        snapshots,
        request.base_calculation_modifiers,
        _matched_effects(matches, rule_items, request.scenario),
        request.scenario.current_operator,
        initial_character_snapshots=request.initial_character_snapshots,
        scenario=request.scenario,
        event=source_event,
        apply_panel=False,
        applied_panel_effect_ids=applied_panel_effect_ids,
    )
    assembly = static_attribute_anomaly_record(
        source_event,
        source_application.character_snapshots,
        source_application.event_modifiers,
        modifier_sources=_modifier_sources(request),
    )
    if assembly is None or assembly.record is None:
        return request, (
            *_match_diagnostics(matches),
            *source_application.diagnostics,
            *(assembly.diagnostics if assembly is not None else ()),
            _diagnostic(
                str(record_id),
                "grace-source-record-unresolved",
                DiagnosticKind.MISSING_DATA,
                "The selected anomaly source record could not be resolved from its active panel effects.",
            ),
        )
    return replace(request, history_records=(*request.history_records, assembly.record)), (
        *_match_diagnostics(matches),
        *source_application.diagnostics,
        *assembly.diagnostics,
    )


def _modifier_sources(request: MoveCalculationRequest):
    """Resolve effect provenance without coupling the calculation helper to UI DTOs."""

    sources = {}
    for rule in _all_rule_items(request):
        for effect in rule.effects:
            sources[str(effect.rule.effect_id)] = (
                effect.rule.source.label,
                effect.rule.owner,
            )
    return sources


def _declared_static_disorder_source(
    request: MoveCalculationRequest,
    event: DisorderDamageEvent,
) -> bool:
    for definition in _all_definitions(request):
        for template in definition.damage_event_templates:
            if isinstance(template, DisorderDamageEventTemplate):
                triggerer = template.disorder_triggerer
            elif isinstance(template, AttributeAnomalyDamageEventTemplate):
                triggerer = template.anomaly_triggerer
            else:
                continue
            if (
                template.history_record_source == event.history_record_source
                and template.damage_dealer == event.metadata.damage_dealer
                and triggerer == event.disorder_triggerer
            ):
                return True
    return False


def _crit_capability(event: DamageEvent) -> CritCapability:
    rule = getattr(event, "crit_rule", None)
    if isinstance(rule, StandardCritRule):
        return CritCapability.STANDARD
    if isinstance(rule, NoCritRule):
        return CritCapability.NONE
    if isinstance(rule, IndependentAnomalyCritRule):
        return CritCapability.ANOMALY_INDEPENDENT
    if isinstance(rule, RecordedAnomalyCritRule):
        return (
            CritCapability.ANOMALY_INDEPENDENT
            if isinstance(rule.capability, IndependentAnomalyCrit)
            else CritCapability.NONE
        )
    if isinstance(rule, Unresolved):
        return CritCapability.UNRESOLVED
    return CritCapability.UNRESOLVED


def _display_snapshots(
    snapshots: tuple[CharacterSnapshot, ...],
    event: DamageEvent,
    mode: CritDisplayMode,
) -> tuple[CharacterSnapshot, ...]:
    if mode is CritDisplayMode.EXPECTED or not isinstance(
        event, (DirectDamageEvent, PenetrationDamageEvent)
    ):
        return snapshots
    if not isinstance(event.crit_rule, StandardCritRule):
        return snapshots
    if event.crit_rule.guaranteed:
        return snapshots
    value = 0.0 if mode is CritDisplayMode.NON_CRIT else 1.0
    updated: list[CharacterSnapshot] = []
    for snapshot in snapshots:
        if snapshot.character_id != event.crit_rule.stat_owner:
            updated.append(snapshot)
            continue
        updated.append(
            replace(
                snapshot,
                settlement_stats=replace(
                    snapshot.settlement_stats,
                    crit_rate=Resolved(value),
                ),
            )
        )
    return tuple(updated)


def _apply_event_stat_modifiers(
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers: tuple[EventStatModifier, ...],
    diagnostics: list[CalculationDiagnostic],
) -> tuple[CharacterSnapshot, ...]:
    """Apply event-only stat edits without changing formal settlement snapshots."""

    if not modifiers:
        return snapshots
    index = {item.character_id: item for item in snapshots}
    for modifier in modifiers:
        target = index.get(modifier.recipient)
        if target is None:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-stat-recipient",
                    DiagnosticKind.MISSING_DATA,
                    "event stat modifier recipient has no character snapshot",
                )
            )
            continue
        if modifier.modifier_path not in {
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        }:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-stat-node",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "Stage-018 only applies event-level current crit-rate and crit-damage modifiers",
                )
            )
            continue
        if modifier.operation is not EffectOperation.ADD:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-stat-operation",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "event-level current crit-rate and crit-damage modifiers support ADD only",
                )
            )
            continue
        current = (
            target.settlement_stats.crit_rate
            if modifier.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
            else target.settlement_stats.crit_damage
        )
        if not isinstance(current, Resolved) or not isinstance(
            modifier.value, Resolved
        ):
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-stat-value",
                    DiagnosticKind.MISSING_DATA,
                    "event-level crit-rate or crit-damage modifier value is unresolved",
                )
            )
            continue
        index[modifier.recipient] = replace(
            target,
            settlement_stats=replace(
                target.settlement_stats,
                **(
                    {"crit_rate": Resolved(current.value + modifier.value.value)}
                    if modifier.modifier_path
                    is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
                    else {"crit_damage": Resolved(current.value + modifier.value.value)}
                ),
            ),
        )
    return tuple(index[item.character_id] for item in snapshots)


def _apply_guaranteed_crit_effects(
    event: DamageEvent,
    effect_ids: tuple[EffectId, ...],
    diagnostics: list[CalculationDiagnostic],
) -> DamageEvent:
    if not effect_ids:
        return event
    if not isinstance(event, (DirectDamageEvent, PenetrationDamageEvent)) or not isinstance(
        event.crit_rule, StandardCritRule
    ):
        for effect_id in effect_ids:
            diagnostics.append(
                _diagnostic(
                    str(effect_id),
                    "guaranteed-crit-event",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "guaranteed crit Effects require a standard-crit Direct or Penetration event",
                )
            )
        return event
    return replace(
        event,
        crit_rule=replace(event.crit_rule, guaranteed=True),
    )


def _apply_event_multiplier_modifiers(
    event: DamageEvent,
    modifiers,
    diagnostics: list[CalculationDiagnostic],
) -> DamageEvent:
    """Apply supported event multiplier operations to a calculation-only copy."""

    if not modifiers:
        return event
    if isinstance(event, (LuminanceDamageEvent, SpecialLuminanceDamageEvent)):
        # The Luminance calculator applies its Skill-multiplier effects after
        # the source AP contribution, which preserves Remielle's explicit
        # (base + AP) * Cinema-4 order.
        return event
    if not isinstance(event, DirectDamageEvent):
        diagnostics.append(
            _diagnostic(
                "event-multiplier",
                "event-kind",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "event multiplier modifiers require a direct damage event",
            )
        )
        return event
    if not isinstance(event.multiplier, FixedMultiplier):
        diagnostics.append(
            _diagnostic(
                str(event.metadata.event_id),
                "event-multiplier-base",
                DiagnosticKind.MISSING_DATA,
                "event multiplier modifiers require a fixed base multiplier",
            )
        )
        return event
    if not isinstance(event.multiplier.value, Resolved):
        diagnostics.append(
            _diagnostic(
                str(event.metadata.event_id),
                "event-multiplier-base",
                DiagnosticKind.MISSING_DATA,
                "base event multiplier is unresolved",
            )
        )
        return event
    value = event.multiplier.value.value
    for modifier in modifiers:
        if modifier.modifier_path is not CalculationNode.DAMAGE_SKILL_MULTIPLIER:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-multiplier-node",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "unsupported event multiplier calculation node",
                )
            )
            continue
        if modifier.operation is not EffectOperation.MULTIPLY:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-multiplier-operation",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "event skill multipliers support MULTIPLY only",
                )
            )
            continue
        if not isinstance(modifier.value, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "event-multiplier-value",
                    DiagnosticKind.MISSING_DATA,
                    "event skill multiplier value is unresolved",
                )
            )
            continue
        value *= modifier.value.value
    return replace(event, multiplier=FixedMultiplier(Resolved(value)))


def _execution_without_events(
    request: MoveCalculationRequest,
    *diagnostics: CalculationDiagnostic,
) -> MoveCalculationExecution:
    output = MoveCalculationOutput(
        move_entry_id=request.move_entry_id,
        crit_display_mode=request.crit_display_mode,
        events=(),
        known_total=None,
        complete=False,
        diagnostics=tuple(diagnostics),
    )
    return MoveCalculationExecution(
        output=output,
        resolved_character_snapshots=request.base_character_snapshots,
        event_traces=(),
        panel_traces=(),
    )


def _diagnostic(
    subject_id: str,
    suffix: str,
    kind: DiagnosticKind,
    message: str,
    *,
    original_text: str | None = None,
    candidates: tuple[str, ...] = (),
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"application:{subject_id}:{suffix}"),
        kind=kind,
        message=message,
        blocking=True,
        original_text=original_text,
        candidates=candidates,
    )
