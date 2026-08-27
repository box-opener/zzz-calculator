"""Direct move application service for the static calculation pipeline."""

from __future__ import annotations

from dataclasses import replace

from core.types import (
    BattleEventKind,
    CalculationContext,
    CharacterSnapshot,
    DamageEvent,
    DirectDamageEvent,
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
from ..characters.templates import DirectDamageEventTemplate
from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId, MoveEntryId
from ..moves import DerivedDamageEventTemplateRef, MoveCalculationEntry
from ..output import (
    CritDisplayMode,
    DamageEventCalculationOutput,
    EventCalculationStatus,
    MoveCalculationOutput,
)
from .contracts import (
    DamageEventExecutionTrace,
    InstantiatedDamageEvent,
    MoveCalculationExecution,
    MoveCalculationRequest,
)
from .event_factory import instantiate_direct_damage_event
from .modifiers import (
    MatchedEffectApplication,
    ModifierApplicationResult,
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

        multiplier = resolve_move_multiplier(entry, request.scenario)
        if multiplier.status is not MultiplierResolutionStatus.RESOLVED:
            return _execution_without_events(
                request,
                *multiplier.diagnostics,
            )
        assert multiplier.multiplier is not None

        definitions = _all_definitions(request)
        rule_items = _all_rule_items(definitions)

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

        main_event = instantiate_direct_damage_event(
            main_template,
            multiplier.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            repeat_count=multiplier.repeat_count,
        )
        main_context = _match_context(
            request,
            main_event.event,
            request.base_character_snapshots,
            request.base_calculation_modifiers,
        )
        main_matches = self._matcher.match_rule_items(rule_items, main_context)
        matched_effects = _matched_effects(
            main_matches,
            rule_items,
            request.scenario,
        )
        panel_application = apply_matched_modifiers(
            request.base_character_snapshots,
            request.base_calculation_modifiers,
            matched_effects,
            request.scenario.current_operator,
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
        while queue:
            instantiated, ancestry, matches, application = queue.pop(0)
            event_diagnostics = list(application.diagnostics)
            event_diagnostics.extend(_match_diagnostics(matches))
            calculation = self._calculate_event(
                request,
                instantiated,
                application,
                event_diagnostics,
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

            for effect_application in _matched_event_creations(
                matches,
                rule_items,
                request.scenario,
            ):
                created = self._create_derived_event(
                    request,
                    effect_application.effect,
                    ancestry,
                    seen_semantics,
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
                )
                child_matches = self._matcher.match_rule_items(rule_items, child_context)
                child_application = apply_matched_modifiers(
                    application.character_snapshots,
                    request.base_calculation_modifiers,
                    _matched_effects(
                        child_matches,
                        rule_items,
                        request.scenario,
                    ),
                    request.scenario.current_operator,
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
        )

    def _calculate_event(
        self,
        request: MoveCalculationRequest,
        instantiated: InstantiatedDamageEvent,
        application: ModifierApplicationResult,
        event_diagnostics: list[CalculationDiagnostic],
    ) -> tuple[
        DamageEventCalculationOutput,
        CalculatorExecutionResult,
        tuple[CalculationDiagnostic, ...],
    ]:
        diagnostics = tuple(event_diagnostics)
        if any(item.blocking for item in diagnostics):
            output = DamageEventCalculationOutput(
                semantic_id=instantiated.semantic_id,
                label=instantiated.label,
                damage_type=instantiated.event.damage_type,
                damage_subtype=instantiated.event.damage_subtype,
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
            application.character_snapshots,
            instantiated.event,
            request.crit_display_mode,
        )
        context = CalculationContext(
            event=instantiated.event,
            battle_state_id=request.battle_state_id,
            character_snapshots=display_snapshots,
            target_snapshot=request.target_snapshot,
            modifiers=application.event_modifiers,
            history_records=request.history_records,
        )
        calculation = self._router.calculate(instantiated.event, context)
        all_diagnostics = diagnostics + calculation.diagnostics
        output = DamageEventCalculationOutput(
            semantic_id=instantiated.semantic_id,
            label=instantiated.label,
            damage_type=instantiated.event.damage_type,
            damage_subtype=instantiated.event.damage_subtype,
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
        child = instantiate_direct_damage_event(
            template,
            derived_ref.multiplier,
            battle_state_id=request.battle_state_id,
            target_enemy=request.target_snapshot.enemy_id,
            created_at=request.battle_time,
            source_rule_item_id=template.ref.source_rule_item_id,
            created_by_effect_id=effect.rule.effect_id,
            repeat_count=derived_ref.repeat_count,
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
) -> DirectDamageEventTemplate | None:
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
    return tuple(
        MatchedEffectApplication(
            effect=effect,
            rule_item_id=item.rule_id,
            stack_count=_resolved_stack_count(rules[item.rule_id], scenario),
        )
        for item in matches
        for effect in item.matched_effects
    )


def _matched_event_creations(
    matches: tuple[RuleItemMatchResult, ...],
    rule_items: tuple,
    scenario,
) -> tuple[MatchedEffectApplication, ...]:
    return tuple(
        application
        for application in _matched_effects(matches, rule_items, scenario)
        if isinstance(application.effect, EventCreationEffect)
        and application.stack_count > 0
    )


def _all_definitions(
    request: MoveCalculationRequest,
) -> tuple[CharacterCalculationDefinition, ...]:
    return (request.definition, *request.supporting_definitions)


def _all_rule_items(
    definitions: tuple[CharacterCalculationDefinition, ...],
) -> tuple:
    return tuple(rule for definition in definitions for rule in definition.rule_items)


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
