from __future__ import annotations

from dataclasses import replace

from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    EnemyMatchProfile,
    MoveCalculationRequest,
    ScenarioRuleStack,
    compile_wengine,
)
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.equipment.wengine import (
    ASTRA_DAMAGE_BUFF_CONDITION_ID,
    ASTRA_ID,
    WENGINE_ASTRA_ID,
    WENGINE_YE_ID,
    YE_ID,
    YE_VEIL_ACTIVE_CONDITION_ID,
)
from core.application.execution import calculate_move
from core.data.loader import load_character_record
from core.types import (
    BattleStateId,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    Element,
    EnemyId,
    EnemySnapshot,
    InitialCharacterSnapshot,
    Resolved,
    WEngineBuildInput,
)


def _stats(attack: float = 1000.0) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
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


def _ye_definition():
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            mingxin_active=True,
            entry_move_uses_linren=True,
        ),
        load_ye_raw_record(load_character_record("character:1431")),
    )


def _request(
    definition,
    *,
    additional_rule_items=(),
    additional_scenario_conditions=(),
    condition_values=None,
    team_snapshots=None,
):
    entry = next(
        item for item in definition.move_entries
        if str(item.entry_id).endswith("basic-fast-1")
    )
    values = condition_values or {}
    conditions = tuple(
        replace(
            condition,
            value=values.get(str(condition.condition_id), condition.value),
        )
        for condition in definition.scenario_conditions
    ) + tuple(
        replace(
            condition,
            value=values.get(str(condition.condition_id), condition.value),
        )
        for condition in additional_scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="scenario:wengine-execution",
        current_operator=YE_ID,
        conditions=conditions,
        parameters=definition.scenario_parameters,
        enabled_rule_item_ids=frozenset(
            item.rule_id for item in additional_rule_items
        ),
        rule_stack_counts=(),
    )
    target = EnemyId("enemy:wengine-execution")
    snapshots = team_snapshots or (
        CharacterSnapshot(YE_ID, 60, _stats()),
    )
    return MoveCalculationRequest(
        definition=definition,
        move_entry_id=entry.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:wengine-execution"),
        battle_time=0.0,
        base_character_snapshots=snapshots,
        initial_character_snapshots=tuple(
            # Initial snapshot and settlement snapshot start from the same
            # assembled panel in this vertical slice.
            InitialCharacterSnapshot(
                item.character_id,
                item.level,
                item.settlement_stats,
            )
            for item in snapshots
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.2)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=tuple(
            CharacterMatchProfile(
                item.character_id,
                CharacterRole.ATTACK if item.character_id is YE_ID else CharacterRole.SUPPORT,
            )
            for item in snapshots
        ),
        target_profile=EnemyMatchProfile(target),
        additional_rule_items=tuple(additional_rule_items),
        additional_scenario_conditions=tuple(additional_scenario_conditions),
    )


def test_ye_signature_resistance_ignore_matches_physical_and_linren() -> None:
    definition = _ye_definition()
    weapon = compile_wengine(
        WEngineBuildInput(WENGINE_YE_ID, YE_ID),
        equipped_character_role=CharacterRole.ATTACK,
    )
    request = _request(
        definition,
        additional_rule_items=(weapon.rule_items[0],),
        additional_scenario_conditions=weapon.scenario_conditions,
    )

    execution = calculate_move(request)

    assert execution.output.complete is True
    modifiers = execution.event_traces[0].applied_modifiers
    resistance = next(
        item for item in modifiers
        if item.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE
    )
    assert resistance.value == Resolved(0.20)


def test_ye_signature_veil_adds_damage_and_crit_damage_only_when_selected() -> None:
    definition = _ye_definition()
    weapon = compile_wengine(
        WEngineBuildInput(WENGINE_YE_ID, YE_ID),
        equipped_character_role=CharacterRole.ATTACK,
    )
    request = _request(
        definition,
        additional_rule_items=(weapon.rule_items[1],),
        additional_scenario_conditions=weapon.scenario_conditions,
        condition_values={str(YE_VEIL_ACTIVE_CONDITION_ID): True},
    )

    execution = calculate_move(request)

    assert execution.output.complete is True
    trace = execution.event_traces[0]
    assert {
        item.modifier_path for item in trace.applied_modifiers
    } == {CalculationNode.DAMAGE_NORMAL_BONUS}
    assert {
        item.modifier_path for item in trace.event_stat_modifiers
    } == {CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE}
    crit_damage = execution.output.events[0].result.breakdown
    assert any(
        item.node is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
        and item.value == Resolved(0.75)
        for item in crit_damage
    )


def test_astra_signature_team_damage_rule_applies_to_ye_event() -> None:
    definition = _ye_definition()
    weapon = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, ASTRA_ID),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    snapshots = (
        CharacterSnapshot(YE_ID, 60, _stats()),
        CharacterSnapshot(ASTRA_ID, 60, _stats(800.0)),
    )
    request = _request(
        definition,
        additional_rule_items=weapon.rule_items,
        additional_scenario_conditions=weapon.scenario_conditions,
        condition_values={str(ASTRA_DAMAGE_BUFF_CONDITION_ID): True},
        team_snapshots=snapshots,
    )
    request = replace(
        request,
        scenario=replace(
            request.scenario,
            rule_stack_counts=(
                ScenarioRuleStack(weapon.rule_items[0].rule_id, 2),
            ),
        ),
    )

    execution = calculate_move(request)

    assert execution.output.complete is True
    modifier = next(
        item for item in execution.event_traces[0].applied_modifiers
        if item.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    )
    assert modifier.value == Resolved(0.20)
