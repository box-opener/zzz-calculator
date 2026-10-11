from __future__ import annotations

import json
from pathlib import Path
from dataclasses import replace

import pytest

from core.application.characters.nanoka_source import load_nanoka_raw_record
from core.application.characters.sunna import SunnaCompileConfig, compile_sunna
from core.application.characters.sunna.compiler import (
    CAT_GAZE_ON_TARGET_ACTIVE,
    _cat_gaze_for_triggerer,
    _cat_gaze_template_id,
    _source,
)
from core.application.characters.sunna.config import (
    SUNNA_ID,
    SunnaCatGazeTriggerer,
)
from core.application.characters.sunna.reviewed import (
    ANGEL_CHORUS_ACTIVE,
    BAD_CAT_ACTIVE,
    CINEMA6_CREATING_ACTIVE,
    COOPERATIVE_PHOTO_EXTRA,
    ETHER_VEIL_ACTIVE,
    EXTRA_STUN_VULNERABILITY_ACTIVE,
    SUNNA_REVIEWED_MAPPING,
    SUNNA_ETHER_VEIL_ACTIVE,
)
from core.application.moves import MultiplierRelation
from core.application.rules import RuleEligibility
from core.application.scenario import ConditionResolution, ParameterResolution
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
    signature_wengine_id_for,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _sunna_additional_ability_eligibility,
    compile_registered_definition,
    equipment_capabilities_for_definition,
    registration_for,
)
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    CharacterRole,
    DamageDealerFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectOperation,
    EffectTarget,
    Element,
    EventCreationEffect,
    EffectSourceType,
    EquipmentDamageScope,
    EventTemplateIdFilter,
    GuaranteedCritEffect,
    InitialAttackValueSource,
    ModifierEffect,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
    WEngineId,
)


_ROOT = Path(__file__).resolve().parents[2]
_RAW_PATH = _ROOT / "core" / "data" / "characters" / "sunna.json"


@pytest.fixture(scope="module")
def raw_record():
    raw = json.loads(_RAW_PATH.read_text(encoding="utf-8"))
    return raw, load_nanoka_raw_record(raw)


def _entry(definition, key: str):
    suffix = f":{key}"
    return next(item for item in definition.move_entries if str(item.entry_id).endswith(suffix))


def _rule(definition, key: str):
    suffix = f":{key}"
    return next(item for item in definition.rule_items if str(item.rule_id).endswith(suffix))


def _modifiers(rule):
    return tuple(item for item in rule.effects if isinstance(item, ModifierEffect))


def _effect_value(effect):
    assert isinstance(effect.result.value, Resolved)
    return effect.result.value.value


