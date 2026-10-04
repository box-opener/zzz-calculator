"""Translate named browser inputs into the existing application request."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    CritDisplayMode,
    HistoryRecordMode,
    EnemyMatchProfile,
    MoveCalculationRequest,
    ScenarioRuleStack,
    ScenarioTriggerFact,
    assemble_build,
    calculate_move,
    compile_wengine,
    compile_drive_discs,
    stable_set_id,
)
from core.application.characters.dialyn import DIALYN_ID
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
)
from core.application.characters.vivian.reviewed import (
    DIRECT_BLOSSOM_MUTATION_SOURCE_EFFECT_ID,
    MUTATION_TRIGGERED,
    PROPHECY_TICK_COUNT,
    VIVIAN_ID,
)
from core.application.characters.nekomata.reviewed import (
    NEKOMATA_C1_STUN_BACK_HIT_RULE_ID,
    NEKOMATA_ID,
)
from core.application.equipment.wengine_ids import (
    NEKOMATA_C1_STUN_BACK_HIT_MECHANISM,
)
from core.application.ids import (
    DamageEventSemanticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
)
from core.application.moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ScenarioCondition
from core.application.execution.modifiers import is_panel_modifier_path
from core.types import (
    AnomalyRecordId,
    BattleEventKind,
    BattleStateId,
    BASE_ELEMENT_BY_ELEMENT,
    DamageSubtype,
    DamageType,
    BuildMode,
    BuildStatContribution,
    CharacterBuildDefinition,
    CharacterId,
    BuildContributionTrace,
    CharacterSnapshot,
    CharacterStats,
    CalculationNode,
    NoCritRule,
    FixedMultiplier,
    EffectId,
    Element,
    EnemyId,
    EnemySnapshot,
    InitialCharacterSnapshot,
    Modifier,
    ModifierEffect,
    EffectOperation,
    Resolved,
    EventTemplateId,
    SnapshotRule,
    StateId,
    Unresolved,
    UnresolvedReason,
    WEngineBuildInput,
    WEngineId,
    DriveDiscBuildInput,
    DriveDiscSlot,
    DriveDiscStatKey,
    DriveDiscSubstatRoll,
    EquippedDriveDisc,
)

from core.presentation.assembler import build_move_calculation_view
from core.presentation.calculation import (
    DamageEventView,
    MoveTotalsView,
    PanelSourceResultView,
)
from core.presentation.diagnostics import DiagnosticView
from core.presentation.requests import (
    CharacterBuildInput,
    EnemyInput,
    MoveCalculationViewRequest,
    SelectedTriggerInput,
)
from core.presentation.serialization import to_jsonable
from core.presentation.registry import (
    VIVIAN_DISCHARGE_SELECTION_ENTRY_ID,
    VIVIAN_PROPHECY_TICK_SELECTION_ENTRY_ID,
    registration_for,
    compile_registered_definition,
)
from core.presentation.frostbite import frostbite_crit_damage_controls
from core.presentation.base_stats import (
    character_base_stat_contributions,
    character_base_stats,
)


@dataclass(frozen=True, slots=True)
class _BuiltCharacterRecord:
    snapshot: CharacterSnapshot
    initial_snapshot: InitialCharacterSnapshot
    rule_items: tuple[CalculationRuleItem, ...] = ()
    scenario_conditions: tuple[ScenarioCondition, ...] = ()
    provenance: tuple[BuildContributionTrace, ...] = ()
    damage_event_templates: tuple[DamageEventTemplate, ...] = ()
    derived_damage_events: tuple[DerivedDamageEventTemplateRef, ...] = ()


def calculate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the three display modes and return one presentation response."""

    requested_move_entry_id = str(payload.get("move_entry_id", ""))
    vivian_discharge_selected = (
        requested_move_entry_id == VIVIAN_DISCHARGE_SELECTION_ENTRY_ID
    )
    vivian_prophecy_tick_selected = (
        requested_move_entry_id == VIVIAN_PROPHECY_TICK_SELECTION_ENTRY_ID
    )
    if vivian_prophecy_tick_selected:
        raw_parameters = payload.get("parameter_values", {})
        if isinstance(raw_parameters, Mapping) and raw_parameters.get(
            str(PROPHECY_TICK_COUNT)
        ) is None:
            payload = {
                **payload,
                "parameter_values": {
                    **raw_parameters,
                    str(PROPHECY_TICK_COUNT): 1,
                },
            }
    if vivian_discharge_selected:
        raw_conditions = payload.get("condition_values", {})
        if isinstance(raw_conditions, Mapping) and raw_conditions.get(
            str(MUTATION_TRIGGERED)
        ) is None:
            payload = {
                **payload,
                "condition_values": {
                    **raw_conditions,
                    str(MUTATION_TRIGGERED): True,
                },
            }

    view_request = _presentation_request(payload)
    definitions = _without_static_vivian_blossom_placeholder(
        _compile_definitions(payload)
    )
    primary = definitions[0]
    if vivian_discharge_selected and primary.character_id != VIVIAN_ID:
        raise ValueError("Vivian Discharge selection requires Vivian as current operator")
    supplied_operator = payload.get("current_operator")
    if supplied_operator is not None and str(supplied_operator) != str(
        primary.character_id
    ):
        raise ValueError(
            "current_operator must equal primary_character_id for Direct UI"
        )
    raw_team_ids = payload.get("team_character_ids")
    if not isinstance(raw_team_ids, (list, tuple)):
        raise ValueError("team_character_ids is required")
    team_ids = tuple(CharacterId(str(item)) for item in raw_team_ids)
    if not team_ids or len(set(team_ids)) != len(team_ids):
        raise ValueError("team_character_ids must be a non-empty unique array")
    expected_team_ids = (
        primary.character_id,
        *tuple(
            CharacterId(str(item))
            for item in payload.get("supporting_character_ids", ())
        ),
    )
    if team_ids != expected_team_ids:
        raise ValueError(
            "team_character_ids must exactly equal primary plus supporting character IDs"
        )
    for character_id in team_ids:
        registration_for(character_id)
    definition_ids = {definition.character_id for definition in definitions}
    if not set(team_ids).issubset(definition_ids):
        raise ValueError("every team character must have a compiled definition")
    current_operator = CharacterId(primary.character_id)
    if current_operator not in set(team_ids):
        raise ValueError("current_operator must be a team member")

    build_records = _build_records(view_request.character_builds, definitions)
    additional_rule_items = tuple(
        rule for record in build_records for rule in record.rule_items
    )
    additional_scenario_conditions = tuple(
        condition
        for record in build_records
        for condition in record.scenario_conditions
    )
    additional_damage_event_templates = tuple(
        template
        for record in build_records
        for template in record.damage_event_templates
    )
    additional_derived_damage_events = tuple(
        derived
        for record in build_records
        for derived in record.derived_damage_events
    )
    build_provenance = tuple(
        trace for record in build_records for trace in record.provenance
    )
    if vivian_discharge_selected and "enabled_rule_item_ids" not in payload:
        payload = {
            **payload,
            "enabled_rule_item_ids": tuple(
                str(rule.rule_id)
                for definition in definitions
                for rule in definition.rule_items
                if rule.eligibility is not RuleEligibility.INELIGIBLE
            )
            + tuple(
                str(rule.rule_id)
                for rule in additional_rule_items
                if rule.eligibility is not RuleEligibility.INELIGIBLE
            ),
        }
    enemy_snapshot, enemy_profile, base_modifiers = _enemy_inputs(view_request.enemy)
    scenario = _scenario(
        payload,
        definitions,
        current_operator,
        team_ids,
        additional_rule_items=additional_rule_items,
        additional_scenario_conditions=additional_scenario_conditions,
    )
    move_entry_id = (
        "move-entry:character:1331:ether-corrosion"
        if vivian_discharge_selected
        else view_request.move_entry_id
    )
    base_snapshots = tuple(item.snapshot for item in build_records)
    initial_snapshots = tuple(item.initial_snapshot for item in build_records)
    team_profiles = tuple(
        CharacterMatchProfile(
            character_id=character_id,
            role=registration_for(character_id).role,
        )
        for character_id in team_ids
    )
    executions = {}
    requests = {}
    for mode in (
        CritDisplayMode.NON_CRIT,
        CritDisplayMode.EXPECTED,
        CritDisplayMode.FULL_CRIT,
    ):
        request = MoveCalculationRequest(
            definition=primary,
            supporting_definitions=definitions[1:],
            move_entry_id=MoveEntryId(move_entry_id),
            scenario=scenario,
            battle_state_id=BattleStateId(
                str(payload.get("battle_state_id", "battle:ui"))
            ),
            battle_time=float(payload.get("battle_time", 0.0)),
            base_character_snapshots=base_snapshots,
            initial_character_snapshots=initial_snapshots,
            target_snapshot=enemy_snapshot,
            team_profiles=team_profiles,
            target_profile=enemy_profile,
            additional_rule_items=additional_rule_items,
            additional_damage_event_templates=additional_damage_event_templates,
            additional_derived_damage_events=additional_derived_damage_events,
            additional_scenario_conditions=additional_scenario_conditions,
            base_calculation_modifiers=base_modifiers,
            history_record_mode=HistoryRecordMode.STATIC_SINGLE_CHARACTER,
            crit_display_mode=mode,
        )
        requests[mode] = request
        executions[mode] = calculate_move(request)
    source_labels = {
        str(rule.rule_id): rule.display_name
        for definition in definitions
        for rule in definition.rule_items
    }
    source_labels.update(
        {str(rule.rule_id): rule.display_name for rule in additional_rule_items}
    )
    source_labels.update(
        {
            str(effect.rule.effect_id): effect.rule.source.label
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
        }
    )
    source_labels.update(
        {
            str(effect.rule.effect_id): effect.rule.source.label
            for rule in additional_rule_items
            for effect in rule.effects
        }
    )
    source_types = {
        str(rule.rule_id): rule.source.source_type.value
        for definition in definitions
        for rule in definition.rule_items
    }
    source_types.update(
        {
            str(rule.rule_id): rule.source.source_type.value
            for rule in additional_rule_items
        }
    )
    source_types.update(
        {
            str(effect.rule.effect_id): effect.rule.source.source_type.value
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
        }
    )
    source_types.update(
        {
            str(effect.rule.effect_id): effect.rule.source.source_type.value
            for rule in additional_rule_items
            for effect in rule.effects
        }
    )
    source_owners = {
        str(effect.rule.effect_id): str(effect.rule.owner)
        for definition in definitions
        for rule in definition.rule_items
        for effect in rule.effects
        if effect.rule.owner is not None
    }
    source_owners.update(
        {
            str(effect.rule.effect_id): str(effect.rule.owner)
            for rule in additional_rule_items
            for effect in rule.effects
            if effect.rule.owner is not None
        }
    )
    panel_source_results = _vivian_panel_source_results(
        definitions=definitions,
        requests=requests,
        executions=executions,
        source_labels=source_labels,
        source_types=source_types,
        source_owners=source_owners,
    )
    selected_entry = next(
        (
            item
            for item in primary.move_entries
            if str(item.entry_id) == move_entry_id
        ),
        None,
    )
    view = build_move_calculation_view(
        executions,
        source_labels,
        build_provenance=build_provenance,
        source_types=source_types,
        source_owners=source_owners,
        selected_entry_diagnostics=(
            tuple(
                item for item in selected_entry.diagnostics if not item.blocking
            )
            if selected_entry is not None
            else ()
        ),
    )
    if vivian_discharge_selected:
        vivian_source_result = next(
            (
                item
                for item in panel_source_results
                if item.source_character_id == str(VIVIAN_ID)
            ),
            None,
        )
        if vivian_source_result is None:
            raise ValueError(
                "Vivian Discharge source result is unavailable for her current panel"
            )
        view = replace(
            view,
            move_entry_id=VIVIAN_DISCHARGE_SELECTION_ENTRY_ID,
            events=vivian_source_result.events,
            totals=vivian_source_result.totals,
            diagnostics=_unique_view_diagnostics(
                (*view.diagnostics, *vivian_source_result.diagnostics)
            ),
        )
    return to_jsonable(replace(view, panel_source_results=panel_source_results))


