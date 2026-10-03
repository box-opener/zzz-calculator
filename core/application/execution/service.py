"""Direct move application service for the static calculation pipeline."""

from __future__ import annotations

from dataclasses import replace

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationContext,
    CalculationNode,
    CharacterSnapshot,
    AttributeAnomalyDamageEvent,
    DamageEvent,
    DamageEventId,
    DamageMultiplier,
    DirectDamageEvent,
    DamageTypeFilter,
    DamageTagFilter,
    ElementFilter,
    DisorderDamageEvent,
    PenetrationDamageEvent,
    EffectId,
    EffectOperation,
    EffectTarget,
    FixedMultiplier,
    EventCreationEffect,
    EventTemplateId,
    IndependentAnomalyCrit,
    IndependentAnomalyCritRule,
    ModifierEffect,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

from ..matching import (
    EffectMatchContext,
    EffectMatcher,
    RuleItemMatchResult,
)

from ..characters.definition import CharacterCalculationDefinition
from ..characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
    DisorderDamageEventTemplate,
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
from .static_records import static_attribute_anomaly_record


def _complete_anomaly_multiplier(
    instantiated: InstantiatedDamageEvent,
) -> DamageMultiplier:
    """Carry the source anomaly's complete multiplier into a Discharge child."""

    multiplier = instantiated.event.multiplier
    if isinstance(multiplier, FixedMultiplier) and isinstance(multiplier.value, Resolved):
        return FixedMultiplier(
            Resolved(multiplier.value.value * instantiated.repeat_count)
        )
    return multiplier


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

        main_template = _find_template(
            definitions,
            entry.main_damage_event.template_id,
        )
        if main_template is None:
            diagnostic = _diagnostic(
                str(entry.main_damage_event.template_id),
                "missing-template",
                DiagnosticKind.MISSING_DATA,
                "main MoveEntry template is not present in the definition",
            )
            return _execution_without_events(request, diagnostic)

        main_event = instantiate_damage_event(
            main_template,
            multiplier.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            repeat_count=multiplier.repeat_count,
        )
        global_panel_application = apply_global_panel_effects(
            request.base_character_snapshots,
            request.initial_character_snapshots,
            rule_items,
            request.scenario,
            frozenset(profile.character_id for profile in request.team_profiles),
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
        )
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
        )
        request = replace(request, history_records=final_history)
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
                )
            )
            move_diagnostics.extend(calculation[2])
            if calculation[0].result is not None and calculation[0].result.value is not None:
                settled_damage_values[instantiated.event.metadata.event_id] = Resolved(
                    calculation[0].result.value
                )

            for effect_application in _matched_event_creations(
                matches,
                rule_items,
                request.scenario,
            ):
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
                created = self._create_derived_event(
                    request,
                    effect_application.effect,
                    ancestry,
                    seen_semantics,
                    source_event_id=instantiated.event.metadata.event_id,
                    source_history_record_id=(
                        instantiated.event.history_record_source
                        if isinstance(instantiated.event, AttributeAnomalyDamageEvent)
                        else None
                    ),
                    source_anomaly_multiplier=(
                        _complete_anomaly_multiplier(instantiated)
                        if isinstance(instantiated.event, AttributeAnomalyDamageEvent)
                        else None
                    ),
                )
                if isinstance(created, CalculationDiagnostic):
                    move_diagnostics.append(created)
                    continue
                if created is None:
                    continue
                child, child_ancestry = created
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
            modifiers=application.event_modifiers,
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
        source_event_id: DamageEventId | None = None,
        source_history_record_id: AnomalyRecordId | None = None,
        source_anomaly_multiplier: DamageMultiplier | None = None,
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
        derived_ref = _find_derived_ref(definitions, template_id)
        if derived_ref is None:
            return _diagnostic(
                str(template_id),
                "missing-derived-reference",
                DiagnosticKind.MISSING_DATA,
                "EventCreation template has no DerivedDamageEventTemplateRef",
            )
        template = _find_template(definitions, template_id)
        if template is None:
            return _diagnostic(
                str(template_id),
                "missing-template",
                DiagnosticKind.MISSING_DATA,
                "EventCreation template is not registered",
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
        child = instantiate_damage_event(
            instance_template,
            derived_ref.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            source_rule_item_id=template.ref.source_rule_item_id,
            created_by_effect_id=effect.rule.effect_id,
            repeat_count=repeat_count,
            source_event_id=source_event_id,
            source_history_record_id=source_history_record_id,
            source_anomaly_multiplier=source_anomaly_multiplier,
        )
        return child, (*ancestry, template_id)


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
    definitions: tuple[CharacterCalculationDefinition, ...],
    template_id: EventTemplateId,
) -> DamageEventTemplate | None:
    return next(
        (
            item
            for definition in definitions
            for item in definition.damage_event_templates
            if item.ref.template_id == template_id
        ),
        None,
    )


