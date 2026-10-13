from __future__ import annotations

import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from core.types import (
    AnomalySourceChoice,
    BattleStateId,
    CharacterId,
    CharacterRole,
    DamageSubtype,
    DamageTag,
    DamageType,
    CalculationNode,
    EnemyId,
    Element,
    EffectOperation,
    SkillGroup,
)
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.nanoka_source import load_nanoka_raw_record
from core.application.characters.promeia import (
    PROMEIA_REVIEWED_MAPPING,
    PromeiaCompileConfig,
    compile_promeia,
    load_raw_record,
)
from core.application.characters.promeia.reviewed import PROMEIA_ID
from core.application.characters.templates import DischargeDamageEventTemplate
from core.application.execution.event_factory import instantiate_damage_event
from core.application.matching import EffectMatchStatus
from core.application.matching.evaluator import match_filters
from core.application.moves import MultiplierRelation
from core.application.rules import RuleEligibility
from core.presentation.calculation_service import calculate_payload
from core.types import FixedMultiplier, Resolved
from core.types import (
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    DamageEventId,
    DamageEventMetadata,
    DischargeDamageEvent,
    DisorderDamageEvent,
    EffectId,
    EventCreationEffect,
    NoCritRule,
    ModifierEffect,
    UnresolvedEffect,
)


_RAW_PATH = Path(__file__).resolve().parents[2] / "core" / "data" / "characters" / "promeia.json"


def _load_raw():
    source = json.loads(_RAW_PATH.read_text(encoding="utf-8"))
    return load_nanoka_raw_record(source, expected_character_id="character:1541")


def _fixed_value(entry) -> float:
    multiplier = entry.multiplier_variants[0].multiplier
    assert isinstance(multiplier, FixedMultiplier)
    assert isinstance(multiplier.value, Resolved)
    return multiplier.value.value


def _source_description(raw, move_name: str) -> str:
    return next(move.description for move in raw.moves if move.name == move_name)


def _derived_value(definition, template_id: str) -> float:
    reference = next(
        item
        for item in definition.independent_derived_damage_events
        if str(item.template.template_id) == template_id
    )
    assert isinstance(reference.multiplier, FixedMultiplier)
    assert isinstance(reference.multiplier.value, Resolved)
    return reference.multiplier.value.value


def test_promeia_identity_and_all_reviewed_direct_curves_match_nanoka_raw():
    source = json.loads(_RAW_PATH.read_text(encoding="utf-8"))
    raw = load_raw_record(source)
    assert raw.character_id == PROMEIA_ID
    assert (raw.name, raw.code_name, raw.rarity, raw.icon) == (
        "普罗米娅",
        "Promeia",
        4,
        "IconRole61",
    )
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1541.json"

    definition = compile_promeia(PromeiaCompileConfig(), raw)
    assert definition.role is CharacterRole.ANOMALY
    assert definition.base_element is Element.ICE
    assert len(PROMEIA_REVIEWED_MAPPING.moves) == 17

    entries = {str(entry.entry_id): entry for entry in definition.move_entries}
    raw_moves = {move.name: move for move in raw.moves}
    for spec in PROMEIA_REVIEWED_MAPPING.moves:
        entry = entries[f"move-entry:character:1541:{spec.entry_key}"]
        source_param = next(
            parameter
            for parameter in raw_moves[spec.source_name].parameters
            if parameter.name == spec.parameters[0].parameter_name
        )
        expected = source_param.value_for_level(12, spec.parameters[0].source_skill_id)
        assert expected is not None
        assert _fixed_value(entry) == pytest.approx(expected / 100.0)
        assert entry.multiplier_relation is spec.multiplier_relation
        assert entry.skill_group is spec.skill_group
        assert entry.damage_tags == spec.damage_tags
        assert entry.main_damage_event.element is Element.ICE


def test_cape_and_heavy_frost_dart_keep_known_curves_without_invented_parent_identity():
    raw = _load_raw()
    definition = compile_promeia(PromeiaCompileConfig(), raw)
    by_id = {str(item.entry_id): item for item in definition.move_entries}

    cape = by_id["move-entry:character:1541:cape-cut-per-second"]
    dart = by_id["move-entry:character:1541:heavy-frost-dart-cut"]
    assert _fixed_value(cape) == pytest.approx(0.393)
    assert cape.multiplier_relation is MultiplierRelation.COMPLETE
    assert cape.move_id is None
    assert cape.skill_group is None
    assert cape.damage_tags == frozenset()
    assert cape.multiplier_variants[0].repeat_count is None

    assert _fixed_value(dart) == pytest.approx(0.242)
    assert dart.multiplier_relation is MultiplierRelation.COMPLETE
    assert dart.move_id is None
    assert dart.skill_group is None
    assert dart.damage_tags == frozenset()
    assert dart.multiplier_variants[0].repeat_count is None