def _without_static_vivian_blossom_placeholder(
    definitions: tuple[CharacterCalculationDefinition, ...],
) -> tuple[CharacterCalculationDefinition, ...]:
    """Keep the browser's separate panel-source model from blocking a known hit.

    The application compiler retains its unresolved child for callers that own
    an explicit historical AnomalyRecord. The browser request instead returns
    per-active-panel source calculations, so that single placeholder is not a
    source of its formal move total.
    """

    updated = []
    for definition in definitions:
        if definition.character_id != VIVIAN_ID:
            updated.append(definition)
            continue
        rules = tuple(
            replace(
                rule,
                effects=tuple(
                    effect
                    for effect in rule.effects
                    if effect.rule.effect_id
                    != DIRECT_BLOSSOM_MUTATION_SOURCE_EFFECT_ID
                ),
            )
            for rule in definition.rule_items
        )
        updated.append(replace(definition, rule_items=rules))
    return tuple(updated)


def _vivian_panel_source_results(
    *,
    definitions: tuple[CharacterCalculationDefinition, ...],
    requests: Mapping[CritDisplayMode, MoveCalculationRequest],
    executions: Mapping[CritDisplayMode, object],
    source_labels: dict[str, str],
    source_types: dict[str, str],
    source_owners: dict[str, str],
) -> tuple[PanelSourceResultView, ...]:
    """Show Vivian mutation results for each active member's own static source.

    Each source is evaluated in a separate calculation using the formal current
    panels already settled for the selected request. These source results are
    presented beside, never added to, the selected move's battle total.
    """

    if not any(item.character_id == VIVIAN_ID for item in definitions):
        return ()

    expected_execution = executions[CritDisplayMode.EXPECTED]
    settled_snapshots = expected_execution.resolved_character_snapshots
    stripped_definitions = tuple(_without_panel_effects(item) for item in definitions)
    base_request = requests[CritDisplayMode.EXPECTED]
    stripped_build_rules = tuple(
        _without_panel_effects_from_rule(item)
        for item in base_request.additional_rule_items
    )
    result_views: list[PanelSourceResultView] = []
    scenario = base_request.scenario
    enabled_rule_ids = {str(item) for item in scenario.enabled_rule_item_ids}
    mutation_condition = next(
        (
            item.value
            for item in scenario.conditions
            if str(item.condition_id) == "condition:vivian:mutation-triggered"
        ),
        None,
    )
    c6_count = next(
        (
            item.value
            for item in scenario.parameters
            if str(item.parameter_id) == "parameter:vivian:cinema6-feather-count"
        ),
        None,
    )
    vivian_definition = next(
        item for item in definitions if item.character_id == VIVIAN_ID
    )
    vivian_rule_items = {str(item.rule_id): item for item in vivian_definition.rule_items}

    for source_definition in definitions:
        registration = registration_for(source_definition.character_id)
        source_entries = _panel_source_entries(source_definition)
        if not source_entries:
            source_element = registration.base_element
            unsupported_diagnostic = (
                None
                if source_element in _FULL_GAUGE_ANOMALY_PROFILE
                else DiagnosticView(
                    diagnostic_id=f"vivian-panel-source:{source_definition.character_id}:{source_element.value}",
                    kind="missing-data",
                    message=(
                        "This active character's element has no supported static "
                        f"attribute-anomaly source: {source_element.value}."
                    ),
                    blocking=True,
                    original_text="The result uses one static full-gauge source from this active character's current panel.",
                )
            )
            specs = ((source_element, None, source_definition, unsupported_diagnostic),)
        else:
            specs = tuple(
                (element, entry, source_definition, None)
                for element, entry, source_definition in source_entries
            )

        for source_element, source_entry, probe_definition, source_data_diagnostic in specs:
            mutation_element_suffix = _VIVIAN_MUTATION_ELEMENT_RULE_SUFFIX.get(
                source_element
            )
            core_rule_id = (
                f"rule:character:1331:core:anomaly-mutation:{mutation_element_suffix}"
                if mutation_element_suffix is not None
                else ""
            )
            c6_rule_id = (
                f"rule:character:1331:cinema6:max-feather-mutation:{mutation_element_suffix}"
                if mutation_element_suffix is not None
                else ""
            )
            core_rule = vivian_rule_items.get(core_rule_id)
            c6_rule = vivian_rule_items.get(c6_rule_id)
            core_enabled = bool(
                core_rule is not None
                and core_rule.eligibility is not RuleEligibility.INELIGIBLE
                and core_rule_id in enabled_rule_ids
            )
            c6_enabled = bool(
                c6_rule is not None
                and c6_rule.eligibility is not RuleEligibility.INELIGIBLE
                and c6_rule_id in enabled_rule_ids
            )
            core_expected = core_enabled and mutation_condition is True
            c6_expected = c6_enabled and c6_count is not None and c6_count > 0
            unresolved_activation = (
                (core_enabled and mutation_condition is None)
                or (c6_enabled and c6_count is None)
            )
            expected_event = core_expected or c6_expected or unresolved_activation

            if not expected_event:
                result_views.append(
                    PanelSourceResultView(
                        source_character_id=str(source_definition.character_id),
                        source_character_name=registration.catalog.display_name,
                        element=source_element.value,
                        events=(),
                        totals=_panel_source_totals((), zero=True),
                    )
                )
                continue

            if source_data_diagnostic is not None:
                totals = _panel_source_totals((), diagnostics=(source_data_diagnostic,))
                result_views.append(
                    PanelSourceResultView(
                        source_character_id=str(source_definition.character_id),
                        source_character_name=registration.catalog.display_name,
                        element=source_element.value,
                        events=(),
                        totals=totals,
                        diagnostics=(source_data_diagnostic,),
                    )
                )
                continue

            if source_entry is None:
                synthetic = _synthetic_panel_source_entry(
                    source_definition.character_id,
                    source_element,
                )
                if synthetic is None:
                    diagnostic = DiagnosticView(
                        diagnostic_id=f"vivian-panel-source:{source_definition.character_id}:{source_element.value}",
                        kind="missing-data",
                        message=(
                            f"No static full-gauge anomaly multiplier is available for {source_element.value}; "
                            "this source result cannot be calculated."
                        ),
                        blocking=True,
                        original_text="The result uses one static full-gauge source from this active character's current panel.",
                    )
                    result_views.append(
                        PanelSourceResultView(
                            source_character_id=str(source_definition.character_id),
                            source_character_name=registration.catalog.display_name,
                            element=source_element.value,
                            events=(),
                            totals=_panel_source_totals((), diagnostics=(diagnostic,)),
                            diagnostics=(diagnostic,),
                        )
                    )
                    continue
                synthetic_entry, synthetic_template = synthetic
                probe_definition = replace(
                    source_definition,
                    move_entries=(*source_definition.move_entries, synthetic_entry),
                    damage_event_templates=(
                        *source_definition.damage_event_templates,
                        synthetic_template,
                    ),
                )
                source_entry = synthetic_entry
            elif source_definition is not probe_definition:
                probe_definition = source_definition

            stripped_probe = _without_panel_effects(probe_definition)
            supporting = tuple(
                _without_panel_effects(item)
                for item in definitions
                if item.character_id != source_definition.character_id
            )
            source_executions = {}
            for mode, original_request in requests.items():
                source_executions[mode] = calculate_move(
                    replace(
                        original_request,
                        definition=stripped_probe,
                        supporting_definitions=supporting,
                        move_entry_id=source_entry.entry_id,
                        base_character_snapshots=settled_snapshots,
                        additional_rule_items=stripped_build_rules,
                    )
                )

            source_view = build_move_calculation_view(
                source_executions,
                source_labels,
                source_types=source_types,
                source_owners=source_owners,
            )
            mutation_events = tuple(
                event
                for event in source_view.events
                if event.damage_subtype == "discharge"
            )
            source_diagnostics: tuple[DiagnosticView, ...] = ()
            if not mutation_events:
                source_diagnostics = _unique_view_diagnostics(
                    (
                        *source_view.diagnostics,
                        DiagnosticView(
                            diagnostic_id=f"vivian-panel-source:{source_definition.character_id}:{source_element.value}:discharge-missing",
                            kind="missing-data",
                            message=(
                                "A Vivian mutation result was selected for this source, "
                                "but no discharge event was produced; inspect the source-rule trace."
                            ),
                            blocking=True,
                            original_text=(
                                core_rule.original_text if core_expected and core_rule is not None
                                else c6_rule.original_text if c6_rule is not None
                                else None
                            ),
                        ),
                    )
                )
                totals = _panel_source_totals((), diagnostics=source_diagnostics)
            else:
                source_diagnostics = _unique_view_diagnostics(source_view.diagnostics)
                totals = _panel_source_totals(
                    mutation_events,
                    diagnostics=source_diagnostics,
                )

            result_views.append(
                PanelSourceResultView(
                    source_character_id=str(source_definition.character_id),
                    source_character_name=registration.catalog.display_name,
                    element=source_element.value,
                    events=mutation_events,
                    totals=totals,
                    diagnostics=source_diagnostics,
                )
            )
    return tuple(result_views)


