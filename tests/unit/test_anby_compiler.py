from __future__ import annotations

import pytest

from core.application.characters.anby import (
    ANBY_ID,
    AnbyCompileConfig,
    compile_anby,
    load_raw_record,
)
from core.application.matching import (
    CharacterMatchProfile,
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.application.scenario import CalculationScenario, ScenarioRuleStack
from core.application.equipment import signature_wengine_id_for
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    AllCondition,
    AnyCondition,
    CalculationNode,
    CalculationContext,
    BattleStateId,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CurrentAttackValueSource,
    DynamicIdentity,
    DynamicIdentityCondition,
    DamageEventId,
    DamageEventMetadata,
    DamageTag,
    Element,
    EnemyStateFilter,
    EnemyId,
    EnemySnapshot,
    DirectDamageEvent,
    FixedMultiplier,
    NotFilter,
    Resolved,
    RuleStackCondition,
    SkillGroup,
    StandardCritRule,
)


def test_anby_live_source_and_level_60_build_are_retained() -> None:
    raw_record = load_character_record(str(ANBY_ID))
    raw = load_raw_record(raw_record)

    assert str(ANBY_ID) in supported_character_ids()
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1011.json"
    assert raw.character_id == ANBY_ID
    assert raw.rarity == 3
    assert raw.specialty == "击破"
    assert raw.element == "电属性"

    stats = character_base_stats(ANBY_ID)
    assert stats.hp.value == pytest.approx(7500.7134)
    assert stats.attack.value == pytest.approx(658.957)
    assert stats.defense.value == pytest.approx(612.6038)
    assert stats.impact == Resolved(136.0)
    assert stats.crit_rate == Resolved(0.05)
    assert stats.crit_damage == Resolved(0.5)
    assert stats.anomaly_mastery == Resolved(94.0)
    assert stats.anomaly_proficiency == Resolved(93.0)
    assert stats.energy_regen == Resolved(1.2)


def test_anby_default_config_is_max_core_zero_cinema_sliders_and_all_skills_level_sixteen() -> None:
    fields = {
        item.field_id: item
        for item in config_fields_for(ANBY_ID, {}, [ANBY_ID])
    }
    assert fields["core_level"].value == 7
    assert fields["core_level"].field_type == "slider"
    assert fields["cinema_level"].value == 0
    assert fields["cinema_level"].field_type == "slider"
    assert {
        key: fields[key].value
        for key in fields
        if key.startswith("skill_level:")
    } == {
        "skill_level:basic-attack": 16,
        "skill_level:dodge": 16,
        "skill_level:special-attack": 16,
        "skill_level:chain-attack": 16,
        "skill_level:assist": 16,
        "skill_level:ultimate": 16,
    }

    definition = compile_registered_definition(
        ANBY_ID,
        {},
        [ANBY_ID],
        strict=False,
    )
    entries = {entry.display_name: entry for entry in definition.move_entries}
    expected_multipliers = {
        "普通攻击：伏特速攻（1段）": 0.747,
        "普通攻击：伏特速攻（2段）": 0.802,
        "普通攻击：伏特速攻（3段）": 2.696,
        "普通攻击：伏特速攻（4段）": 5.661,
        "普通攻击：落雷": 7.771,
        "冲刺攻击：电弧斩": 1.347,
        "闪避反击：迅雷": 4.262,
        "特殊技：电光挥击": 2.209,
        "强化特殊技：苍雷斩": 13.78,
        "连携技：电磁引擎": 12.834,
        "终结技：过载引擎": 35.766,
        "快速支援：降雷": 1.472,
        "支援突击：回旋闪电": 7.927,
    }
    for label, multiplier in expected_multipliers.items():
        resolved_multiplier = entries[label].multiplier_variants[0].multiplier
        assert resolved_multiplier.value.value == pytest.approx(multiplier)


