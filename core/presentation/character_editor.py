"""Views for a compiled character definition and its scenario controls."""

from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import DiagnosticView


@dataclass(frozen=True, slots=True)
class ScenarioConditionView:
    condition_id: str
    label: str
    resolution: str
    value: bool | None
    editable: bool
    original_text: str


@dataclass(frozen=True, slots=True)
class CompileConfigFieldView:
    field_id: str
    label: str
    field_type: str
    value: bool | int | float | str
    minimum: int | float | None = None
    maximum: int | float | None = None
    editable: bool = True
    options: tuple[str, ...] = ()
    help_text: str | None = None


@dataclass(frozen=True, slots=True)
class ScenarioParameterView:
    parameter_id: str
    label: str
    resolution: str
    value: int | None
    minimum: int
    maximum: int | None
    original_text: str


@dataclass(frozen=True, slots=True)
class ScenarioTriggerInputView:
    input_id: str
    label: str
    actor_options: tuple[str, ...]
    required: bool
    selected_actor: str | None
    rule_item_id: str | None = None


@dataclass(frozen=True, slots=True)
class RuleStackView:
    default: int | None
    minimum: int | None
    maximum: int | None


@dataclass(frozen=True, slots=True)
class RuleItemView:
    rule_id: str
    label: str
    source_label: str
    source_type: str
    eligibility: str
    availability: str
    enabled_by_default: bool
    toggleable: bool
    stack: RuleStackView
    condition_ids: tuple[str, ...]
    condition_not_ids: tuple[str, ...]
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class MoveVariantView:
    variant_id: str
    label: str
    parameter_name: str
    multiplier: float | None
    condition_ids: tuple[str, ...]
    repeat_count: int | None
    repeat_count_parameter_id: str | None


@dataclass(frozen=True, slots=True)
class MoveView:
    entry_id: str
    move_id: str | None
    label: str
    skill_group: str | None
    damage_tags: tuple[str, ...]
    multiplier_relation: str
    variants: tuple[MoveVariantView, ...]
    condition_ids: tuple[str, ...]
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class CharacterEditorView:
    schema_version: str
    character_id: str
    display_name: str
    role: str
    base_element: str
    compile_config_fields: tuple[CompileConfigFieldView, ...]
    moves: tuple[MoveView, ...]
    rule_items: tuple[RuleItemView, ...]
    scenario_conditions: tuple[ScenarioConditionView, ...]
    scenario_parameters: tuple[ScenarioParameterView, ...]
    scenario_trigger_inputs: tuple[ScenarioTriggerInputView, ...]
    diagnostics: tuple[DiagnosticView, ...]
    luminance_source_elements: tuple[str, ...] = ()
    anomaly_source_elements: tuple[str, ...] = ()
    effective_damage_element: str | None = None


@dataclass(frozen=True, slots=True)
class WEngineEditorView:
    """Editor contract for one equipped W-Engine instance.

    Rule and condition IDs are instance IDs produced for the equipped owner;
    they must never be stored on the model-level catalog item.
    """

    schema_version: str
    wengine_id: str
    equipped_character_id: str
    display_name: str
    rarity: str
    specialty: str
    rule_items: tuple[RuleItemView, ...]
    scenario_conditions: tuple[ScenarioConditionView, ...]
    scenario_parameters: tuple[ScenarioParameterView, ...] = ()
    scenario_trigger_inputs: tuple[ScenarioTriggerInputView, ...] = ()
    diagnostics: tuple[DiagnosticView, ...] = ()


@dataclass(frozen=True, slots=True)
class DriveDiscStatOptionView:
    stat_key: str
    label: str
    value_per_roll: float


@dataclass(frozen=True, slots=True)
class DriveDiscSlotSchemaView:
    slot: int
    main_stat_options: tuple[DriveDiscStatOptionView, ...]


@dataclass(frozen=True, slots=True)
class DriveDiscSetCountView:
    set_id: str
    count: int


@dataclass(frozen=True, slots=True)
class DriveDiscEditorView:
    schema_version: str
    equipped_character_id: str
    set_counts: tuple[DriveDiscSetCountView, ...]
    slot_schemas: tuple[DriveDiscSlotSchemaView, ...]
    substat_options: tuple[DriveDiscStatOptionView, ...]
    rule_items: tuple[RuleItemView, ...]
    scenario_conditions: tuple[ScenarioConditionView, ...]
    scenario_trigger_inputs: tuple[ScenarioTriggerInputView, ...]
    diagnostics: tuple[DiagnosticView, ...]


__all__ = [
    "CharacterEditorView",
    "CompileConfigFieldView",
    "DriveDiscEditorView",
    "DriveDiscSetCountView",
    "DriveDiscSlotSchemaView",
    "DriveDiscStatOptionView",
    "MoveVariantView",
    "MoveView",
    "RuleItemView",
    "RuleStackView",
    "ScenarioConditionView",
    "ScenarioParameterView",
    "ScenarioTriggerInputView",
    "WEngineEditorView",
]
