"""Shared helpers for the reviewed Nanoka character compilers.

The production character payloads in this repository all use the same Nanoka
detail shape.  This module contains only mechanical compilation helpers: the
character modules still own the reviewed mapping and the rules for their own
identity.  Keeping the mechanical part here makes it harder for one of the
new character slices to accidentally read a legacy fixture or to hard-code a
level-12 multiplier.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

from core.types import (
    CharacterId,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageTag,
    DamageType,
    Element,
    FixedMultiplier,
    MoveId,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
    EffectSourceType,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DamageEventSemanticId, DiagnosticId, MoveEntryId, MultiplierVariantId
from ..moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from .definition import CharacterCalculationDefinition
from .templates import DirectDamageEventTemplate
from .nanoka_source import NanokaRawMoveRecord, NanokaRawRecord


@dataclass(frozen=True, slots=True)
class NanokaDamageParameterSpec:
    """One reviewed raw parameter used by a direct damage entry."""

    variant_key: str
    parameter_name: str
    condition_ids: tuple[object, ...] = ()
    source_skill_id: str | None = None
    source_skill_components: tuple[tuple[str, float], ...] = ()
    repeat_count: int | None = None

    def __post_init__(self) -> None:
        if self.source_skill_id is not None and self.source_skill_components:
            raise ValueError("choose one source skill ID or explicit source components")
        for source_id, coefficient in self.source_skill_components:
            if not source_id.strip() or not math.isfinite(coefficient):
                raise ValueError("source skill components require finite coefficients and IDs")
        if (
            self.repeat_count is not None
            and (
                isinstance(self.repeat_count, bool)
                or not isinstance(self.repeat_count, int)
                or self.repeat_count < 1
            )
        ):
            raise ValueError("reviewed source repeat_count must be a positive integer")


@dataclass(frozen=True, slots=True)
class NanokaMoveSpec:
    """Reviewed taxonomy for one displayed MoveCalculationEntry."""

    entry_key: str
    move_id: MoveId
    display_name: str
    source_name: str
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]
    parameters: tuple[NanokaDamageParameterSpec, ...]
    multiplier_relation: MultiplierRelation
    element: Element
    stage_index: int | None = None
    condition_ids: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class NanokaReviewedMapping:
    moves: tuple[NanokaMoveSpec, ...]
    data_quality_notes: tuple[str, ...] = ()


def source_for(
    character_id: CharacterId,
    source_key: str,
    source_type: EffectSourceType,
    label: str,
    raw_text: str | None,
) -> RuleSource:
    return RuleSource(
        source_id=RuleSourceId(f"source:{character_id}:{source_key}"),
        source_type=source_type,
        label=label,
        raw_text=raw_text,
    )


def effective_skill_level(config: object, group: SkillGroup) -> int:
    """Resolve the selected level and the reviewed C3/C5 skill bonuses."""

    selected = getattr(config, "skill_level_for")(group) or 12
    cinema = int(getattr(config, "cinema_level", 0))
    # All three new S-rank records use the standard C3/C5 wording: basic,
    # dodge, assist, special and chain receive +2, while ultimate does not.
    if group is not SkillGroup.ULTIMATE:
        if cinema >= 3:
            selected += 2
        if cinema >= 5:
            selected += 2
    return min(16, selected)


def raw_move_index(raw: NanokaRawRecord) -> dict[str, NanokaRawMoveRecord]:
    indexed: dict[str, NanokaRawMoveRecord] = {}
    for move in raw.moves:
        if move.name in indexed:
            raise ValueError(f"raw {raw.code_name} record contains duplicate move: {move.name}")
        indexed[move.name] = move
    return indexed


def raw_multiplier(
    raw_moves: Mapping[str, NanokaRawMoveRecord],
    source_name: str,
    parameter_name: str,
    level: int,
    subject: str,
    diagnostics: list[CalculationDiagnostic],
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
) -> float | Unresolved:
    move = raw_moves.get(source_name)
    parameter = (
        next((item for item in move.parameters if item.name == parameter_name), None)
        if move is not None
        else None
    )
    value = None
    if parameter is not None and parameter.format == "%":
        if source_skill_components:
            component_values = tuple(
                parameter.value_for_level(level, component_id) for component_id, _ in source_skill_components
            )
            if all(component is not None for component in component_values):
                value = sum(
                    float(component) * coefficient
                    for component, (_, coefficient) in zip(
                        component_values,
                        source_skill_components,
                    )
                )
        else:
            value = parameter.value_for_level(level, source_skill_id)
    if value is None:
        message = f"{subject}: missing {parameter_name} from {source_name} at skill level {level}"
        diagnostics.append(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(
                    f"data:{subject}:{source_name}:{parameter_name}:{level}"
                ),
                kind=DiagnosticKind.MISSING_DATA,
                message=message,
                blocking=True,
                original_text=parameter_name,
            )
        )
        return Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=message,
            original_text=parameter_name,
        )
    return value / 100.0


def compile_direct_moves(
    *,
    character_id: CharacterId,
    config: object,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping,
    id_namespace: str | None = None,
) -> tuple[
    tuple[MoveCalculationEntry, ...],
    tuple[DirectDamageEventTemplate, ...],
    tuple[CalculationDiagnostic, ...],
]:
    """Compile reviewed move specs from their matching raw parameter curves."""

    raw_moves = raw_move_index(raw_record)
    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    namespace = id_namespace or str(character_id)
    for spec in reviewed_mapping.moves:
        raw_move = raw_moves.get(spec.source_name)
        level = effective_skill_level(config, spec.skill_group)
        variants: list[MultiplierVariant] = []
        entry_diagnostics: list[CalculationDiagnostic] = []
        for parameter in spec.parameters:
            multiplier = raw_multiplier(
                raw_moves,
                spec.source_name,
                parameter.parameter_name,
                level,
                f"{character_id}:{spec.entry_key}",
                entry_diagnostics,
                parameter.source_skill_id,
                parameter.source_skill_components,
            )
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:{namespace}:{spec.entry_key}:{parameter.variant_key}"
                    ),
                    label=parameter.parameter_name,
                    parameter_name=parameter.parameter_name,
                    multiplier=(
                        multiplier
                        if isinstance(multiplier, Unresolved)
                        else FixedMultiplier(Resolved(multiplier))
                    ),
                    repeat_count=parameter.repeat_count,
                    condition_ids=tuple(parameter.condition_ids),
                )
            )
        template_id = f"template:{namespace}:{spec.entry_key}:main"
        semantic_id = f"event:{namespace}:{spec.entry_key}:main"
        ref = DamageEventTemplateRef(
            template_id=template_id,
            semantic_id=semantic_id,
            label=spec.display_name,
            damage_type=DamageType.DIRECT,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
            element=spec.element,
        )
        typed = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=character_id,
            element=spec.element,
            base_source=CurrentAttackValueSource(character_id),
            crit_rule=StandardCritRule(character_id),
            move_id=spec.move_id,
        )
        entry = MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:{namespace}:{spec.entry_key}"),
            character_id=character_id,
            move_id=spec.move_id,
            display_name=spec.display_name,
            original_text=(raw_move.description if raw_move is not None else spec.source_name),
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
            multiplier_relation=spec.multiplier_relation,
            multiplier_variants=tuple(variants),
            main_damage_event=ref,
            condition_ids=tuple(spec.condition_ids),
            stage_index=spec.stage_index,
            diagnostics=tuple(entry_diagnostics),
        )
        entries.append(entry)
        templates.append(typed)
        diagnostics.extend(entry_diagnostics)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def build_definition(
    *,
    character_id: CharacterId,
    role: CharacterRole,
    element: Element,
    source: RuleSource,
    entries: Sequence[MoveCalculationEntry],
    templates: Sequence[object],
    rules: Sequence[object],
    conditions: Sequence[object],
    parameters: Sequence[object] = (),
    independent_derived_damage_events: Sequence[object] = (),
    diagnostics: Sequence[CalculationDiagnostic] = (),
) -> CharacterCalculationDefinition:
    return CharacterCalculationDefinition(
        character_id=character_id,
        role=role,
        base_element=element,
        source=source,
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        scenario_parameters=tuple(parameters),
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=tuple(independent_derived_damage_events),
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "NanokaDamageParameterSpec",
    "NanokaMoveSpec",
    "NanokaReviewedMapping",
    "build_definition",
    "compile_direct_moves",
    "effective_skill_level",
    "raw_move_index",
    "raw_multiplier",
    "source_for",
]
