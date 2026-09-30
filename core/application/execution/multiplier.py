"""Resolve a compiled MoveEntry into one multiplier and an optional repeat count."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from core.types import DamageMultiplier, FixedMultiplier, Resolved, Unresolved

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..moves import MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ..scenario import CalculationScenario


class MultiplierResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_MATCHED = "not-matched"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class MoveMultiplierResolution:
    status: MultiplierResolutionStatus
    variant: MultiplierVariant | None = None
    multiplier: DamageMultiplier | None = None
    repeat_count: int = 1
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


def resolve_move_multiplier(
    entry: MoveCalculationEntry,
    scenario: CalculationScenario,
) -> MoveMultiplierResolution:
    condition_status, condition_diagnostics = _resolve_conditions(
        entry.condition_ids,
        scenario,
        str(entry.entry_id),
    )
    if condition_status is not MultiplierResolutionStatus.RESOLVED:
        return MoveMultiplierResolution(
            status=condition_status,
            diagnostics=condition_diagnostics,
        )

    if entry.multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION:
        return MoveMultiplierResolution(
            status=MultiplierResolutionStatus.BLOCKED,
            diagnostics=condition_diagnostics
            + (
                _diagnostic(
                    str(entry.entry_id),
                    "unresolved-multiplier-relation",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "the multiplier relationship is unresolved",
                    blocking=True,
                ),
            ),
        )

    variant_status, variant, variant_diagnostics = _select_variant(
        entry,
        scenario,
    )
    diagnostics = condition_diagnostics + variant_diagnostics
    if variant_status is not MultiplierResolutionStatus.RESOLVED or variant is None:
        return MoveMultiplierResolution(
            status=variant_status,
            diagnostics=diagnostics,
        )

    if isinstance(variant.multiplier, Unresolved):
        return MoveMultiplierResolution(
            status=MultiplierResolutionStatus.BLOCKED,
            variant=variant,
            diagnostics=diagnostics
            + (
                _diagnostic(
                    str(entry.entry_id),
                    "unresolved-multiplier",
                    DiagnosticKind.MISSING_DATA,
                    variant.multiplier.notes,
                    blocking=True,
                    original_text=variant.multiplier.original_text,
                ),
            ),
        )

    dynamic_multiplier, dynamic_diagnostics = _resolve_dynamic_multiplier(
        variant,
        variant.multiplier,
        scenario,
    )
    if dynamic_multiplier is None:
        return MoveMultiplierResolution(
            status=MultiplierResolutionStatus.BLOCKED,
            variant=variant,
            diagnostics=diagnostics + dynamic_diagnostics,
        )
    diagnostics += dynamic_diagnostics
    if dynamic_multiplier != variant.multiplier:
        variant = replace(variant, multiplier=dynamic_multiplier)

    repeat_status, repeat_count, repeat_diagnostics = _resolve_repeat_count(
        entry,
        variant,
        scenario,
    )
    diagnostics += repeat_diagnostics
    if repeat_status is not MultiplierResolutionStatus.RESOLVED:
        return MoveMultiplierResolution(
            status=repeat_status,
            variant=variant,
            multiplier=variant.multiplier,
            diagnostics=diagnostics,
        )
    return MoveMultiplierResolution(
        status=MultiplierResolutionStatus.RESOLVED,
        variant=variant,
        multiplier=variant.multiplier,
        repeat_count=repeat_count,
        diagnostics=diagnostics,
    )


def _resolve_dynamic_multiplier(
    variant: MultiplierVariant,
    multiplier: DamageMultiplier,
    scenario: CalculationScenario,
) -> tuple[DamageMultiplier | None, tuple[CalculationDiagnostic, ...]]:
    if variant.parameter_value_id is None:
        return multiplier, ()
    parameter = next(
        (
            item
            for item in scenario.parameters
            if item.parameter_id == variant.parameter_value_id
        ),
        None,
    )
    if parameter is None or parameter.value is None:
        return None, (
            _diagnostic(
                str(variant.variant_id),
                "dynamic-parameter-unresolved",
                DiagnosticKind.MISSING_DATA,
                f"multiplier scenario parameter is unresolved: {variant.parameter_value_id}",
                blocking=True,
            ),
        )
    if not isinstance(multiplier, FixedMultiplier) or not isinstance(
        multiplier.value, Resolved
    ):
        return None, (
            _diagnostic(
                str(variant.variant_id),
                "dynamic-base-unresolved",
                DiagnosticKind.MISSING_DATA,
                "dynamic multiplier requires a resolved fixed base multiplier",
                blocking=True,
            ),
        )
    assert variant.parameter_base_value is not None
    assert variant.parameter_coefficient is not None
    value = variant.parameter_base_value + variant.parameter_coefficient * parameter.value
    return FixedMultiplier(Resolved(value)), ()


def _select_variant(
    entry: MoveCalculationEntry,
    scenario: CalculationScenario,
) -> tuple[
    MultiplierResolutionStatus,
    MultiplierVariant | None,
    tuple[CalculationDiagnostic, ...],
]:
    variants = entry.multiplier_variants
    if entry.multiplier_relation in (
        MultiplierRelation.COMPLETE,
        MultiplierRelation.SEQUENTIAL_STAGE,
        MultiplierRelation.UNIT_REPEAT,
    ):
        status, diagnostics = _resolve_conditions(
            variants[0].condition_ids,
            scenario,
            str(variants[0].variant_id),
        )
        return (
            status,
            variants[0] if status is MultiplierResolutionStatus.RESOLVED else None,
            diagnostics,
        )

    active: list[MultiplierVariant] = []
    unresolved_variants: list[MultiplierVariant] = []
    for variant in variants:
        status, diagnostics = _resolve_conditions(
            variant.condition_ids,
            scenario,
            str(variant.variant_id),
        )
        if status is MultiplierResolutionStatus.BLOCKED:
            unresolved_variants.append(variant)
        elif status is MultiplierResolutionStatus.RESOLVED:
            active.append(variant)
        if diagnostics and status is not MultiplierResolutionStatus.NOT_MATCHED:
            unresolved_variants.append(variant)
    if unresolved_variants:
        unresolved_labels = ", ".join(
            _variant_condition_summary(variant)
            for variant in _unique_variants(unresolved_variants)
        )
        return (
            MultiplierResolutionStatus.BLOCKED,
            None,
            (
                _diagnostic(
                    str(entry.entry_id),
                    "variant-condition-unresolved",
                    DiagnosticKind.MISSING_DATA,
                    f"{entry.display_name} has unresolved mutually exclusive "
                    f"multiplier conditions: {unresolved_labels}",
                    blocking=True,
                    candidates=tuple(variant.label for variant in variants),
                ),
            ),
        )
    if len(active) == 1:
        return MultiplierResolutionStatus.RESOLVED, active[0], ()
    if not active:
        return (
            MultiplierResolutionStatus.BLOCKED,
            None,
            (
                _diagnostic(
                    str(entry.entry_id),
                    "no-variant-selected",
                    DiagnosticKind.MISSING_DATA,
                    f"{entry.display_name} has no selected mutually exclusive "
                    "multiplier variant; choose exactly one: "
                    + "; ".join(
                        _variant_condition_summary(variant)
                        for variant in variants
                    ),
                    blocking=True,
                    candidates=tuple(variant.label for variant in variants),
                ),
            ),
        )
    active_summary = "; ".join(
        _variant_condition_summary(variant) for variant in active
    )
    return (
        MultiplierResolutionStatus.BLOCKED,
        None,
        (
            _diagnostic(
                str(entry.entry_id),
                "multiple-variants-matched",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                f"{entry.display_name} has multiple mutually exclusive "
                f"multiplier variants selected: {active_summary}",
                blocking=True,
                candidates=tuple(variant.label for variant in active),
            ),
        ),
    )


def _resolve_repeat_count(
    entry: MoveCalculationEntry,
    variant: MultiplierVariant,
    scenario: CalculationScenario,
) -> tuple[
    MultiplierResolutionStatus,
    int,
    tuple[CalculationDiagnostic, ...],
]:
    if entry.multiplier_relation is not MultiplierRelation.UNIT_REPEAT:
        return MultiplierResolutionStatus.RESOLVED, 1, ()
    if variant.repeat_count is not None:
        return MultiplierResolutionStatus.RESOLVED, variant.repeat_count, ()
    parameter_id = variant.repeat_count_parameter_id
    if parameter_id is None:
        return (
            MultiplierResolutionStatus.BLOCKED,
            1,
            (
                _diagnostic(
                    str(entry.entry_id),
                    "missing-repeat-count",
                    DiagnosticKind.MISSING_DATA,
                    "unit-repeat variant has no repeat-count source",
                    blocking=True,
                ),
            ),
        )
    parameter = next(
        (item for item in scenario.parameters if item.parameter_id == parameter_id),
        None,
    )
    if parameter is None or parameter.value is None:
        return (
            MultiplierResolutionStatus.BLOCKED,
            1,
            (
                _diagnostic(
                    str(entry.entry_id),
                    "repeat-count-unresolved",
                    DiagnosticKind.MISSING_DATA,
                    f"repeat-count parameter is unresolved: {parameter_id}",
                    blocking=True,
                ),
            ),
        )
    return MultiplierResolutionStatus.RESOLVED, parameter.value, ()


def _resolve_conditions(
    condition_ids,
    scenario: CalculationScenario,
    subject_id: str,
) -> tuple[MultiplierResolutionStatus, tuple[CalculationDiagnostic, ...]]:
    if not condition_ids:
        return MultiplierResolutionStatus.RESOLVED, ()
    values = {item.condition_id: item.value for item in scenario.conditions}
    missing = [
        condition_id for condition_id in condition_ids if condition_id not in values
    ]
    if missing:
        return (
            MultiplierResolutionStatus.BLOCKED,
            (
                _diagnostic(
                    subject_id,
                    "missing-condition",
                    DiagnosticKind.MISSING_DATA,
                    f"missing scenario condition: {missing[0]}",
                    blocking=True,
                ),
            ),
        )
    if any(values[condition_id] is False for condition_id in condition_ids):
        return MultiplierResolutionStatus.NOT_MATCHED, ()
    if any(values[condition_id] is None for condition_id in condition_ids):
        return (
            MultiplierResolutionStatus.BLOCKED,
            (
                _diagnostic(
                    subject_id,
                    "unresolved-condition",
                    DiagnosticKind.MISSING_DATA,
                    "scenario condition has no selected value",
                    blocking=True,
                ),
            ),
        )
    return MultiplierResolutionStatus.RESOLVED, ()


def _diagnostic(
    subject_id: str,
    suffix: str,
    kind: DiagnosticKind,
    message: str,
    *,
    blocking: bool,
    original_text: str | None = None,
    candidates: tuple[str, ...] = (),
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{subject_id}:{suffix}"),
        kind=kind,
        message=message,
        blocking=blocking,
        original_text=original_text,
        candidates=candidates,
    )


def _variant_condition_summary(variant: MultiplierVariant) -> str:
    condition_ids = ", ".join(map(str, variant.condition_ids)) or "none"
    return f"{variant.label} (conditions: {condition_ids})"


def _unique_variants(
    variants: list[MultiplierVariant],
) -> tuple[MultiplierVariant, ...]:
    seen: set[object] = set()
    unique: list[MultiplierVariant] = []
    for variant in variants:
        if variant.variant_id in seen:
            continue
        seen.add(variant.variant_id)
        unique.append(variant)
    return tuple(unique)
