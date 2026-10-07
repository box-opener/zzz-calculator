"""Translate application contracts into stable UI views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from core.application.characters.definition import CharacterCalculationDefinition
from core.application.execution.contracts import MoveCalculationExecution
from core.application.equipment.wengine import WEngineBuildResolution
from core.application.equipment.drive_disc import DriveDiscBuildResolution
from core.application.ids import DamageEventSemanticId
from core.application.output import CritCapability, CritDisplayMode
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import CalculationScenario
from core.types import (
    BattleEventKind,
    CharacterId,
    Element,
    ANOMALY_ELEMENTS,
    DRIVE_DISC_MAIN_STATS_BY_SLOT,
    DRIVE_DISC_MAIN_STAT_VALUES,
    DRIVE_DISC_SUBSTAT_VALUES,
    FixedMultiplier,
    Resolved,
)

from .calculation import (
    CalculationView,
    BuildContributionView,
    DamageEventModeView,
    DamageEventView,
    MoveTotalsView,
    PanelTraceView,
    event_trace_view,
    build_contribution_view,
    panel_snapshot_view,
    _mode_view,
)
from .catalog import CharacterCatalogItem, supported_character_catalog
from .character_editor import (
    CharacterEditorView,
    CompileConfigFieldView,
    MoveVariantView,
    MoveView,
    RuleItemView,
    RuleStackView,
    ScenarioConditionView,
    ScenarioParameterView,
    ScenarioTriggerInputView,
    WEngineEditorView,
    DriveDiscEditorView,
    DriveDiscSetCountView,
    DriveDiscSlotSchemaView,
    DriveDiscStatOptionView,
)
from .diagnostics import DiagnosticView, diagnostic_view
from .drive_disc_display import drive_disc_stat_label
from core.application.characters.templates import (
    AttributeAnomalyDamageEventTemplate,
)


SCHEMA_VERSION = "presentation-v1"


def _drive_stat_view(stat, value: float) -> DriveDiscStatOptionView:
    return DriveDiscStatOptionView(
        stat_key=stat.value,
        label=drive_disc_stat_label(stat),
        value_per_roll=value,
    )


def build_drive_disc_editor_view(
    resolution: DriveDiscBuildResolution,
    scenario: CalculationScenario | None = None,
    team_character_ids: Sequence[CharacterId] = (),
    condition_context: Mapping[str, bool | None] | None = None,
) -> DriveDiscEditorView:
    selected_conditions = (
        {item.condition_id: item for item in scenario.conditions} if scenario else {}
    )
    scenario_conditions = tuple(
        selected_conditions.get(item.condition_id, item)
        for item in resolution.scenario_conditions
    )
    return DriveDiscEditorView(
        schema_version=SCHEMA_VERSION,
        equipped_character_id=str(resolution.build_input.equipped_character_id),
        set_counts=tuple(
            DriveDiscSetCountView(str(set_id), count)
            for set_id, count in resolution.set_counts
        ),
        slot_schemas=tuple(
            DriveDiscSlotSchemaView(
                slot=int(slot),
                main_stat_options=tuple(
                    _drive_stat_view(stat, DRIVE_DISC_MAIN_STAT_VALUES[stat])
                    for stat in sorted(stats, key=lambda item: item.value)
                ),
            )
            for slot, stats in DRIVE_DISC_MAIN_STATS_BY_SLOT.items()
        ),
        substat_options=tuple(
            _drive_stat_view(stat, value)
            for stat, value in DRIVE_DISC_SUBSTAT_VALUES.items()
        ),
        rule_items=tuple(
            _rule_view(
                rule,
                scenario,
                resolution.scenario_conditions,
                condition_values=condition_context,
            )
            for rule in resolution.rule_items
        ),
        scenario_conditions=tuple(
            ScenarioConditionView(
                condition_id=str(item.condition_id),
                label=item.label,
                resolution=item.resolution.value,
                value=item.value,
                editable=item.resolution.value == "user-selected",
                original_text=item.original_text,
            )
            for item in scenario_conditions
        ),
        scenario_trigger_inputs=_trigger_inputs_for_rules(
            resolution.rule_items,
            scenario,
            tuple(str(item) for item in team_character_ids),
        ),
        diagnostics=tuple(diagnostic_view(item) for item in resolution.diagnostics),
    )


def build_wengine_editor_view(
    resolution: WEngineBuildResolution,
    scenario: CalculationScenario | None = None,
    team_character_ids: Sequence[CharacterId] = (),
    condition_context: Mapping[str, bool | None] | None = None,
) -> WEngineEditorView:
    """Expose one owner-qualified W-Engine instance to the editor.

    The catalog intentionally contains only model metadata.  This view is
    assembled after an owner, refinement, and level are known, so every rule
    and condition ID belongs to the concrete equipment instance.
    """

    selected_conditions = (
        {item.condition_id: item for item in scenario.conditions} if scenario else {}
    )
    scenario_conditions = tuple(
        selected_conditions.get(item.condition_id, item)
        for item in resolution.scenario_conditions
    )
    resolved_context = dict(condition_context or {})
    return WEngineEditorView(
        schema_version=SCHEMA_VERSION,
        wengine_id=str(resolution.raw.wengine_id),
        equipped_character_id=str(resolution.build_input.equipped_character_id),
        display_name=resolution.raw.name,
        rarity=resolution.raw.rarity,
        specialty=resolution.raw.specialty.value,
        rule_items=tuple(
            _rule_view(
                rule,
                scenario,
                resolution.scenario_conditions,
                condition_values=resolved_context,
            )
            for rule in resolution.rule_items
        ),
        scenario_conditions=tuple(
            ScenarioConditionView(
                condition_id=str(item.condition_id),
                label=item.label,
                resolution=item.resolution.value,
                value=item.value,
                editable=item.resolution.value == "user-selected",
                original_text=item.original_text,
            )
            for item in scenario_conditions
        ),
        diagnostics=tuple(diagnostic_view(item) for item in resolution.diagnostics),
    )


def build_character_editor_view(
    definition: CharacterCalculationDefinition,
    scenario: CalculationScenario | None = None,
    team_character_ids: Sequence[CharacterId] = (),
    compile_config_fields: Sequence[CompileConfigFieldView] = (),
) -> CharacterEditorView:
    """Build controls without exposing raw Domain/Application objects."""

    catalog = next(
        (
            item
            for item in supported_character_catalog()
            if item.character_id == str(definition.character_id)
        ),
        None,
    )
    display_name = catalog.display_name if catalog else definition.source.label
    selected_conditions = (
        {item.condition_id: item for item in scenario.conditions} if scenario else {}
    )
    scenario_conditions = tuple(
        selected_conditions.get(item.condition_id, item)
        for item in definition.scenario_conditions
    )
    selected_parameters = (
        {item.parameter_id: item for item in scenario.parameters} if scenario else {}
    )
    scenario_parameters = tuple(
        selected_parameters.get(item.parameter_id, item)
        for item in definition.scenario_parameters
    )
    condition_views = tuple(
        ScenarioConditionView(
            condition_id=str(item.condition_id),
            label=item.label,
            resolution=item.resolution.value,
            value=item.value,
            editable=item.resolution.value == "user-selected",
            original_text=item.original_text,
        )
        for item in scenario_conditions
    )
    parameter_views = tuple(
        ScenarioParameterView(
            parameter_id=str(item.parameter_id),
            label=item.label,
            resolution=item.resolution.value,
            value=item.value,
            minimum=item.minimum,
            maximum=item.maximum,
            original_text=item.original_text,
        )
        for item in scenario_parameters
    )
    team_ids = tuple(str(item) for item in team_character_ids)
    if not team_ids:
        team_ids = (str(definition.character_id),)
    trigger_inputs = _trigger_inputs(definition, scenario, team_ids)
    return CharacterEditorView(
        schema_version=SCHEMA_VERSION,
        character_id=str(definition.character_id),
        display_name=display_name,
        role=definition.role.value,
        base_element=definition.base_element.value,
        compile_config_fields=tuple(compile_config_fields),
        moves=tuple(_move_view(item) for item in definition.move_entries),
        rule_items=tuple(
            _rule_view(rule, scenario, definition.scenario_conditions)
            for rule in definition.rule_items
        ),
        scenario_conditions=condition_views,
        scenario_parameters=parameter_views,
        scenario_trigger_inputs=trigger_inputs,
        diagnostics=tuple(diagnostic_view(item) for item in definition.diagnostics),
        luminance_source_elements=tuple(
            element.value
            for element in _source_anomaly_elements(definition)
        ),
        anomaly_source_elements=tuple(
            element.value
            for element in _source_anomaly_elements(definition)
        ),
        effective_damage_element=_effective_damage_element(definition).value,
    )


def _source_anomaly_elements(definition):
    elements = {
        template.element
        for template in definition.damage_event_templates
        if isinstance(
            template,
            AttributeAnomalyDamageEventTemplate,
        )
    }
    if not elements and definition.base_element in ANOMALY_ELEMENTS:
        elements.add(definition.base_element)
    return tuple(sorted(elements, key=lambda item: item.value))


def _effective_damage_element(definition):
    if str(definition.character_id) == "character:1581":
        elements = tuple(
            item.main_damage_event.element
            for item in definition.move_entries
            if item.main_damage_event.element is not None
        )
        if elements and all(item is elements[0] for item in elements):
            return elements[0]
    return definition.base_element


def build_move_calculation_view(
    executions: Mapping[CritDisplayMode, MoveCalculationExecution],
    source_labels: Mapping[str, str] | None = None,
    build_provenance=(),
    *,
    source_types: Mapping[str, str] | None = None,
    source_owners: Mapping[str, str] | None = None,
    selected_entry_diagnostics=(),
) -> CalculationView:
    """Align three application executions by semantic event ID."""

    required_modes = (
        CritDisplayMode.NON_CRIT,
        CritDisplayMode.EXPECTED,
        CritDisplayMode.FULL_CRIT,
    )
    missing = tuple(mode.value for mode in required_modes if mode not in executions)
    if missing:
        raise ValueError(f"presentation calculation is missing modes: {missing}")

    expected = executions[CritDisplayMode.EXPECTED]
    mode_outputs = {mode: executions[mode].output for mode in required_modes}
    semantic_ids = tuple(item.semantic_id for item in expected.output.events)
    mode_event_maps = {
        mode: {item.semantic_id: item for item in executions[mode].output.events}
        for mode in required_modes
    }
    diagnostics: list[DiagnosticView] = []
    expected_semantic_ids = set(semantic_ids)
    for mode in required_modes:
        actual_semantic_ids = set(mode_event_maps[mode])
        if actual_semantic_ids != expected_semantic_ids:
            diagnostics.append(
                _presentation_diagnostic(
                    f"event-set-{mode.value}",
                    "three crit-mode executions do not expose the same event IDs",
                )
            )
    events: list[DamageEventView] = []
    for semantic_id in semantic_ids:
        items = [mode_event_maps[mode].get(semantic_id) for mode in required_modes]
        if any(item is None for item in items):
            diagnostics.append(
                _presentation_diagnostic(
                    f"event-set-{semantic_id}",
                    "three crit-mode executions do not expose the same event IDs",
                )
            )
            continue
        typed_items = tuple(item for item in items if item is not None)
        first = typed_items[0]
        if any(
            item.repeat_count != first.repeat_count
            or item.label != first.label
            or item.damage_type != first.damage_type
            or item.damage_subtype != first.damage_subtype
            or item.element != first.element
            for item in typed_items[1:]
        ):
            diagnostics.append(
                _presentation_diagnostic(
                    f"event-shape-{semantic_id}",
                    "three crit-mode executions disagree on event metadata",
                )
            )
            continue
        if any(item.crit_capability != first.crit_capability for item in typed_items[1:]):
            diagnostics.append(
                _presentation_diagnostic(
                    f"crit-capability-{semantic_id}",
                    "three crit-mode executions disagree on event crit capability",
                )
            )
        mode_views = {
            mode.value: _mode_view(
                mode_event_maps[mode][semantic_id],
                source_labels=dict(source_labels or {}),
                source_owners=dict(source_owners or {}),
            )
            for mode in required_modes
        }
        traces = tuple(
            event_trace_view(
                next(
                    trace
                    for trace in executions[mode].event_traces
                    if trace.semantic_id == semantic_id
                ),
                source_labels=dict(source_labels or {}),
                source_types=dict(source_types or {}),
            )
            for mode in required_modes
        )
        common_trace = (
            traces[0] if all(item == traces[0] for item in traces[1:]) else None
        )
        event_display_modes = _display_modes_for_capability(first.crit_capability)
        if common_trace is None:
            diagnostics.append(
                _presentation_diagnostic(
                    f"trace-{semantic_id}",
                    "three crit-mode executions disagree on application trace",
                )
            )
        events.append(
            DamageEventView(
                semantic_id=str(semantic_id),
                label=first.label,
                damage_type=first.damage_type.value,
                damage_subtype=(
                    first.damage_subtype.value
                    if first.damage_subtype is not None
                    else None
                ),
                element=(first.element.value if first.element is not None else None),
                repeat_count=first.repeat_count,
                modes=mode_views,
                common_application_trace=common_trace,
                crit_capability=first.crit_capability.value,
                display_modes=event_display_modes,
            )
        )

    totals = {
        mode.value: MoveTotalsView(
            value=mode_outputs[mode].known_total,
            complete=mode_outputs[mode].complete,
            diagnostics=tuple(
                diagnostic_view(item) for item in mode_outputs[mode].diagnostics
            ),
        )
        for mode in required_modes
    }
    panel_views = tuple(
        PanelTraceView(
            recipient_character_id=str(item.recipient_character_id),
            owner_character_id=(
                str(item.owner_character_id)
                if item.owner_character_id is not None
                else None
            ),
            rule_item_id=(str(item.rule_item_id) if item.rule_item_id else None),
            effect_id=str(item.effect_id),
            source_label=(source_labels or {}).get(str(item.effect_id)),
            modifier_path=item.modifier_path.value,
            operation=item.operation.value,
            resolved_value=item.resolved_value,
            stack_count=item.stack_count,
            source_type=(source_types or {}).get(str(item.effect_id)),
        )
        for item in expected.panel_traces
    )
    if any(
        tuple(executions[mode].panel_traces) != tuple(expected.panel_traces)
        for mode in required_modes
        if mode is not CritDisplayMode.EXPECTED
    ):
        diagnostics.append(
            _presentation_diagnostic(
                "panel-trace-mismatch",
                "three crit-mode executions disagree on panel provenance",
            )
        )
    snapshots = tuple(
        panel_snapshot_view(item) for item in expected.resolved_character_snapshots
    )
    if any(
        executions[mode].resolved_character_snapshots
        != expected.resolved_character_snapshots
        for mode in required_modes
        if mode is not CritDisplayMode.EXPECTED
    ):
        diagnostics.append(
            _presentation_diagnostic(
                "panel-snapshot-mismatch",
                "three crit-mode executions disagree on resolved panel snapshots",
            )
        )
    seen_output_diagnostics = set()
    for mode in required_modes:
        for item in executions[mode].output.diagnostics:
            identity = (
                item.diagnostic_id,
                item.kind,
                item.message,
                item.original_text,
                item.candidates,
            )
            if identity in seen_output_diagnostics:
                continue
            seen_output_diagnostics.add(identity)
            diagnostics.append(diagnostic_view(item))
    for item in selected_entry_diagnostics:
        identity = (
            item.diagnostic_id,
            item.kind,
            item.message,
            item.original_text,
            item.candidates,
        )
        if identity in seen_output_diagnostics:
            continue
        seen_output_diagnostics.add(identity)
        diagnostics.append(diagnostic_view(item))
    return CalculationView(
        schema_version=SCHEMA_VERSION,
        move_entry_id=str(expected.output.move_entry_id),
        events=tuple(events),
        totals=totals,
        resolved_character_snapshots=snapshots,
        panel_traces=panel_views,
        build_provenance=tuple(
            build_contribution_view(item) for item in build_provenance
        ),
        diagnostics=tuple(diagnostics),
        display_modes=_move_display_modes(
            tuple(item.crit_capability for item in expected.output.events)
        ),
    )


def _display_modes_for_capability(capability: CritCapability) -> tuple[str, ...]:
    if capability == CritCapability.STANDARD:
        return tuple(item.value for item in CritDisplayMode)
    # Backend execution remains three-mode compatible, but a non-standard
    # anomaly result is one value in the presentation contract.  In
    # particular, ordinary panel crit values never leak into anomaly cards.
    return (CritDisplayMode.EXPECTED.value,)


def _move_display_modes(capabilities) -> tuple[str, ...]:
    return (
        tuple(item.value for item in CritDisplayMode)
        if any(item == CritCapability.STANDARD for item in capabilities)
        else (CritDisplayMode.EXPECTED.value,)
    )


def _move_view(entry) -> MoveView:
    return MoveView(
        entry_id=str(entry.entry_id),
        move_id=str(entry.move_id) if entry.move_id is not None else None,
        label=entry.display_name,
        skill_group=entry.skill_group.value if entry.skill_group else None,
        damage_tags=tuple(sorted(item.value for item in entry.damage_tags)),
        multiplier_relation=entry.multiplier_relation.value,
        variants=tuple(
            MoveVariantView(
                variant_id=str(item.variant_id),
                label=item.label,
                parameter_name=item.parameter_name,
                multiplier=(
                    item.multiplier.value.value
                    if isinstance(item.multiplier, FixedMultiplier)
                    and isinstance(item.multiplier.value, Resolved)
                    else None
                ),
                condition_ids=tuple(str(condition) for condition in item.condition_ids),
                repeat_count=item.repeat_count,
                repeat_count_parameter_id=(
                    str(item.repeat_count_parameter_id)
                    if item.repeat_count_parameter_id is not None
                    else None
                ),
            )
            for item in entry.multiplier_variants
        ),
        condition_ids=tuple(str(condition) for condition in entry.condition_ids),
        diagnostics=tuple(diagnostic_view(item) for item in entry.diagnostics),
    )


def _rule_view(
    rule: CalculationRuleItem,
    scenario: CalculationScenario | None,
    definition_conditions,
    *,
    condition_values: Mapping[str, bool | None] | None = None,
) -> RuleItemView:
    values = {
        str(item.condition_id): item.value
        for item in (scenario.conditions if scenario else definition_conditions)
    }
    values.update({str(key): value for key, value in (condition_values or {}).items()})
    availability = "available"
    if rule.eligibility is RuleEligibility.INELIGIBLE:
        availability = "unavailable"
    elif (
        any(values.get(str(condition)) is False for condition in rule.condition_ids)
        or any(values.get(str(condition)) is True for condition in rule.condition_not_ids)
    ):
        availability = "unavailable"
    elif any(
        values.get(str(condition)) is None
        for condition in (*rule.condition_ids, *rule.condition_not_ids)
    ):
        availability = "blocked"
    elif any(item.blocking for item in rule.diagnostics):
        availability = "blocked"
    enabled = availability == "available"
    return RuleItemView(
        rule_id=str(rule.rule_id),
        label=rule.display_name,
        source_label=rule.source.label,
        source_type=rule.source.source_type.value,
        eligibility=rule.eligibility.value,
        availability=availability,
        enabled_by_default=enabled,
        toggleable=availability == "available",
        stack=RuleStackView(rule.stack_count, rule.stack_min, rule.stack_max),
        condition_ids=tuple(str(condition) for condition in rule.condition_ids),
        condition_not_ids=tuple(
            str(condition) for condition in rule.condition_not_ids
        ),
        diagnostics=tuple(diagnostic_view(item) for item in rule.diagnostics),
    )


def _trigger_inputs(
    definition: CharacterCalculationDefinition,
    scenario: CalculationScenario | None,
    team_ids: tuple[str, ...],
) -> tuple[ScenarioTriggerInputView, ...]:
    return _trigger_inputs_for_rules(
        definition.rule_items,
        scenario,
        team_ids,
    )


def _trigger_inputs_for_rules(
    rules: Sequence[CalculationRuleItem],
    scenario: CalculationScenario | None,
    team_ids: tuple[str, ...],
) -> tuple[ScenarioTriggerInputView, ...]:
    facts = scenario.trigger_facts if scenario else ()
    inputs: list[ScenarioTriggerInputView] = []
    for rule in rules:
        for effect in rule.effects:
            trigger = effect.rule.trigger
            if (
                trigger is None
                or trigger.event_kind is not BattleEventKind.SUPPORT_ENTRY
            ):
                continue
            selected = next(
                (
                    str(fact.actor)
                    for fact in facts
                    if fact.effect_id == effect.rule.effect_id
                    and fact.event_kind is BattleEventKind.SUPPORT_ENTRY
                    and fact.actor is not None
                ),
                None,
            )
            inputs.append(
                ScenarioTriggerInputView(
                    input_id=f"scenario-trigger:{effect.rule.effect_id}:actor",
                    label=f"{effect.rule.source.label}的入场角色",
                    actor_options=team_ids,
                    required=True,
                    selected_actor=selected,
                    rule_item_id=str(rule.rule_id),
                )
            )
    return tuple(inputs)


def _presentation_diagnostic(subject: str, message: str) -> DiagnosticView:
    return DiagnosticView(
        diagnostic_id=f"presentation:{subject}",
        kind="data-quality",
        message=message,
        blocking=True,
    )


__all__ = [
    "build_character_editor_view",
    "build_drive_disc_editor_view",
    "build_move_calculation_view",
    "build_wengine_editor_view",
]
