"""Resolve matched Effects into settlement snapshots and calculator Modifiers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import floor, prod

from core.types import (
    AllCondition,
    AlwaysCondition,
    AnyCondition,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    DirectDamageEvent,
    PenetrationDamageEvent,
    DynamicIdentity,
    DynamicIdentityCondition,
    EffectId,
    EffectOperation,
    EventCreationEffect,
    GuaranteedCritEffect,
    Modifier,
    ModifierEffect,
    Effect,
    EffectTarget,
    InitialCharacterSnapshot,
    PanelStatDerivedValue,
    ScenarioParameterDerivedValue,
    PanelStatThresholdCondition,
    Resolved,
    RuleStackCondition,
    ScenarioParameterRangeCondition,
    NotCondition,
    StandardCritRule,
    StandardVulnerabilityPolicy,
    Unresolved,
    VeilVulnerabilityPolicy,
    VulnerabilitySettlementPolicy,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..ids import RuleItemId
from ..matching import EffectMatchStatus
from ..rules import CalculationRuleItem, RuleEligibility
from ..scenario import CalculationScenario
from .contracts import EventStatModifier, PanelModifierExecutionTrace


@dataclass(frozen=True, slots=True)
class MatchedEffectApplication:
    """A matched Effect together with its owning RuleItem's stack count."""

    effect: Effect
    rule_item_id: RuleItemId | None = None
    stack_count: int = 1
    non_stacking_group_id: str | None = None

    def __post_init__(self) -> None:
        if self.stack_count < 0:
            raise ValueError("matched Effect stack_count must be non-negative")


def _select_non_stacking_event_effects(
    applications: tuple[object, ...],
    snapshots: tuple[CharacterSnapshot, ...],
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    scenario: CalculationScenario | None,
    event: object | None,
    diagnostics: list[CalculationDiagnostic],
) -> tuple[object, ...]:
    candidates: dict[
        tuple[str, CharacterId, CalculationNode],
        dict[str, list[tuple[MatchedEffectApplication, float, EffectOperation]]],
    ] = {}
    unresolved: dict[
        tuple[str, CharacterId, CalculationNode],
        list[tuple[MatchedEffectApplication, str, str]],
    ] = {}
    passthrough: list[object] = []

    for raw_application in applications:
        application = (
            raw_application
            if isinstance(raw_application, MatchedEffectApplication)
            else MatchedEffectApplication(raw_application)
        )
        effect = application.effect
        group_id = application.non_stacking_group_id
        if group_id is None or not isinstance(effect, ModifierEffect):
            passthrough.append(application)
            continue
        source_id = (
            str(application.rule_item_id)
            if application.rule_item_id is not None
            else str(effect.rule.effect_id)
        )

        if isinstance(event, (DirectDamageEvent, PenetrationDamageEvent)) and isinstance(
            event.crit_rule, StandardCritRule
        ) and effect.result.modifier_path in {
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        }:
            recipient = event.crit_rule.stat_owner
        elif event is not None and hasattr(event, "metadata"):
            recipient = event.metadata.damage_dealer
        elif effect.rule.owner is not None:
            recipient = effect.rule.owner
        else:
            recipient = CharacterId("unknown-non-stacking-recipient")
        key = (group_id, recipient, effect.result.modifier_path)

        # A zero-layer instance contributes nothing. Do not require its value
        # source to resolve before comparing the other active copies.
        if application.stack_count == 0:
            continue

        if not isinstance(effect.result.value, Resolved):
            effect_diagnostics: list[CalculationDiagnostic] = []
            resolved_effect = _resolve_effect_value(
                effect,
                initial_character_snapshots,
                effect_diagnostics,
                scenario=scenario,
                current_character_snapshots=snapshots,
            )
            if resolved_effect is None or not isinstance(
                resolved_effect.result.value, Resolved
            ):
                message = (
                    effect_diagnostics[0].message
                    if effect_diagnostics
                    else (
                        effect.result.value.notes
                        if isinstance(effect.result.value, Unresolved)
                        else "the matched effect value is not resolved"
                    )
                )
                unresolved.setdefault(key, []).append((application, source_id, message))
                continue
            application = replace(application, effect=resolved_effect)
            effect = resolved_effect

        value = effect.result.value
        assert isinstance(value, Resolved)
        if effect.result.operation is EffectOperation.ADD:
            effective_value = value.value * application.stack_count
        elif application.stack_count == 1:
            effective_value = value.value
        else:
            unresolved.setdefault(key, []).append(
                (
                    application,
                    source_id,
                    "stacked non-ADD effects cannot be compared as one static maximum",
                )
            )
            continue
        candidates.setdefault(key, {}).setdefault(source_id, []).append(
            (application, effective_value, effect.result.operation)
        )

    selected: list[object] = list(passthrough)
    for group_id, recipient, path in sorted(
        set(candidates) | set(unresolved),
        key=lambda item: (item[0], str(item[1]), item[2].value),
    ):
        key = (group_id, recipient, path)
        source_candidates = candidates.get(key, {})
        group_unresolved = unresolved.get(key, [])
        source_ids = set(source_candidates) | {item[1] for item in group_unresolved}
        if len(source_ids) == 1:
            source_id = next(iter(source_ids))
            selected.extend(
                item[0] for item in source_candidates.get(source_id, ())
            )
            selected.extend(
                item[0] for item in group_unresolved if item[1] == source_id
            )
            continue
        if group_unresolved:
            all_applications = [
                *(
                    candidate[0]
                    for source_effects in source_candidates.values()
                    for candidate in source_effects
                ),
                *(item[0] for item in group_unresolved),
            ]
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:{group_id}:{recipient}:{path.value}:max-unresolved"
                    ),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=(
                        "Matched same-name event effects for this recipient and region "
                        "could not all be resolved, so the maximum was not selected. "
                        + "; ".join(
                            dict.fromkeys(reason for _, _, reason in group_unresolved)
                        )
                    ),
                    blocking=True,
                    original_text=(
                        group_unresolved[0][0].effect.rule.source.raw_text
                        if group_unresolved
                        and isinstance(group_unresolved[0][0].effect, ModifierEffect)
                        else None
                    ),
                    candidates=tuple(
                        (
                            item.effect.rule.source.raw_text
                            or item.effect.rule.source.label
                            if isinstance(item.effect, ModifierEffect)
                            else str(item.effect.rule.effect_id)
                        )
                        for item in all_applications
                    ),
                )
            )
            continue
        if not source_candidates:
            continue
        operations = {
            item[2]
            for source_effects in source_candidates.values()
            for item in source_effects
        }
        if len(operations) != 1:
            group_candidates = [
                item
                for source_effects in source_candidates.values()
                for item in source_effects
            ]
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:{group_id}:{recipient}:{path.value}:max-operation"
                    ),
                    kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    message=(
                        "Matched same-name event effects use different operations, "
                        "so their values cannot be compared for a static maximum: "
                        + ", ".join(sorted(item.value for item in operations))
                    ),
                    blocking=True,
                    original_text=(
                        group_candidates[0][0].effect.rule.source.raw_text
                        if group_candidates
                        else None
                    ),
                    candidates=tuple(
                        item[0].effect.rule.source.raw_text
                        or item[0].effect.rule.source.label
                        for item in group_candidates
                    ),
                )
            )
            continue
        operation = next(iter(operations))
        effective_by_source: dict[str, float] = {}
        unsupported_source: tuple[str, tuple[MatchedEffectApplication, ...]] | None = None
        for source_id, source_effects in source_candidates.items():
            if operation is EffectOperation.ADD:
                effective_by_source[source_id] = sum(item[1] for item in source_effects)
            elif operation is EffectOperation.MULTIPLY:
                effective_by_source[source_id] = prod(item[1] for item in source_effects)
            else:
                unsupported_source = (
                    source_id,
                    tuple(item[0] for item in source_effects),
                )
                break
        if unsupported_source is not None:
            source_id, source_apps = unsupported_source
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:{group_id}:{recipient}:{path.value}:max-operation"
                    ),
                    kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    message=(
                        "Matched same-name event effects use an operation that cannot "
                        "be compared as a static maximum: "
                        f"{operation.value}"
                    ),
                    blocking=True,
                    original_text=(
                        source_apps[0].effect.rule.source.raw_text
                        if source_apps
                        and isinstance(source_apps[0].effect, ModifierEffect)
                        else None
                    ),
                    candidates=tuple(
                        app.effect.rule.source.raw_text
                        or app.effect.rule.source.label
                        for app in source_apps
                        if isinstance(app.effect, ModifierEffect)
                    ),
                )
            )
            continue
        winner_source = max(
            effective_by_source,
            key=lambda source_id: (effective_by_source[source_id], source_id),
        )
        selected.extend(
            item[0] for item in source_candidates[winner_source]
        )
    return tuple(selected)