_FULL_GAUGE_ANOMALY_PROFILE: dict[Element, tuple[float, int]] = {
    Element.PHYSICAL: (7.13, 1),
    Element.LINREN: (7.13, 1),
    Element.ICE: (5.0, 1),
    Element.LIESHUANG: (5.0, 1),
    Element.ETHER: (0.625, 20),
    Element.XUANMO: (0.625, 20),
    Element.FIRE: (0.5, 20),
    Element.ELECTRIC: (1.25, 10),
    Element.WIND: (17.5, 1),
}

_VIVIAN_MUTATION_ELEMENT_RULE_SUFFIX = {
    Element.ETHER: "ether",
    Element.XUANMO: "ether:xuanmo",
    Element.ELECTRIC: "electric",
    Element.FIRE: "fire",
    Element.PHYSICAL: "physical",
    Element.LINREN: "physical:linren",
    Element.ICE: "ice",
    Element.LIESHUANG: "ice:lieshuang",
    Element.WIND: "wind",
}


def _panel_source_entries(definition):
    templates = {item.ref.template_id: item for item in definition.damage_event_templates}
    entries: dict[Element, object] = {}
    for entry in definition.move_entries:
        template = templates.get(entry.main_damage_event.template_id)
        if isinstance(template, AttributeAnomalyDamageEventTemplate):
            entries.setdefault(template.element, entry)
    if entries:
        return tuple((element, entry, definition) for element, entry in entries.items())
    return ()