@pytest.mark.parametrize("core_level", range(1, 8))
def test_core_type2_ratio_matches_raw_and_never_uses_source_tick_profile(core_level: int):
    raw = _load_raw()
    text = raw.core_levels[core_level - 1].description
    match = re.search(
        r"固定结算\s*<color=[^>]*>(?P<rate>[\d.]+)%</color>倍率的对应属性的属性异常伤害",
        text,
    )
    assert match is not None
    expected = float(match.group("rate")) / 100.0

    definition = compile_promeia(PromeiaCompileConfig(core_level=core_level), raw)
    core_template = next(
        item
        for item in definition.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
        and str(item.ref.template_id) == "template:character:1541:core-frost-consuming-discharge"
    )
    assert _derived_value(
        definition,
        "template:character:1541:core-frost-consuming-discharge",
    ) == pytest.approx(expected)
    assert core_template.ref.damage_type is DamageType.ANOMALY
    assert core_template.ref.damage_subtype is DamageSubtype.DISCHARGE
    assert core_template.ref.skill_group is None
    assert core_template.ref.damage_tags == frozenset()
    assert core_template.source_multiplier_uses_tick_profile is False
    # The dynamic source map is only a selector/profile bridge; the fixed ratio
    # comes from the independent derived reference and is never tick-multiplied.
    assert all(value == 1.0 for _, value in core_template.source_multiplier_by_element)

    # The instantiated type-2 ratio remains fixed for different selected
    # original records; their element/history context does not add a tick ratio.
    ratio = FixedMultiplier(Resolved(expected))
    for element in (Element.ETHER, Element.PHYSICAL, Element.LIESHUANG):
        instantiated = instantiate_damage_event(
            core_template,
            ratio,
            battle_state_id=BattleStateId("battle:test"),
            target_enemy=EnemyId("enemy:test"),
            created_at=0.0,
            discharge_anomaly_source_choice=AnomalySourceChoice(
                source_character_id=CharacterId("character:test-source"),
                element=element,
            ),
        )
        assert instantiated.event.multiplier == ratio
        assert instantiated.event.metadata.element is element


def test_chain_and_ultimate_type2_rates_are_raw_fixed_ratios_and_locked_rules_stay_locked():
    raw = _load_raw()
    definition = compile_promeia(PromeiaCompileConfig(), raw)
    for key, move_name in (
        ("chain-anomaly-discharge", "连携技：倒悬清算"),
        ("ultimate-anomaly-discharge", "终结技：彻骨磔罚"),
    ):
        description = _source_description(raw, move_name)
        match = re.search(
            r"结算一次(?P<rate>[\d.]+)%倍率的对应属性的属性异常伤害",
            description,
        )
        assert match is not None
        assert _derived_value(
            definition,
            f"template:character:1541:{key}",
        ) == pytest.approx(float(match.group("rate")) / 100.0)

    discharges = [
        item
        for item in definition.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
    ]
    assert len(discharges) == 4
    assert all(item.source_multiplier_uses_tick_profile is False for item in discharges)
    rules = {str(rule.rule_id): rule for rule in definition.rule_items}
    for level in (1, 2, 3, 5, 6):
        rule = rules[f"rule:character:1541:cinema{level}:" + {
            1: "verdict-discharge-defense-ignore",
            2: "anomaly-proficiency-and-frost-discharge",
            3: "skill-levels",
            5: "skill-levels",
            6: "anomaly-disorder-resistance-ignore",
        }[level]]
        assert rule.eligibility is RuleEligibility.INELIGIBLE


def test_c3_and_c5_levels_include_ultimate_and_cap_at_sixteen():
    assert effective_skill_level(PromeiaCompileConfig(), SkillGroup.ULTIMATE) == 12
    assert effective_skill_level(PromeiaCompileConfig(cinema_level=3), SkillGroup.ULTIMATE) == 14
    assert effective_skill_level(PromeiaCompileConfig(cinema_level=5), SkillGroup.ULTIMATE) == 16
    assert effective_skill_level(
        PromeiaCompileConfig(cinema_level=5, skill_levels=()), SkillGroup.BASIC_ATTACK
    ) == 16


