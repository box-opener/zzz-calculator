"""Static matching of CalculationRuleItems against one settlement event."""

from __future__ import annotations

from core.types import Effect, EffectId, UnresolvedEffect

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..rules import CalculationRuleItem, RuleEligibility
from .context import EffectMatchContext
from .evaluator import (
    diagnostic,
    match_condition,
    match_filters,
    match_target,
    match_trigger,
)
from .result import EffectMatchResult, EffectMatchStatus, RuleItemMatchResult


class EffectMatcher:
    def match_rule_item(
        self,
        rule_item: CalculationRuleItem,
        context: EffectMatchContext,
    ) -> RuleItemMatchResult:
        if rule_item.rule_id not in context.scenario.enabled_rule_item_ids:
            return RuleItemMatchResult(
                rule_id=rule_item.rule_id,
                status=EffectMatchStatus.NOT_MATCHED,
            )
        if rule_item.eligibility is RuleEligibility.INELIGIBLE:
            return RuleItemMatchResult(
                rule_id=rule_item.rule_id,
                status=EffectMatchStatus.NOT_MATCHED,
                diagnostics=(
                    diagnostic(
                        str(rule_item.rule_id),
                        "ineligible-rule",
                        DiagnosticKind.DATA_QUALITY,
                        "an ineligible rule was ignored even though it was selected",
                        blocking=False,
                    ),
                ),
            )

        gate_status, gate_diagnostics = self._match_rule_conditions(
            rule_item,
            context,
        )
        if gate_status is not EffectMatchStatus.MATCHED:
            return RuleItemMatchResult(
                rule_id=rule_item.rule_id,
                status=gate_status,
                diagnostics=gate_diagnostics,
            )

        effect_results = tuple(
            self.match_effect(effect, context)
            for effect in rule_item.effects
        )
        statuses = tuple(item.status for item in effect_results)
        if not statuses:
            status = EffectMatchStatus.NOT_MATCHED
        elif EffectMatchStatus.MATCHED in statuses:
            status = EffectMatchStatus.MATCHED
        elif EffectMatchStatus.BLOCKED in statuses:
            status = EffectMatchStatus.BLOCKED
        else:
            status = EffectMatchStatus.NOT_MATCHED
        diagnostics = tuple(
            diagnostic_item
            for item in effect_results
            for diagnostic_item in item.diagnostics
        )
        return RuleItemMatchResult(
            rule_id=rule_item.rule_id,
            status=status,
            effects=effect_results,
            diagnostics=diagnostics,
        )

    def match_rule_items(
        self,
        rule_items: tuple[CalculationRuleItem, ...],
        context: EffectMatchContext,
    ) -> tuple[RuleItemMatchResult, ...]:
        rule_ids = tuple(item.rule_id for item in rule_items)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("rule item IDs must be unique for a matching pass")
        return tuple(self.match_rule_item(item, context) for item in rule_items)

    def match_effect(
        self,
        effect: Effect,
        context: EffectMatchContext,
    ) -> EffectMatchResult:
        effect_id: EffectId = effect.rule.effect_id
        if isinstance(effect, UnresolvedEffect):
            return EffectMatchResult(
                effect_id=effect_id,
                status=EffectMatchStatus.BLOCKED,
                diagnostics=(
                    diagnostic(
                        str(effect_id),
                        "unresolved-effect",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        effect.unresolved.notes,
                        blocking=True,
                        original_text=effect.unresolved.original_text,
                    ),
                ),
            )

        decisions = []
        diagnostics: list[CalculationDiagnostic] = []
        for status, item_diagnostics in (
            match_target(effect.rule.target, effect.rule.owner, context, str(effect_id)),
            match_trigger(effect.rule, context, str(effect_id)),
            match_condition(
                effect.rule.condition,
                context,
                effect.rule.owner,
                str(effect_id),
            ),
            match_filters(
                effect.rule.filters,
                context,
                str(effect_id),
                effect.rule.target,
            ),
        ):
            decisions.append(status)
            diagnostics.extend(item_diagnostics)

        if EffectMatchStatus.NOT_MATCHED in decisions:
            status = EffectMatchStatus.NOT_MATCHED
        elif EffectMatchStatus.BLOCKED in decisions:
            status = EffectMatchStatus.BLOCKED
        else:
            status = EffectMatchStatus.MATCHED
        return EffectMatchResult(
            effect_id=effect_id,
            status=status,
            effect=effect if status is EffectMatchStatus.MATCHED else None,
            diagnostics=tuple(diagnostics),
        )

    @staticmethod
    def _match_rule_conditions(
        rule_item: CalculationRuleItem,
        context: EffectMatchContext,
    ):
        if not rule_item.condition_ids:
            return EffectMatchStatus.MATCHED, ()
        condition_map = {
            item.condition_id: item
            for item in context.scenario.conditions
        }
        statuses = []
        diagnostics = []
        for condition_id in rule_item.condition_ids:
            condition = condition_map.get(condition_id)
            if condition is None:
                statuses.append(EffectMatchStatus.BLOCKED)
                diagnostics.append(
                    diagnostic(
                        str(rule_item.rule_id),
                        f"missing-condition-{condition_id}",
                        DiagnosticKind.MISSING_DATA,
                        f"missing scenario condition: {condition_id}",
                        blocking=True,
                    )
                )
            elif condition.value is None:
                statuses.append(EffectMatchStatus.BLOCKED)
                diagnostics.append(
                    diagnostic(
                        str(rule_item.rule_id),
                        f"unresolved-condition-{condition_id}",
                        DiagnosticKind.MISSING_DATA,
                        f"scenario condition has no selected value: {condition_id}",
                        blocking=True,
                    )
                )
            elif condition.value:
                statuses.append(EffectMatchStatus.MATCHED)
            else:
                statuses.append(EffectMatchStatus.NOT_MATCHED)
        if EffectMatchStatus.NOT_MATCHED in statuses:
            status = EffectMatchStatus.NOT_MATCHED
        elif EffectMatchStatus.BLOCKED in statuses:
            status = EffectMatchStatus.BLOCKED
        else:
            status = EffectMatchStatus.MATCHED
        return status, tuple(diagnostics)
