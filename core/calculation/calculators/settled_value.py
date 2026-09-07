"""Calculator for anomaly-labelled damage derived from a settled value.

This lane is intentionally tiny: Alice's periodic physical-anomaly effect is
defined as a percentage of an already settled damage result.  Reapplying the
source event's defense, resistance, or vulnerability regions would be a
second calculation, so this calculator multiplies only the referenced final
value by the declared child multiplier.
"""

from __future__ import annotations

from core.types import (
    CalculationContext,
    CalculationNode,
    FixedMultiplier,
    NoCritRule,
    Resolved,
    SettledAnomalyDamageEvent,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from ..result import CalculationResult
from .errors import InvalidCalculationContextError


class SettledAnomalyDamageCalculator:
    """Calculate a typed child from one previously settled final value."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, SettledAnomalyDamageEvent):
            raise InvalidCalculationContextError(
                "SettledAnomalyDamageCalculator only accepts SettledAnomalyDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )
        unresolved: list[Unresolved] = []
        settled = context.settled_damage_values.get(
            event.base_settlement_data_source.event_id
        )
        if not isinstance(settled, Resolved):
            if isinstance(settled, Unresolved):
                unresolved.append(settled)
            else:
                unresolved.append(
                    Unresolved(
                        reason=UnresolvedReason.MISSING_DATA,
                        notes=(
                            "settled damage value is missing for "
                            f"{event.base_settlement_data_source.event_id}"
                        ),
                    )
                )
        if not isinstance(event.multiplier, FixedMultiplier):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes="settled anomaly damage requires a fixed multiplier",
                )
            )
            multiplier = None
        elif not isinstance(event.multiplier.value, Resolved):
            unresolved.append(event.multiplier.value)
            multiplier = None
        else:
            multiplier = event.multiplier.value.value
        if not isinstance(event.crit_rule, NoCritRule):
            if isinstance(event.crit_rule, Unresolved):
                unresolved.append(event.crit_rule)
            else:
                unresolved.append(
                    Unresolved(
                        reason=UnresolvedReason.MISSING_SPEC_RULE,
                        notes="settled anomaly child supports NoCritRule only",
                    )
                )
        if unresolved or not isinstance(settled, Resolved) or multiplier is None:
            return CalculationResult(value=None, breakdown=(), unresolved=tuple(unresolved))
        base = float(settled.value)
        value = base * multiplier
        return CalculationResult(
            value=value,
            breakdown=(
                CalculationNodeValue(
                    node=CalculationNode.DAMAGE_SETTLED_VALUE,
                    value=Resolved(base),
                    read_rule=SnapshotRule.INHERITED,
                ),
                CalculationNodeValue(
                    node=CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                    value=Resolved(multiplier),
                    read_rule=SnapshotRule.INHERITED,
                ),
                CalculationNodeValue(
                    node=CalculationNode.DAMAGE_BASE_VALUE,
                    value=Resolved(value),
                    read_rule=SnapshotRule.INHERITED,
                ),
            ),
        )


__all__ = ["SettledAnomalyDamageCalculator"]