_PANEL_NODES = frozenset(
    {
        CalculationNode.CHARACTER_CURRENT_MAX_HP,
        CalculationNode.CHARACTER_CURRENT_ATTACK,
        CalculationNode.CHARACTER_CURRENT_DEFENSE,
        CalculationNode.CHARACTER_CURRENT_IMPACT,
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_FLAT,
        CalculationNode.CHARACTER_CURRENT_ENERGY_REGEN,
        CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
    }
)


def is_panel_modifier_path(path: CalculationNode) -> bool:
    """Return whether a modifier is resolved into a character snapshot."""

    return path in _PANEL_NODES

_PANEL_FLAT_FIELDS = {
    CalculationNode.CHARACTER_COMBAT_HP_FLAT_BONUS: "hp",
    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS: "attack",
    CalculationNode.CHARACTER_COMBAT_DEFENSE_FLAT_BONUS: "defense",
    CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS: "impact",
    CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS: "anomaly_mastery",
    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS: "anomaly_proficiency",
    CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS: "energy_regen",
}

_PANEL_PERCENT_FIELDS = {
    CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS: "hp",
    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS: "attack",
    CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS: "defense",
    CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS: "impact",
    CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS: "anomaly_mastery",
    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS: "anomaly_proficiency",
    CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS: "energy_regen",
}


@dataclass(frozen=True, slots=True)
class ModifierApplicationResult:
    character_snapshots: tuple[CharacterSnapshot, ...]
    event_modifiers: tuple[Modifier, ...]
    event_stat_modifiers: tuple[EventStatModifier, ...] = ()
    event_multiplier_modifiers: tuple[Modifier, ...] = ()
    event_crit_guarantee_effect_ids: tuple[EffectId, ...] = ()
    vulnerability_policy: VulnerabilitySettlementPolicy = field(
        default_factory=StandardVulnerabilityPolicy
    )
    applied_panel_effect_ids: frozenset[EffectId] = frozenset()
    panel_traces: tuple[PanelModifierExecutionTrace, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


def apply_matched_modifiers(
    base_character_snapshots: tuple[CharacterSnapshot, ...],
    base_calculation_modifiers: tuple[Modifier, ...],
    matched_effects: tuple[object, ...],
    current_operator: CharacterId,
    *,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = (),
    scenario: CalculationScenario | None = None,
    event: object | None = None,
    apply_panel: bool = True,
    applied_panel_effect_ids: frozenset[EffectId] = frozenset(),
) -> ModifierApplicationResult:
    """Apply event-independent panel Effects and normalize event modifiers.

    Effects have already passed target/condition/filter matching.  This layer
    therefore applies only their declared result operations; it never searches
    BattleState or resolves why an Effect matched.
    """

    diagnostics: list[CalculationDiagnostic] = []
    snapshots = tuple(base_character_snapshots)
    for modifier in base_calculation_modifiers:
        if modifier.operation is not EffectOperation.ADD:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "base-operation",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "base calculation modifiers must already use ADD",
                )
            )
        if modifier.modifier_path in _PANEL_NODES:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "base-panel-node",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "base calculation modifiers cannot contain panel nodes",
                )
            )

    matched_effects = _select_non_stacking_event_effects(
        tuple(matched_effects),
        snapshots,
        initial_character_snapshots,
        scenario,
        event,
        diagnostics,
    )

    panel_effects: list[tuple[ModifierEffect, int]] = []
    rule_modifiers: list[Modifier] = []
    event_stat_modifiers: list[EventStatModifier] = []
    event_multiplier_modifiers: list[Modifier] = []
    event_crit_guarantee_effect_ids: list[EffectId] = []
    vulnerability_policy: VulnerabilitySettlementPolicy = StandardVulnerabilityPolicy()
    vulnerability_policy_effect_seen = False
    for application in matched_effects:
        if isinstance(application, MatchedEffectApplication):
            effect = application.effect
            stack_count = application.stack_count
        else:
            effect = application
            stack_count = 1
        if isinstance(effect, GuaranteedCritEffect):
            if stack_count != 1:
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "guaranteed-crit-stack",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "guaranteed crit Effects do not support stacks",
                    )
                )
                continue
            if not isinstance(event, (DirectDamageEvent, PenetrationDamageEvent)) or not isinstance(
                event.crit_rule, StandardCritRule
            ):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "guaranteed-crit-event",
                        DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        "guaranteed crit Effects require a standard-crit Direct or Penetration event",
                    )
                )
                continue
            event_crit_guarantee_effect_ids.append(effect.rule.effect_id)
            continue
        if not isinstance(effect, ModifierEffect):
            if stack_count != 1 and not isinstance(effect, EventCreationEffect):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "stack-effect",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "stacked non-Modifier effects are unsupported",
                    )
                )
            continue
        effect = _resolve_effect_value(
            effect,
            initial_character_snapshots,
            diagnostics,
            scenario=scenario,
            current_character_snapshots=snapshots,
        )
        if effect is None:
            continue
        if effect.result.modifier_path in _PANEL_NODES and apply_panel:
            if _is_recipient_panel_effect(effect):
                panel_effects.append((effect, stack_count))
                continue
            event_stat = _event_stat_modifier(
                effect,
                event,
                stack_count,
                diagnostics,
            )
            if event_stat is not None:
                event_stat_modifiers.append(event_stat)
            continue
        if effect.result.modifier_path in _PANEL_NODES:
            if _is_recipient_panel_effect(effect):
                if effect.rule.effect_id not in applied_panel_effect_ids:
                    diagnostics.append(
                        _diagnostic(
                            str(effect.rule.effect_id),
                            "derived-panel",
                            DiagnosticKind.UNSUPPORTED_CALCULATOR,
                            "a panel Effect matched a derived event but was not applied globally",
                        )
                    )
                continue
            event_stat = _event_stat_modifier(
                effect,
                event,
                stack_count,
                diagnostics,
            )
            if event_stat is not None:
                event_stat_modifiers.append(event_stat)
            continue
        if effect.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER:
            event_multiplier = _event_multiplier_modifier(
                effect,
                diagnostics,
                stack_count,
            )
            if event_multiplier is not None:
                event_multiplier_modifiers.append(event_multiplier)
            continue
        if effect.result.modifier_path is CalculationNode.DAMAGE_VEIL_VULNERABILITY_CAP:
            if vulnerability_policy_effect_seen:
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "multiple-vulnerability-policies",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "multiple vulnerability settlement policies are not defined",
                    )
                )
                continue
            vulnerability_policy_effect_seen = True
            if effect.result.operation is not EffectOperation.SET:
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "vulnerability-policy-operation",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "veil vulnerability policy requires SET",
                    )
                )
                continue
            value = effect.result.value
            if not isinstance(value, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "vulnerability-policy-value",
                        DiagnosticKind.MISSING_DATA,
                        value.notes,
                    )
                )
                continue
            if stack_count != 1:
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "vulnerability-policy-stack",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "veil vulnerability policy cannot be stacked",
                    )
                )
                continue
            vulnerability_policy = VeilVulnerabilityPolicy(value.value)
            continue
        event_modifier = _event_modifier(effect, diagnostics, stack_count)
        if event_modifier is not None:
            rule_modifiers.append(event_modifier)

    snapshots, applied_panel_ids, panel_traces = _apply_panel_effects_to_recipients(
        snapshots,
        panel_effects,
        diagnostics,
        initial_character_snapshots=initial_character_snapshots,
        current_operator=current_operator,
        rule_item_id_by_effect={
            application.effect.rule.effect_id: application.rule_item_id
            for application in matched_effects
            if isinstance(application, MatchedEffectApplication)
        },
    )
    event_modifiers = _normalize_event_modifiers(
        base_calculation_modifiers,
        rule_modifiers,
        diagnostics,
    )
    return ModifierApplicationResult(
        character_snapshots=snapshots,
        event_modifiers=event_modifiers,
        event_stat_modifiers=tuple(event_stat_modifiers),
        event_multiplier_modifiers=tuple(event_multiplier_modifiers),
        event_crit_guarantee_effect_ids=tuple(event_crit_guarantee_effect_ids),
        vulnerability_policy=vulnerability_policy,
        applied_panel_effect_ids=applied_panel_ids,
        panel_traces=panel_traces,
        diagnostics=tuple(diagnostics),
    )