def test_anby_reviewed_moves_preserve_elements_and_cinema_rule_scopes() -> None:
    raw = load_raw_record(load_character_record(str(ANBY_ID)))
    definition = compile_anby(
        AnbyCompileConfig(core_level=7, cinema_level=6),
        raw,
    )
    direct = [entry for entry in definition.move_entries if entry.skill_group is not None]
    assert len(direct) == 13
    assert [entry.stage_index for entry in direct[:4]] == [1, 2, 3, 4]
    assert [entry.main_damage_event.element for entry in direct[:4]] == [
        Element.PHYSICAL,
        Element.PHYSICAL,
        Element.PHYSICAL,
        Element.ELECTRIC,
    ]
    falling = next(entry for entry in direct if str(entry.move_id).endswith("falling-thunder"))
    assert falling.main_damage_event.element is Element.ELECTRIC
    assert all(item.blocking is False for item in definition.diagnostics)

    rules = {str(rule.rule_id): rule for rule in definition.rule_items}
    core_daze = rules["rule:character:1011:core:daze-after-basic-third"]
    assert core_daze.effects[0].result.modifier_path is CalculationNode.DAZE_OUTGOING_BONUS
    assert core_daze.effects[0].result.value == Resolved(0.64)
    assert core_daze.condition_ids
    assert core_daze.effects[0].rule.target.value == "team"
    assert core_daze.effects[0].rule.condition == DynamicIdentityCondition(
        DynamicIdentity.DAMAGE_DEALER
    )

    c2_damage = rules["rule:character:1011:cinema2:falling-thunder-damage-vs-stunned"]
    assert c2_damage.effects[0].result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert c2_damage.effects[0].result.value == Resolved(0.30)
    assert c2_damage.effects[0].rule.target.value == "team"
    assert c2_damage.effects[0].rule.condition == DynamicIdentityCondition(
        DynamicIdentity.DAMAGE_DEALER
    )
    assert any(
        isinstance(filter_, EnemyStateFilter)
        for filter_ in c2_damage.effects[0].rule.filters
    )

    c2_ex_daze = rules["rule:character:1011:cinema2:ex-special-daze-vs-not-stunned"]
    assert c2_ex_daze.condition_ids == ()
    assert c2_ex_daze.condition_not_ids == ()
    assert any(isinstance(item, NotFilter) for item in c2_ex_daze.effects[0].rule.filters)
    assert c2_ex_daze.effects[0].result.value == Resolved(0.10)
    assert c2_ex_daze.effects[0].rule.target.value == "team"
    assert c2_ex_daze.effects[0].rule.condition == DynamicIdentityCondition(
        DynamicIdentity.DAMAGE_DEALER
    )

    c6_stacks = rules["rule:character:1011:cinema6:charge-stacks"]
    c6_bonus = rules["rule:character:1011:cinema6:basic-dash-damage-bonus"]
    assert (c6_stacks.stack_count, c6_stacks.stack_min, c6_stacks.stack_max) == (0, 0, 8)
    assert c6_bonus.effects[0].result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert c6_bonus.effects[0].result.value == Resolved(0.45)
    assert isinstance(c6_bonus.effects[0].rule.condition, AllCondition)
    assert any(
        isinstance(item, AnyCondition)
        for item in c6_bonus.effects[0].rule.condition.conditions
    )
    assert c6_bonus.effects[0].rule.target.value == "team"
    active_charges = next(
        item
        for item in c6_bonus.effects[0].rule.condition.conditions
        if isinstance(item, AnyCondition)
    )
    assert {
        item.required_value
        for item in active_charges.conditions
        if isinstance(item, RuleStackCondition)
    } == set(range(1, 9))


def test_anby_additional_ability_eligibility_and_signature_are_explicit() -> None:
    solo = compile_registered_definition(ANBY_ID, {"core_level": 1, "cinema_level": 0}, [ANBY_ID])
    qingyi = compile_registered_definition(
        ANBY_ID,
        {"core_level": 1, "cinema_level": 0},
        [ANBY_ID, CharacterId("character:1251")],
    )
    solo_extra = next(rule for rule in solo.rule_items if "extra-ability" in str(rule.rule_id))
    qingyi_extra = next(rule for rule in qingyi.rule_items if "extra-ability" in str(rule.rule_id))
    assert solo_extra.eligibility is RuleEligibility.INELIGIBLE
    assert qingyi_extra.eligibility is RuleEligibility.ELIGIBLE
    assert solo_extra.effects == qingyi_extra.effects == ()
    assert solo_extra.diagnostics[0].blocking is False
    assert signature_wengine_id_for(ANBY_ID) == "wengine:13101"