def _synthetic_panel_source_entry(character_id: CharacterId, element: Element):
    profile = _FULL_GAUGE_ANOMALY_PROFILE.get(element)
    if profile is None:
        return None
    multiplier, source_repeat_count = profile
    repeat_count = source_repeat_count if source_repeat_count > 1 else None
    suffix = f"{character_id}:{element.value}"
    template_id = EventTemplateId(f"template:panel-source:{suffix}")
    semantic_id = DamageEventSemanticId(f"event:panel-source:{suffix}")
    record_id = AnomalyRecordId(f"anomaly:panel-source:{suffix}")
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label=f"当前面板满异常来源（{element.value}）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=element,
    )
    template = AttributeAnomalyDamageEventTemplate(
        ref=ref,
        damage_dealer=character_id,
        element=element,
        anomaly_triggerer=character_id,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:panel-source:{suffix}"),
        character_id=character_id,
        move_id=None,
        display_name=f"当前面板满异常来源（{element.value}）",
        original_text="按静态单人100%积蓄假设，从该上场角色已结算面板创建一份来源记录。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=(
            MultiplierRelation.UNIT_REPEAT
            if repeat_count is not None
            else MultiplierRelation.COMPLETE
        ),
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:panel-source:{suffix}"),
                label=(
                    "每跳异常倍率（满异常持续周期）"
                    if repeat_count is not None
                    else "单次满异常倍率"
                ),
                parameter_name=(
                    "异常单跳倍率" if repeat_count is not None else "满异常倍率"
                ),
                multiplier=FixedMultiplier(Resolved(multiplier)),
                repeat_count=repeat_count,
            ),
        ),
        main_damage_event=ref,
    )
    return entry, template


def _panel_source_totals(
    events: tuple[DamageEventView, ...],
    *,
    zero: bool = False,
    diagnostics: tuple[DiagnosticView, ...] = (),
) -> dict[str, MoveTotalsView]:
    totals: dict[str, MoveTotalsView] = {}
    for mode in CritDisplayMode:
        event_modes = tuple(item.modes[mode.value] for item in events)
        known_values = tuple(
            item.known_value for item in event_modes if item.known_value is not None
        )
        event_diagnostics = _unique_view_diagnostics(
            (
                *diagnostics,
                *(diagnostic for item in event_modes for diagnostic in item.diagnostics),
            )
        )
        totals[mode.value] = MoveTotalsView(
            value=0.0 if zero else sum(known_values) if known_values else None,
            complete=(
                zero
                or (
                    bool(event_modes)
                    and len(known_values) == len(event_modes)
                    and all(item.status == "calculated" for item in event_modes)
                    and not any(item.blocking for item in event_diagnostics)
                )
            ),
            diagnostics=event_diagnostics,
        )
    return totals


def _without_panel_effects(
    definition: CharacterCalculationDefinition,
) -> CharacterCalculationDefinition:
    return replace(
        definition,
        rule_items=tuple(
            _without_panel_effects_from_rule(item)
            for item in definition.rule_items
        ),
    )


def _without_panel_effects_from_rule(rule: CalculationRuleItem) -> CalculationRuleItem:
    return replace(
        rule,
        effects=tuple(
            effect
            for effect in rule.effects
            if not (
                isinstance(effect, ModifierEffect)
                and is_panel_modifier_path(effect.result.modifier_path)
            )
        ),
    )