def apply_global_panel_effects(
    base_character_snapshots: tuple[CharacterSnapshot, ...],
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    rule_items: tuple[CalculationRuleItem, ...],
    scenario: CalculationScenario,
    team_character_ids: frozenset[CharacterId] | None = None,
) -> ModifierApplicationResult:
    """Apply event-independent Panel Effects to SELF or the active TEAM."""

    diagnostics: list[CalculationDiagnostic] = []
    snapshots = tuple(base_character_snapshots)
    applied_ids: set[EffectId] = set()
    traces: list[PanelModifierExecutionTrace] = []
    (
        selected_recipients,
        suppressed_non_stacking_effects,
        zero_stack_non_stacking_effects,
        selection_diagnostics,
        deferred_non_stacking_groups,
    ) = (
        _select_non_stacking_panel_effects(
            rule_items,
            scenario,
            snapshots,
            initial_character_snapshots,
            team_character_ids,
        )
    )
    diagnostics.extend(selection_diagnostics)
    # Current-panel derived values must observe all ordinary panel effects
    # first.  In particular, an equipment anomaly-mastery or crit-rate bonus
    # must be part of the value read by reviewed character effects, regardless
    # of RuleItem ordering.  Initial-attack-derived values keep their original
    # initial snapshot semantics and can be applied in the ordinary pass.
    deferred_current_panel_effects: list[
        tuple[ModifierEffect, int, RuleItemId, frozenset[CharacterId] | None]
    ] = []
    for rule in rule_items:
        if rule.rule_id not in scenario.enabled_rule_item_ids:
            continue
        if rule.eligibility is RuleEligibility.INELIGIBLE:
            continue
        condition_status, condition_diagnostics = _resolve_rule_conditions(
            rule,
            scenario,
        )
        diagnostics.extend(condition_diagnostics)
        if condition_status is not EffectMatchStatus.MATCHED:
            continue
        trigger_status, trigger_diagnostics = _resolve_rule_trigger(rule, scenario)
        diagnostics.extend(trigger_diagnostics)
        if trigger_status is not EffectMatchStatus.MATCHED:
            continue
        stack_count = _resolved_rule_stack(rule, scenario)
        for effect in rule.effects:
            if not isinstance(effect, ModifierEffect):
                continue
            if effect.result.modifier_path not in _PANEL_NODES:
                continue
            if not _is_recipient_panel_effect(effect):
                continue
            if rule.non_stacking_group_id in deferred_non_stacking_groups:
                continue
            recipient_override = selected_recipients.get(effect.rule.effect_id)
            if effect.rule.effect_id in zero_stack_non_stacking_effects:
                applied_ids.add(effect.rule.effect_id)
                continue
            if (
                recipient_override is None
                and effect.rule.effect_id in suppressed_non_stacking_effects
            ):
                continue
            if _is_current_panel_derived_effect(effect):
                deferred_current_panel_effects.append(
                    (effect, stack_count, rule.rule_id, recipient_override)
                )
                continue
            effect_status, effect_diagnostics = _resolve_panel_effect_condition(
                effect,
                scenario,
                initial_character_snapshots,
                snapshots,
            )
            diagnostics.extend(effect_diagnostics)
            if effect_status is not EffectMatchStatus.MATCHED:
                continue
            resolved_effect = _resolve_effect_value(
                effect,
                initial_character_snapshots,
                diagnostics,
                scenario=scenario,
            )
            if resolved_effect is None:
                continue
            updated, effect_ids, panel_traces = _apply_panel_effects_to_recipients(
                snapshots,
                [(resolved_effect, stack_count)],
                diagnostics,
                initial_character_snapshots=initial_character_snapshots,
                team_character_ids=team_character_ids,
                current_operator=scenario.current_operator,
                recipient_overrides=(
                    {effect.rule.effect_id: recipient_override}
                    if recipient_override is not None
                    else None
                ),
                rule_item_id_by_effect={resolved_effect.rule.effect_id: rule.rule_id},
            )
            snapshots = updated
            applied_ids.update(effect_ids)
            traces.extend(panel_traces)

    # Resolve current-panel derived values only after the ordinary panel pass.
    # Conditions are evaluated against that final ordinary settlement panel as
    # well, so a threshold cannot accidentally read a pre-equipment value.
    for effect, stack_count, rule_id, recipient_override in deferred_current_panel_effects:
        effect_status, effect_diagnostics = _resolve_panel_effect_condition(
            effect,
            scenario,
            initial_character_snapshots,
            snapshots,
        )
        diagnostics.extend(effect_diagnostics)
        if effect_status is not EffectMatchStatus.MATCHED:
            continue
        resolved_effect = _resolve_effect_value(
            effect,
            initial_character_snapshots,
            diagnostics,
            scenario=scenario,
            current_character_snapshots=snapshots,
        )
        if resolved_effect is None:
            continue
        updated, effect_ids, panel_traces = _apply_panel_effects_to_recipients(
            snapshots,
            [(resolved_effect, stack_count)],
            diagnostics,
            initial_character_snapshots=initial_character_snapshots,
            team_character_ids=team_character_ids,
            current_operator=scenario.current_operator,
            recipient_overrides=(
                {effect.rule.effect_id: recipient_override}
                if recipient_override is not None
                else None
            ),
            rule_item_id_by_effect={resolved_effect.rule.effect_id: rule_id},
        )
        snapshots = updated
        applied_ids.update(effect_ids)
        traces.extend(panel_traces)

    if deferred_non_stacking_groups:
        deferred_rules = tuple(
            rule
            for rule in rule_items
            if rule.non_stacking_group_id in deferred_non_stacking_groups
        )
        (
            deferred_recipients,
            _,
            deferred_zero_stack_effects,
            deferred_diagnostics,
            _,
        ) = _select_non_stacking_panel_effects(
            deferred_rules,
            scenario,
            snapshots,
            initial_character_snapshots,
            team_character_ids,
            defer_current_panel_groups=False,
        )
        zero_stack_non_stacking_effects = frozenset(
            {*zero_stack_non_stacking_effects, *deferred_zero_stack_effects}
        )
        diagnostics.extend(deferred_diagnostics)
        for rule in deferred_rules:
            if rule.rule_id not in scenario.enabled_rule_item_ids:
                continue
            if rule.eligibility is RuleEligibility.INELIGIBLE:
                continue
            condition_status, condition_diagnostics = _resolve_rule_conditions(
                rule,
                scenario,
            )
            diagnostics.extend(condition_diagnostics)
            if condition_status is not EffectMatchStatus.MATCHED:
                continue
            trigger_status, trigger_diagnostics = _resolve_rule_trigger(rule, scenario)
            diagnostics.extend(trigger_diagnostics)
            if trigger_status is not EffectMatchStatus.MATCHED:
                continue
            stack_count = _resolved_rule_stack(rule, scenario)
            for effect in rule.effects:
                if (
                    not isinstance(effect, ModifierEffect)
                    or effect.result.modifier_path not in _PANEL_NODES
                    or not _is_recipient_panel_effect(effect)
                ):
                    continue
                if effect.rule.effect_id in zero_stack_non_stacking_effects:
                    applied_ids.add(effect.rule.effect_id)
                    continue
                recipient_override = deferred_recipients.get(effect.rule.effect_id)
                if recipient_override is None:
                    continue
                effect_status, effect_diagnostics = _resolve_panel_effect_condition(
                    effect,
                    scenario,
                    initial_character_snapshots,
                    snapshots,
                )
                diagnostics.extend(effect_diagnostics)
                if effect_status is not EffectMatchStatus.MATCHED:
                    continue
                resolved_effect = _resolve_effect_value(
                    effect,
                    initial_character_snapshots,
                    diagnostics,
                    scenario=scenario,
                    current_character_snapshots=snapshots,
                )
                if resolved_effect is None:
                    continue
                updated, effect_ids, effect_traces = _apply_panel_effects_to_recipients(
                    snapshots,
                    [(resolved_effect, stack_count)],
                    diagnostics,
                    initial_character_snapshots=initial_character_snapshots,
                    team_character_ids=team_character_ids,
                    current_operator=scenario.current_operator,
                    recipient_overrides={effect.rule.effect_id: recipient_override},
                    rule_item_id_by_effect={resolved_effect.rule.effect_id: rule.rule_id},
                )
                snapshots = updated
                applied_ids.update(effect_ids)
                traces.extend(effect_traces)

    return ModifierApplicationResult(
        character_snapshots=snapshots,
        event_modifiers=(),
        applied_panel_effect_ids=frozenset(applied_ids),
        panel_traces=tuple(traces),
        diagnostics=tuple(diagnostics),
    )