def test_no_damage_invisible_ex_or_daze_only_parry_entries_are_created():
    raw = _load_raw()
    definition = compile_promeia(PromeiaCompileConfig(), raw)
    labels = tuple(item.display_name for item in definition.move_entries)
    assert not any("匿影" in label for label in labels)
    assert not any("招架支援" in label for label in labels)
    assert sum(
        item.main_damage_event.damage_type is DamageType.DIRECT
        for item in definition.move_entries
    ) == 19
    assert sum(
        item.main_damage_event.damage_subtype is DamageSubtype.ATTRIBUTE_ANOMALY
        for item in definition.move_entries
    ) == 1
    assert sum(
        item.main_damage_event.damage_type is DamageType.DISORDER
        for item in definition.move_entries
    ) == 1


def test_standard_ice_anomaly_disorder_and_frost_chill_duration_match_rule_scope():
    raw = _load_raw()
    eligible = compile_promeia(
        PromeiaCompileConfig(additional_ability_eligible=True), raw
    )
    ineligible = compile_promeia(PromeiaCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in eligible.move_entries}
    assert _fixed_value(entries["move-entry:character:1541:ice-anomaly"]) == pytest.approx(5.0)
    disorder = entries["move-entry:character:1541:ice-disorder"]
    assert _fixed_value(disorder) == pytest.approx(4.5)
    assert disorder.multiplier_variants[0].parameter_base_value == pytest.approx(4.5)
    assert disorder.multiplier_variants[0].parameter_coefficient == pytest.approx(0.075)
    eligible_parameter = eligible.scenario_parameters[0]
    assert eligible_parameter.maximum == 13
    assert eligible_parameter.value == 13
    ineligible_parameter = ineligible.scenario_parameters[0]
    assert ineligible_parameter.maximum == 10
    assert ineligible_parameter.value == 10

    extra_rule = next(
        rule
        for rule in eligible.rule_items
        if str(rule.rule_id) == "rule:character:1541:extra-ability:frost-chill-duration"
    )
    assert extra_rule.eligibility is RuleEligibility.ELIGIBLE
    modifier = extra_rule.effects[0]
    assert modifier.result.modifier_path is CalculationNode.ANOMALY_DURATION_BONUS
    assert modifier.result.value.value == pytest.approx(3.0)
    assert (
        _matcher_status(modifier.rule.filters, _anomaly_like_event("attribute-anomaly"))
        is EffectMatchStatus.MATCHED
    )
    assert (
        _matcher_status(modifier.rule.filters, _anomaly_like_event("discharge"))
        is EffectMatchStatus.NOT_MATCHED
    )
    ineligible_rule = next(
        rule
        for rule in ineligible.rule_items
        if str(rule.rule_id) == "rule:character:1541:extra-ability:frost-chill-duration"
    )
    assert ineligible_rule.eligibility is RuleEligibility.INELIGIBLE
    assert not ineligible_rule.effects


def _matcher_status(filters, event, *, created_by_effect_id=None):
    context = SimpleNamespace(
        current_event=event,
        current_template_id=None,
        created_by_effect_id=created_by_effect_id,
    )
    return match_filters(filters, context, "test:promeia-scope")[0]