def _unique_view_diagnostics(items):
    seen = set()
    result = []
    for item in items:
        identity = (item.message, item.blocking)
        if identity not in seen:
            seen.add(identity)
            result.append(item)
    return tuple(result)


def _compile_definitions(
    payload: Mapping[str, Any]
) -> tuple[CharacterCalculationDefinition, ...]:
    primary_id = str(payload.get("primary_character_id", ""))
    if not primary_id:
        raise ValueError("primary_character_id is required")
    supporting = tuple(
        str(item) for item in payload.get("supporting_character_ids", ())
    )
    ids = (primary_id, *supporting)
    if len(set(ids)) != len(ids):
        raise ValueError("primary and supporting character IDs must be unique")
    raw_formation_ids = payload.get("formation_character_ids")
    formation_ids = None
    if raw_formation_ids is not None:
        if not isinstance(raw_formation_ids, (list, tuple)):
            raise ValueError("formation_character_ids must be an ordered array")
        formation_ids = tuple(str(item) for item in raw_formation_ids)
        if len(set(formation_ids)) != len(formation_ids) or set(formation_ids) != set(ids):
            raise ValueError(
                "formation_character_ids must contain each active teammate exactly once"
            )
    configs = payload.get("compile_configs", {})
    if not isinstance(configs, Mapping):
        raise ValueError("compile_configs must be an object")
    definitions = []
    for character_id in ids:
        config = configs.get(character_id, {})
        if not isinstance(config, Mapping):
            raise ValueError(f"compile config must be an object: {character_id}")
        compile_values = dict(config)
        if character_id == str(DIALYN_ID):
            compile_values["formation_character_ids"] = formation_ids
        definitions.append(
            compile_registered_definition(
                character_id,
                compile_values,
                ids,
                strict=False,
            )
        )
    primary_definition = definitions[0]
    frostbite_condition, frostbite_rule = frostbite_crit_damage_controls(
        primary_definition.character_id,
        primary_definition.base_element,
    )
    definitions[0] = replace(
        primary_definition,
        rule_items=(*primary_definition.rule_items, frostbite_rule),
        scenario_conditions=(
            *primary_definition.scenario_conditions,
            frostbite_condition,
        ),
    )
    return tuple(definitions)


def _presentation_request(payload: Mapping[str, Any]) -> MoveCalculationViewRequest:
    """Validate the browser-shaped request before domain assembly."""

    primary_id = str(payload.get("primary_character_id", ""))
    if not primary_id:
        raise ValueError("primary_character_id is required")
    supporting_ids = tuple(
        str(item) for item in payload.get("supporting_character_ids", ())
    )
    team_ids = (primary_id, *supporting_ids)
    supplied_team_ids = payload.get("team_character_ids")
    if not isinstance(supplied_team_ids, (list, tuple)):
        raise ValueError("team_character_ids is required")
    if tuple(str(item) for item in supplied_team_ids) != team_ids:
        raise ValueError(
            "team_character_ids must exactly equal primary plus supporting character IDs"
        )
    raw_formation_ids = payload.get("formation_character_ids")
    if raw_formation_ids is not None:
        if not isinstance(raw_formation_ids, (list, tuple)):
            raise ValueError("formation_character_ids must be an ordered array")
        formation_ids = tuple(str(item) for item in raw_formation_ids)
        if len(set(formation_ids)) != len(formation_ids) or set(formation_ids) != set(team_ids):
            raise ValueError(
                "formation_character_ids must contain each active teammate exactly once"
            )
    raw_builds = payload.get("character_builds")
    if not isinstance(raw_builds, Mapping):
        raise ValueError("character_builds must be an object keyed by character ID")
    builds = []
    for character_id in team_ids:
        if character_id not in raw_builds:
            raise ValueError(f"character build is required: {character_id}")
        raw = raw_builds[character_id]
        if not isinstance(raw, Mapping):
            raise ValueError(f"character build must be an object: {character_id}")
        if "level" not in raw:
            raise ValueError(f"character build level is required: {character_id}")
        try:
            build_mode = BuildMode(
                str(raw.get("build_mode", BuildMode.MANUAL_PANEL.value))
            )
        except ValueError as exc:
            raise ValueError(f"unsupported build_mode: {character_id}") from exc
        if build_mode is BuildMode.EQUIPMENT_BUILD:
            base_stats = raw.get("base_stats")
            if base_stats is None:
                base_stats = _stats_mapping(
                    character_base_stats(character_id, level=int(raw["level"]))
                )
            elif not isinstance(base_stats, Mapping):
                raise ValueError(f"base_stats must be an object: {character_id}")
            stats = raw.get("out_of_combat_stats", base_stats)
        else:
            base_stats = None
            stats = raw.get("out_of_combat_stats", raw.get("stats"))
        if not isinstance(stats, Mapping):
            raise ValueError(f"out_of_combat_stats must be an object: {character_id}")
        if build_mode is BuildMode.MANUAL_PANEL:
            # Preserve the legacy API's required panel sources. Damage-bonus
            # maps remain optional and default to zero in _character_stats.
            required_stats = {
                "attack",
                "crit_rate",
                "crit_damage",
                "penetration_rate",
                "penetration_flat",
            }
            missing_stats = required_stats - set(stats)
            if missing_stats:
                raise ValueError(
                    f"character build stats are missing for {character_id}: "
                    f"{sorted(missing_stats)}"
                )
            element_bonus = stats.get("element_damage_bonus", {})
            if not isinstance(element_bonus, Mapping):
                raise ValueError(
                    f"element_damage_bonus must be an object: {character_id}"
                )
        builds.append(
            CharacterBuildInput(
                character_id=character_id,
                level=int(raw["level"]),
                out_of_combat_stats=stats,
                build_mode=build_mode,
                base_stats=base_stats,
                wengine_id=(
                    str(raw["wengine_id"])
                    if raw.get("wengine_id") is not None
                    else None
                ),
                wengine_level=int(raw.get("wengine_level", 60)),
                wengine_refinement=int(raw.get("wengine_refinement", 1)),
                drive_discs=_parse_drive_discs(raw.get("drive_discs", ())),
            )
        )
    raw_enemy = payload.get("enemy")
    if not isinstance(raw_enemy, Mapping):
        raise ValueError("enemy must be an object")
    resistances = raw_enemy.get("damage_resistance", {})
    if not isinstance(resistances, Mapping):
        raise ValueError("enemy damage_resistance must be an object")
    required_enemy_fields = {
        "enemy_id",
        "level",
        "initial_defense",
        "damage_resistance",
        "damage_reduction",
        "stun_vulnerability_bonus",
        "is_stunned",
    }
    missing_enemy_fields = required_enemy_fields - set(raw_enemy)
    if missing_enemy_fields:
        raise ValueError(f"enemy fields are missing: {sorted(missing_enemy_fields)}")
    if not isinstance(raw_enemy["is_stunned"], bool):
        raise ValueError("enemy is_stunned must be a boolean")
    enemy = EnemyInput(
        enemy_id=str(raw_enemy["enemy_id"]),
        level=int(raw_enemy["level"]),
        initial_defense=float(raw_enemy["initial_defense"]),
        damage_resistance=resistances,
        damage_reduction=float(raw_enemy["damage_reduction"]),
        stun_vulnerability_bonus=float(raw_enemy["stun_vulnerability_bonus"]),
        is_stunned=raw_enemy["is_stunned"],
    )
    selected = payload.get("selected_trigger_inputs", ())
    if not isinstance(selected, (list, tuple)):
        raise ValueError("selected_trigger_inputs must be an array")
    selected_inputs = tuple(
        SelectedTriggerInput(
            input_id=str(item.get("input_id", "")),
            actor_id=(
                str(item["actor_id"]) if item.get("actor_id") is not None else None
            ),
        )
        for item in selected
        if isinstance(item, Mapping)
    )
    if len(selected_inputs) != len(selected):
        raise ValueError("selected trigger input must be an object")
    if any(
        item.actor_id is None or not item.actor_id.strip() for item in selected_inputs
    ):
        raise ValueError(
            "an unspecified trigger must be omitted instead of sending an empty actor"
        )
    selected_conditions = payload.get("condition_values", {})
    selected_parameters = payload.get("parameter_values", {})
    if not isinstance(selected_conditions, Mapping) or not isinstance(
        selected_parameters, Mapping
    ):
        raise ValueError("condition_values and parameter_values must be objects")
    move_entry_id = str(payload.get("move_entry_id", ""))
    if not move_entry_id.strip():
        raise ValueError("move_entry_id is required")
    return MoveCalculationViewRequest(
        primary_character_id=primary_id,
        supporting_character_ids=supporting_ids,
        move_entry_id=move_entry_id,
        character_builds=tuple(builds),
        enemy=enemy,
        selected_condition_values=selected_conditions,
        selected_parameter_values=selected_parameters,
        enabled_rule_item_ids=frozenset(
            str(item) for item in payload.get("enabled_rule_item_ids", ())
        ),
        selected_trigger_inputs=selected_inputs,
        rule_stack_counts=(
            {
                str(key): int(value)
                for key, value in payload.get("rule_stack_counts", {}).items()
            }
            if isinstance(payload.get("rule_stack_counts", {}), Mapping)
            else {}
        ),
    )