def _select_non_stacking_panel_effects(
    rule_items: tuple[CalculationRuleItem, ...],
    scenario: CalculationScenario,
    snapshots: tuple[CharacterSnapshot, ...],
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    team_character_ids: frozenset[CharacterId] | None,
    *,
    defer_current_panel_groups: bool = True,
) -> tuple[
    dict[EffectId, frozenset[CharacterId]],
    frozenset[EffectId],
    frozenset[EffectId],
    tuple[CalculationDiagnostic, ...],
    frozenset[str],
]:
    candidates: dict[
        tuple[str, CharacterId, CalculationNode],
        dict[RuleItemId, list[tuple[ModifierEffect, float]]],
    ] = {}
    unknowns: dict[
        tuple[str, CharacterId, CalculationNode],
        list[tuple[ModifierEffect, RuleItemId, str]],
    ] = {}
    selected_recipients: dict[EffectId, set[CharacterId]] = {}
    suppressed_effect_ids: set[EffectId] = set()
    zero_stack_effect_ids: set[EffectId] = set()
    diagnostics: list[CalculationDiagnostic] = []
    deferred_groups: set[str] = set()
    for rule in rule_items:
        group_id = rule.non_stacking_group_id
        if (
            group_id is None
            or rule.rule_id not in scenario.enabled_rule_item_ids
            or rule.eligibility is RuleEligibility.INELIGIBLE
        ):
            continue
        panel_effects = tuple(
            effect
            for effect in rule.effects
            if isinstance(effect, ModifierEffect)
            and effect.result.modifier_path in _PANEL_NODES
            and _is_recipient_panel_effect(effect)
        )
        if not panel_effects:
            continue
        if defer_current_panel_groups and any(
            _is_current_panel_derived_effect(effect)
            or _has_current_panel_threshold(effect.rule.condition)
            for effect in panel_effects
        ):
            deferred_groups.add(group_id)
            continue
        rule_status, _ = _resolve_rule_conditions(rule, scenario)
        if rule_status is EffectMatchStatus.NOT_MATCHED:
            continue
        rule_blocked = rule_status is EffectMatchStatus.BLOCKED
        trigger_status, _ = _resolve_rule_trigger(rule, scenario)
        if trigger_status is EffectMatchStatus.NOT_MATCHED:
            continue
        rule_blocked = rule_blocked or trigger_status is EffectMatchStatus.BLOCKED
        stack_count = _resolved_rule_stack(rule, scenario)
        if stack_count == 0:
            suppressed_effect_ids.update(
                effect.rule.effect_id for effect in panel_effects
            )
            zero_stack_effect_ids.update(
                effect.rule.effect_id for effect in panel_effects
            )
            continue
        for effect in panel_effects:
            recipients = _panel_recipients(
                effect,
                snapshots,
                team_character_ids,
                scenario.current_operator,
            )
            if not recipients:
                # Keep the existing valid no-op behavior for TEAM_OTHER on a
                # roster that has no other active recipient.
                selected_recipients.setdefault(effect.rule.effect_id, set())
                continue
            effect_status, effect_condition_diagnostics = (
                (EffectMatchStatus.BLOCKED, ())
                if rule_blocked
                else _resolve_panel_effect_condition(
                    effect,
                    scenario,
                    initial_character_snapshots,
                    snapshots,
                )
            )
            if effect_status is EffectMatchStatus.NOT_MATCHED:
                continue
            reason: str | None = None
            if rule_blocked or effect_status is EffectMatchStatus.BLOCKED:
                reason = "; ".join(
                    item.message for item in effect_condition_diagnostics
                ) or "A matching rule or effect condition is unresolved."
            elif effect.rule.filters:
                reason = (
                    "The panel candidate has event filters, so its "
                    "actual recipient match is unavailable in the global panel pass."
                )
            elif effect.result.operation is not EffectOperation.ADD:
                reason = "The active panel candidate does not use the comparable ADD operation."

            resolved_effect = None
            if reason is None:
                effect_diagnostics: list[CalculationDiagnostic] = []
                resolved_effect = _resolve_effect_value(
                    effect,
                    initial_character_snapshots,
                    effect_diagnostics,
                    scenario=scenario,
                    current_character_snapshots=snapshots,
                )
                if (
                    resolved_effect is None
                    or not isinstance(resolved_effect.result.value, Resolved)
                ):
                    reason = (
                        effect_diagnostics[0].message
                        if effect_diagnostics
                        else "The active panel candidate has an unresolved effective value."
                    )

            for recipient in recipients:
                key = (group_id, recipient, effect.result.modifier_path)
                if reason is not None:
                    unknowns.setdefault(key, []).append((effect, rule.rule_id, reason))
                    continue
                assert resolved_effect is not None
                preview_diagnostics: list[CalculationDiagnostic] = []
                _, _, preview_traces = _apply_panel_effects_to_recipients(
                    snapshots,
                    [(resolved_effect, stack_count)],
                    preview_diagnostics,
                    initial_character_snapshots=initial_character_snapshots,
                    team_character_ids=team_character_ids,
                    current_operator=scenario.current_operator,
                    rule_item_id_by_effect={effect.rule.effect_id: rule.rule_id},
                )
                trace = next(
                    (
                        item
                        for item in preview_traces
                        if item.effect_id == effect.rule.effect_id
                        and item.recipient_character_id == recipient
                    ),
                    None,
                )
                if trace is None:
                    message = (
                        preview_diagnostics[0].message
                        if preview_diagnostics
                        else "The active panel candidate could not be resolved for this recipient."
                    )
                    unknowns.setdefault(key, []).append(
                        (effect, rule.rule_id, message)
                    )
                    continue
                candidates.setdefault(key, {}).setdefault(rule.rule_id, []).append(
                    (effect, trace.resolved_value)
                )

    for group_id, recipient, path in sorted(
        set(candidates) | set(unknowns),
        key=lambda item: (item[0], str(item[1]), item[2].value),
    ):
        key = (group_id, recipient, path)
        source_candidates = candidates.get(key, {})
        group_unknowns = unknowns.get(key, [])
        source_ids = set(source_candidates) | {item[1] for item in group_unknowns}
        if len(source_ids) == 1:
            source_rule_id = next(iter(source_ids))
            for effect, _ in source_candidates.get(source_rule_id, ()):
                selected_recipients.setdefault(effect.rule.effect_id, set()).add(
                    recipient
                )
            for effect, rule_id, _ in group_unknowns:
                if rule_id == source_rule_id:
                    selected_recipients.setdefault(effect.rule.effect_id, set()).add(
                        recipient
                    )
            continue
        if group_unknowns:
            text_items = [
                *(
                    effect
                    for source_effects in source_candidates.values()
                    for effect, _ in source_effects
                ),
                *(item[0] for item in group_unknowns),
            ]
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:{group_id}:{recipient}:{path.value}:max-unresolved"
                    ),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=(
                        "Same-name panel candidates for this recipient and stat "
                        "could not all be resolved, so a static maximum was not selected. "
                        + "; ".join(dict.fromkeys(reason for _, _, reason in group_unknowns))
                    ),
                    blocking=True,
                    original_text=(
                        group_unknowns[0][0].rule.source.raw_text
                        if group_unknowns
                        else text_items[0].rule.source.raw_text
                        if text_items
                        else None
                    ),
                    candidates=tuple(
                        item.rule.source.raw_text
                        or item.rule.source.label
                        or str(item.rule.effect_id)
                        for item in text_items
                    ),
                )
            )
            suppressed_effect_ids.update(item.rule.effect_id for item in text_items)
            continue
        if not source_candidates:
            continue
        # Multiple effects in one RuleItem are one source instance. Preserve
        # their combined contribution, then compare that RuleItem with the
        # other active copies.
        values_by_source = {
            rule_id: sum(value for _, value in source_effects)
            for rule_id, source_effects in source_candidates.items()
        }
        winner_rule_id = max(
            values_by_source,
            key=lambda rule_id: (values_by_source[rule_id], str(rule_id)),
        )
        for effect, _ in source_candidates[winner_rule_id]:
            selected_recipients.setdefault(effect.rule.effect_id, set()).add(recipient)
        suppressed_effect_ids.update(
            effect.rule.effect_id
            for rule_id, source_effects in source_candidates.items()
            if rule_id != winner_rule_id
            for effect, _ in source_effects
        )

    return (
        {
            effect_id: frozenset(recipients)
            for effect_id, recipients in selected_recipients.items()
        },
        frozenset(suppressed_effect_ids),
        frozenset(zero_stack_effect_ids),
        tuple(diagnostics),
        frozenset(deferred_groups),
    )


