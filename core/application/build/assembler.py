"""Build Assembly for out-of-combat character panels.

The assembler is deliberately independent from combat matching and
calculation.  It turns typed static contributions into a CharacterStats
snapshot, preserving unresolved values and provenance instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.ids import DiagnosticId
from core.application.rules import CalculationRuleItem
from core.types import (
    BuildContributionLayer,
    BuildContributionTrace,
    BuildMode,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    CharacterBuildDefinition,
    CharacterId,
    CharacterSnapshot,
    CharacterStat,
    CharacterStats,
    Element,
    InitialCharacterSnapshot,
    Resolvable,
    Resolved,
    Unresolved,
    UnresolvedReason,
)


@dataclass(frozen=True, slots=True)
class ResolvedBuild:
    """Build Assembly output consumed by later application stages."""

    character_id: CharacterId
    level: int
    mode: BuildMode
    base_stats: CharacterStats | None
    initial_stats: CharacterStats
    initial_snapshot: InitialCharacterSnapshot
    provenance: tuple[BuildContributionTrace, ...] = ()
    rule_items: tuple[CalculationRuleItem, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()
    unresolved: tuple[Unresolved, ...] = ()

    @property
    def out_of_combat_stats(self) -> CharacterStats:
        """The public name used by presentation and build consumers."""

        return self.initial_stats

    @property
    def character_snapshot(self) -> CharacterSnapshot:
        """A settlement-compatible snapshot before combat Panel Effects."""

        return CharacterSnapshot(
            character_id=self.character_id,
            level=self.level,
            settlement_stats=self.initial_stats,
        )

    @property
    def complete(self) -> bool:
        return not self.unresolved and not any(item.blocking for item in self.diagnostics)


_SCALAR_FIELDS: tuple[tuple[CharacterStat, str], ...] = (
    (CharacterStat.HP, "hp"),
    (CharacterStat.ATTACK, "attack"),
    (CharacterStat.DEFENSE, "defense"),
    (CharacterStat.IMPACT, "impact"),
    (CharacterStat.ANOMALY_MASTERY, "anomaly_mastery"),
    (CharacterStat.ANOMALY_PROFICIENCY, "anomaly_proficiency"),
    (CharacterStat.PENETRATION_FLAT, "penetration_flat"),
    (CharacterStat.ENERGY_REGEN, "energy_regen"),
    (CharacterStat.CRIT_RATE, "crit_rate"),
    (CharacterStat.CRIT_DAMAGE, "crit_damage"),
    (CharacterStat.PENETRATION_RATE, "penetration_rate"),
)

def assemble_build(
    definition: CharacterBuildDefinition,
    *,
    rule_items: tuple[CalculationRuleItem, ...] = (),
) -> ResolvedBuild:
    """Assemble one immutable out-of-combat panel.

    `rule_items` is intentionally only carried through.  It is not matched or
    executed here; conditional equipment effects belong to the application
    matcher/execution pipeline.
    """

    if definition.mode is BuildMode.MANUAL_PANEL:
        assert definition.manual_panel_stats is not None
        diagnostics, unresolved = _validate_stats(
            definition.manual_panel_stats,
            definition.character_id,
        )
        provenance = _manual_provenance(definition.manual_panel_stats)
        return ResolvedBuild(
            character_id=definition.character_id,
            level=definition.level,
            mode=definition.mode,
            base_stats=None,
            initial_stats=definition.manual_panel_stats,
            initial_snapshot=InitialCharacterSnapshot(
                character_id=definition.character_id,
                level=definition.level,
                initial_stats=definition.manual_panel_stats,
            ),
            provenance=provenance,
            rule_items=tuple(rule_items),
            diagnostics=diagnostics,
            unresolved=unresolved,
        )

    assert definition.base_stats is not None
    return _assemble_equipment_build(definition, tuple(rule_items))


def _assemble_equipment_build(
    definition: CharacterBuildDefinition,
    rule_items: tuple[CalculationRuleItem, ...],
) -> ResolvedBuild:
    base_stats = definition.base_stats
    diagnostics, unresolved = _validate_stats(base_stats, definition.character_id)
    traces: list[BuildContributionTrace] = []
    unresolved_list = list(unresolved)
    diagnostics_list = list(diagnostics)

    grouped: dict[CharacterStat, list[BuildStatContribution]] = {
        stat: [] for stat, _ in _SCALAR_FIELDS
    }
    element_contributions: dict[Element, list[BuildStatContribution]] = {}
    for contribution in definition.contributions:
        if contribution.stat is CharacterStat.ELEMENT_DAMAGE_BONUS:
            assert contribution.element is not None
            element_contributions.setdefault(contribution.element, []).append(contribution)
        else:
            grouped[contribution.stat].append(contribution)

    values: dict[CharacterStat, Resolvable[float]] = {}
    for stat, field_name in _SCALAR_FIELDS:
        base_value = getattr(base_stats, field_name)
        stat_value, stat_traces, stat_unresolved, stat_diagnostics = _assemble_scalar(
            definition.character_id,
            stat,
            base_value,
            grouped[stat],
        )
        values[stat] = stat_value
        traces.extend(stat_traces)
        unresolved_list.extend(stat_unresolved)
        diagnostics_list.extend(stat_diagnostics)

    element_bonus = dict(base_stats.element_damage_bonus)
    for element, contributions in element_contributions.items():
        base_value = element_bonus.get(element, Resolved(0.0))
        total, element_traces, element_unresolved, element_diagnostics = _assemble_ratio(
            definition.character_id,
            CharacterStat.ELEMENT_DAMAGE_BONUS,
            base_value,
            contributions,
            element,
        )
        element_bonus[element] = total
        traces.extend(element_traces)
        unresolved_list.extend(element_unresolved)
        diagnostics_list.extend(element_diagnostics)

    initial_stats = CharacterStats(
        hp=values[CharacterStat.HP],
        attack=values[CharacterStat.ATTACK],
        defense=values[CharacterStat.DEFENSE],
        impact=values[CharacterStat.IMPACT],
        crit_rate=values[CharacterStat.CRIT_RATE],
        crit_damage=values[CharacterStat.CRIT_DAMAGE],
        anomaly_mastery=values[CharacterStat.ANOMALY_MASTERY],
        anomaly_proficiency=values[CharacterStat.ANOMALY_PROFICIENCY],
        penetration_rate=values[CharacterStat.PENETRATION_RATE],
        penetration_flat=values[CharacterStat.PENETRATION_FLAT],
        energy_regen=values[CharacterStat.ENERGY_REGEN],
        element_damage_bonus=element_bonus,
    )
    return ResolvedBuild(
        character_id=definition.character_id,
        level=definition.level,
        mode=definition.mode,
        base_stats=base_stats,
        initial_stats=initial_stats,
        initial_snapshot=InitialCharacterSnapshot(
            character_id=definition.character_id,
            level=definition.level,
            initial_stats=initial_stats,
        ),
        provenance=tuple(traces),
        rule_items=rule_items,
        diagnostics=tuple(dict.fromkeys(diagnostics_list)),
        unresolved=tuple(dict.fromkeys(unresolved_list)),
    )


def _assemble_scalar(
    character_id: CharacterId,
    stat: CharacterStat,
    base_value: Resolvable[float],
    contributions: list[BuildStatContribution],
) -> tuple[
    Resolvable[float],
    list[BuildContributionTrace],
    list[Unresolved],
    list[CalculationDiagnostic],
]:
    if stat in {
        CharacterStat.CRIT_RATE,
        CharacterStat.CRIT_DAMAGE,
        CharacterStat.PENETRATION_RATE,
    }:
        return _assemble_ratio(character_id, stat, base_value, contributions, None)

    traces: list[BuildContributionTrace] = []
    unresolved: list[Unresolved] = []
    diagnostics: list[CalculationDiagnostic] = []
    base_numeric = _numeric_or_unresolved(
        base_value,
        character_id,
        f"base-{stat.value}",
        unresolved,
        diagnostics,
    )
    if base_numeric is None:
        final: Resolvable[float] = base_value
        for contribution in contributions:
            traces.append(_trace(contribution, contribution.value))
            if isinstance(contribution.value, Unresolved):
                unresolved.append(contribution.value)
                diagnostics.append(_missing_contribution_diagnostic(contribution))
        return final, traces, unresolved, diagnostics

    white_add = 0.0
    percent_add = 0.0
    flat_add = 0.0
    failed = False
    for contribution in contributions:
        numeric = _numeric_or_unresolved(
            contribution.value,
            character_id,
            contribution.contribution_id,
            unresolved,
            diagnostics,
        )
        traces.append(_trace(contribution, contribution.value))
        if numeric is None:
            failed = True
            continue
        if contribution.layer is BuildContributionLayer.WHITE_VALUE:
            white_add += numeric
        elif contribution.layer is BuildContributionLayer.OUT_OF_COMBAT_PERCENT:
            percent_add += numeric
        elif contribution.layer is BuildContributionLayer.OUT_OF_COMBAT_FLAT:
            flat_add += numeric
        else:
            raise AssertionError(
                f"unexpected layer for scalar stat: {contribution.layer}"
            )

    if failed:
        return (
            Unresolved(
                UnresolvedReason.MISSING_DATA,
                f"cannot assemble {stat.value}: one or more contributions are unresolved",
            ),
            traces,
            unresolved,
            diagnostics,
        )
    return (
        Resolved((base_numeric + white_add) * (1.0 + percent_add) + flat_add),
        traces,
        unresolved,
        diagnostics,
    )


def _assemble_ratio(
    character_id: CharacterId,
    stat: CharacterStat,
    base_value: Resolvable[float],
    contributions: list[BuildStatContribution],
    element: Element | None,
) -> tuple[
    Resolvable[float],
    list[BuildContributionTrace],
    list[Unresolved],
    list[CalculationDiagnostic],
]:
    traces: list[BuildContributionTrace] = []
    unresolved: list[Unresolved] = []
    diagnostics: list[CalculationDiagnostic] = []
    base_numeric = _numeric_or_unresolved(
        base_value,
        character_id,
        f"base-{stat.value}-{element.value if element else 'scalar'}",
        unresolved,
        diagnostics,
    )
    failed = base_numeric is None
    total = base_numeric or 0.0
    for contribution in contributions:
        numeric = _numeric_or_unresolved(
            contribution.value,
            character_id,
            contribution.contribution_id,
            unresolved,
            diagnostics,
        )
        traces.append(_trace(contribution, contribution.value))
        if numeric is None:
            failed = True
        else:
            if contribution.layer is not BuildContributionLayer.DIRECT_RATIO:
                raise AssertionError(
                    f"unexpected layer for ratio stat: {contribution.layer}"
                )
            total += numeric
    if failed:
        return (
            Unresolved(
                UnresolvedReason.MISSING_DATA,
                f"cannot assemble {stat.value}: one or more values are unresolved",
            ),
            traces,
            unresolved,
            diagnostics,
        )
    return Resolved(total), traces, unresolved, diagnostics


def _numeric_or_unresolved(
    value: Resolvable[float],
    character_id: CharacterId,
    field_id: str,
    unresolved: list[Unresolved],
    diagnostics: list[CalculationDiagnostic],
) -> float | None:
    if isinstance(value, Resolved):
        return float(value.value)
    unresolved.append(value)
    diagnostics.append(
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId(f"build:{character_id}:{field_id}"),
            kind=DiagnosticKind.MISSING_DATA,
            message=value.notes,
            blocking=True,
        )
    )
    return None


def _trace(
    contribution: BuildStatContribution,
    applied_value: Resolvable[float],
) -> BuildContributionTrace:
    return BuildContributionTrace(
        contribution_id=contribution.contribution_id,
        source=contribution.source,
        stat=contribution.stat,
        layer=contribution.layer,
        input_value=contribution.value,
        applied_value=applied_value,
        element=contribution.element,
    )


def _missing_contribution_diagnostic(
    contribution: BuildStatContribution,
) -> CalculationDiagnostic:
    value = contribution.value
    assert isinstance(value, Unresolved)
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"build:{contribution.contribution_id}:missing"),
        kind=DiagnosticKind.MISSING_DATA,
        message=value.notes,
        blocking=True,
    )


def _validate_stats(
    stats: CharacterStats,
    character_id: CharacterId,
) -> tuple[tuple[CalculationDiagnostic, ...], tuple[Unresolved, ...]]:
    diagnostics: list[CalculationDiagnostic] = []
    unresolved: list[Unresolved] = []
    scalar_values: Iterable[Resolvable[float]] = (
        stats.hp,
        stats.attack,
        stats.defense,
        stats.impact,
        stats.crit_rate,
        stats.crit_damage,
        stats.anomaly_mastery,
        stats.anomaly_proficiency,
        stats.penetration_rate,
        stats.penetration_flat,
        stats.energy_regen,
    )
    for index, value in enumerate(scalar_values):
        if isinstance(value, Unresolved):
            unresolved.append(value)
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(f"build:{character_id}:base:{index}"),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=value.notes,
                    blocking=True,
                )
            )
        elif not isinstance(value.value, (int, float)) or not math.isfinite(float(value.value)):
            raise ValueError("base character stat values must be finite numbers")
    for element, value in stats.element_damage_bonus.items():
        if not isinstance(element, Element):
            raise ValueError("element_damage_bonus keys must be Element values")
        if isinstance(value, Unresolved):
            unresolved.append(value)
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"build:{character_id}:base:element:{element.value}"
                    ),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=value.notes,
                    blocking=True,
                )
            )
        elif not isinstance(value.value, (int, float)) or not math.isfinite(float(value.value)):
            raise ValueError("base element damage bonus values must be finite numbers")
    return tuple(diagnostics), tuple(unresolved)


def _manual_provenance(stats: CharacterStats) -> tuple[BuildContributionTrace, ...]:
    source = BuildSource(
        source_id="build:manual-panel",
        source_type=BuildSourceType.MANUAL_PANEL,
        label="手工局外面板",
    )
    traces: list[BuildContributionTrace] = []
    for stat, field_name in _SCALAR_FIELDS:
        value = getattr(stats, field_name)
        traces.append(
            BuildContributionTrace(
                contribution_id=f"manual:{stat.value}",
                source=source,
                stat=stat,
                layer=BuildContributionLayer.MANUAL_PANEL,
                input_value=value,
                applied_value=value,
            )
        )
    for element, value in stats.element_damage_bonus.items():
        traces.append(
            BuildContributionTrace(
                contribution_id=f"manual:element:{element.value}",
                source=source,
                stat=CharacterStat.ELEMENT_DAMAGE_BONUS,
                layer=BuildContributionLayer.MANUAL_PANEL,
                input_value=value,
                applied_value=value,
                element=element,
            )
        )
    return tuple(traces)


__all__ = ["ResolvedBuild", "assemble_build"]