def _anomaly_like_event(event_kind: str, *, dealer=PROMEIA_ID, event_suffix="event"):
    target = EnemyId("enemy:promeia-scope")
    record_id = AnomalyRecordId("anomaly:promeia-scope")
    metadata = DamageEventMetadata(
        event_id=DamageEventId(f"damage:promeia-scope:{event_suffix}"),
        battle_state_id=BattleStateId("battle:promeia-scope"),
        damage_dealer=dealer,
        target_enemy=target,
        element=Element.ICE,
        created_at=1.0,
    )
    common = dict(
        metadata=metadata,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    if event_kind == "attribute-anomaly":
        return AttributeAnomalyDamageEvent(**common, anomaly_triggerer=dealer)
    if event_kind == "disorder":
        return DisorderDamageEvent(**common, disorder_triggerer=dealer)
    if event_kind == "discharge":
        return DischargeDamageEvent(**common, discharge_triggerer=dealer)
    raise AssertionError(f"unexpected test damage kind: {event_kind}")


def test_c6_resistance_ignore_matches_attribute_anomaly_and_disorder_but_never_discharge():
    definition = compile_promeia(PromeiaCompileConfig(cinema_level=6), _load_raw())
    c6_rule = next(
        rule
        for rule in definition.rule_items
        if str(rule.rule_id)
        == "rule:character:1541:cinema6:anomaly-disorder-resistance-ignore"
    )
    filters = c6_rule.effects[0].rule.filters
    for kind in ("attribute-anomaly", "disorder"):
        assert (
            _matcher_status(filters, _anomaly_like_event(kind))
            is EffectMatchStatus.MATCHED
        )
    for key in ("core", "chain", "ultimate", "cinema6"):
        discharge = _anomaly_like_event("discharge", event_suffix=key)
        assert discharge.damage_type is DamageType.ANOMALY
        assert discharge.damage_subtype is DamageSubtype.DISCHARGE
        assert (
            _matcher_status(filters, discharge)
            is EffectMatchStatus.NOT_MATCHED
        )


def test_c2_additive_multiplier_scope_is_only_frost_consuming_core_and_c6_discharge():
    definition = compile_promeia(PromeiaCompileConfig(cinema_level=6), _load_raw())
    c2_rule = next(
        rule
        for rule in definition.rule_items
        if str(rule.rule_id)
        == "rule:character:1541:cinema2:anomaly-proficiency-and-frost-discharge"
    )
    effect = next(item for item in c2_rule.effects if isinstance(item, ModifierEffect)
                  and item.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER)
    assert effect.result.operation is EffectOperation.ADD
    assert effect.result.value == Resolved(1.2)
    creation_ids = {
        str(effect.rule.effect_id)
        for rule in definition.rule_items
        for effect in rule.effects
        if isinstance(effect, EventCreationEffect)
    }
    core_creation_id = next(item for item in creation_ids if ":core:discharge-creation" in item)
    c6_creation_id = next(item for item in creation_ids if ":cinema6:extra-discharge-creation" in item)
    chain_creation_id = next(item for item in creation_ids if ":chain:discharge-creation" in item)
    ultimate_creation_id = next(item for item in creation_ids if ":ultimate:discharge-creation" in item)

    for effect_id in (core_creation_id, c6_creation_id):
        assert (
            _matcher_status(
                effect.rule.filters,
                _anomaly_like_event("discharge", event_suffix=effect_id),
                created_by_effect_id=EffectId(effect_id),
            )
            is EffectMatchStatus.MATCHED
        )
    for effect_id in (chain_creation_id, ultimate_creation_id):
        assert (
            _matcher_status(
                effect.rule.filters,
                _anomaly_like_event("discharge", event_suffix=effect_id),
                created_by_effect_id=EffectId(effect_id),
            )
            is EffectMatchStatus.NOT_MATCHED
        )


@pytest.mark.parametrize(
    ("source_character_id", "source_element"),
    (("character:1501", "ether"), ("character:1261", "physical")),
)
def test_core_type2_discharge_uses_selected_source_context_without_source_tick_multiplier(
    source_character_id: str,
    source_element: str,
):
    primary_id = "character:1541"
    team_ids = [primary_id, source_character_id]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    element_bonus = {"ice": 0.0, source_element: 0.0}
    payload = {
        "primary_character_id": primary_id,
        "current_operator": primary_id,
        "supporting_character_ids": [source_character_id],
        "team_character_ids": team_ids,
        "formation_character_ids": team_ids,
        "move_entry_id": "move-entry:character:1541:ex-judgment",
        "compile_configs": {
            primary_id: {"core_level": 7, "cinema_level": 0},
            source_character_id: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {
            "condition:character:1541:target-has-anomaly": True,
            "condition:character:1541:current-action-consumes-frost-punishment": True,
        },
        "parameter_values": {},
        "character_builds": {
            primary_id: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"ice": 0.0},
                },
            },
            source_character_id: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": element_bonus,
                },
            },
        },
        "enemy": {
            "enemy_id": f"enemy:promeia-{source_element}-source",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ice": 0.0, source_element: 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [
            "rule:character:1541:core:panel-bonuses",
            "rule:character:1541:core:discharge",
        ],
        "discharge_anomaly_source": {
            "source_character_id": source_character_id,
            "element": source_element,
        },
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }

    response = calculate_payload(payload)
    event = next(
        item for item in response["events"] if item["damage_subtype"] == "discharge"
    )
    assert event["element"] == source_element
    assert event["modes"]["expected"]["status"] == "calculated"
    breakdown = event["modes"]["expected"]["calculation_breakdown"]
    total_ratio = next(
        float(item["value"])
        for item in breakdown
        if item["node"] == "anomaly.discharge.total-multiplier"
    )
    assert total_ratio == pytest.approx(6.35)


