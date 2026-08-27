from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    DamageEventSemanticId,
    EnemyMatchProfile,
    RuleItemId,
    ScenarioRuleStack,
    ScenarioTriggerFact,
)
from core.application.characters.astra import (
    ARIA_ACTIVE_CONDITION_ID,
    ASTRA_ID,
    CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID,
    ASTRA_REVIEWED_MAPPING,
    ENERGY_AVAILABLE_CONDITION_ID,
    RHAPSODY_STAGE3_FULL_CONDITION_ID,
    RHAPSODY_STAGE3_MIN_CONDITION_ID,
    RHAPSODY_MOVE_ID,
    WIND_CHIME_COUNT_PARAMETER_ID,
    AstraCompileConfig,
    compile_astra,
    load_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.execution import (
    MoveCalculationRequest,
    calculate_move,
    instantiate_direct_damage_event,
)
from core.application.matching import (
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
)
from core.application.output import EventCalculationStatus
from core.calculation import CalculationNode
from core.types import (
    BattleEventKind,
    BattleStateId,
    CalculationContext,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    DamageType,
    EffectId,
    Element,
    EnemyId,
    EnemySnapshot,
    InitialCharacterSnapshot,
    ModifierEffect,
    Resolved,
    SkillGroup,
)


ASTRA_FIXTURE = Path(__file__).parents[1] / "fixtures" / "characters" / "astra.json"
YE_FIXTURE = Path(__file__).parents[1] / "fixtures" / "characters" / "ye_shunguang.json"


def _raw():
    return load_raw_record(json.loads(ASTRA_FIXTURE.read_text(encoding="utf-8")))


def _definition(
    *,
    cinema_level: int = 0,
    core_level: int = 1,
    additional_ability_eligible: bool = False,
):
    return compile_astra(
        AstraCompileConfig(
            cinema_level=cinema_level,
            core_level=core_level,
            additional_ability_eligible=additional_ability_eligible,
        ),
        _raw(),
    )


def _entry(definition, suffix: str):
    return next(
        item for item in definition.move_entries if str(item.entry_id).endswith(suffix)
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
        element_damage_bonus={Element.ETHER: Resolved(0.0)},
    )


def _scenario(
    definition,
    *,
    enabled: tuple[str, ...] = (),
    aria: bool | None = True,
    energy: bool | None = True,
    core_attack_buff_active: bool | None = True,
    rhapsody_full: bool | None = False,
    wind_count: int | None = 1,
    current_operator: CharacterId | None = None,
    trigger_facts: tuple[ScenarioTriggerFact, ...] = (),
    stacks: tuple[ScenarioRuleStack, ...] = (),
) -> CalculationScenario:
    values = {
        ARIA_ACTIVE_CONDITION_ID: aria,
        CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID: core_attack_buff_active,
        ENERGY_AVAILABLE_CONDITION_ID: energy,
        RHAPSODY_STAGE3_MIN_CONDITION_ID: (
            not rhapsody_full if rhapsody_full is not None else None
        ),
        RHAPSODY_STAGE3_FULL_CONDITION_ID: rhapsody_full,
    }
    conditions = tuple(
        replace(item, value=values[item.condition_id])
        for item in definition.scenario_conditions
    )
    parameters = tuple(
        (
            replace(item, value=wind_count)
            if item.parameter_id == WIND_CHIME_COUNT_PARAMETER_ID
            else item
        )
        for item in definition.scenario_parameters
    )
    return CalculationScenario(
        scenario_id="scenario:astra-test",
        current_operator=current_operator or ASTRA_ID,
        conditions=conditions,
        parameters=parameters,
        trigger_facts=trigger_facts,
        enabled_rule_item_ids=frozenset(RuleItemId(item) for item in enabled),
        rule_stack_counts=stacks,
    )


def _request(
    definition,
    suffix: str,
    *,
    enabled: tuple[str, ...] = (),
    scenario: CalculationScenario | None = None,
    snapshots: tuple[CharacterSnapshot, ...] | None = None,
    initial_snapshots=(),
    team_profiles: tuple[CharacterMatchProfile, ...] | None = None,
    supporting_definitions=(),
    target: EnemyId = EnemyId("enemy:astra-test"),
) -> MoveCalculationRequest:
    entry = _entry(definition, suffix)
    if scenario is None:
        scenario = _scenario(definition, enabled=enabled)
    return MoveCalculationRequest(
        definition=definition,
        supporting_definitions=tuple(supporting_definitions),
        move_entry_id=entry.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:astra-test"),
        battle_time=0.0,
        base_character_snapshots=snapshots
        or (CharacterSnapshot(definition.character_id, 60, _stats()),),
        initial_character_snapshots=tuple(initial_snapshots),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.ETHER: Resolved(0.2)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=team_profiles
        or (CharacterMatchProfile(definition.character_id, definition.role),),
        target_profile=EnemyMatchProfile(target),
    )


def test_raw_record_and_reviewed_mapping_are_separate() -> None:
    raw = _raw()
    assert raw.character_id == ASTRA_ID
    assert len(raw.moves) == 12
    assert len(raw.core_levels) == 7
    assert tuple(item.level for item in raw.mindscapes) == (1, 2, 4, 6)
    wind = next(item for item in raw.moves if item.name == "特殊技：《风铃与旧约》")
    assert wind.parameters[0].value_for_level(12) == pytest.approx(110.0)
    assert wind.description
    assert not hasattr(ASTRA_REVIEWED_MAPPING, "core_levels")
    assert not hasattr(ASTRA_REVIEWED_MAPPING.moves[0].parameters[0], "values")


def test_raw_multipliers_drive_derived_templates() -> None:
    raw = _raw()
    chord = next(item for item in raw.moves if item.name == "和弦")
    tremolo = next(item for item in chord.parameters if item.name == "追加震音伤害倍率")
    changed_tremolo = replace(
        tremolo,
        values=((12, 99.0), (14, 100.6), (16, 109.0)),
    )
    changed_chord = replace(
        chord,
        parameters=tuple(
            changed_tremolo if item.name == tremolo.name else item
            for item in chord.parameters
        ),
    )
    changed_raw = replace(
        raw,
        moves=tuple(
            changed_chord if item.name == chord.name else item for item in raw.moves
        ),
    )
    definition = compile_astra(AstraCompileConfig(), changed_raw)
    changed_ref = next(
        item
        for item in definition.independent_derived_damage_events
        if item.template.semantic_id
        == DamageEventSemanticId("event:astra:1311:finale-tremolo")
    )
    assert changed_ref.multiplier.value.value == pytest.approx(0.99)  # type: ignore[union-attr]


def test_skill_level_selection_reads_the_matching_raw_level() -> None:
    levels = tuple(CharacterSkillLevel(group, 14) for group in SkillGroup)
    definition = compile_astra(
        AstraCompileConfig(skill_levels=levels),
        _raw(),
    )
    rhapsody = _entry(definition, "basic-rhapsody-1")
    wind = _entry(definition, "special-wind-chime")
    chord_tremolo = next(
        item
        for item in definition.independent_derived_damage_events
        if item.template.semantic_id
        == DamageEventSemanticId("event:astra:1311:finale-tremolo")
    )
    assert rhapsody.multiplier_variants[0].multiplier.value.value == pytest.approx(0.958)  # type: ignore[union-attr]
    assert wind.multiplier_variants[0].multiplier.value.value == pytest.approx(1.2)  # type: ignore[union-attr]
    assert chord_tremolo.multiplier.value.value == pytest.approx(1.006)  # type: ignore[union-attr]


def test_astra_compiles_all_direct_moves_and_explicit_taxonomy() -> None:
    definition = _definition()
    assert definition.character_id == ASTRA_ID
    assert definition.role is CharacterRole.SUPPORT
    assert definition.base_element is Element.ETHER
    assert len(definition.move_entries) == 17
    assert all(
        item.main_damage_event.damage_type is DamageType.DIRECT
        for item in definition.move_entries
    )
    interlude = _entry(definition, "basic-interlude-1")
    assert interlude.damage_tags == frozenset(
        {DamageTag.BASIC_ATTACK, DamageTag.TREMOLO}
    )
    dash = _entry(definition, "dodge-dash")
    counter = _entry(definition, "dodge-counter")
    assert dash.skill_group is SkillGroup.DODGE
    assert dash.damage_tags == frozenset({DamageTag.DASH_ATTACK})
    assert counter.skill_group is SkillGroup.DODGE
    assert counter.damage_tags == frozenset({DamageTag.DODGE_COUNTER})


def test_wind_chime_is_unit_repeat_with_user_selected_count() -> None:
    definition = _definition()
    wind = _entry(definition, "special-wind-chime")
    assert wind.multiplier_relation.value == "unit-repeat"
    assert wind.multiplier_variants[0].multiplier.value.value == pytest.approx(1.10)  # type: ignore[union-attr]
    assert (
        wind.multiplier_variants[0].repeat_count_parameter_id
        == WIND_CHIME_COUNT_PARAMETER_ID
    )
    scenario = _scenario(definition, wind_count=5)
    execution = calculate_move(
        _request(definition, "special-wind-chime", scenario=scenario)
    )
    assert execution.output.events[0].repeat_count == 5
    multiplier = next(
        item.value.value
        for item in execution.output.events[0].result.breakdown  # type: ignore[union-attr]
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    assert multiplier == pytest.approx(1.10)


def test_rhapsody_stage_three_variants_are_conditioned() -> None:
    definition = _definition()
    entry = _entry(definition, "basic-rhapsody-3")
    assert len(entry.multiplier_variants) == 2
    assert entry.multiplier_relation.value == "mutually-exclusive-variant"
    minimum = calculate_move(
        _request(
            definition,
            "basic-rhapsody-3",
            scenario=_scenario(definition, rhapsody_full=False),
        )
    )
    full = calculate_move(
        _request(
            definition,
            "basic-rhapsody-3",
            scenario=_scenario(definition, rhapsody_full=True),
        )
    )
    assert minimum.output.events[0].result.value != full.output.events[0].result.value  # type: ignore[union-attr]
    with pytest.raises(ValueError, match="multiple mutually exclusive variants"):
        definition.validate_scenario(
            _scenario(definition, rhapsody_full=True).__class__(
                scenario_id="scenario:bad",
                current_operator=ASTRA_ID,
                conditions=tuple(
                    (
                        replace(item, value=True)
                        if item.condition_id
                        in {
                            RHAPSODY_STAGE3_MIN_CONDITION_ID,
                            RHAPSODY_STAGE3_FULL_CONDITION_ID,
                        }
                        else item
                    )
                    for item in _scenario(definition, rhapsody_full=True).conditions
                ),
                parameters=_scenario(definition, rhapsody_full=True).parameters,
            )
        )


def test_core_and_cinema_values_are_compiled_without_fixed_build_attack() -> None:
    base = _definition(core_level=1)
    c2 = _definition(core_level=1, cinema_level=2)
    base_core = next(
        item
        for item in base.rule_items
        if item.rule_id == RuleItemId("rule:astra:1311:core-passive-self")
    )
    c2_core = next(
        item
        for item in c2.rule_items
        if item.rule_id == RuleItemId("rule:astra:1311:core-passive-self")
    )
    base_effect = base_core.effects[0]
    c2_effect = c2_core.effects[0]
    assert isinstance(base_effect, ModifierEffect)
    assert isinstance(c2_effect, ModifierEffect)
    assert base_effect.result.value.coefficient.value == pytest.approx(0.22)  # type: ignore[union-attr]
    assert base_effect.result.value.cap_max.value == pytest.approx(1200.0)  # type: ignore[union-attr]
    assert c2_effect.result.value.coefficient.value == pytest.approx(0.41)  # type: ignore[union-attr]
    assert c2_effect.result.value.cap_max.value == pytest.approx(1600.0)  # type: ignore[union-attr]
    assert not hasattr(base_effect.result.value, "resolved_value")


def test_core_attack_buff_requires_its_explicit_active_condition() -> None:
    definition = _definition()
    rule_id = RuleItemId("rule:astra:1311:core-passive-self")
    execution = calculate_move(
        _request(
            definition,
            "basic-rhapsody-1",
            scenario=_scenario(
                definition,
                enabled=(str(rule_id),),
                core_attack_buff_active=False,
            ),
        )
    )

    snapshot = execution.resolved_character_snapshots[0]
    assert snapshot.settlement_stats.attack == Resolved(1000.0)
    assert execution.output.complete is True


def test_unlocked_cinema_items_remain_ineligible_and_registry_is_closed() -> None:
    definition = _definition(cinema_level=0)
    rules = {item.rule_id: item for item in definition.rule_items}
    assert (
        rules[RuleItemId("rule:astra:1311:cinema1")].eligibility.value == "ineligible"
    )
    assert (
        rules[RuleItemId("rule:astra:1311:cinema2")].eligibility.value == "ineligible"
    )
    assert (
        rules[RuleItemId("rule:astra:1311:cinema4")].eligibility.value == "ineligible"
    )
    assert (
        rules[RuleItemId("rule:astra:1311:cinema6")].eligibility.value == "ineligible"
    )
    assert len(definition.independent_derived_damage_events) == 10
    typed_independent = {
        item.template.semantic_id: next(
            typed
            for typed in definition.damage_event_templates
            if typed.ref == item.template
        )
        for item in definition.independent_derived_damage_events
    }
    assert all(
        typed.move_id is None
        for semantic_id, typed in typed_independent.items()
        if semantic_id != DamageEventSemanticId("event:astra:1311:cinema6-rhapsody")
    )
    assert (
        typed_independent[
            DamageEventSemanticId("event:astra:1311:cinema6-rhapsody")
        ].move_id
        == RHAPSODY_MOVE_ID
    )
    assert all(
        item.template.source_rule_item_id in rules
        for item in definition.independent_derived_damage_events
    )


def test_finale_extra_set_is_doubled_by_additional_ability_rule() -> None:
    definition = _definition(additional_ability_eligible=True)
    enabled = ("rule:astra:1311:finale-derived",)
    base = calculate_move(
        _request(
            definition,
            "basic-finale",
            enabled=enabled,
            scenario=_scenario(definition, enabled=enabled),
        )
    )
    with_extra = calculate_move(
        _request(
            definition,
            "basic-finale",
            enabled=enabled + ("rule:astra:1311:extra-ability",),
            scenario=_scenario(
                definition,
                enabled=enabled + ("rule:astra:1311:extra-ability",),
            ),
        )
    )
    assert len(base.output.events) == 3
    assert len(with_extra.output.events) == 5
    assert sorted(item.repeat_count for item in base.output.events) == [1, 1, 3]
    assert sorted(item.repeat_count for item in with_extra.output.events) == [
        1,
        1,
        1,
        3,
        3,
    ]


def test_cinema_one_resistance_reduction_uses_selected_stack_count() -> None:
    definition = _definition(cinema_level=1)
    rule_id = RuleItemId("rule:astra:1311:cinema1")
    execution = calculate_move(
        _request(
            definition,
            "basic-rhapsody-1",
            scenario=_scenario(
                definition,
                enabled=(str(rule_id),),
                stacks=(ScenarioRuleStack(rule_id, 2),),
            ),
        )
    )
    modifier = next(
        item
        for item in execution.event_traces[0].applied_modifiers
        if item.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
    )
    assert modifier.value == Resolved(0.12)


def test_cinema_four_creates_astra_identity_extra_for_attack_assist() -> None:
    astra = _definition(cinema_level=4)
    ye_raw = load_ye_raw_record(json.loads(YE_FIXTURE.read_text(encoding="utf-8")))
    ye = compile_ye_shunguang(
        YeShunguangCompileConfig(
            mingxin_active=True,
            entry_move_uses_linren=True,
            enemy_stun_vulnerability_bonus=1.5,
        ),
        ye_raw,
    )
    c4_id = RuleItemId("rule:astra:1311:cinema4")
    scenario = CalculationScenario(
        scenario_id="scenario:astra-c4",
        current_operator=ye.character_id,
        conditions=tuple(ye.scenario_conditions)
        + tuple(
            replace(
                condition,
                value=(
                    condition.condition_id == ARIA_ACTIVE_CONDITION_ID
                    or condition.condition_id == RHAPSODY_STAGE3_MIN_CONDITION_ID
                ),
            )
            for condition in astra.scenario_conditions
        ),
        parameters=tuple(ye.scenario_parameters) + tuple(astra.scenario_parameters),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:cinema4-attack-extra"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ye.character_id,
            ),
        ),
        enabled_rule_item_ids=frozenset({c4_id}),
    )
    request = MoveCalculationRequest(
        definition=ye,
        supporting_definitions=(astra,),
        move_entry_id=next(
            item
            for item in ye.move_entries
            if str(item.entry_id).endswith("assist-yuanshou")
        ).entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:astra-c4"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(ye.character_id, 60, _stats()),
            CharacterSnapshot(astra.character_id, 60, _stats(800.0)),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=EnemyId("enemy:astra-c4"),
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={
                Element.PHYSICAL: Resolved(0.0),
                Element.ETHER: Resolved(0.0),
            },
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(ye.character_id, CharacterRole.ATTACK),
            CharacterMatchProfile(astra.character_id, CharacterRole.SUPPORT),
        ),
        target_profile=EnemyMatchProfile(EnemyId("enemy:astra-c4")),
    )
    execution = calculate_move(request)
    assert len(execution.output.events) == 2
    extra_ref = next(
        item
        for item in astra.independent_derived_damage_events
        if item.template.semantic_id
        == DamageEventSemanticId("event:astra:1311:cinema4-attack-extra")
    )
    extra_template = next(
        item for item in astra.damage_event_templates if item.ref == extra_ref.template
    )
    assert extra_template.damage_dealer == ASTRA_ID
    assert extra_template.base_source.character_id == ASTRA_ID
    assert extra_template.crit_rule.stat_owner == ASTRA_ID
    assert extra_template.element is Element.ETHER
    assert extra_template.move_id is None
    assert extra_template.ref.skill_group is None
    assert extra_template.ref.damage_tags == frozenset()