def _parse_drive_discs(raw_value: object) -> tuple[EquippedDriveDisc, ...]:
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, (str, bytes)):
        raise ValueError("drive_discs must be an array")
    discs = []
    for raw in raw_value:
        if not isinstance(raw, Mapping):
            raise ValueError("Drive Disc must be an object")
        raw_substats = raw.get("substats", ())
        if not isinstance(raw_substats, Sequence) or isinstance(
            raw_substats,
            (str, bytes),
        ):
            raise ValueError("Drive Disc substats must be an array")
        substats = []
        for item in raw_substats:
            if not isinstance(item, Mapping):
                raise ValueError("Drive Disc substat must be an object")
            substats.append(
                DriveDiscSubstatRoll(
                    DriveDiscStatKey(str(item.get("stat", ""))),
                    int(item.get("roll_count", 0)),
                )
            )
        raw_main_stat = raw.get("main_stat")
        main_stat = (
            None
            if raw_main_stat is None or str(raw_main_stat) == ""
            else DriveDiscStatKey(str(raw_main_stat))
        )
        discs.append(
            EquippedDriveDisc(
                slot=DriveDiscSlot(int(raw.get("slot", 0))),
                set_id=stable_set_id(
                    str(raw.get("set_id", "")).removeprefix("drive-disc:")
                ),
                main_stat=main_stat,
                substats=tuple(substats),
            )
        )
    return tuple(discs)


def _build_records(
    builds: tuple[CharacterBuildInput, ...],
    definitions: tuple[CharacterCalculationDefinition, ...],
) -> tuple[_BuiltCharacterRecord, ...]:
    records = []
    nekomata_definition = next(
        (item for item in definitions if item.character_id == NEKOMATA_ID),
        None,
    )
    nekomata_c1_unlocked = bool(
        nekomata_definition
        and any(
            item.rule_id == NEKOMATA_C1_STUN_BACK_HIT_RULE_ID
            and item.eligibility is RuleEligibility.ELIGIBLE
            for item in nekomata_definition.rule_items
        )
    )
    for build in builds:
        character_id = CharacterId(build.character_id)
        registration = registration_for(character_id)
        if build.build_mode is BuildMode.MANUAL_PANEL:
            stats = _character_stats(build.out_of_combat_stats, character_id)
            resolved_build = assemble_build(
                CharacterBuildDefinition(
                    character_id=character_id,
                    level=build.level,
                    mode=BuildMode.MANUAL_PANEL,
                    manual_panel_stats=stats,
                )
            )
            records.append(
                _BuiltCharacterRecord(
                    snapshot=resolved_build.character_snapshot,
                    initial_snapshot=resolved_build.initial_snapshot,
                    provenance=resolved_build.provenance,
                )
            )
            continue

        if build.base_stats is None:
            base_stats = character_base_stats(character_id, level=build.level)
        else:
            base_stats = _character_stats(build.base_stats, character_id)
        rule_items: tuple[CalculationRuleItem, ...] = ()
        conditions: tuple[ScenarioCondition, ...] = ()
        damage_event_templates: tuple[DamageEventTemplate, ...] = ()
        derived_damage_events: tuple[DerivedDamageEventTemplateRef, ...] = ()
        contributions: tuple[BuildStatContribution, ...] = (
            character_base_stat_contributions(character_id)
        )
        if build.wengine_id is not None:
            owner_capabilities = registration.equipment_capabilities
            if (
                character_id == NEKOMATA_ID
                and nekomata_c1_unlocked
                and owner_capabilities is not None
            ):
                owner_capabilities = replace(
                    owner_capabilities,
                    mechanisms=owner_capabilities.mechanisms
                    | frozenset({NEKOMATA_C1_STUN_BACK_HIT_MECHANISM}),
                )
            wengine = compile_wengine(
                WEngineBuildInput(
                    WEngineId(build.wengine_id),
                    character_id,
                    level=build.wengine_level,
                    refinement=build.wengine_refinement,
                ),
                owner_capabilities=owner_capabilities,
            )
            if not wengine.complete:
                messages = "; ".join(item.message for item in wengine.diagnostics)
                raise ValueError(messages)
            contributions = (*contributions, *wengine.contributions)
            rule_items = wengine.rule_items
            conditions = wengine.scenario_conditions
            damage_event_templates = wengine.damage_event_templates
            derived_damage_events = wengine.derived_damage_events
        if build.drive_discs:
            drive = compile_drive_discs(
                DriveDiscBuildInput(character_id, build.drive_discs),
                owner_capabilities=registration.equipment_capabilities,
            )
            if not drive.complete:
                messages = "; ".join(item.message for item in drive.diagnostics)
                raise ValueError(messages)
            contributions = (*contributions, *drive.contributions)
            rule_items = (*rule_items, *drive.rule_items)
            conditions = (*conditions, *drive.scenario_conditions)
        resolved_build = assemble_build(
            CharacterBuildDefinition(
                character_id=character_id,
                level=build.level,
                mode=BuildMode.EQUIPMENT_BUILD,
                base_stats=base_stats,
                contributions=contributions,
            ),
            rule_items=rule_items,
        )
        if not resolved_build.complete:
            messages = "; ".join(item.message for item in resolved_build.diagnostics)
            raise ValueError(
                messages or f"equipment build is unresolved: {character_id}"
            )
        records.append(
            _BuiltCharacterRecord(
                snapshot=resolved_build.character_snapshot,
                initial_snapshot=resolved_build.initial_snapshot,
                rule_items=rule_items,
                scenario_conditions=conditions,
                provenance=resolved_build.provenance,
                damage_event_templates=damage_event_templates,
                derived_damage_events=derived_damage_events,
            )
        )
    return tuple(records)