def _disorder_duration_payload(
    primary_id: str,
    support_id: str,
    move_entry_id: str,
    *,
    extra_enabled: bool,
):
    team_ids = [primary_id, support_id]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    element_by_character = {
        "character:1541": "ice",
        "character:1501": "ether",
        "character:1091": "ice:lieshuang",
    }
    element_bonuses = {
        character_id: {element_by_character[character_id]: 0.0}
        for character_id in team_ids
    }
    return {
        "primary_character_id": primary_id,
        "current_operator": primary_id,
        "supporting_character_ids": [support_id],
        "team_character_ids": team_ids,
        "formation_character_ids": team_ids,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            character_id: {"core_level": 7, "cinema_level": 0}
            for character_id in team_ids
        },
        "condition_values": {},
        "parameter_values": {},
        "character_builds": {
            character_id: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": element_bonuses[character_id],
                },
            }
            for character_id in team_ids
        },
        "enemy": {
            "enemy_id": f"enemy:promeia-duration:{primary_id}",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "ice": 0.0,
                "ice:lieshuang": 0.0,
                "ether": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": (
            ["rule:character:1541:extra-ability:frost-chill-duration"]
            if extra_enabled
            else []
        ),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


@pytest.mark.parametrize(
    ("primary_id", "support_id", "entry_id", "extra_enabled", "expected_ratio"),
    (
        (
            "character:1541",
            "character:1501",
            "move-entry:character:1541:ice-disorder",
            True,
            5.475,
        ),
        (
            "character:1541",
            "character:1501",
            "move-entry:character:1541:ice-disorder",
            False,
            5.25,
        ),
        (
            "character:1091",
            "character:1541",
            "move-entry:character:1091:lieshuang-disorder",
            True,
            21.75,
        ),
        (
            "character:1091",
            "character:1541",
            "move-entry:character:1091:lieshuang-disorder",
            False,
            19.5,
        ),
    ),
)
def test_extra_duration_defaults_follow_ice_and_lieshuang_record_families(
    primary_id: str,
    support_id: str,
    entry_id: str,
    extra_enabled: bool,
    expected_ratio: float,
):
    result = calculate_payload(
        _disorder_duration_payload(
            primary_id,
            support_id,
            entry_id,
            extra_enabled=extra_enabled,
        )
    )
    assert result["totals"]["expected"]["complete"] is True
    event = next(item for item in result["events"] if item["damage_type"] == "disorder")
    assert event["modes"]["expected"]["status"] == "calculated"
    ratio = next(
        float(item["value"])
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "disorder.total-multiplier"
    )
    assert ratio == pytest.approx(expected_ratio)


def _promeia_discharge_payload(
    move_entry_id: str,
    *,
    cinema: int = 0,
    support_id: str | None = "character:1501",
    verdict_active: bool = True,
    enabled_rule_ids: tuple[str, ...] = (),
):
    primary_id = "character:1541"
    team_ids = [primary_id, *([support_id] if support_id is not None else [])]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    creation_rules = {
        "move-entry:character:1541:ex-judgment": "rule:character:1541:core:discharge",
        "move-entry:character:1541:chain-hanging-reckoning": "rule:character:1541:chain:discharge",
        "move-entry:character:1541:ultimate-bone-punishment": "rule:character:1541:ultimate:discharge",
    }
    payload = {
        "primary_character_id": primary_id,
        "current_operator": primary_id,
        "supporting_character_ids": team_ids[1:],
        "team_character_ids": team_ids,
        "formation_character_ids": team_ids,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            character_id: {
                "core_level": 7,
                "cinema_level": cinema if character_id == primary_id else 0,
            }
            for character_id in team_ids
        },
        "condition_values": {
            "condition:character:1541:target-has-anomaly": True,
            "condition:character:1541:verdict-active": verdict_active,
            **(
                {"condition:character:1541:current-action-consumes-frost-punishment": True}
                if move_entry_id == "move-entry:character:1541:ex-judgment"
                else {}
            ),
        },
        "parameter_values": {},
        "character_builds": {
            character_id: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"ice": 0.0, "ether": 0.0},
                },
            }
            for character_id in team_ids
        },
        "enemy": {
            "enemy_id": "enemy:promeia-verdict-api",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ice": 0.0, "ether": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [
            "rule:character:1541:core:panel-bonuses",
            *(
                (creation_rules[move_entry_id],)
                if move_entry_id in creation_rules
                else ()
            ),
            *enabled_rule_ids,
        ],
        "discharge_anomaly_source": {
            "source_character_id": primary_id,
            "element": "ice",
        },
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }
    return payload


