"""Move entries and typed references to their damage-event templates."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from core.types import (
    BattleEventKind,
    CharacterId,
    DamageMultiplier,
    DamageSubtype,
    DamageTag,
    DamageType,
    Element,
    EventTemplateId,
    MoveId,
    SkillGroup,
)

from .diagnostics import CalculationDiagnostic
from .ids import (
    DamageEventSemanticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)


class MultiplierRelation(StrEnum):
    COMPLETE = "complete"
    SEQUENTIAL_STAGE = "sequential-stage"
    MUTUALLY_EXCLUSIVE_VARIANT = "mutually-exclusive-variant"
    UNIT_REPEAT = "unit-repeat"
    UNRESOLVED_RELATION = "unresolved-relation"


@dataclass(frozen=True, slots=True)
class MultiplierVariant:
    variant_id: MultiplierVariantId
    label: str
    parameter_name: str
    multiplier: DamageMultiplier
    condition_ids: tuple[ScenarioConditionId, ...] = ()
    repeat_count: int | None = None
    repeat_count_parameter_id: ScenarioParameterId | None = None

    def __post_init__(self) -> None:
        if not str(self.variant_id):
            raise ValueError("variant_id must not be empty")
        if not self.label.strip() or not self.parameter_name.strip():
            raise ValueError("multiplier variant labels must not be empty")
        condition_ids = tuple(self.condition_ids)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("variant condition IDs must be unique")
        if self.repeat_count is not None and self.repeat_count < 0:
            raise ValueError("repeat_count must be non-negative")
        if self.repeat_count_parameter_id is not None and self.repeat_count is not None:
            raise ValueError(
                "a repeat count cannot be both fixed and parameter-selected"
            )


@dataclass(frozen=True, slots=True)
class DamageEventTemplateRef:
    template_id: EventTemplateId
    semantic_id: DamageEventSemanticId
    label: str
    damage_type: DamageType
    damage_subtype: DamageSubtype | None = None
    skill_group: SkillGroup | None = None
    damage_tags: frozenset[DamageTag] = frozenset()
    element: Element | None = None
    source_rule_item_id: RuleItemId | None = None
    event_kind: Literal[BattleEventKind.DAMAGE] = field(
        default=BattleEventKind.DAMAGE,
        init=False,
    )

    def __post_init__(self) -> None:
        if not str(self.template_id) or not str(self.semantic_id):
            raise ValueError("event template and semantic IDs must not be empty")
        if not self.label.strip():
            raise ValueError("event template label must not be empty")


@dataclass(frozen=True, slots=True)
class DerivedDamageEventTemplateRef:
    template: DamageEventTemplateRef
    multiplier: DamageMultiplier

    @property
    def semantic_id(self) -> DamageEventSemanticId:
        return self.template.semantic_id


@dataclass(frozen=True, slots=True)
class MoveCalculationEntry:
    entry_id: MoveEntryId
    character_id: CharacterId
    move_id: MoveId
    display_name: str
    original_text: str
    skill_group: SkillGroup | None
    damage_tags: frozenset[DamageTag]
    multiplier_relation: MultiplierRelation
    multiplier_variants: tuple[MultiplierVariant, ...]
    main_damage_event: DamageEventTemplateRef
    derived_damage_events: tuple[DerivedDamageEventTemplateRef, ...] = ()
    stage_index: int | None = None
    condition_ids: tuple[ScenarioConditionId, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.entry_id) or not self.character_id or not self.move_id:
            raise ValueError("move entry identities must not be empty")
        if not self.display_name.strip():
            raise ValueError("move display_name must not be empty")
        if not self.multiplier_variants:
            raise ValueError("a move entry requires at least one multiplier variant")
        if self.multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE:
            if self.stage_index is None or self.stage_index < 1:
                raise ValueError("sequential stages require a positive stage_index")
        elif self.stage_index is not None:
            raise ValueError("stage_index is only valid for sequential stages")
        if self.multiplier_relation in (
            MultiplierRelation.COMPLETE,
            MultiplierRelation.SEQUENTIAL_STAGE,
        ):
            if len(self.multiplier_variants) != 1:
                raise ValueError(
                    "complete and sequential entries require one multiplier variant"
                )
            variant = self.multiplier_variants[0]
            if (
                variant.repeat_count is not None
                or variant.repeat_count_parameter_id is not None
            ):
                raise ValueError(
                    "complete and sequential entries cannot define repeat counts"
                )
        elif self.multiplier_relation is MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT:
            if len(self.multiplier_variants) < 2:
                raise ValueError(
                    "mutually exclusive entries require multiple variants"
                )
        elif self.multiplier_relation is MultiplierRelation.UNIT_REPEAT:
            if len(self.multiplier_variants) != 1:
                raise ValueError("unit-repeat entries require one multiplier variant")
            variant = self.multiplier_variants[0]
            if (
                variant.repeat_count is None
                and variant.repeat_count_parameter_id is None
            ):
                raise ValueError("unit-repeat entries require a repeat count")
        if self.multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION:
            if not any(item.blocking for item in self.diagnostics):
                raise ValueError(
                    "unresolved multiplier relations require a blocking diagnostic"
                )

        variant_ids = tuple(item.variant_id for item in self.multiplier_variants)
        if len(set(variant_ids)) != len(variant_ids):
            raise ValueError("multiplier variant IDs must be unique within a move")
        event_ids = (
            self.main_damage_event.semantic_id,
            *(item.template.semantic_id for item in self.derived_damage_events),
        )
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("damage event semantic IDs must be unique within a move")
        if self.main_damage_event.skill_group is not self.skill_group:
            raise ValueError("main event skill_group must match its move entry")
        if self.main_damage_event.damage_tags != self.damage_tags:
            raise ValueError("main event damage_tags must match its move entry")
        condition_ids = tuple(self.condition_ids)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("move condition IDs must be unique")