def _character_stats(
    raw: Mapping[str, Any], character_id: CharacterId
) -> CharacterStats:
    values = dict(raw)
    element_bonus = raw.get("element_damage_bonus", {})
    if not isinstance(element_bonus, Mapping):
        raise ValueError(f"element_damage_bonus must be an object: {character_id}")
    bonuses = {
        _element(key): Resolved(float(value)) for key, value in element_bonus.items()
    }
    bonuses.setdefault(registration_for(character_id).base_element, Resolved(0.0))

    def stat(name: str):
        if name in values:
            return Resolved(float(values[name]))
        return Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=f"character stat is not supplied: {name}",
        )

    return CharacterStats(
        hp=stat("hp"),
        attack=stat("attack"),
        defense=stat("defense"),
        impact=stat("impact"),
        crit_rate=stat("crit_rate"),
        crit_damage=stat("crit_damage"),
        anomaly_mastery=stat("anomaly_mastery"),
        anomaly_proficiency=stat("anomaly_proficiency"),
        penetration_rate=stat("penetration_rate"),
        penetration_flat=stat("penetration_flat"),
        energy_regen=stat("energy_regen"),
        element_damage_bonus=bonuses,
    )


def _stats_mapping(stats: CharacterStats) -> dict[str, object]:
    """Convert reviewed domain stats to the browser/build input shape."""

    def value(item):
        if isinstance(item, Resolved):
            return float(item.value)
        raise ValueError(f"reviewed character base stat is unresolved: {item.notes}")

    return {
        "hp": value(stats.hp),
        "attack": value(stats.attack),
        "defense": value(stats.defense),
        "impact": value(stats.impact),
        "crit_rate": value(stats.crit_rate),
        "crit_damage": value(stats.crit_damage),
        "anomaly_mastery": value(stats.anomaly_mastery),
        "anomaly_proficiency": value(stats.anomaly_proficiency),
        "penetration_rate": value(stats.penetration_rate),
        "penetration_flat": value(stats.penetration_flat),
        "energy_regen": value(stats.energy_regen),
        "element_damage_bonus": {
            element.value: value(item)
            for element, item in stats.element_damage_bonus.items()
        },
    }


def _enemy_inputs(enemy: EnemyInput):
    enemy_id = EnemyId(enemy.enemy_id)
    specified_resistances: dict[Element, float] = {}
    for key, value in enemy.damage_resistance.items():
        element = _element(key)
        base_element = BASE_ELEMENT_BY_ELEMENT[element]
        numeric = float(value)
        previous = specified_resistances.get(base_element)
        if previous is not None and previous != numeric:
            raise ValueError(
                "enemy resistance aliases must share the base-element value: "
                f"{base_element.value}"
            )
        specified_resistances[base_element] = numeric
    base_resistances = {
        element: Resolved(specified_resistances.get(element, 0.0))
        for element in Element
        if BASE_ELEMENT_BY_ELEMENT[element] is element
    }
    resistances = {
        element: base_resistances[BASE_ELEMENT_BY_ELEMENT[element]]
        for element in Element
    }
    snapshot = EnemySnapshot(
        enemy_id=enemy_id,
        level=enemy.level,
        initial_defense=Resolved(enemy.initial_defense),
        damage_resistance=resistances,
        anomaly_buildup_resistance={},
        daze_resistance=Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes="daze resistance is not supplied by the Direct UI",
        ),
        damage_reduction=Resolved(enemy.damage_reduction),
        is_stunned=enemy.is_stunned,
    )
    profile = EnemyMatchProfile(
        enemy_id=enemy_id,
        states=(
            frozenset({StateId("state:enemy:stunned")})
            if enemy.is_stunned
            else frozenset()
        ),
    )
    base = Modifier(
        effect_id=EffectId("base:ui:enemy-stun-vulnerability"),
        modifier_path=CalculationNode.ENEMY_STUN_VULNERABILITY,
        operation=EffectOperation.ADD,
        value=Resolved(enemy.stun_vulnerability_bonus),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )
    return snapshot, profile, (base,)