def _resolve_rule_trigger(
    rule: CalculationRuleItem,
    scenario: CalculationScenario,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    """Resolve a trigger fact without treating its actor as a recipient."""

    effect_triggers = {
        effect.rule.effect_id: effect.rule.trigger
        for effect in rule.effects
        if isinstance(effect, ModifierEffect) and effect.rule.trigger is not None
    }
    if not effect_triggers:
        return EffectMatchStatus.MATCHED, ()
    for effect_id, selector in effect_triggers.items():
        facts = tuple(
            fact
            for fact in scenario.trigger_facts
            if fact.effect_id == effect_id
            and fact.event_kind is selector.event_kind
            and (selector.move_id is None or fact.move_id == selector.move_id)
        )
        if facts:
            continue
        return (
            EffectMatchStatus.BLOCKED,
            (
                _diagnostic(
                    str(effect_id),
                    "missing-trigger-fact",
                    DiagnosticKind.MISSING_DATA,
                    "Panel Effect trigger has no matching scenario trigger fact",
                ),
            ),
        )
    return EffectMatchStatus.MATCHED, ()


def _resolve_panel_effect_condition(
    effect: ModifierEffect,
    scenario: CalculationScenario,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    current_character_snapshots: tuple[CharacterSnapshot, ...],
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    condition = effect.rule.condition
    if condition is None or isinstance(condition, AlwaysCondition):
        return EffectMatchStatus.MATCHED, ()
    if isinstance(condition, AllCondition):
        evaluations = tuple(
            _resolve_panel_condition(
                item,
                effect.rule.effect_id,
                scenario,
                initial_character_snapshots,
                current_character_snapshots,
                effect.rule.owner,
            )
            for item in condition.conditions
        )
        if any(status is EffectMatchStatus.NOT_MATCHED for status, _ in evaluations):
            return EffectMatchStatus.NOT_MATCHED, ()
        if any(status is EffectMatchStatus.BLOCKED for status, _ in evaluations):
            return EffectMatchStatus.BLOCKED, tuple(
                diagnostic
                for _, diagnostics in evaluations
                for diagnostic in diagnostics
            )
        return EffectMatchStatus.MATCHED, ()
    if isinstance(condition, AnyCondition):
        evaluations = tuple(
            _resolve_panel_condition(
                item,
                effect.rule.effect_id,
                scenario,
                initial_character_snapshots,
                current_character_snapshots,
                effect.rule.owner,
            )
            for item in condition.conditions
        )
        if any(status is EffectMatchStatus.MATCHED for status, _ in evaluations):
            return EffectMatchStatus.MATCHED, ()
        if any(status is EffectMatchStatus.BLOCKED for status, _ in evaluations):
            return EffectMatchStatus.BLOCKED, tuple(
                diagnostic
                for _, diagnostics in evaluations
                for diagnostic in diagnostics
            )
        return EffectMatchStatus.NOT_MATCHED, ()
    if isinstance(condition, NotCondition):
        status, diagnostics = _resolve_panel_condition(
            condition.condition,
            effect.rule.effect_id,
            scenario,
            initial_character_snapshots,
            current_character_snapshots,
            effect.rule.owner,
        )
        if status is EffectMatchStatus.MATCHED:
            return EffectMatchStatus.NOT_MATCHED, diagnostics
        if status is EffectMatchStatus.NOT_MATCHED:
            return EffectMatchStatus.MATCHED, diagnostics
        return status, diagnostics
    return _resolve_panel_condition(
        condition,
        effect.rule.effect_id,
        scenario,
        initial_character_snapshots,
        current_character_snapshots,
        effect.rule.owner,
    )


def _resolve_panel_condition(
    condition,
    effect_id: EffectId,
    scenario: CalculationScenario,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = (),
    current_character_snapshots: tuple[CharacterSnapshot, ...] = (),
    owner: CharacterId | None = None,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if condition is None or isinstance(condition, AlwaysCondition):
        return EffectMatchStatus.MATCHED, ()
    if isinstance(condition, RuleStackCondition):
        if (
            condition.requires_rule_enabled
            and RuleItemId(condition.rule_item_id) not in scenario.enabled_rule_item_ids
        ):
            return EffectMatchStatus.NOT_MATCHED, ()
        selected = scenario.selected_stack(RuleItemId(condition.rule_item_id))
        if selected is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    _diagnostic(
                        str(effect_id),
                        "missing-rule-stack",
                        DiagnosticKind.MISSING_DATA,
                        f"missing resolved RuleItem stack: {condition.rule_item_id}",
                    ),
                ),
            )
        return (
            (
                EffectMatchStatus.MATCHED
                if selected == condition.required_value
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    if isinstance(condition, ScenarioParameterRangeCondition):
        parameter = next(
            (
                item
                for item in scenario.parameters
                if str(item.parameter_id) == condition.parameter_id
            ),
            None,
        )
        if parameter is None or parameter.value is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    _diagnostic(
                        str(effect_id),
                        "missing-scenario-parameter",
                        DiagnosticKind.MISSING_DATA,
                        f"missing resolved scenario parameter: {condition.parameter_id}",
                    ),
                ),
            )
        matches_minimum = condition.minimum is None or parameter.value >= condition.minimum
        matches_maximum = condition.maximum is None or parameter.value <= condition.maximum
        return (
            EffectMatchStatus.MATCHED
            if matches_minimum and matches_maximum
            else EffectMatchStatus.NOT_MATCHED,
            (),
        )
    if isinstance(condition, DynamicIdentityCondition):
        if condition.identity is DynamicIdentity.CURRENT_OPERATOR and owner is not None:
            return (
                (
                    EffectMatchStatus.MATCHED
                    if owner == scenario.current_operator
                    else EffectMatchStatus.NOT_MATCHED
                ),
                (),
            )
        return EffectMatchStatus.NOT_MATCHED, ()
    if isinstance(condition, PanelStatThresholdCondition):
        if condition.source_node in {
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        }:
            current_snapshot = next(
                (
                    item
                    for item in current_character_snapshots
                    if item.character_id == condition.source_character_id
                ),
                None,
            )
            if current_snapshot is None:
                value = None
            elif condition.source_node is CalculationNode.CHARACTER_CURRENT_CRIT_RATE:
                value = current_snapshot.settlement_stats.crit_rate
            elif condition.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY:
                value = current_snapshot.settlement_stats.anomaly_proficiency
            else:
                value = current_snapshot.settlement_stats.anomaly_mastery
        else:
            initial_snapshot = next(
                (
                    item
                    for item in initial_character_snapshots
                    if item.character_id == condition.source_character_id
                ),
                None,
            )
            if initial_snapshot is None:
                value = None
            elif condition.source_node is CalculationNode.CHARACTER_INITIAL_DEFENSE:
                value = initial_snapshot.initial_stats.defense
            else:
                value = initial_snapshot.initial_stats.anomaly_mastery
        if not isinstance(value, Resolved):
            return (
                EffectMatchStatus.BLOCKED,
                (
                    _diagnostic(
                        str(effect_id),
                        "missing-panel-threshold-value",
                        DiagnosticKind.MISSING_DATA,
                        f"missing resolved panel value for {condition.source_node.value}",
                    ),
                ),
            )
        return (
            (
                EffectMatchStatus.MATCHED
                if float(value.value) >= condition.minimum
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    return (
        EffectMatchStatus.BLOCKED,
        (
            _diagnostic(
                str(effect_id),
                "panel-condition",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "event-dependent Panel Effect cannot enter global pre-pass",
            ),
        ),
    )


def _resolve_rule_conditions(
    rule: CalculationRuleItem,
    scenario: CalculationScenario,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if not rule.condition_ids and not rule.condition_not_ids:
        return EffectMatchStatus.MATCHED, ()
    values = {item.condition_id: item.value for item in scenario.conditions}
    evaluations: list[tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]] = []
    requirements = (
        *((condition_id, True) for condition_id in rule.condition_ids),
        *((condition_id, False) for condition_id in rule.condition_not_ids),
    )
    for condition_id, expected_value in requirements:
        if condition_id not in values:
            evaluations.append(
                (
                    EffectMatchStatus.BLOCKED,
                    (
                        _diagnostic(
                            str(rule.rule_id),
                            f"missing-condition-{condition_id}",
                            DiagnosticKind.MISSING_DATA,
                            f"missing scenario condition: {condition_id}",
                        ),
                    ),
                )
            )
        elif values[condition_id] is None:
            evaluations.append(
                (
                    EffectMatchStatus.BLOCKED,
                    (
                        _diagnostic(
                            str(rule.rule_id),
                            f"unresolved-condition-{condition_id}",
                            DiagnosticKind.MISSING_DATA,
                            f"scenario condition has no selected value: {condition_id}",
                        ),
                    ),
                )
            )
        elif values[condition_id] is expected_value:
            evaluations.append((EffectMatchStatus.MATCHED, ()))
        else:
            evaluations.append((EffectMatchStatus.NOT_MATCHED, ()))
    if any(status is EffectMatchStatus.NOT_MATCHED for status, _ in evaluations):
        return EffectMatchStatus.NOT_MATCHED, ()
    if any(status is EffectMatchStatus.BLOCKED for status, _ in evaluations):
        return (
            EffectMatchStatus.BLOCKED,
            tuple(
                diagnostic
                for _, item_diagnostics in evaluations
                for diagnostic in item_diagnostics
            ),
        )
    return (
        EffectMatchStatus.MATCHED,
        tuple(
            diagnostic
            for _, item_diagnostics in evaluations
            for diagnostic in item_diagnostics
        ),
    )


def _resolved_rule_stack(
    rule: CalculationRuleItem,
    scenario: CalculationScenario,
) -> int:
    if rule.stack_count is None:
        return 1
    selected = scenario.selected_stack(rule.rule_id)
    return rule.stack_count if selected is None else selected


def _panel_recipients(
    effect: ModifierEffect,
    snapshots: tuple[CharacterSnapshot, ...],
    team_character_ids: frozenset[CharacterId] | None = None,
    current_operator: CharacterId | None = None,
) -> tuple[CharacterId, ...]:
    rule = effect.rule
    if rule.target is EffectTarget.SELF:
        return (rule.owner,) if rule.owner is not None else ()
    if rule.target is EffectTarget.CURRENT_OPERATOR:
        if current_operator is None:
            return ()
        if team_character_ids is not None and current_operator not in team_character_ids:
            return ()
        return (
            (current_operator,)
            if any(item.character_id == current_operator for item in snapshots)
            else ()
        )
    if rule.target is EffectTarget.TEAM:
        return tuple(
            item.character_id
            for item in snapshots
            if team_character_ids is None or item.character_id in team_character_ids
        )
    if rule.target is EffectTarget.TEAM_OTHER:
        return tuple(
            item.character_id
            for item in snapshots
            if item.character_id != rule.owner
            and (team_character_ids is None or item.character_id in team_character_ids)
        )
    return ()


def _resolve_effect_value(
    effect: ModifierEffect,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    diagnostics: list[CalculationDiagnostic],
    *,
    scenario: CalculationScenario | None = None,
    current_character_snapshots: tuple[CharacterSnapshot, ...] = (),
) -> ModifierEffect | None:
    value = effect.result.value
    if isinstance(value, ScenarioParameterDerivedValue):
        if scenario is None:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-parameter-scenario",
                    DiagnosticKind.MISSING_DATA,
                    "scenario parameter value source requires a calculation scenario",
                )
            )
            return None
        parameter = next(
            (
                item
                for item in scenario.parameters
                if str(item.parameter_id) == value.parameter_id
            ),
            None,
        )
        if parameter is None or parameter.value is None:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-parameter-value",
                    DiagnosticKind.MISSING_DATA,
                    f"scenario parameter is unresolved: {value.parameter_id}",
                )
            )
            return None
        coefficient = value.coefficient
        base = value.base
        if not isinstance(coefficient, Resolved) or not isinstance(base, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-parameter-coefficient",
                    DiagnosticKind.MISSING_DATA,
                    "scenario parameter derived value is unresolved",
                )
            )
            return None
        result = base.value + coefficient.value * parameter.value
        if value.cap_max is not None:
            if not isinstance(value.cap_max, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "derived-parameter-cap",
                        DiagnosticKind.MISSING_DATA,
                        "scenario parameter derived value cap is unresolved",
                    )
                )
                return None
            result = min(result, value.cap_max.value)
        return replace(effect, result=replace(effect.result, value=Resolved(result)))
    if not isinstance(value, PanelStatDerivedValue):
        return effect

    coefficient = value.coefficient
    base = value.base
    cap_max = value.cap_max
    if not isinstance(coefficient, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-coefficient",
                DiagnosticKind.MISSING_DATA,
                coefficient.notes,
            )
        )
        return None
    if not isinstance(base, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-base",
                DiagnosticKind.MISSING_DATA,
                base.notes,
            )
        )
        return None

    if value.source_node in {
        CalculationNode.CHARACTER_CURRENT_MAX_HP,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_IMPACT,
    }:
        current = next(
            (
                item
                for item in current_character_snapshots
                if item.character_id == value.source_character_id
            ),
            None,
        )
        if current is None:
            current_stat = None
        elif value.source_node is CalculationNode.CHARACTER_CURRENT_MAX_HP:
            current_stat = current.settlement_stats.hp
        elif value.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY:
            current_stat = current.settlement_stats.anomaly_mastery
        elif value.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY:
            current_stat = current.settlement_stats.anomaly_proficiency
        elif value.source_node is CalculationNode.CHARACTER_CURRENT_IMPACT:
            current_stat = current.settlement_stats.impact
        else:
            current_stat = current.settlement_stats.crit_rate
        if not isinstance(current_stat, Resolved):
            label = (
                "current anomaly mastery"
                if value.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY
                else "current maximum HP"
                if value.source_node is CalculationNode.CHARACTER_CURRENT_MAX_HP
                else "current anomaly proficiency"
                if value.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY
                else "current impact"
                if value.source_node is CalculationNode.CHARACTER_CURRENT_IMPACT
                else "current crit rate"
            )
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    f"derived-value-{value.source_node.value}",
                    DiagnosticKind.MISSING_DATA,
                    f"{label} is unresolved for a derived panel value",
                )
            )
            return None
        threshold = value.threshold if value.threshold is not None else value.minimum
        if threshold is None:
            threshold = Resolved(0.0)
        if not isinstance(threshold, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-value-threshold",
                    DiagnosticKind.MISSING_DATA,
                    threshold.notes,
                )
            )
            return None
        result = (
            base.value
            + max(current_stat.value - threshold.value, 0.0) * coefficient.value
        )
    else:
        source = next(
            (
                item
                for item in initial_character_snapshots
                if item.character_id == value.source_character_id
            ),
            None,
        )
        if source is None:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-value-source",
                    DiagnosticKind.MISSING_DATA,
                    "derived panel value is missing its initial character snapshot",
                )
            )
            return None
        if value.source_node is CalculationNode.CHARACTER_INITIAL_HP:
            source_panel_value = source.initial_stats.hp
            source_stat_label = "initial maximum HP"
        elif value.source_node is CalculationNode.CHARACTER_INITIAL_DEFENSE:
            source_panel_value = source.initial_stats.defense
            source_stat_label = "initial defense"
        elif value.source_node is CalculationNode.CHARACTER_INITIAL_CRIT_RATE:
            source_panel_value = source.initial_stats.crit_rate
            source_stat_label = "initial crit rate"
        elif value.source_node is CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN:
            source_panel_value = source.initial_stats.energy_regen
            source_stat_label = "initial energy regeneration"
        else:
            source_panel_value = source.initial_stats.attack
            source_stat_label = "initial attack"
        if not isinstance(source_panel_value, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    f"derived-value-{value.source_node.value}",
                    DiagnosticKind.MISSING_DATA,
                    f"{source_stat_label} is unresolved for a derived panel value",
                )
            )
            return None
        if value.source_node in {
            CalculationNode.CHARACTER_INITIAL_HP,
            CalculationNode.CHARACTER_INITIAL_CRIT_RATE,
            CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        }:
            threshold = value.threshold if value.threshold is not None else value.minimum
            if threshold is None:
                threshold = Resolved(0.0)
            if not isinstance(threshold, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "derived-value-threshold",
                        DiagnosticKind.MISSING_DATA,
                        threshold.notes,
                    )
                )
                return None
            excess = max(source_panel_value.value - threshold.value, 0.0)
            if value.step_size is not None:
                step_size = value.step_size
                if not isinstance(step_size, Resolved):
                    diagnostics.append(
                        _diagnostic(
                            str(effect.rule.effect_id),
                            "derived-value-step-size",
                            DiagnosticKind.MISSING_DATA,
                            step_size.notes,
                        )
                    )
                    return None
                # Initial energy regeneration is recorded as decimal panel
                # data. A tiny tolerance preserves exact hundredth thresholds
                # after normal floating-point build arithmetic (e.g. 2.16).
                steps = floor(excess / step_size.value + 1e-9)
                result = base.value + steps * coefficient.value
            else:
                result = base.value + excess * coefficient.value
        else:
            result = base.value + source_panel_value.value * coefficient.value
    if cap_max is not None:
        if not isinstance(cap_max, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-value-cap",
                    DiagnosticKind.MISSING_DATA,
                    cap_max.notes,
                )
            )
            return None
        result = min(result, cap_max.value)
    return replace(
        effect,
        result=replace(effect.result, value=Resolved(result)),
    )