def test_sunna_raw_identity_and_default_source_curves(raw_record) -> None:
    raw, parsed = raw_record
    assert (
        parsed.character_id,
        parsed.name,
        parsed.code_name,
        parsed.rarity,
        parsed.specialty,
        parsed.element,
        parsed.faction,
        parsed.icon,
    ) == (
        SUNNA_ID,
        "千夏",
        "Sunna",
        4,
        "支援",
        "物理",
        "妄想天使",
        "IconRole58",
    )
    assert (raw["source_version"], raw["source_url"]) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1491.json",
    )
    definition = compile_sunna(SunnaCompileConfig(), parsed)
    assert definition.role is CharacterRole.SUPPORT
    assert definition.base_element is Element.PHYSICAL

    expected = {
        "basic-stage-1": 0.874,
        "basic-stage-2": 3.519,
        "basic-stage-3": 3.627,
        "basic-stage-4": 8.112,
        "bad-cat": 4.170,
        "dash-attack": 1.998,
        "dodge-counter": 6.378,
        "special": 1.136,
        "ex-special-bubblegum-bombardment": 18.274,
        "ex-special-photo-technique": 16.564,
        "chain-attack": 16.231,
        "ultimate": 41.820,
        "quick-assist": 1.464,
        "assist-strike": 10.714,
    }
    assert len(definition.move_entries) == len(expected)
    for key, ratio in expected.items():
        assert _entry(definition, key).multiplier_variants[0].multiplier.value.value == pytest.approx(ratio)
    for stage in range(1, 5):
        entry = _entry(definition, f"basic-stage-{stage}")
        assert entry.multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE
        assert entry.stage_index == stage
        assert entry.skill_group is SkillGroup.BASIC_ATTACK
        assert entry.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
        assert entry.main_damage_event.element is Element.PHYSICAL
    assert all(
        item.ref.damage_type not in {DamageType.ANOMALY, DamageType.DISORDER}
        for item in definition.damage_event_templates
    )
    bad_cat_entry = _entry(definition, "bad-cat")
    bad_cat_template = next(
        item
        for item in definition.damage_event_templates
        if item.ref.template_id == bad_cat_entry.main_damage_event.template_id
    )
    bad_cat = next(item for item in parsed.moves if item.name == "普通攻击：坏猫出没")
    assert bad_cat.parameters[0].value_for_level(12, "1491005") == 417.0
    assert isinstance(bad_cat_template.base_source, InitialAttackValueSource)
    assert bad_cat_template.base_source.character_id == SUNNA_ID
    assert bad_cat_entry.condition_ids == (BAD_CAT_ACTIVE,)
    assert next(
        item for item in definition.scenario_conditions if item.condition_id == BAD_CAT_ACTIVE
    ).value is False


def test_sunna_registry_panel_catalog_signature_and_eligibility(raw_record) -> None:
    _, parsed = raw_record
    assert parsed.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1491.json"
    assert str(SUNNA_ID) in supported_character_ids()
    registration = registration_for(SUNNA_ID)
    assert registration.role is CharacterRole.SUPPORT
    assert registration.base_element is Element.PHYSICAL
    assert registration.catalog.display_name == "千夏"
    assert registration.catalog.specialty == "support"
    assert compile_registered_definition(
        SUNNA_ID,
        {"core_level": 7, "cinema_level": 0},
        (SUNNA_ID,),
    ).role is CharacterRole.SUPPORT
    panel = character_base_stats(SUNNA_ID)
    assert panel.attack.value == pytest.approx(750.7503)
    assert panel.hp.value == pytest.approx(8477.1696)

    capabilities = equipment_capabilities_for_definition(
        compile_registered_definition(
            SUNNA_ID,
            {"core_level": 7, "cinema_level": 0},
            (SUNNA_ID,),
        )
    )
    assert capabilities.role is CharacterRole.SUPPORT
    assert capabilities.native_element is Element.PHYSICAL
    assert capabilities.possible_elements == frozenset({Element.PHYSICAL})
    assert capabilities.damage_scopes == frozenset(
        EquipmentDamageScope(spec.element, spec.skill_group, spec.damage_tags)
        for spec in SUNNA_REVIEWED_MAPPING.moves
    )

    engine_id = WEngineId("wengine:14149")
    assert SIGNATURE_WENGINE_BY_CHARACTER[SUNNA_ID] == engine_id
    assert signature_wengine_id_for(SUNNA_ID) == engine_id
    assert load_wengine_raw_record(engine_id).icon == "Weapon_S_1491"
    assert any(
        item.wengine_id == str(engine_id)
        and item.signature_character_id == str(SUNNA_ID)
        for item in supported_wengine_catalog()
    )
    assert any(
        item.character_id == str(SUNNA_ID)
        and item.code_name == "Sunna"
        for item in supported_character_catalog()
    )

    assert _sunna_additional_ability_eligibility(
        (SUNNA_ID, CharacterId("character:1461"))
    )
    assert not _sunna_additional_ability_eligibility(
        (SUNNA_ID, CharacterId("character:1421"))
    )
    assert not _sunna_additional_ability_eligibility((SUNNA_ID,))


def _panel(attack: float) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 90.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0, "electric": 0.0},
    }