def _find_derived_ref(
    definitions: tuple[CharacterCalculationDefinition, ...],
    template_id: EventTemplateId,
) -> DerivedDamageEventTemplateRef | None:
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
    seen_non_stacking_groups: set[str] = set()
    conflicting_event_groups = _conflicting_non_stacking_event_groups(
        matches,
        rules,
        diagnostics,
    )
    for item in matches:
        rule = rules[item.rule_id]
        group_id = rule.non_stacking_group_id
        if group_id is not None and group_id in conflicting_event_groups:
            continue
        if item.matched_effects and group_id is not None:
            if group_id in seen_non_stacking_groups:
                continue
            seen_non_stacking_groups.add(group_id)
        applications.extend(
            MatchedEffectApplication(
                effect=effect,
                rule_item_id=item.rule_id,
                stack_count=_resolved_stack_count(rule, scenario),
            )
            for effect in item.matched_effects
        )
    return tuple(applications)


def _conflicting_non_stacking_event_groups(
    matches: tuple[RuleItemMatchResult, ...],
    rules: dict,
    diagnostics: list[CalculationDiagnostic] | None,
) -> frozenset[str]:
    """Block conflicting fixed event-scoped non-stacking modifiers.

    This handles statically comparable target-scoped crit modifiers and simple
    TEAM damage/Daze modifiers. The existing panel conflict path remains
    responsible for SELF/TEAM panel values and condition-sensitive rules.
    """

    grouped: dict[str, list[tuple[tuple[tuple[object, ...], ...], CalculationRuleItem]]] = {}
    for match in matches:
        rule = rules[match.rule_id]
        group_id = rule.non_stacking_group_id
        if group_id is None or not match.matched_effects:
            continue
        effects = tuple(match.matched_effects)
        if not all(
            isinstance(effect, ModifierEffect)
            and effect.rule.target in {EffectTarget.ENEMY, EffectTarget.TEAM}
            and effect.rule.condition is None
            and effect.rule.trigger is None
            and effect.result.modifier_path
            in {
                CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                CalculationNode.DAZE_OUTGOING_BONUS,
            }
            and effect.result.operation is EffectOperation.ADD
            and isinstance(effect.result.value, Resolved)
            and _has_only_static_event_filters(effect.rule.filters)
            for effect in effects
        ):
            continue
        signature = tuple(
            (
                effect.result.modifier_path,
                effect.result.operation,
                effect.result.value,
                effect.rule.target,
                effect.rule.filters,
            )
            for effect in effects
        )
        grouped.setdefault(group_id, []).append((signature, rule))

    conflicts = frozenset(
        group_id
        for group_id, items in grouped.items()
        if len(items) > 1 and any(signature != items[0][0] for signature, _ in items[1:])
    )
    if diagnostics is not None:
        for group_id in sorted(conflicts):
            items = grouped[group_id]
            diagnostics.append(
                _diagnostic(
                    group_id,
                    "conflicting-non-stacking-event-values",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "Active same-name event-scope effects resolve to "
                    "different values; the source does not define which copy wins, "
                    "so none is applied.",
                    original_text=items[0][1].original_text,
                    candidates=tuple(rule.original_text for _, rule in items),
                )
            )
    return conflicts


def _has_only_static_event_filters(filters) -> bool:
    if not filters:
        return True

    def is_static_target_filter(item) -> bool:
        if isinstance(item, (DamageTypeFilter, ElementFilter, DamageTagFilter)):
            return True
        if isinstance(item, AnyFilter):
            return all(is_static_target_filter(nested) for nested in item.filters)
        return False

    return all(is_static_target_filter(item) for item in filters)


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
    if isinstance(event, DisorderDamageEvent) and not _declared_static_disorder_source(
        request,
        event,
    ):
        # A static disorder record is permitted only when the active
        # definition explicitly declares the source record and its triggerer.
        # This keeps the adapter from guessing an owner or numeric record from
        # an arbitrary history-record ID.
        return request.history_records, ()
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
