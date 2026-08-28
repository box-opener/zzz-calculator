"""Resolve matched Effects into settlement snapshots and calculator Modifiers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from core.types import (
    AlwaysCondition,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    DirectDamageEvent,
    DynamicIdentity,
    DynamicIdentityFilter,
    EffectId,
    EffectOperation,
    EventCreationEffect,
    Modifier,
    ModifierEffect,
    Effect,
    EffectTarget,
    InitialCharacterSnapshot,
    PanelStatDerivedValue,
    Resolved,
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

    def __post_init__(self) -> None:
        if self.stack_count < 0:
            raise ValueError("matched Effect stack_count must be non-negative")


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


@dataclass(frozen=True, slots=True)
class ModifierApplicationResult:
    character_snapshots: tuple[CharacterSnapshot, ...]
    event_modifiers: tuple[Modifier, ...]
    event_stat_modifiers: tuple[EventStatModifier, ...] = ()
    event_multiplier_modifiers: tuple[Modifier, ...] = ()
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

    panel_effects: list[tuple[ModifierEffect, int]] = []
    rule_modifiers: list[Modifier] = []
    event_stat_modifiers: list[EventStatModifier] = []
    event_multiplier_modifiers: list[Modifier] = []
    vulnerability_policy: VulnerabilitySettlementPolicy = StandardVulnerabilityPolicy()
    vulnerability_policy_effect_seen = False
    for application in matched_effects:
        if isinstance(application, MatchedEffectApplication):
            effect = application.effect
            stack_count = application.stack_count
        else:
            effect = application
            stack_count = 1
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

    snapshots, applied_panel_ids, panel_traces = _apply_panel_effects(
        snapshots,
        panel_effects,
        current_operator,
        diagnostics,
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
    """Apply event-independent Panel Effects to their declared recipients.

    This pre-pass is intentionally separate from current-event matching.  It
    allows a support character's SELF panel Effect to update that support's
    snapshot before a different character's event is settled.
    """

    diagnostics: list[CalculationDiagnostic] = []
    snapshots = tuple(base_character_snapshots)
    applied_ids: set[EffectId] = set()
    traces: list[PanelModifierExecutionTrace] = []
    for rule in rule_items:
        if rule.rule_id not in scenario.enabled_rule_item_ids:
            continue
        if rule.eligibility is RuleEligibility.INELIGIBLE:
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
        condition_status, condition_diagnostics = _resolve_rule_conditions(
            rule,
            scenario,
        )
        diagnostics.extend(condition_diagnostics)
        if condition_status is not EffectMatchStatus.MATCHED:
            continue
        stack_count = _resolved_rule_stack(rule, scenario)
        for effect in panel_effects:
            effect = _resolve_effect_value(
                effect,
                initial_character_snapshots,
                diagnostics,
            )
            if effect is None:
                continue
            recipient = _panel_recipient(
                effect,
                scenario,
                diagnostics,
                team_character_ids,
            )
            if recipient is None:
                continue
            updated, effect_ids, panel_traces = _apply_panel_effects(
                snapshots,
                [(effect, stack_count)],
                recipient,
                diagnostics,
                rule_item_id_by_effect={effect.rule.effect_id: rule.rule_id},
            )
            snapshots = updated
            applied_ids.update(effect_ids)
            traces.extend(panel_traces)

    return ModifierApplicationResult(
        character_snapshots=snapshots,
        event_modifiers=(),
        applied_panel_effect_ids=frozenset(applied_ids),
        panel_traces=tuple(traces),
        diagnostics=tuple(diagnostics),
    )


def _resolve_rule_conditions(
    rule: CalculationRuleItem,
    scenario: CalculationScenario,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if not rule.condition_ids:
        return EffectMatchStatus.MATCHED, ()
    values = {item.condition_id: item.value for item in scenario.conditions}
    evaluations: list[tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]] = []
    for condition_id in rule.condition_ids:
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
        elif values[condition_id]:
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


def _panel_recipient(
    effect: ModifierEffect,
    scenario: CalculationScenario,
    diagnostics: list[CalculationDiagnostic],
    team_character_ids: frozenset[CharacterId] | None = None,
) -> CharacterId | None:
    rule = effect.rule
    if rule.target is EffectTarget.SELF:
        if rule.owner is None:
            diagnostics.append(
                _diagnostic(
                    str(rule.effect_id),
                    "panel-recipient-owner",
                    DiagnosticKind.MISSING_DATA,
                    "SELF Panel Effect has no owner",
                )
            )
            return None
        recipient = rule.owner
        if team_character_ids is not None and recipient not in team_character_ids:
            diagnostics.append(
                _diagnostic(
                    str(rule.effect_id),
                    "panel-recipient-team",
                    DiagnosticKind.DATA_QUALITY,
                    "SELF Panel Effect owner is not in the active team",
                )
            )
            return None
        return recipient

    facts = tuple(
        fact
        for fact in scenario.trigger_facts
        if str(fact.effect_id) == str(rule.effect_id)
        and fact.event_kind is BattleEventKind.SUPPORT_ENTRY
        and fact.actor is not None
    )
    if not facts:
        diagnostics.append(
            _diagnostic(
                str(rule.effect_id),
                "panel-recipient-fact",
                DiagnosticKind.MISSING_DATA,
                "support-entry Panel Effect has no recipient trigger fact",
            )
        )
        return None
    actors = {fact.actor for fact in facts if fact.actor is not None}
    if len(actors) != 1:
        diagnostics.append(
            _diagnostic(
                str(rule.effect_id),
                "panel-recipient-ambiguous",
                DiagnosticKind.DATA_QUALITY,
                "support-entry Panel Effect has multiple recipient actors",
            )
        )
        return None
    recipient = next(iter(actors))
    if team_character_ids is not None and recipient not in team_character_ids:
        diagnostics.append(
            _diagnostic(
                str(rule.effect_id),
                "panel-recipient-team",
                DiagnosticKind.DATA_QUALITY,
                "support-entry Panel Effect recipient is not in the active team",
            )
        )
        return None
    return recipient


def _resolve_effect_value(
    effect: ModifierEffect,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    diagnostics: list[CalculationDiagnostic],
) -> ModifierEffect | None:
    value = effect.result.value
    if not isinstance(value, PanelStatDerivedValue):
        return effect

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

    source_attack = source.initial_stats.attack
    coefficient = value.coefficient
    cap_max = value.cap_max
    if not isinstance(source_attack, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-attack",
                DiagnosticKind.MISSING_DATA,
                "initial attack is unresolved for a derived panel value",
            )
        )
        return None
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
    result = source_attack.value * coefficient.value
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
    if rule.trigger is None and (
        rule.condition is None or isinstance(rule.condition, AlwaysCondition)
    ) and not rule.filters:
        return True
    return (
        rule.target is EffectTarget.TEAM
        and rule.trigger is not None
        and rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        and rule.trigger.move_id is None
        and (rule.condition is None or isinstance(rule.condition, AlwaysCondition))
        and bool(rule.filters)
        and all(
            isinstance(item, DynamicIdentityFilter)
            and item.identity is DynamicIdentity.SUPPORT_ENTRY_CHARACTER
            for item in rule.filters
        )
    )


def _event_stat_modifier(
    effect: ModifierEffect,
    event: object | None,
    stack_count: int,
    diagnostics: list[CalculationDiagnostic],
) -> EventStatModifier | None:
    if not isinstance(event, DirectDamageEvent) or not isinstance(
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


def _apply_panel_effects(
    snapshots: tuple[CharacterSnapshot, ...],
    effects: list[tuple[ModifierEffect, int]],
    recipient: CharacterId,
    diagnostics: list[CalculationDiagnostic],
    *,
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
        if effect.result.modifier_path in {
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        }:
            is_crit_rate = (
                effect.result.modifier_path
                is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
            )
            current = updated_stats.crit_rate if is_crit_rate else updated_stats.crit_damage
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
                    {
                        "crit_rate": Resolved(
                            current.value + value.value * stack_count
                        )
                    }
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
                    rule_item_id=(rule_item_id_by_effect or {}).get(effect.rule.effect_id),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=value.value * stack_count,
                    stack_count=stack_count,
                )
            )
        elif effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS:
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
                    rule_item_id=(rule_item_id_by_effect or {}).get(effect.rule.effect_id),
                    effect_id=effect.rule.effect_id,
                    modifier_path=effect.result.modifier_path,
                    operation=effect.result.operation,
                    resolved_value=value.value * stack_count,
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
