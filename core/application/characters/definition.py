"""Immutable, scenario-specific character calculation definitions."""

from dataclasses import dataclass

from core.types import (
    CharacterId,
    CharacterRole,
    Element,
    EventCreationEffect,
    EventTemplateId,
    MoveId,
    RuleSource,
)

from ..diagnostics import CalculationDiagnostic
from ..ids import (
    DamageEventSemanticId,
    ScenarioConditionId,
)
from ..moves import (
    DamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
)
from ..rules import CalculationRuleItem
from ..scenario import (
    CalculationScenario,
    ConditionResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
    ParameterResolution,
)
from .config import YeShunguangCompileConfig
from .templates import DirectDamageEventTemplate


@dataclass(frozen=True, slots=True)
class CharacterCalculationDefinition:
    character_id: CharacterId
    role: CharacterRole
    base_element: Element
    source: RuleSource
    compile_config: YeShunguangCompileConfig
    move_entries: tuple[MoveCalculationEntry, ...]
    rule_items: tuple[CalculationRuleItem, ...]
    scenario_conditions: tuple[ScenarioCondition, ...]
    scenario_parameters: tuple[ScenarioIntegerParameter, ...]
    damage_event_templates: tuple[DirectDamageEventTemplate, ...]
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if self.character_id != self.compile_config.character_id:
            raise ValueError("definition character_id must match compile_config")
        self._assert_unique(
            (item.entry_id for item in self.move_entries),
            "MoveEntryId",
        )
        self._assert_unique(
            (item.rule_id for item in self.rule_items),
            "RuleItemId",
        )
        self._assert_unique(
            (
                effect.rule.effect_id
                for rule in self.rule_items
                for effect in rule.effects
            ),
            "EffectId",
        )
        self._assert_unique(
            (item.condition_id for item in self.scenario_conditions),
            "ScenarioConditionId",
        )
        self._assert_unique(
            (item.parameter_id for item in self.scenario_parameters),
            "ScenarioParameterId",
        )
        self._assert_unique(
            (item.ref.template_id for item in self.damage_event_templates),
            "EventTemplateId",
        )
        self._assert_unique(
            (item.ref.semantic_id for item in self.damage_event_templates),
            "DamageEventSemanticId",
        )

        template_map = {
            item.ref.template_id: item
            for item in self.damage_event_templates
        }
        rule_map = {item.rule_id: item for item in self.rule_items}
        condition_ids = {
            item.condition_id for item in self.scenario_conditions
        }
        definition_event_ids: set[DamageEventSemanticId] = set()
        for entry in self.move_entries:
            self._assert_condition_references(entry.condition_ids, condition_ids)
            for variant in entry.multiplier_variants:
                self._assert_condition_references(
                    variant.condition_ids,
                    condition_ids,
                )
            self._assert_template_ref(
                entry.main_damage_event,
                template_map,
                entry.move_id,
                expect_move_id=True,
            )
            definition_event_ids.add(entry.main_damage_event.semantic_id)
            for derived in entry.derived_damage_events:
                self._assert_template_ref(
                    derived.template,
                    template_map,
                    entry.move_id,
                    expect_move_id=False,
                )
                definition_event_ids.add(derived.template.semantic_id)
                source_rule_id = derived.template.source_rule_item_id
                if source_rule_id is None:
                    raise ValueError("derived template requires a source rule item")
                rule = rule_map.get(source_rule_id)
                if rule is None:
                    raise ValueError(
                        "derived template references an unknown source rule item"
                    )
                if not self._rule_creates_template(rule, derived.template.template_id):
                    raise ValueError(
                        "source rule item does not create its derived template"
                    )
        template_semantic_ids = {
            item.ref.semantic_id for item in self.damage_event_templates
        }
        if definition_event_ids != template_semantic_ids:
            raise ValueError(
                "all typed event templates must be referenced by a move entry"
            )

    @staticmethod
    def _assert_unique(values, label: str) -> None:
        values = tuple(values)
        if len(set(values)) != len(values):
            raise ValueError(f"{label} values must be unique")

    @staticmethod
    def _assert_condition_references(
        references: tuple[ScenarioConditionId, ...],
        known_ids: set[ScenarioConditionId],
    ) -> None:
        unknown = set(references) - known_ids
        if unknown:
            raise ValueError(
                "move or multiplier variant references unknown scenario conditions: "
                f"{sorted(map(str, unknown))}"
            )

    @staticmethod
    def _assert_template_ref(
        ref: DamageEventTemplateRef,
        templates: dict[EventTemplateId, DirectDamageEventTemplate],
        move_id: MoveId,
        *,
        expect_move_id: bool,
    ) -> None:
        typed = templates.get(ref.template_id)
        if typed is None:
            raise ValueError(f"missing typed event template: {ref.template_id}")
        if typed.ref != ref:
            raise ValueError("typed template ref does not match MoveEntry ref")
        if expect_move_id and typed.move_id != move_id:
            raise ValueError("main template move_id must match MoveEntry move_id")
        if not expect_move_id and typed.move_id is not None:
            raise ValueError("derived template move_id must be None")

    @staticmethod
    def _rule_creates_template(
        rule: CalculationRuleItem,
        template_id: EventTemplateId,
    ) -> bool:
        return any(
            isinstance(effect, EventCreationEffect)
            and effect.result.event_template_id == template_id
            for effect in rule.effects
        )

    def validate_scenario(self, scenario: CalculationScenario) -> None:
        condition_map = {
            item.condition_id: item for item in scenario.conditions
        }
        for condition in self.scenario_conditions:
            actual = condition_map.get(condition.condition_id)
            if actual is None:
                raise ValueError(
                    f"scenario is missing condition: {condition.condition_id}"
                )
            if actual.resolution is not condition.resolution:
                raise ValueError(
                    "scenario condition resolution does not match definition"
                )
            if condition.resolution is ConditionResolution.STATIC and (
                actual.value != condition.value
            ):
                raise ValueError(
                    "scenario cannot override a static compilation condition"
                )
        parameter_map = {
            item.parameter_id: item for item in scenario.parameters
        }
        for parameter in self.scenario_parameters:
            actual_parameter = parameter_map.get(parameter.parameter_id)
            if actual_parameter is None:
                raise ValueError(
                    f"scenario is missing parameter: {parameter.parameter_id}"
                )
            if parameter.resolution is ParameterResolution.STATIC and (
                actual_parameter.resolution is not parameter.resolution
                or actual_parameter.value != parameter.value
            ):
                raise ValueError(
                    "scenario cannot override a static compilation parameter"
                )

        variants = {
            variant.variant_id
            for entry in self.move_entries
            for variant in entry.multiplier_variants
        }
        unknown_variants = set(scenario.selected_multiplier_variant_ids) - variants
        if unknown_variants:
            raise ValueError(
                "scenario selects unknown multiplier variants: "
                f"{sorted(map(str, unknown_variants))}"
            )
        for entry in self.move_entries:
            if (
                entry.multiplier_relation
                is not MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT
            ):
                continue
            selected = {
                variant.variant_id
                for variant in entry.multiplier_variants
                if variant.variant_id in scenario.selected_multiplier_variant_ids
            }
            if len(selected) > 1:
                raise ValueError(
                    "scenario cannot select multiple mutually exclusive variants"
                )