def _is_recipient_panel_effect(effect: ModifierEffect) -> bool:
    rule = effect.rule
    return (
        rule.target
        in {
            EffectTarget.SELF,
            EffectTarget.CURRENT_OPERATOR,
            EffectTarget.TEAM,
            EffectTarget.TEAM_OTHER,
        }
        and not rule.filters
        and _is_event_independent_condition(rule.condition)
    )


def _is_current_panel_derived_effect(effect: ModifierEffect) -> bool:
    value = effect.result.value
    return (
        isinstance(value, PanelStatDerivedValue)
        and value.source_node
        in {
            CalculationNode.CHARACTER_CURRENT_MAX_HP,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_IMPACT,
        }
    )


def _has_current_panel_threshold(condition) -> bool:
    if isinstance(condition, PanelStatThresholdCondition):
        return condition.source_node in {
            CalculationNode.CHARACTER_CURRENT_MAX_HP,
            CalculationNode.CHARACTER_CURRENT_ATTACK,
            CalculationNode.CHARACTER_CURRENT_DEFENSE,
            CalculationNode.CHARACTER_CURRENT_IMPACT,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
            CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
            CalculationNode.CHARACTER_CURRENT_PENETRATION_FLAT,
            CalculationNode.CHARACTER_CURRENT_ENERGY_REGEN,
            CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
        }
    if isinstance(condition, (AllCondition, AnyCondition)):
        return any(_has_current_panel_threshold(item) for item in condition.conditions)
    if isinstance(condition, NotCondition):
        return _has_current_panel_threshold(condition.condition)
    return False