def _breakdown_value(event: dict, node: str) -> float:
    return next(
        float(item["value"])
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == node
    )


def test_verdict_discharge_defense_ignore_is_40_plus_c1_20_and_rule_scoped():
    core_entry = "move-entry:character:1541:ex-judgment"
    extra_rule = "rule:character:1541:extra-ability:verdict-discharge-defense-ignore"
    c1_rule = "rule:character:1541:cinema1:verdict-discharge-defense-ignore"
    cases = (
        (0, "character:1501", (extra_rule,), True, 0.40),
        (1, "character:1501", (extra_rule, c1_rule), True, 0.60),
        (1, None, (c1_rule,), True, 0.20),
        (1, "character:1501", (extra_rule, c1_rule), False, 0.0),
        (1, None, (), True, 0.0),
    )
    for cinema, support_id, enabled, verdict_active, expected_ignore in cases:
        result = calculate_payload(
            _promeia_discharge_payload(
                core_entry,
                cinema=cinema,
                support_id=support_id,
                verdict_active=verdict_active,
                enabled_rule_ids=enabled,
            )
        )
        discharge = next(
            item for item in result["events"] if item["damage_subtype"] == "discharge"
        )
        assert discharge["modes"]["expected"]["status"] == "calculated"
        assert _breakdown_value(discharge, "defense.damage-ignore") == pytest.approx(
            expected_ignore
        )


@pytest.mark.parametrize(
    ("move_entry_id", "cinema", "enable_c2", "expected_complete", "expected_ratio"),
    (
        ("move-entry:character:1541:ex-judgment", 2, True, True, 7.55),
        ("move-entry:character:1541:ex-judgment", 2, False, True, 6.35),
        ("move-entry:character:1541:chain-hanging-reckoning", 2, True, True, 1.0),
        ("move-entry:character:1541:ultimate-bone-punishment", 2, True, True, 2.5),
    ),
)
def test_c2_adds_120_points_only_to_frost_consuming_core_type2_event(
    move_entry_id: str,
    cinema: int,
    enable_c2: bool,
    expected_complete: bool,
    expected_ratio: float | None,
):
    source_rule = {
        "move-entry:character:1541:ex-judgment": "rule:character:1541:core:discharge",
        "move-entry:character:1541:chain-hanging-reckoning": "rule:character:1541:chain:discharge",
        "move-entry:character:1541:ultimate-bone-punishment": "rule:character:1541:ultimate:discharge",
    }[move_entry_id]
    enabled = [source_rule]
    if enable_c2:
        enabled.append(
            "rule:character:1541:cinema2:anomaly-proficiency-and-frost-discharge"
        )
    result = calculate_payload(
        _promeia_discharge_payload(
            move_entry_id,
            cinema=cinema,
            enabled_rule_ids=tuple(enabled),
        )
    )
    assert result["totals"]["expected"]["complete"] is expected_complete
    discharge = next(
        (item for item in result["events"] if item["damage_subtype"] == "discharge"),
        None,
    )
    assert discharge is not None
    assert discharge["modes"]["expected"]["status"] == "calculated"
    assert _breakdown_value(
        discharge, "anomaly.discharge.total-multiplier"
    ) == pytest.approx(expected_ratio)


def test_c2_adds_120_points_to_the_cinema6_frost_special_discharge():
    entry = "move-entry:character:1541:ex-judgment"
    result = calculate_payload(
        _promeia_discharge_payload(
            entry,
            cinema=6,
            enabled_rule_ids=(
                "rule:character:1541:core:discharge",
                "rule:character:1541:cinema2:anomaly-proficiency-and-frost-discharge",
                "rule:character:1541:cinema6:extra-discharge",
            ),
        )
    )
    special = next(
        item for item in result["events"]
        if item["damage_subtype"] == "discharge"
        and ":cinema6-frost-special-discharge" in item["semantic_id"]
    )
    assert special["modes"]["expected"]["status"] == "calculated"
    assert _breakdown_value(special, "anomaly.discharge.total-multiplier") == pytest.approx(3.2)
