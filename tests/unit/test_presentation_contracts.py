from __future__ import annotations

from dataclasses import FrozenInstanceError

from core.application import CritDisplayMode
from core.application.characters.astra import (
    AstraCompileConfig,
    compile_astra,
    load_raw_record as load_astra_raw_record,
)
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.execution.contracts import (
    DamageEventExecutionTrace,
    MoveCalculationExecution,
)
from core.application.execution.modifiers import (
    MatchedEffectApplication,
    apply_matched_modifiers,
)
from core.application.ids import DamageEventSemanticId, MoveEntryId
from core.application.output import (
    DamageEventCalculationOutput,
    EventCalculationStatus,
    MoveCalculationOutput,
)
from core.calculation import CalculationNode, CalculationResult
from core.calculation.nodes import CalculationNodeValue
from core.data.loader import load_character_record, supported_character_ids
from core.presentation import (
    build_character_editor_view,
    build_move_calculation_view,
    compile_registered_definition,
    config_fields_for,
)
from core.presentation.serialization import to_jsonable
from core.types import (
    CharacterId,
    DamageType,
    Element,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    ModifierEffect,
    ModifierResult,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    Resolved,
)


def _execution(mode: CritDisplayMode, value: float) -> MoveCalculationExecution:
    semantic_id = DamageEventSemanticId("event:test:main")
    result = CalculationResult(
        value=value,
        breakdown=(
            CalculationNodeValue(
                node=CalculationNode.DAMAGE_NORMAL_BONUS,
                value=Resolved(1.0),
                read_rule=SnapshotRule.SETTLEMENT,
            ),
        ),
    )
    event = DamageEventCalculationOutput(
        semantic_id=semantic_id,
        label="测试伤害",
        damage_type=DamageType.DIRECT,
        damage_subtype=None,
        status=EventCalculationStatus.CALCULATED,
        result=result,
        repeat_count=2,
    )
    output = MoveCalculationOutput(
        move_entry_id=MoveEntryId("move-entry:test"),
        crit_display_mode=mode,
        events=(event,),
        known_total=value * 2,
        complete=True,
    )
    return MoveCalculationExecution(
        output=output,
        resolved_character_snapshots=(),
        event_traces=(
            DamageEventExecutionTrace(
                semantic_id=semantic_id,
                rule_matches=(),
            ),
        ),
    )


def test_production_character_records_are_the_single_raw_data_source() -> None:
    assert supported_character_ids() == ("character:1311", "character:1431")
    assert load_character_record("character:1311")["name"] == "耀嘉音"
    assert load_character_record("character:1431")["name"] == "叶瞬光"


def test_character_editor_exposes_static_conditions_and_trigger_inputs() -> None:
    astra = compile_astra(
        AstraCompileConfig(additional_ability_eligible=True),
        load_astra_raw_record(load_character_record("character:1311")),
    )
    view = build_character_editor_view(
        astra,
        team_character_ids=(CharacterId("character:1311"), CharacterId("character:1431")),
    )
    assert view.schema_version == "presentation-v1"
    assert {item.resolution for item in view.scenario_conditions} == {"user-selected"}
    assert view.scenario_trigger_inputs
    assert all(
        item.input_id.startswith("scenario-trigger:")
        for item in view.scenario_trigger_inputs
    )
    assert all(
        "effect:" not in option
        for item in view.scenario_trigger_inputs
        for option in item.actor_options
    )
    with __import__("pytest").raises(FrozenInstanceError):
        view.character_id = "character:other"  # type: ignore[misc]


def test_registry_derives_astra_eligibility_from_team_and_exposes_config_schema() -> None:
    from core.application.rules import RuleEligibility

    values = {"core_level": 1, "cinema_level": 0}
    solo = compile_registered_definition(
        "character:1311",
        values,
        ("character:1311",),
    )
    with_attack = compile_registered_definition(
        "character:1311",
        values,
        ("character:1311", "character:1431"),
    )
    solo_extra = next(item for item in solo.rule_items if str(item.rule_id).endswith("extra-ability"))
    team_extra = next(item for item in with_attack.rule_items if str(item.rule_id).endswith("extra-ability"))
    assert solo_extra.eligibility is RuleEligibility.INELIGIBLE
    assert team_extra.eligibility is RuleEligibility.ELIGIBLE
    fields = config_fields_for("character:1311", values, ("character:1311",))
    assert {"core_level", "cinema_level"}.issubset(
        {item.field_id for item in fields}
    )
    with __import__("pytest").raises(ValueError, match="unknown compile config fields"):
        compile_registered_definition(
            "character:1311",
            {**values, "additional_ability_eligible": True},
            ("character:1311",),
        )


def test_move_calculation_view_keeps_each_crit_mode_and_repeat_trace() -> None:
    view = build_move_calculation_view(
        {
            CritDisplayMode.NON_CRIT: _execution(CritDisplayMode.NON_CRIT, 100.0),
            CritDisplayMode.EXPECTED: _execution(CritDisplayMode.EXPECTED, 150.0),
            CritDisplayMode.FULL_CRIT: _execution(CritDisplayMode.FULL_CRIT, 200.0),
        }
    )
    event = view.events[0]
    assert event.repeat_count == 2
    assert event.modes["non-crit"].value == 100.0
    assert event.modes["non-crit"].known_value == 200.0
    assert event.modes["expected"].known_value == 300.0
    assert event.modes["full-crit"].known_value == 400.0
    assert event.modes["expected"].calculation_breakdown[0].node == "damage.normal-bonus"
    payload = to_jsonable(view)
    assert payload["schema_version"] == "presentation-v1"
    assert payload["events"][0]["modes"]["expected"]["known_value"] == 300.0
    assert "CalculationResult" not in repr(payload)


def test_definition_views_do_not_use_legacy_fixture_paths() -> None:
    ye = compile_ye_shunguang(
        YeShunguangCompileConfig(
            mingxin_active=True,
            entry_move_uses_linren=True,
        ),
        load_ye_raw_record(load_character_record("character:1431")),
    )
    view = build_character_editor_view(ye)
    assert view.character_id == "character:1431"
    assert all("fixtures" not in item.original_text for item in view.scenario_conditions)


def test_panel_application_emits_recipient_provenance() -> None:
    owner = CharacterId("character:panel-owner")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:presentation:panel"),
            source=RuleSource(
                source_id=RuleSourceId("source:presentation:panel"),
                source_type=EffectSourceType.CORE_PASSIVE,
                label="测试面板效果",
            ),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(120.0),
        ),
    )
    from core.types import CharacterSnapshot, CharacterStats

    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )
    result = apply_matched_modifiers(
        (CharacterSnapshot(owner, 60, stats),),
        (),
        (MatchedEffectApplication(effect, rule_item_id="rule:presentation:panel"),),
        owner,
    )
    assert len(result.panel_traces) == 1
    assert result.panel_traces[0].recipient_character_id == owner
    assert result.panel_traces[0].resolved_value == 120.0