def _is_event_independent_condition(condition) -> bool:
    if condition is None or isinstance(
        condition,
        (
            AlwaysCondition,
            RuleStackCondition,
            ScenarioParameterRangeCondition,
            PanelStatThresholdCondition,
        ),
    ):
        return True
    if isinstance(condition, (AllCondition, AnyCondition)):
        return all(
            _is_event_independent_condition(item) for item in condition.conditions
        )
    if isinstance(condition, NotCondition):
        return _is_event_independent_condition(condition.condition)
    if isinstance(condition, DynamicIdentityCondition):
        return condition.identity is DynamicIdentity.CURRENT_OPERATOR
    return False


def _event_stat_modifier(
    effect: ModifierEffect,
    event: object | None,
    stack_count: int,
    diagnostics: list[CalculationDiagnostic],
) -> EventStatModifier | None:
    if not isinstance(event, (DirectDamageEvent, PenetrationDamageEvent)) or not isinstance(
        event.crit_rule, StandardCritRule
    ):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-recipient",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "event stat modifiers require a standard-crit damage event",
            )
        )
        return None
    if effect.result.modifier_path not in {
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
    }:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-node",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "Stage-018 only supports event-level current crit-rate and crit-damage modifiers",
            )
        )
        return None
    if effect.result.operation is not EffectOperation.ADD:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "event-level crit-rate and crit-damage modifiers support ADD only",
            )
        )
        return None
    value = effect.result.value
    if not isinstance(value, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    return EventStatModifier(
        effect_id=effect.rule.effect_id,
        recipient=event.crit_rule.stat_owner,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=Resolved(value.value * stack_count),
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _event_multiplier_modifier(
    effect: ModifierEffect,
    diagnostics: list[CalculationDiagnostic],
    stack_count: int,
) -> Modifier | None:
    if effect.result.operation is not EffectOperation.MULTIPLY:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-multiplier-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "event skill multipliers support MULTIPLY only",
            )
        )
        return None
    if stack_count != 1:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "stack-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "stacked non-ADD modifier operation has no defined semantics",
            )
        )
        return None
    value = effect.result.value
    if not isinstance(value, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-multiplier-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    return Modifier(
        effect_id=effect.rule.effect_id,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=value,
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _event_modifier(
    effect: ModifierEffect,
    diagnostics: list[CalculationDiagnostic],
    stack_count: int = 1,
) -> Modifier | None:
    value = effect.result.value
    if isinstance(value, Unresolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "unresolved-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    if stack_count != 1 and effect.result.operation is not EffectOperation.ADD:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "stack-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "stacked non-ADD modifier operation has no defined semantics",
            )
        )
        return None
    if stack_count != 1 and isinstance(value, Resolved):
        value = Resolved(value.value * stack_count)
    return Modifier(
        effect_id=effect.rule.effect_id,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=value,
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _apply_panel_effects_to_recipients(
    snapshots: tuple[CharacterSnapshot, ...],
    effects: list[tuple[ModifierEffect, int]],
    diagnostics: list[CalculationDiagnostic],
    *,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = (),
    team_character_ids: frozenset[CharacterId] | None = None,
    current_operator: CharacterId | None = None,
    recipient_overrides: dict[EffectId, frozenset[CharacterId]] | None = None,
    rule_item_id_by_effect: dict[EffectId, RuleItemId | None] | None = None,
) -> tuple[
    tuple[CharacterSnapshot, ...],
    frozenset[EffectId],
    tuple[PanelModifierExecutionTrace, ...],
]:
    updated_snapshots = snapshots
    applied_ids: set[EffectId] = set()
    traces: list[PanelModifierExecutionTrace] = []
    for effect, stack_count in effects:
        override = (recipient_overrides or {}).get(effect.rule.effect_id)
        recipients = (
            tuple(
                item.character_id
                for item in updated_snapshots
                if item.character_id in override
            )
            if override is not None
            else _panel_recipients(
                effect,
                updated_snapshots,
                team_character_ids,
                current_operator,
            )
        )
        if not recipients:
            owner_is_active = (
                effect.rule.owner is not None
                and any(
                    item.character_id == effect.rule.owner
                    for item in updated_snapshots
                )
                and (
                    team_character_ids is None
                    or effect.rule.owner in team_character_ids
                )
            )
            if effect.rule.target is EffectTarget.TEAM_OTHER and owner_is_active:
                # An owner-only team has no recipients by definition; the
                # effect is valid and has no-op semantics in that roster.
                applied_ids.add(effect.rule.effect_id)
                continue
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-recipient",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "Panel Effect target has no active CharacterSnapshot recipient",
                )
            )
            continue
        for recipient in recipients:
            updated_snapshots, effect_ids, effect_traces = _apply_panel_effects(
                updated_snapshots,
                [(effect, stack_count)],
                recipient,
                diagnostics,
                initial_character_snapshots=initial_character_snapshots,
                rule_item_id_by_effect=rule_item_id_by_effect,
            )
            applied_ids.update(effect_ids)
            traces.extend(effect_traces)
    return updated_snapshots, frozenset(applied_ids), tuple(traces)