def _calculation_payload(
    *,
    primary: str,
    support_ids: tuple[str, ...],
    entry_id: str,
    conditions: dict[str, bool],
    attacks: dict[str, float],
    configs: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    team = (primary, *support_ids)
    configs = configs or {
        character_id: {"core_level": 7, "cinema_level": 0}
        for character_id in team
    }
    definitions = tuple(
        compile_registered_definition(character_id, configs[character_id], team)
        for character_id in team
    )
    enabled = [
        str(rule.rule_id)
        for definition in definitions
        for rule in definition.rule_items
        if rule.eligibility is RuleEligibility.ELIGIBLE
    ]
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(support_ids),
        "team_character_ids": list(team),
        "move_entry_id": entry_id,
        "compile_configs": configs,
        "condition_values": conditions,
        "parameter_values": {},
        "character_builds": {
            character_id: {
                "level": 60,
                "out_of_combat_stats": _panel(attack),
            }
            for character_id, attack in attacks.items()
        },
        "enemy": {
            "enemy_id": "enemy:sunna-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.0, "electric": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": enabled,
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def test_sunna_bad_cat_api_uses_initial_attack_while_current_panel_is_buffed() -> None:
    character = str(SUNNA_ID)
    result = calculate_payload(
        _calculation_payload(
            primary=character,
            support_ids=(),
            entry_id="move-entry:character:1491:bad-cat",
            conditions={
                str(BAD_CAT_ACTIVE): True,
                str(ANGEL_CHORUS_ACTIVE): True,
            },
            attacks={character: 1200.0},
        )
    )
    assert result["totals"]["expected"]["complete"] is True
    snapshot = result["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == pytest.approx(1560.0)
    event = result["events"][0]
    assert event["modes"]["expected"]["status"] == "calculated"
    breakdown = event["modes"]["expected"]["calculation_breakdown"]
    initial_attack = next(item for item in breakdown if item["node"] == "character.initial.attack")
    base_value = next(item for item in breakdown if item["node"] == "damage.base-value")
    assert initial_attack["value"] == pytest.approx(1200.0)
    assert initial_attack["read_rule"] == "initial"
    assert base_value["value"] == pytest.approx(5004.0)


def test_sunna_cat_gaze_child_uses_triggerer_element_not_physical_parent() -> None:
    seed = "character:1461"
    sunna = str(SUNNA_ID)
    result = calculate_payload(
        _calculation_payload(
            primary=seed,
            support_ids=(sunna,),
            entry_id="move-entry:character:1461:basic-stage-1",
            conditions={str(CAT_GAZE_ON_TARGET_ACTIVE): True},
            attacks={seed: 1400.0, sunna: 900.0},
        )
    )
    parent = next(
        item for item in result["events"]
        if item["semantic_id"] == "event:character:1461:basic-stage-1:main"
    )
    child = next(
        item for item in result["events"]
        if item["semantic_id"].startswith(
            "event:character:1491:core:cat-gaze:character_1461:source:"
        )
    )
    assert sum("event:character:1491:core:cat-gaze:" in item["semantic_id"] for item in result["events"]) == 1
    assert parent["element"] == "physical"
    assert child["element"] == "electric"
    assert child["damage_type"] == "direct"
    assert child["common_application_trace"]["base_source_character_id"] == seed
    assert child["modes"]["expected"]["status"] == "calculated"
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("core_level", "cinema_level", "expected_multiplier"),
    (
        (1, 0, 1.5),
        (1, 2, 3.5),
        (7, 0, 3.0),
        (7, 2, 5.0),
    ),
)
def test_sunna_cinema_two_attack_cat_gaze_ratio_uses_core_base_without_veil(
    core_level: int,
    cinema_level: int,
    expected_multiplier: float,
) -> None:
    seed = "character:1461"
    sunna = str(SUNNA_ID)
    result = calculate_payload(
        _calculation_payload(
            primary=seed,
            support_ids=(sunna,),
            entry_id="move-entry:character:1461:basic-stage-1",
            conditions={str(CAT_GAZE_ON_TARGET_ACTIVE): True},
            attacks={seed: 1400.0, sunna: 900.0},
            configs={
                seed: {"core_level": 7, "cinema_level": 0},
                sunna: {"core_level": core_level, "cinema_level": cinema_level},
            },
        )
    )
    child = next(
        item for item in result["events"]
        if item["semantic_id"].startswith(
            "event:character:1491:core:cat-gaze:character_1461:source:"
        )
    )
    breakdown = child["modes"]["expected"]["calculation_breakdown"]
    multiplier = next(item["value"] for item in breakdown if item["node"] == "damage.skill-multiplier")
    base_value = next(item["value"] for item in breakdown if item["node"] == "damage.base-value")
    assert multiplier == pytest.approx(expected_multiplier)
    assert base_value == pytest.approx(1400.0 * expected_multiplier)
    assert child["modes"]["expected"]["status"] == "calculated"
    assert result["totals"]["expected"]["complete"] is True
    assert result["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(1400.0)


def test_sunna_cinema_two_veil_team_attack_is_separate_from_cat_gaze_ratio() -> None:
    seed = "character:1461"
    sunna = str(SUNNA_ID)
    result = calculate_payload(
        _calculation_payload(
            primary=seed,
            support_ids=(sunna,),
            entry_id="move-entry:character:1461:basic-stage-1",
            conditions={
                str(CAT_GAZE_ON_TARGET_ACTIVE): True,
                str(ETHER_VEIL_ACTIVE): True,
            },
            attacks={seed: 1400.0, sunna: 900.0},
            configs={
                seed: {"core_level": 7, "cinema_level": 0},
                sunna: {"core_level": 7, "cinema_level": 2},
            },
        )
    )
    child = next(
        item for item in result["events"]
        if item["semantic_id"].startswith(
            "event:character:1491:core:cat-gaze:character_1461:source:"
        )
    )
    breakdown = child["modes"]["expected"]["calculation_breakdown"]
    assert next(item["value"] for item in breakdown if item["node"] == "character.current.attack") == pytest.approx(1540.0)
    assert next(item["value"] for item in breakdown if item["node"] == "damage.skill-multiplier") == pytest.approx(5.0)
    assert next(item["value"] for item in breakdown if item["node"] == "damage.base-value") == pytest.approx(7700.0)
    assert result["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(1540.0)
    assert result["totals"]["expected"]["complete"] is True


def test_sunna_anomaly_cat_gaze_api_applies_bonus_crit_damage_and_guarantee() -> None:
    jane = "character:1261"
    sunna = str(SUNNA_ID)
    result = calculate_payload(
        _calculation_payload(
            primary=jane,
            support_ids=(sunna,),
            entry_id="move-entry:character:1261:basic-footwork-1",
            conditions={str(CAT_GAZE_ON_TARGET_ACTIVE): True},
            attacks={jane: 1400.0, sunna: 900.0},
            configs={
                jane: {"core_level": 7, "cinema_level": 0},
                sunna: {"core_level": 7, "cinema_level": 2},
            },
        )
    )
    child = next(
        item for item in result["events"]
        if item["semantic_id"].startswith(
            "event:character:1491:core:cat-gaze:character_1261:source:"
        )
    )
    assert child["element"] == "physical"
    assert child["common_application_trace"]["base_source_character_id"] == jane
    assert child["common_application_trace"]["guaranteed_crit_effect_ids"] == [
        "effect:character:1491:core:cat-gaze:triggerer:character_1261:anomaly-guaranteed-crit"
    ]
    stat_modifiers = child["common_application_trace"]["event_stat_modifiers"]
    crit_damage = next(item for item in stat_modifiers if item["modifier_path"] == "character.current.crit-damage")
    assert crit_damage["value"] == pytest.approx(1.5)
    assert crit_damage["recipient_character_id"] == jane
    breakdown = child["modes"]["expected"]["calculation_breakdown"]
    assert next(item["value"] for item in breakdown if item["node"] == "damage.skill-multiplier") == pytest.approx(7.8)
    assert next(item["value"] for item in breakdown if item["node"] == "character.current.crit-damage") == pytest.approx(2.0)
    assert child["modes"]["expected"]["value"] == pytest.approx(
        child["modes"]["full-crit"]["value"]
    )
    assert child["modes"]["expected"]["status"] == "calculated"
    assert result["totals"]["expected"]["complete"] is True


def test_cinema_three_and_five_skill_bonuses_include_ultimate(raw_record) -> None:
    _, parsed = raw_record
    c3 = compile_sunna(SunnaCompileConfig(cinema_level=3), parsed)
    c5 = compile_sunna(SunnaCompileConfig(cinema_level=5), parsed)
    assert _entry(c3, "ultimate").multiplier_variants[0].multiplier.value.value == pytest.approx(45.622)
    assert _entry(c5, "ultimate").multiplier_variants[0].multiplier.value.value == pytest.approx(49.424)
    assert _entry(c3, "basic-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(0.954)
    assert _entry(c5, "basic-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(1.034)
    assert _rule(c3, "cinema3:skill-levels").eligibility is RuleEligibility.ELIGIBLE
    assert _rule(c5, "cinema5:skill-levels").eligibility is RuleEligibility.ELIGIBLE


def test_core_cat_gaze_uses_each_triggerer_role_element_panels_and_scope(raw_record) -> None:
    _, parsed = raw_record
    anomaly_id = CharacterId("character:1511")
    attack_id = CharacterId("character:1111")
    for level, attack_ratio, anomaly_ratio, anomaly_cd in (
        (1, 1.50, 2.40, 0.80),
        (2, 1.75, 2.80, 0.90),
        (3, 2.00, 3.20, 1.00),
        (4, 2.25, 3.60, 1.20),
        (5, 2.50, 4.00, 1.30),
        (6, 2.75, 4.40, 1.40),
        (7, 3.00, 4.80, 1.50),
    ):
        config = SunnaCompileConfig(core_level=level)
        source = _source(
            "core-passive",
            EffectSourceType.CORE_PASSIVE,
            parsed.core_levels[level - 1].name,
            parsed.core_levels[level - 1].description,
        )
        excluded = (_cat_gaze_template_id(attack_id), _cat_gaze_template_id(anomaly_id))
        attack_rule, attack_template, attack_derived = _cat_gaze_for_triggerer(
            parsed,
            config,
            SunnaCatGazeTriggerer(attack_id, CharacterRole.ATTACK, Element.ETHER),
            source,
            excluded,
        )
        anomaly_rule, anomaly_template, anomaly_derived = _cat_gaze_for_triggerer(
            parsed,
            config,
            SunnaCatGazeTriggerer(anomaly_id, CharacterRole.ANOMALY, Element.ETHER),
            source,
            excluded,
        )
        assert attack_derived.multiplier.value.value == pytest.approx(attack_ratio)
        assert anomaly_derived.multiplier.value.value == pytest.approx(anomaly_ratio)
        for triggerer_id, rule, template in (
            (attack_id, attack_rule, attack_template),
            (anomaly_id, anomaly_rule, anomaly_template),
        ):
            assert template.damage_dealer == triggerer_id
            assert template.base_source.character_id == triggerer_id
            assert template.crit_rule.stat_owner == triggerer_id
            assert template.element is Element.ETHER
            assert template.move_id is None
            assert template.ref.skill_group is None
            assert template.ref.damage_tags == frozenset()
            creation = next(item for item in rule.effects if isinstance(item, EventCreationEffect))
            assert creation.rule.owner == SUNNA_ID
            assert creation.rule.target is EffectTarget.TEAM
            assert creation.rule.condition is None
            assert DamageDealerFilter(triggerer_id) in creation.rule.filters
            assert DamageTypeFilter(DamageType.DIRECT) in creation.rule.filters
            recursive_exclusions = {
                item.filter.template_id
                for item in creation.rule.filters
                if isinstance(item, NotFilter) and isinstance(item.filter, EventTemplateIdFilter)
            }
            assert recursive_exclusions == set(excluded)
        assert anomaly_template.crit_rule.guaranteed is True
        assert attack_template.crit_rule.guaranteed is False
        anomaly_cd_effect = _modifiers(anomaly_rule)[0]
        assert anomaly_cd_effect.rule.target is EffectTarget.RECIPIENT
        assert anomaly_cd_effect.rule.recipient_character_id == anomaly_id
        assert _effect_value(anomaly_cd_effect) == pytest.approx(anomaly_cd)
        assert not _modifiers(attack_rule)


def test_cross_dealer_cat_gaze_is_only_allowed_as_an_independent_created_child(raw_record) -> None:
    _, parsed = raw_record
    actor_id = CharacterId("character:1111")
    definition = compile_sunna(
        SunnaCompileConfig(
            cat_gaze_triggerers=(
                SunnaCatGazeTriggerer(actor_id, CharacterRole.ATTACK, Element.ELECTRIC),
            )
        ),
        parsed,
    )
    child_template = next(
        item
        for item in definition.damage_event_templates
        if item.damage_dealer == actor_id
    )
    assert child_template.damage_dealer == actor_id
    assert child_template.ref.source_rule_item_id is not None
    assert any(
        item.template.template_id == child_template.ref.template_id
        and not item.required
        for item in definition.independent_derived_damage_events
    )

    main_entry = definition.move_entries[0]
    unsafe_main_entry = replace(
        main_entry,
        move_id=None,
        skill_group=None,
        damage_tags=frozenset(),
        main_damage_event=child_template.ref,
    )
    with pytest.raises(ValueError, match="move main-damage event must be owned"):
        replace(
            definition,
            move_entries=(unsafe_main_entry, *definition.move_entries[1:]),
        )


def test_core_attack_buff_and_sunna_ether_veil_are_initial_and_scoped(raw_record) -> None:
    _, parsed = raw_record
    expected_caps = (525, 615, 705, 795, 885, 975, 1050)
    for level, cap in enumerate(expected_caps, start=1):
        definition = compile_sunna(SunnaCompileConfig(core_level=level, sunna_ether_veil_active=True), parsed)
        buff = _modifiers(_rule(definition, "core:angel-chorus-attack"))[0]
        assert isinstance(buff.result.value, PanelStatDerivedValue)
        assert buff.result.value.source_character_id == SUNNA_ID
        assert buff.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ATTACK
        assert buff.result.value.coefficient.value == pytest.approx(0.30)
        assert buff.result.value.cap_max.value == pytest.approx(cap)
        assert buff.rule.target is EffectTarget.TEAM
        assert _rule(definition, "core:angel-chorus-attack").condition_ids == (ANGEL_CHORUS_ACTIVE,)

    definition = compile_sunna(SunnaCompileConfig(sunna_ether_veil_active=True), parsed)
    veil_rule = _rule(definition, "special-photo-technique:sunna-ether-veil-attack")
    veil_effect = _modifiers(veil_rule)[0]
    assert veil_rule.condition_ids == (SUNNA_ETHER_VEIL_ACTIVE,)
    assert veil_effect.rule.target is EffectTarget.TEAM
    assert veil_effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS
    assert _effect_value(veil_effect) == 50


def test_cinema_two_splits_veil_attack_from_unconditional_cat_gaze_ratio(raw_record) -> None:
    _, parsed = raw_record
    definition = compile_sunna(
        SunnaCompileConfig(cinema_level=6, cinema6_creating_active=True), parsed
    )
    team_attack = _rule(definition, "cinema2:ether-veil-team-attack")
    ratio_rule = _rule(definition, "cinema2:cat-gaze-ratio")
    assert team_attack.condition_ids == (ETHER_VEIL_ACTIVE,)
    assert _effect_value(_modifiers(team_attack)[0]) == pytest.approx(0.10)
    assert ratio_rule.condition_ids == ()
    ratio_effect = next(
        item for item in _modifiers(ratio_rule)
        if str(item.rule.effect_id).endswith("character_1491")
    )
    assert ratio_effect.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    assert ratio_effect.result.operation is EffectOperation.MULTIPLY
    assert _effect_value(ratio_effect) == pytest.approx(5.0 / 3.0)
    assert ratio_effect.rule.filters == (
        DamageDealerFilter(SUNNA_ID),
        EventTemplateIdFilter(_cat_gaze_template_id(SUNNA_ID)),
    )

    attack = CharacterId("character:1111")
    anomaly = CharacterId("character:1261")
    for core_level, attack_factor, anomaly_factor in (
        (1, 3.5 / 1.5, 5.4 / 2.4),
        (7, 5.0 / 3.0, 7.8 / 4.8),
    ):
        core_source = _source(
            "core-passive",
            EffectSourceType.CORE_PASSIVE,
            parsed.core_levels[core_level - 1].name,
            parsed.core_levels[core_level - 1].description,
        )
        config = SunnaCompileConfig(
            core_level=core_level,
            cinema_level=2,
            cat_gaze_triggerers=(
                SunnaCatGazeTriggerer(attack, CharacterRole.ATTACK, Element.ELECTRIC),
                SunnaCatGazeTriggerer(anomaly, CharacterRole.ANOMALY, Element.PHYSICAL),
            ),
        )
        c2_definition = compile_sunna(config, parsed)
        effects = _modifiers(_rule(c2_definition, "cinema2:cat-gaze-ratio"))
        attack_effect = next(
            item for item in effects
            if DamageDealerFilter(attack) in item.rule.filters
        )
        anomaly_effect = next(
            item for item in effects
            if DamageDealerFilter(anomaly) in item.rule.filters
        )
        assert attack_effect.result.operation is EffectOperation.MULTIPLY
        assert anomaly_effect.result.operation is EffectOperation.MULTIPLY
        assert _effect_value(attack_effect) == pytest.approx(attack_factor)
        assert _effect_value(anomaly_effect) == pytest.approx(anomaly_factor)


def test_photo_technique_cooperative_parameter_uses_the_matching_source_curve(raw_record) -> None:
    _, parsed = raw_record
    normal = compile_sunna(SunnaCompileConfig(angel_chorus_active=True), parsed)
    coordinated = compile_sunna(
        SunnaCompileConfig(angel_chorus_active=True, cooperative_photo_extra=1), parsed
    )
    normal_variant = _entry(normal, "ex-special-photo-technique").multiplier_variants[0]
    coordinated_variant = _entry(coordinated, "ex-special-photo-technique").multiplier_variants[0]
    assert normal_variant.multiplier.value.value == pytest.approx(16.564)
    assert normal_variant.parameter_value_id == COOPERATIVE_PHOTO_EXTRA
    assert normal_variant.parameter_base_value == pytest.approx(16.564)
    assert normal_variant.parameter_coefficient == pytest.approx(2.486)
    assert coordinated.scenario_parameters[0].parameter_id == COOPERATIVE_PHOTO_EXTRA
    assert coordinated.scenario_parameters[0].resolution is ParameterResolution.USER_SELECTED
    assert coordinated.scenario_parameters[0].value == 1
    assert normal.scenario_parameters[0].value == 0
    assert coordinated_variant.condition_ids == (ANGEL_CHORUS_ACTIVE,)


def test_cinema_conditions_and_cinema_six_scope_are_explicit(raw_record) -> None:
    _, parsed = raw_record
    config = SunnaCompileConfig(
        cinema_level=6,
        cinema1_defense_reduction_stacks=2,
        cinema4_team_damage_active=True,
        cinema6_creating_active=True,
        additional_ability_eligible=True,
        extra_stun_vulnerability_active=True,
    )
    definition = compile_sunna(config, parsed)
    conditions = {item.condition_id: item for item in definition.scenario_conditions}
    for condition_id in (
        CINEMA6_CREATING_ACTIVE,
        EXTRA_STUN_VULNERABILITY_ACTIVE,
    ):
        assert conditions[condition_id].resolution is ConditionResolution.USER_SELECTED
        assert conditions[condition_id].value is True
    assert conditions[ETHER_VEIL_ACTIVE].value is False

    c1 = _rule(definition, "cinema1:enemy-defense-reduction")
    assert c1.stack_count == 2
    assert (c1.stack_min, c1.stack_max) == (0, 3)
    assert _effect_value(_modifiers(c1)[0]) == pytest.approx(0.07)

    c4 = _rule(definition, "cinema4:team-damage-after-ultimate")
    assert c4.condition_ids
    assert _modifiers(c4)[0].result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert _effect_value(_modifiers(c4)[0]) == pytest.approx(0.18)

    extra = _rule(definition, "extra-ability:ether-veil-stun-vulnerability")
    assert extra.condition_ids == (EXTRA_STUN_VULNERABILITY_ACTIVE,)
    assert _modifiers(extra)[0].result.modifier_path is CalculationNode.ENEMY_STUN_VULNERABILITY
    assert _effect_value(_modifiers(extra)[0]) == pytest.approx(0.30)

    self_child_id = _cat_gaze_template_id(SUNNA_ID)
    self_child = next(
        item for item in definition.independent_derived_damage_events
        if item.template.template_id == self_child_id
    )
    assert self_child.multiplier.value.value == pytest.approx(3.0)
    self_rule = _rule(definition, "core:cat-gaze:triggerer:character_1491")
    assert CINEMA6_CREATING_ACTIVE in self_rule.condition_ids

    c6_self = _rule(definition, "cinema6:self-crit-and-cat-gaze-state")
    assert CINEMA6_CREATING_ACTIVE in c6_self.condition_ids
    self_cd = next(
        item for item in _modifiers(c6_self)
        if item.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
    )
    assert self_cd.rule.target is EffectTarget.SELF
    assert isinstance(self_cd.result.value, PanelStatDerivedValue)
    assert self_cd.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ATTACK
    assert self_cd.result.value.coefficient.value == pytest.approx(0.0003)
    assert self_cd.result.value.cap_max.value == pytest.approx(1.05)
    guaranteed = next(item for item in c6_self.effects if isinstance(item, GuaranteedCritEffect))
    assert DamageDealerFilter(SUNNA_ID) in guaranteed.rule.filters
    assert DamageTypeFilter(DamageType.DIRECT) in guaranteed.rule.filters

    c6_damage = _modifiers(_rule(definition, "cinema6:cat-gaze-damage-bonus"))[0]
    assert c6_damage.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert _effect_value(c6_damage) == pytest.approx(0.50)
    assert isinstance(c6_damage.rule.filters[0], AnyFilter)
    assert c6_damage.rule.filters[0].filters == (EventTemplateIdFilter(self_child_id),)


def test_cinema_six_markers_remain_ineligible_when_locked(raw_record) -> None:
    _, parsed = raw_record
    definition = compile_sunna(SunnaCompileConfig(cinema_level=5), parsed)
    c6_self = _rule(definition, "cinema6:self-crit-and-cat-gaze-state")
    c6_damage = _rule(definition, "cinema6:cat-gaze-damage-bonus")
    assert c6_self.eligibility is RuleEligibility.INELIGIBLE
    assert c6_self.effects == ()
    assert c6_damage.eligibility is RuleEligibility.INELIGIBLE
    assert c6_damage.effects == ()
    assert not any(item.template.template_id == _cat_gaze_template_id(SUNNA_ID) for item in definition.independent_derived_damage_events)