def test_cinema_two_creates_one_tremolo_and_three_clusters_on_support_entry() -> None:
    definition = _definition(cinema_level=2)
    enabled = ("rule:astra:1311:cinema2",)
    scenario = _scenario(
        definition,
        enabled=enabled,
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:cinema2-entry-tremolo"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ASTRA_ID,
            ),
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:cinema2-entry-cluster"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ASTRA_ID,
            ),
        ),
    )
    execution = calculate_move(
        _request(
            definition,
            "assist-quick-fireworks",
            enabled=enabled,
            scenario=scenario,
        )
    )
    assert len(execution.output.events) == 3
    assert sorted(item.repeat_count for item in execution.output.events) == [1, 1, 3]


def test_cinema_two_does_not_require_the_energy_condition() -> None:
    definition = _definition(cinema_level=2)
    enabled = ("rule:astra:1311:cinema2",)
    scenario = _scenario(
        definition,
        enabled=enabled,
        energy=False,
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:cinema2-entry-tremolo"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ASTRA_ID,
            ),
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:cinema2-entry-cluster"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ASTRA_ID,
            ),
        ),
    )
    execution = calculate_move(
        _request(
            definition,
            "assist-quick-fireworks",
            enabled=enabled,
            scenario=scenario,
        )
    )

    assert len(execution.output.events) == 3