def _apply_panel_effects(
    snapshots: tuple[CharacterSnapshot, ...],
    effects: list[tuple[ModifierEffect, int]],
    recipient: CharacterId,
    diagnostics: list[CalculationDiagnostic],
    *,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = (),
    rule_item_id_by_effect: dict[EffectId, RuleItemId | None] | None = None,
) -> tuple[
    tuple[CharacterSnapshot, ...],
    frozenset[EffectId],
    tuple[PanelModifierExecutionTrace, ...],
]:
    index = {item.character_id: item for item in snapshots}
    target = index.get(recipient)
    if target is None and effects:
        diagnostics.append(
            _diagnostic(
                str(recipient),
                "missing-panel-recipient-snapshot",
                DiagnosticKind.MISSING_DATA,
                "matched panel Effect has no snapshot for its recipient",
            )
        )
        return snapshots, frozenset(), ()
    if target is None:
        return snapshots, frozenset(), ()

    updated_stats = target.settlement_stats
    applied_effect_ids: set[EffectId] = set()
    traces: list[PanelModifierExecutionTrace] = []
    for effect, stack_count in effects:
        if not _is_recipient_panel_effect(effect):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-recipient",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "panel Effect does not have a supported recipient scope",
                )
            )
            continue
        if effect.result.operation is not EffectOperation.ADD:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-operation",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "Stage-015 panel Effects support ADD only",
                )
            )
            continue
        value = effect.result.value
        if isinstance(value, Unresolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-value",
                    DiagnosticKind.MISSING_DATA,
                    value.notes,
                )
            )
            continue
        if effect.result.modifier_path in _PANEL_FLAT_FIELDS:
            field_name = _PANEL_FLAT_FIELDS[effect.result.modifier_path]
            current = getattr(updated_stats, field_name)
            if not isinstance(current, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        f"current {field_name} is unresolved",
                    )
                )
                continue
            applied_value = value.value * stack_count
            updated_stats = replace(
                updated_stats,
                **{field_name: Resolved(current.value + applied_value)},
            )
            applied_effect_ids.add(effect.rule.effect_id)
            traces.append(
                PanelModifierExecutionTrace(
                    recipient_character_id=recipient,
                    owner_character_id=effect.rule.owner,
                    rule_item_id=(rule_item_id_by_effect or {}).get(
                        effect.rule.effect_id
                    ),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=applied_value,
                    stack_count=stack_count,
                )
            )
            continue
        if effect.result.modifier_path in _PANEL_PERCENT_FIELDS:
            field_name = _PANEL_PERCENT_FIELDS[effect.result.modifier_path]
            initial = next(
                (
                    item
                    for item in initial_character_snapshots
                    if item.character_id == recipient
                ),
                None,
            )
            base_value = (
                getattr(initial.initial_stats, field_name)
                if initial is not None
                else None
            )
            current = getattr(updated_stats, field_name)
            if not isinstance(base_value, Resolved) or not isinstance(
                current, Resolved
            ):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        f"initial/current {field_name} is unresolved for a percent Panel Effect",
                    )
                )
                continue
            applied_value = base_value.value * value.value * stack_count
            updated_stats = replace(
                updated_stats,
                **{field_name: Resolved(current.value + applied_value)},
            )
            applied_effect_ids.add(effect.rule.effect_id)
            traces.append(
                PanelModifierExecutionTrace(
                    recipient_character_id=recipient,
                    owner_character_id=effect.rule.owner,
                    rule_item_id=(rule_item_id_by_effect or {}).get(
                        effect.rule.effect_id
                    ),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=applied_value,
                    stack_count=stack_count,
                )
            )
            continue
        if effect.result.modifier_path in {
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        }:
            is_crit_rate = (
                effect.result.modifier_path
                is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
            )
            current = (
                updated_stats.crit_rate if is_crit_rate else updated_stats.crit_damage
            )
            if isinstance(current, Unresolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        (
                            "current crit rate is unresolved"
                            if is_crit_rate
                            else "current crit damage is unresolved"
                        ),
                    )
                )
                continue
            updated_stats = replace(
                updated_stats,
                **(
                    {"crit_rate": Resolved(current.value + value.value * stack_count)}
                    if is_crit_rate
                    else {
                        "crit_damage": Resolved(
                            current.value + value.value * stack_count
                        )
                    }
                ),
            )
            applied_effect_ids.add(effect.rule.effect_id)
            traces.append(
                PanelModifierExecutionTrace(
                    recipient_character_id=recipient,
                    owner_character_id=effect.rule.owner,
                    rule_item_id=(rule_item_id_by_effect or {}).get(
                        effect.rule.effect_id
                    ),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=value.value * stack_count,
                    stack_count=stack_count,
                )
            )
        elif (
            effect.result.modifier_path
            is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS
        ):
            current = updated_stats.attack
            if isinstance(current, Unresolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        "current attack is unresolved",
                    )
                )
                continue
            updated_stats = replace(
                updated_stats,
                attack=Resolved(current.value + value.value * stack_count),
            )
            applied_effect_ids.add(effect.rule.effect_id)
            traces.append(
                PanelModifierExecutionTrace(
                    recipient_character_id=recipient,
                    owner_character_id=effect.rule.owner,
                    rule_item_id=(rule_item_id_by_effect or {}).get(
                        effect.rule.effect_id
                    ),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=value.value * stack_count,
                    stack_count=stack_count,
                )
            )
        elif (
            effect.result.modifier_path
            is CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS
        ):
            initial = next(
                (
                    item
                    for item in initial_character_snapshots
                    if item.character_id == recipient
                ),
                None,
            )
            base_attack = initial.initial_stats.attack if initial is not None else None
            if not isinstance(base_attack, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        "initial attack is unresolved for a combat attack-percent Panel Effect",
                    )
                )
                continue
            current = updated_stats.attack
            if not isinstance(current, Resolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        "current attack is unresolved",
                    )
                )
                continue
            updated_stats = replace(
                updated_stats,
                attack=Resolved(
                    current.value + base_attack.value * value.value * stack_count
                ),
            )
            applied_effect_ids.add(effect.rule.effect_id)
            traces.append(
                PanelModifierExecutionTrace(
                    recipient_character_id=recipient,
                    owner_character_id=effect.rule.owner,
                    rule_item_id=(rule_item_id_by_effect or {}).get(
                        effect.rule.effect_id
                    ),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=base_attack.value * value.value * stack_count,
                    stack_count=stack_count,
                )
            )
        else:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-node",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    f"Stage-015 does not resolve panel node {effect.result.modifier_path.value}",
                )
            )

    index[recipient] = replace(
        target,
        settlement_stats=updated_stats,
    )
    return (
        tuple(index[item.character_id] for item in snapshots),
        frozenset(applied_effect_ids),
        tuple(traces),
    )


def _normalize_event_modifiers(
    base_modifiers: tuple[Modifier, ...],
    rule_modifiers: list[Modifier],
    diagnostics: list[CalculationDiagnostic],
) -> tuple[Modifier, ...]:
    by_path: dict[CalculationNode, list[Modifier]] = {}
    for modifier in (*base_modifiers, *rule_modifiers):
        by_path.setdefault(modifier.modifier_path, []).append(modifier)

    normalized: list[Modifier] = []
    for path, modifiers in by_path.items():
        overrides = [
            item for item in modifiers if item.operation is EffectOperation.OVERRIDE
        ]
        if len(overrides) > 1:
            diagnostics.append(
                _diagnostic(
                    path.value,
                    "multiple-overrides",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "multiple OVERRIDE modifiers target the same calculation node",
                )
            )
            continue
        if overrides:
            rule_conflicts = [
                item
                for item in rule_modifiers
                if item.modifier_path == path
                and item.operation is not EffectOperation.OVERRIDE
            ]
            if rule_conflicts:
                diagnostics.append(
                    _diagnostic(
                        path.value,
                        "override-operation-conflict",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "an OVERRIDE and another rule operation have no defined order",
                    )
                )
                continue
            normalized.append(replace(overrides[0], operation=EffectOperation.ADD))
            continue
        for modifier in modifiers:
            if modifier.operation is EffectOperation.ADD:
                normalized.append(modifier)
            elif (
                path is CalculationNode.ANOMALY_MUTATION_COEFFICIENT
                and modifier.operation is EffectOperation.MULTIPLY
            ):
                # Mutation has one reviewed multiplicative source factor plus
                # explicit additive coefficient increments.  The anomaly
                # record assembler applies these together before the source
                # record is frozen.
                normalized.append(modifier)
            else:
                diagnostics.append(
                    _diagnostic(
                        str(modifier.effect_id),
                        "unsupported-operation",
                        DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        f"unsupported event modifier operation: {modifier.operation.value}",
                    )
                )
    return tuple(normalized)


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
