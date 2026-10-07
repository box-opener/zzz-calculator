from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.application import CritDisplayMode
from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.ids import DiagnosticId
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
from core.presentation.calculation import panel_snapshot_view
from core.presentation.diagnostics import diagnostic_view
from core.presentation.serialization import to_jsonable
from core.types import (
    CharacterId,
    InitialCharacterSnapshot,
    CharacterSnapshot,
    CharacterStats,
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


def test_only_named_nonblocking_static_notes_are_details_only() -> None:
    def view(diagnostic_id: str, *, blocking: bool = False):
        return diagnostic_view(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(diagnostic_id),
                kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                message="static analysis note",
                blocking=blocking,
                original_text="source text",
            )
        )

    expected_notes = (
        "unsupported:character:1331:core:prophecy-timing",
        "unsupported:character:1331:core:feather-resource-sequence",
        "wengine:wengine:14133:result-scope",
    )
    assert all(view(item).details_only for item in expected_notes)
    assert not view("unsupported:some-other:real-unimplemented-lane").details_only
    assert not view(expected_notes[0], blocking=True).details_only


def test_production_character_records_are_the_single_raw_data_source() -> None:
    assert supported_character_ids() == (
        "character:1011",
        "character:1021",
        "character:1031",
        "character:1041",
        "character:1051",
        "character:1581",
        "character:1561",
        "character:1311",
        "character:1431",
        "character:1401",
        "character:1411",
        "character:1361",
        "character:1091",
        "character:1371",
        "character:1451",
        "character:1481",
        "character:1221",
        "character:1331",
        "character:1341",
        "character:1251",
        "character:1061",
    )
    assert load_character_record("character:1011")["name"] == "安比"
    assert load_character_record("character:1011")["source_version"] == "3.2"
    assert load_character_record("character:1021")["name"] == "猫又"
    assert load_character_record("character:1021")["source_version"] == "3.2"
    assert load_character_record("character:1021")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1021.json"
    assert load_character_record("character:1031")["name"] == "妮可"
    assert load_character_record("character:1031")["source_version"] == "3.2"
    assert load_character_record("character:1031")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1031.json"
    assert load_character_record("character:1041")["name"] == "「11号」"
    assert load_character_record("character:1041")["source_version"] == "3.2"
    assert load_character_record("character:1041")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1041.json"
    assert load_character_record("character:1051")["name"] == "伊德海莉"
    assert load_character_record("character:1051")["source_version"] == "3.2"
    assert load_character_record("character:1051")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1051.json"
    assert load_character_record("character:1311")["name"] == "耀嘉音"
    assert load_character_record("character:1431")["name"] == "叶瞬光"
    assert load_character_record("character:1401")["name"] == "爱丽丝"
    assert load_character_record("character:1411")["name"] == "柚叶"
    assert load_character_record("character:1361")["name"] == "「扳机」"
    assert load_character_record("character:1091")["name"] == "雅"
    assert load_character_record("character:1091")["source_version"] == "3.2"
    assert load_character_record("character:1371")["name"] == "仪玄"
    assert load_character_record("character:1371")["source_version"] == "3.2"
    assert load_character_record("character:1451")["name"] == "卢西娅"
    assert load_character_record("character:1451")["source_version"] == "3.2"
    assert load_character_record("character:1451")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1451.json"
    assert load_character_record("character:1481")["name"] == "琉音"
    assert load_character_record("character:1481")["source_version"] == "3.2"
    assert load_character_record("character:1481")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1481.json"
    assert load_character_record("character:1331")["name"] == "薇薇安"
    assert load_character_record("character:1331")["source_version"] == "3.2"
    assert load_character_record("character:1331")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1331.json"
    assert load_character_record("character:1341")["name"] == "照"
    assert load_character_record("character:1341")["source_version"] == "3.2"
    assert load_character_record("character:1341")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1341.json"
    assert load_character_record("character:1251")["name"] == "青衣"
    assert load_character_record("character:1251")["source_version"] == "3.2"
    assert load_character_record("character:1251")["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1251.json"


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
    assert all(item.rule_item_id for item in view.scenario_trigger_inputs)
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
    assert panel_snapshot_view(result.character_snapshots[0]).stats["element_damage_bonus"] == {
        "physical": 0.0,
    }


def test_team_other_panel_target_excludes_effect_owner() -> None:
    owner = CharacterId("character:team-other-owner")
    teammate = CharacterId("character:team-other-teammate")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:presentation:team-other-panel"),
            source=RuleSource(
                source_id=RuleSourceId("source:presentation:team-other-panel"),
                source_type=EffectSourceType.CINEMA,
                label="其他队员攻击力提升",
            ),
            owner=owner,
            target=EffectTarget.TEAM_OTHER,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.15),
        ),
    )
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
        (CharacterSnapshot(owner, 60, stats), CharacterSnapshot(teammate, 60, stats)),
        (),
        (MatchedEffectApplication(effect, rule_item_id="rule:presentation:team-other-panel"),),
        owner,
        initial_character_snapshots=(
            InitialCharacterSnapshot(owner, 60, stats),
            InitialCharacterSnapshot(teammate, 60, stats),
        ),
    )
    assert [item.recipient_character_id for item in result.panel_traces] == [teammate]
    assert result.panel_traces[0].resolved_value == pytest.approx(150.0)
    snapshots = {item.character_id: item.settlement_stats for item in result.character_snapshots}
    assert snapshots[owner].attack == Resolved(1000.0)
    assert snapshots[teammate].attack == Resolved(1150.0)