def test_cinema_six_precise_support_creates_crit_boosted_rhapsody_event() -> None:
    definition = _definition(cinema_level=6)
    enabled = ("rule:astra:1311:cinema6",)
    effect_id = EffectId("effect:astra:1311:cinema6:rhapsody")
    scenario = _scenario(
        definition,
        enabled=enabled,
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=effect_id,
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ASTRA_ID,
            ),
        ),
    )
    execution = calculate_move(
        _request(
            definition,
            "assist-quick-fireworks",
            enabled=enabled,
            scenario=scenario,
        )
    )
    assert len(execution.output.events) == 2
    child_trace = execution.event_traces[1]
    assert len(child_trace.event_stat_modifiers) == 1
    assert child_trace.event_stat_modifiers[0].recipient == ASTRA_ID


def test_cinema_six_requires_astra_as_damage_dealer_for_tremolo_lanes() -> None:
    definition = _definition(cinema_level=6)
    entry = _entry(definition, "basic-interlude-1")
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.main_damage_event
    )
    other = CharacterId("character:other-tremolo-dealer")
    original = instantiate_direct_damage_event(
        template,
        entry.multiplier_variants[0].multiplier,
        battle_state_id=BattleStateId("battle:astra-other-tremolo"),
        target_enemy=EnemyId("enemy:astra-other-tremolo"),
        created_at=0.0,
    ).event
    event = replace(
        original,
        metadata=replace(
            original.metadata,
            damage_dealer=other,
            damage_tags=frozenset({DamageTag.TREMOLO}),
        ),
    )
    scenario = _scenario(
        definition,
        enabled=("rule:astra:1311:cinema6",),
        current_operator=other,
    )
    target = event.metadata.target_enemy
    context = EffectMatchContext(
        current_event=event,
        calculation_context=CalculationContext(
            event=event,
            battle_state_id=event.metadata.battle_state_id,
            character_snapshots=(
                CharacterSnapshot(ASTRA_ID, 60, _stats()),
                CharacterSnapshot(other, 60, _stats()),
            ),
            target_snapshot=EnemySnapshot(
                enemy_id=target,
                level=70,
                initial_defense=Resolved(794.0),
                damage_resistance={Element.ETHER: Resolved(0.0)},
                anomaly_buildup_resistance={},
                daze_resistance=Resolved(0.0),
                damage_reduction=Resolved(0.0),
            ),
        ),
        scenario=scenario,
        team=(
            CharacterMatchProfile(ASTRA_ID, CharacterRole.SUPPORT),
            CharacterMatchProfile(other, CharacterRole.SUPPORT),
        ),
        target=EnemyMatchProfile(target),
    )
    c6_rule = next(
        item
        for item in definition.rule_items
        if item.rule_id == RuleItemId("rule:astra:1311:cinema6")
    )

    result = EffectMatcher().match_rule_item(c6_rule, context)
    assert result.status is EffectMatchStatus.NOT_MATCHED
    assert result.matched_effects == ()


