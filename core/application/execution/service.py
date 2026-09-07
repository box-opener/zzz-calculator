"""Direct move application service for the static calculation pipeline."""

from __future__ import annotations

from dataclasses import replace

from core.types import (
    BattleEventKind,
    CalculationContext,
    CalculationNode,
    CharacterSnapshot,
    DamageEvent,
    DamageEventId,
    DirectDamageEvent,
    EffectId,
    EffectOperation,
    FixedMultiplier,
    EventCreationEffect,
    EventTemplateId,
    Resolved,
    StandardCritRule,
)

from ..matching import (
    EffectMatchContext,
    EffectMatcher,
    RuleItemMatchResult,
)

from ..characters.definition import CharacterCalculationDefinition
from ..characters.templates import DamageEventTemplate
from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId, MoveEntryId
from ..moves import DerivedDamageEventTemplateRef, MoveCalculationEntry
from ..scenario import ScenarioRuleStack
from ..rules import CalculationRuleItem
from ..output import (
    CritDisplayMode,
    DamageEventCalculationOutput,
    EventCalculationStatus,
    MoveCalculationOutput,
)
from .contracts import (
    DamageEventExecutionTrace,
    EventStatModifier,
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
        main_context = _match_context(
            request,
            main_event.event,
            global_panel_application.character_snapshots,
            request.base_calculation_modifiers,
        )
        main_matches = self._matcher.match_rule_items(rule_items, main_context)
        matched_effects = _matched_effects(
            main_matches,
            rule_items,
            request.scenario,
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
        panel_application = _merge_modifier_applications(
            global_panel_application,
            panel_application,
        )

        event_outputs: list[DamageEventCalculationOutput] = []
        traces: list[DamageEventExecutionTrace] = []
        move_diagnostics: list[CalculationDiagnostic] = [
            *multiplier.diagnostics,
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
                )
                if isinstance(created, CalculationDiagnostic):
                    move_diagnostics.append(created)
                    continue
                child, child_ancestry = created
                seen_semantics.add(child.semantic_id)
                child_context = _match_context(
                    request,
                    child.event,
                    application.character_snapshots,
                    request.base_calculation_modifiers,
                    created_by_effect_id=child.created_by_effect_id,
                )
                child_matches = self._matcher.match_rule_items(
                    rule_items, child_context
                )
                child_application = apply_matched_modifiers(
                    application.character_snapshots,
                    request.base_calculation_modifiers,
                    _matched_effects(
                        child_matches,
                        rule_items,
                        request.scenario,
                    ),
                    request.scenario.current_operator,
                    initial_character_snapshots=request.initial_character_snapshots,
                    scenario=request.scenario,
                    event=child.event,
                    apply_panel=False,
                    applied_panel_effect_ids=panel_application.applied_panel_effect_ids,
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
        calculation_event = _apply_event_multiplier_modifiers(
            instantiated.event,
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
    ) -> (
        tuple[InstantiatedDamageEvent, tuple[EventTemplateId, ...]]
        | CalculationDiagnostic
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
            return _diagnostic(
                str(effect.rule.effect_id),
                "unresolved-template",
                DiagnosticKind.MISSING_DATA,
                (
                    unresolved.notes
                    if unresolved is not None
                    else "event template is unresolved"
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
        if derived_ref.semantic_id in seen_semantics:
            return _diagnostic(
                str(derived_ref.semantic_id),
                "duplicate-semantic-event",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "the same semantic event was created more than once",
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
        child = instantiate_damage_event(
            template,
            derived_ref.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            source_rule_item_id=template.ref.source_rule_item_id,
            created_by_effect_id=effect.rule.effect_id,
            repeat_count=repeat_count,
            source_event_id=source_event_id,
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
) -> tuple[MatchedEffectApplication, ...]:
    rules = {item.rule_id: item for item in rule_items}
    applications: list[MatchedEffectApplication] = []
    seen_non_stacking_groups: set[str] = set()
    for item in matches:
        rule = rules[item.rule_id]
        group_id = rule.non_stacking_group_id
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
    )


def _display_snapshots(
    snapshots: tuple[CharacterSnapshot, ...],
    event: DamageEvent,
    mode: CritDisplayMode,
) -> tuple[CharacterSnapshot, ...]:
    if mode is CritDisplayMode.EXPECTED or not isinstance(event, DirectDamageEvent):
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
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"application:{subject_id}:{suffix}"),
        kind=kind,
        message=message,
        blocking=True,
    )