def _scenario(
    payload: Mapping[str, Any],
    definitions: tuple[CharacterCalculationDefinition, ...],
    current_operator: CharacterId,
    team_ids: tuple[CharacterId, ...],
    *,
    additional_rule_items: tuple[CalculationRuleItem, ...] = (),
    additional_scenario_conditions: tuple[ScenarioCondition, ...] = (),
) -> CalculationScenario:
    condition_values = payload.get("condition_values", {})
    parameter_values = payload.get("parameter_values", {})
    if not isinstance(condition_values, Mapping) or not isinstance(
        parameter_values, Mapping
    ):
        raise ValueError("condition_values and parameter_values must be objects")
    known_condition_ids = {
        condition.condition_id
        for definition in definitions
        for condition in definition.scenario_conditions
    }
    known_condition_ids.update(
        condition.condition_id for condition in additional_scenario_conditions
    )
    known_parameter_ids = {
        parameter.parameter_id
        for definition in definitions
        for parameter in definition.scenario_parameters
    }
    unknown_conditions = set(condition_values) - {
        str(item) for item in known_condition_ids
    }
    if unknown_conditions:
        raise ValueError(f"unknown scenario conditions: {sorted(unknown_conditions)}")
    unknown_parameters = set(parameter_values) - {
        str(item) for item in known_parameter_ids
    }
    if unknown_parameters:
        raise ValueError(f"unknown scenario parameters: {sorted(unknown_parameters)}")
    static_condition_values = {
        str(condition.condition_id): condition.value
        for definition in definitions
        for condition in definition.scenario_conditions
        if condition.resolution.value == "static"
    }
    static_condition_values.update(
        {
            str(condition.condition_id): condition.value
            for condition in additional_scenario_conditions
            if condition.resolution.value == "static"
        }
    )
    overridden_static = set(condition_values) & set(static_condition_values)
    if overridden_static:
        raise ValueError(
            "static scenario conditions must not be submitted: "
            f"{sorted(overridden_static)}"
        )
    conditions = []
    parameters = []
    for definition in definitions:
        for condition in definition.scenario_conditions:
            if any(item.condition_id == condition.condition_id for item in conditions):
                continue
            if condition.resolution.value == "static":
                conditions.append(condition)
            else:
                conditions.append(
                    replace(
                        condition,
                        value=condition_values.get(
                            str(condition.condition_id), condition.value
                        ),
                    )
                )
        for parameter in definition.scenario_parameters:
            if any(item.parameter_id == parameter.parameter_id for item in parameters):
                continue
            parameters.append(
                replace(
                    parameter,
                    value=parameter_values.get(
                        str(parameter.parameter_id), parameter.value
                    ),
                )
            )
    for condition in additional_scenario_conditions:
        if any(item.condition_id == condition.condition_id for item in conditions):
            continue
        if condition.resolution.value == "static":
            conditions.append(condition)
        else:
            conditions.append(
                replace(
                    condition,
                    value=condition_values.get(
                        str(condition.condition_id), condition.value
                    ),
                )
            )
    for condition_id, value in condition_values.items():
        if value is not None and not isinstance(value, bool):
            raise ValueError(
                f"scenario condition must be boolean or null: {condition_id}"
            )
    for parameter_id, value in parameter_values.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValueError(
                f"scenario parameter must be integer or null: {parameter_id}"
            )
    trigger_facts = []
    trigger_inputs = payload.get("selected_trigger_inputs", ())
    if not isinstance(trigger_inputs, (list, tuple)):
        raise ValueError("selected_trigger_inputs must be an array")
    for item in trigger_inputs:
        if not isinstance(item, Mapping):
            raise ValueError("selected trigger input must be an object")
        input_id = str(item.get("input_id", ""))
        prefix = "scenario-trigger:"
        suffix = ":actor"
        if not input_id.startswith(prefix) or not input_id.endswith(suffix):
            raise ValueError(f"invalid presentation trigger input: {input_id}")
        effect_id = EffectId(input_id[len(prefix) : -len(suffix)])
        known_trigger_effect_ids = {
            effect.rule.effect_id
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
            if effect.rule.trigger is not None
            and effect.rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        }
        known_trigger_effect_ids.update(
            effect.rule.effect_id
            for rule in additional_rule_items
            for effect in rule.effects
            if effect.rule.trigger is not None
            and effect.rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        )
        if effect_id not in known_trigger_effect_ids:
            raise ValueError(f"unknown presentation trigger input: {input_id}")
        actor = item.get("actor_id")
        actor_id = CharacterId(str(actor)) if actor is not None else None
        if actor_id is not None and actor_id not in team_ids:
            raise ValueError("trigger actor must be a team member")
        trigger_facts.append(
            ScenarioTriggerFact(
                effect_id=effect_id,
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=actor_id,
            )
        )
    enabled = payload.get("enabled_rule_item_ids")
    if "enabled_rule_item_ids" not in payload:
        raise ValueError("enabled_rule_item_ids is required")
    known_rule_ids = {
        rule.rule_id for definition in definitions for rule in definition.rule_items
    }
    known_rule_ids.update(rule.rule_id for rule in additional_rule_items)
    if enabled is None:
        enabled_ids = frozenset(
            {
                rule.rule_id
                for definition in definitions
                for rule in definition.rule_items
                if rule.eligibility.value != "ineligible"
            }
            | {
                rule.rule_id
                for rule in additional_rule_items
                if rule.eligibility.value != "ineligible"
            }
        )
    else:
        if not isinstance(enabled, (list, tuple, set, frozenset)):
            raise ValueError("enabled_rule_item_ids must be an array")
        enabled_ids = frozenset(RuleItemId(str(item)) for item in enabled)
        unknown_enabled = enabled_ids - known_rule_ids
        if unknown_enabled:
            raise ValueError(
                "enabled_rule_item_ids contains unknown rules: "
                f"{sorted(map(str, unknown_enabled))}"
            )
    stack_counts = payload.get("rule_stack_counts", {})
    if not isinstance(stack_counts, Mapping):
        raise ValueError("rule_stack_counts must be an object")
    return CalculationScenario(
        scenario_id=str(payload.get("scenario_id", "ui")),
        current_operator=current_operator,
        conditions=tuple(conditions),
        parameters=tuple(parameters),
        trigger_facts=tuple(trigger_facts),
        enabled_rule_item_ids=enabled_ids,
        rule_stack_counts=tuple(
            ScenarioRuleStack(RuleItemId(str(rule_id)), int(value))
            for rule_id, value in stack_counts.items()
        ),
    )


def _element(value: Any) -> Element:
    aliases = {
        "物理": Element.PHYSICAL,
        "物理属性": Element.PHYSICAL,
        "以太": Element.ETHER,
        "以太属性": Element.ETHER,
        "火": Element.FIRE,
        "火属性": Element.FIRE,
        "电": Element.ELECTRIC,
        "电属性": Element.ELECTRIC,
        "冰": Element.ICE,
        "冰属性": Element.ICE,
        "风": Element.WIND,
        "风属性": Element.WIND,
        "明光": Element.LUMINANCE,
        "烈霜": Element.LIESHUANG,
        "玄墨": Element.XUANMO,
        "凛刃": Element.LINREN,
    }
    if str(value) in aliases:
        return aliases[str(value)]
    try:
        return Element(str(value))
    except ValueError as exc:
        raise ValueError(f"unsupported element value: {value}") from exc


__all__ = ["calculate_payload"]