def test_cinema_six_event_lanes_and_precise_support_identity() -> None:
    definition = _definition(cinema_level=6)
    enabled = ("rule:astra:1311:cinema6",)
    scenario = _scenario(definition, enabled=enabled)
    execution = calculate_move(
        _request(definition, "basic-interlude-1", enabled=enabled, scenario=scenario)
    )
    event = execution.output.events[0]
    trace = execution.event_traces[0]
    assert event.status is EventCalculationStatus.CALCULATED
    assert len(trace.event_stat_modifiers) == 1
    assert len(trace.event_multiplier_modifiers) == 1
    multiplier = next(
        item.value.value
        for item in event.result.breakdown  # type: ignore[union-attr]
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    assert multiplier == pytest.approx(2.20)


def test_astra_supporting_definition_changes_ye_settlement() -> None:
    astra = _definition(cinema_level=6, additional_ability_eligible=True)
    ye_raw = load_ye_raw_record(json.loads(YE_FIXTURE.read_text(encoding="utf-8")))
    ye = compile_ye_shunguang(
        YeShunguangCompileConfig(
            mingxin_active=True,
            entry_move_uses_linren=True,
            enemy_stun_vulnerability_bonus=1.5,
        ),
        ye_raw,
    )
    scenario = CalculationScenario(
        scenario_id="scenario:astra-supporting",
        current_operator=ye.character_id,
        conditions=tuple(ye.scenario_conditions)
        + tuple(
            replace(
                condition,
                value=(
                    condition.condition_id
                    in {
                        ARIA_ACTIVE_CONDITION_ID,
                        CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID,
                        ENERGY_AVAILABLE_CONDITION_ID,
                        RHAPSODY_STAGE3_MIN_CONDITION_ID,
                    }
                ),
            )
            for condition in astra.scenario_conditions
        ),
        parameters=tuple(ye.scenario_parameters) + tuple(astra.scenario_parameters),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:astra:1311:core-entry-attack"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=ye.character_id,
            ),
        ),
        enabled_rule_item_ids=frozenset(
            {
                RuleItemId("rule:astra:1311:core-passive-self"),
                RuleItemId("rule:astra:1311:core-passive-entry"),
            }
        ),
    )
    target = EnemyId("enemy:astra-supporting")
    request = MoveCalculationRequest(
        definition=ye,
        supporting_definitions=(astra,),
        move_entry_id=next(
            item
            for item in ye.move_entries
            if str(item.entry_id).endswith("basic-fast-1")
        ).entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:astra-supporting"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(ye.character_id, 60, _stats()),
            CharacterSnapshot(astra.character_id, 60, _stats(800.0)),
        ),
        initial_character_snapshots=(
            InitialCharacterSnapshot(astra.character_id, 60, _stats(6000.0)),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(ye.character_id, CharacterRole.ATTACK),
            CharacterMatchProfile(astra.character_id, CharacterRole.SUPPORT),
        ),
        target_profile=EnemyMatchProfile(target),
    )
    execution = calculate_move(request)
    snapshots = {
        item.character_id: item for item in execution.resolved_character_snapshots
    }
    assert snapshots[astra.character_id].settlement_stats.attack == Resolved(2400.0)
    assert snapshots[ye.character_id].settlement_stats.attack == Resolved(2600.0)