def test_anby_current_cinema_six_charge_parameter_and_static_anomaly_entries() -> None:
    definition = compile_anby(
        AnbyCompileConfig(core_level=1, cinema_level=6),
        load_raw_record(load_character_record(str(ANBY_ID))),
    )
    anomaly = next(
        entry for entry in definition.move_entries
        if str(entry.move_id).endswith("electric-anomaly")
    )
    disorder = next(
        entry for entry in definition.move_entries
        if str(entry.move_id).endswith("electric-disorder")
    )
    assert anomaly.multiplier_variants[0].repeat_count == 10
    assert anomaly.multiplier_variants[0].multiplier.value == Resolved(1.25)
    assert disorder.multiplier_variants[0].parameter_base_value == 4.5
    assert disorder.multiplier_variants[0].parameter_coefficient == 1.25
    assert definition.scenario_parameters[0].value == 10
    assert definition.scenario_parameters[0].maximum == 10
    assert len(definition.damage_event_templates) == 15


def test_anby_owner_damage_scopes_do_not_invent_physical_ex_special() -> None:
    capabilities = registration_for(ANBY_ID).equipment_capabilities
    assert capabilities.can_produce_damage_scope(
        element=Element.ELECTRIC,
        skill_groups=(SkillGroup.SPECIAL_ATTACK,),
        tags=(DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
    )
    assert capabilities.can_produce_damage_scope(
        element=Element.PHYSICAL,
        skill_groups=(SkillGroup.BASIC_ATTACK,),
        tags=(DamageTag.BASIC_ATTACK,),
    )
    assert not capabilities.can_produce_damage_scope(
        element=Element.PHYSICAL,
        skill_groups=(SkillGroup.SPECIAL_ATTACK,),
        tags=(DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
    )


def test_anby_cinema6_charge_effect_follows_actual_damage_dealer_off_field() -> None:
    from core.application.characters.anby.reviewed import BASIC_VOLT_MOVE_ID

    definition = compile_anby(
        AnbyCompileConfig(core_level=1, cinema_level=6),
        load_raw_record(load_character_record(str(ANBY_ID))),
    )
    stack_rule = next(
        item for item in definition.rule_items
        if item.rule_id.endswith("cinema6:charge-stacks")
    )
    bonus_rule = next(
        item for item in definition.rule_items
        if item.rule_id.endswith("cinema6:basic-dash-damage-bonus")
    )
    selected_rule_ids = frozenset({stack_rule.rule_id, bonus_rule.rule_id})
    target = EnemyId("enemy:anby-cinema6")
    battle_state = BattleStateId("battle:anby-cinema6")
    anby_snapshot = CharacterSnapshot(ANBY_ID, 60, character_base_stats(ANBY_ID))
    ye_id = CharacterId("character:1431")
    ye_snapshot = CharacterSnapshot(ye_id, 60, character_base_stats(ye_id))

    def match(*, operator: CharacterId, dealer: CharacterId):
        metadata = DamageEventMetadata(
            event_id=DamageEventId(f"event:anby-test:{operator}:{dealer}"),
            battle_state_id=battle_state,
            damage_dealer=dealer,
            target_enemy=target,
            element=Element.PHYSICAL,
            created_at=0.0,
            skill_group=SkillGroup.BASIC_ATTACK,
            move_id=BASIC_VOLT_MOVE_ID,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        )
        event = DirectDamageEvent(
            metadata=metadata,
            base_settlement_data_source=CurrentAttackValueSource(dealer),
            multiplier=FixedMultiplier(Resolved(0.747)),
            crit_rule=StandardCritRule(dealer),
        )
        enemy = EnemySnapshot(
            enemy_id=target,
            level=60,
            initial_defense=Resolved(1000.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.2)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        )
        scenario = CalculationScenario(
            scenario_id="scenario:anby-cinema6-actual-dealer",
            current_operator=operator,
            conditions=definition.scenario_conditions,
            parameters=definition.scenario_parameters,
            enabled_rule_item_ids=selected_rule_ids,
            rule_stack_counts=(ScenarioRuleStack(stack_rule.rule_id, 1),),
        )
        context = EffectMatchContext(
            current_event=event,
            calculation_context=CalculationContext(
                event=event,
                battle_state_id=battle_state,
                character_snapshots=(anby_snapshot, ye_snapshot),
                target_snapshot=enemy,
            ),
            scenario=scenario,
            team=(
                CharacterMatchProfile(ANBY_ID, CharacterRole.STUN),
                CharacterMatchProfile(ye_id, CharacterRole.ATTACK),
            ),
            target=EnemyMatchProfile(target),
        )
        return EffectMatcher().match_effect(bonus_rule.effects[0], context)

    assert match(operator=ANBY_ID, dealer=ye_id).status is EffectMatchStatus.NOT_MATCHED
    assert match(operator=ye_id, dealer=ANBY_ID).status is EffectMatchStatus.MATCHED
