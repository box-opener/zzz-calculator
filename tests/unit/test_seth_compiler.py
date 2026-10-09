from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient
import pytest

from core.application import CalculationScenario
from core.application.characters.seth import SethCompileConfig, compile_seth, load_raw_record
from core.application.execution.modifiers import apply_global_panel_effects
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record
from core.application.equipment import load_wengine_raw_record, signature_wengine_id_for
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import compile_registered_definition, config_fields_for
from core.data.wengines.loader import load_wengine_record
from core.types import WEngineId
from web.api import app
from core.types import (
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    EffectTarget,
    Element,
    InitialCharacterSnapshot,
    Resolved,
    SkillGroup,
)
from core.application.characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
)


SETH = CharacterId("character:1271")
NEKO = CharacterId("character:1021")
ANBY = CharacterId("character:1011")
client = TestClient(app)


def _stats(ap: float = 90.0) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(8701.3125),
        attack=Resolved(643.2987),
        defense=Resolved(746.1361),
        impact=Resolved(94.0),
        crit_rate=Resolved(0.05),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(86.0),
        anomaly_proficiency=Resolved(ap),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.56),
        element_damage_bonus={Element.ELECTRIC: Resolved(0.0)},
    )


def _seth_api_payload(entry: str, *, cinema: int = 0, enabled: tuple[str, ...] = ()) -> dict:
    return {
        "primary_character_id": str(SETH),
        "supporting_character_ids": [],
        "team_character_ids": [str(SETH)],
        "formation_character_ids": [str(SETH)],
        "move_entry_id": f"move-entry:character:1271:{entry}",
        "compile_configs": {str(SETH): {"core_level": 7, "cinema_level": cinema}},
        "condition_values": {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            str(SETH): {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": None,
                "drive_discs": [],
            }
        },
        "enemy": {
            "enemy_id": "enemy:seth-full-shock",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"physical": 0.0, "electric": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
    }


def test_seth_live_source_registration_and_reviewed_damage_scope() -> None:
    raw = load_raw_record(load_character_record(str(SETH)))
    definition = compile_seth(SethCompileConfig(), raw)

    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1271.json"
    assert raw.name == "赛斯" and raw.code_name == "Seth" and raw.rarity == 3
    assert raw.icon == "IconRole30"
    assert definition.role.value == "defense"
    assert definition.base_element is Element.ELECTRIC
    legacy_c6_rule = next(
        item for item in definition.rule_items
        if str(item.rule_id) == "rule:character:1271:cinema6:basic-shock-extra"
    )
    assert legacy_c6_rule.eligibility is RuleEligibility.INELIGIBLE
    assert legacy_c6_rule.effects == ()

    catalog_item = next(
        item for item in supported_character_catalog() if item.character_id == str(SETH)
    )
    assert (catalog_item.rarity, catalog_item.specialty, catalog_item.element) == (
        "A",
        "defense",
        "electric",
    )
    assert signature_wengine_id_for(SETH) == WEngineId("wengine:13127")
    engine = load_wengine_raw_record("wengine:13127")
    assert engine.name == "维序者-特化型"
    assert load_wengine_record("wengine:13127")["raw_nanoka_detail"]["code_name"] == "Weapon_A_1271"
    fields = config_fields_for(str(SETH), {}, (SETH, NEKO))
    assert all(field.value == 16 for field in fields if field.field_id.startswith("skill_level:"))
    assert not any(field.field_id == "potential_level" for field in fields)

    templates = {item.ref.template_id: item for item in definition.damage_event_templates}
    by_key = {str(item.entry_id): item for item in definition.move_entries}
    assert any("dash-attack" in key for key in by_key)
    assert any("dodge-counter" in key for key in by_key)
    assert any("quick-assist" in key for key in by_key)
    assert any("assist-strike" in key for key in by_key)
    assert any("ultimate" in key for key in by_key)
    shock_full = next(
        item for item in definition.move_entries if str(item.entry_id).endswith("basic-shock-full")
    )
    assert shock_full.derived_damage_events == ()
    full_template = templates[shock_full.main_damage_event.template_id]
    assert isinstance(full_template, DirectDamageEventTemplate)
    assert full_template.element is Element.ELECTRIC
    assert full_template.move_id == shock_full.move_id
    raw_shock = next(item for item in raw.moves if item.name == "普通攻击：雷霆击-感电")
    continuous_curve = next(item for item in raw_shock.parameters if item.name == "连续攻击伤害倍率")
    finisher_curve = next(item for item in raw_shock.parameters if item.name == "终结一击伤害倍率")
    expected_total = (
        continuous_curve.value_for_level(16, "1271005")
        + finisher_curve.value_for_level(16, "1271006")
    ) / 100
    assert shock_full.multiplier_variants[0].multiplier.value == Resolved(expected_total)

    dash_entry = next(item for item in definition.move_entries if "dash-attack" in str(item.entry_id))
    dash_template = templates[dash_entry.main_damage_event.template_id]
    assert isinstance(dash_template, DirectDamageEventTemplate)
    assert dash_template.element is Element.PHYSICAL
    assert dash_template.ref.damage_tags == frozenset({DamageTag.DASH_ATTACK})

    counter_entry = next(item for item in definition.move_entries if "dodge-counter" in str(item.entry_id))
    counter_template = templates[counter_entry.main_damage_event.template_id]
    assert isinstance(counter_template, DirectDamageEventTemplate)
    assert counter_template.element is Element.ELECTRIC
    assert counter_template.ref.damage_tags == frozenset({DamageTag.DODGE_COUNTER})

    basic_stages = [item for item in definition.move_entries if "basic-stage-" in str(item.entry_id)]
    assert len(basic_stages) == 4
    expected_basic = (0.857, 1.345, 4.573, 2.309)
    expected_elements = (Element.PHYSICAL, Element.PHYSICAL, Element.PHYSICAL, Element.ELECTRIC)
    for entry, expected_ratio, expected_element in zip(basic_stages, expected_basic, expected_elements):
        assert entry.multiplier_relation.value == "sequential-stage"
        assert entry.multiplier_variants[0].multiplier.value == Resolved(expected_ratio)
        template = templates[entry.main_damage_event.template_id]
        assert isinstance(template, DirectDamageEventTemplate)
        assert template.element is expected_element
        assert entry.main_damage_event.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert not any(
        isinstance(template, AttributeAnomalyDamageEventTemplate)
        and template.element is Element.PHYSICAL
        for template in definition.damage_event_templates
    )


def test_seth_shield_ap_is_owned_by_seth_and_applied_to_each_named_off_field_holder() -> None:
    registered = compile_registered_definition(
        str(SETH),
        {"core_level": 7, "cinema_level": 0},
        (SETH, NEKO, ANBY),
    )
    assert {item.label for item in registered.scenario_conditions} == {
        "赛斯当前持有匪石之盾",
        "猫又当前持有匪石之盾",
        "安比当前持有匪石之盾",
    }

    raw = load_raw_record(load_character_record(str(SETH)))
    definition = compile_seth(
        SethCompileConfig(shield_recipient_ids=(SETH, NEKO, ANBY)),
        raw,
    )
    shield_rules = tuple(
        item
        for item in definition.rule_items
        if item.rule_id.startswith("rule:character:1271:core:shield-holder-ap:")
    )
    assert len(shield_rules) == 3
    assert all(item.owner == SETH for item in shield_rules)
    assert all(item.effects[0].rule.owner == SETH for item in shield_rules)
    assert all(item.effects[0].rule.target is EffectTarget.RECIPIENT for item in shield_rules)
    assert {
        item.effects[0].rule.recipient_character_id for item in shield_rules
    } == {SETH, NEKO, ANBY}
    assert all(item.effects[0].result.value == Resolved(100.0) for item in shield_rules)

    base = tuple(CharacterSnapshot(actor, 60, _stats()) for actor in (SETH, NEKO, ANBY))
    initial = tuple(InitialCharacterSnapshot(actor, 60, _stats()) for actor in (SETH, NEKO, ANBY))
    rule_by_recipient = {
        item.effects[0].rule.recipient_character_id: item for item in shield_rules
    }
    enabled = frozenset(rule.rule_id for rule in shield_rules)
    conditions = tuple(
        replace(
            condition,
            value=str(condition.condition_id).endswith(str(NEKO).replace(":", "-"))
            or str(condition.condition_id).endswith(str(ANBY).replace(":", "-")),
        )
        for condition in definition.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="scenario:seth:shield-holders",
        current_operator=SETH,
        conditions=conditions,
        enabled_rule_item_ids=enabled,
    )
    result = apply_global_panel_effects(
        base,
        initial,
        shield_rules,
        scenario,
        team_character_ids=frozenset({SETH, NEKO, ANBY}),
    )
    by_actor = {item.character_id: item.settlement_stats for item in result.character_snapshots}
    assert by_actor[SETH].anomaly_proficiency == Resolved(90.0)
    assert by_actor[NEKO].anomaly_proficiency == Resolved(190.0)
    assert by_actor[ANBY].anomaly_proficiency == Resolved(190.0)
    assert {trace.recipient_character_id for trace in result.panel_traces} == {NEKO, ANBY}
    assert set(rule_by_recipient) == {SETH, NEKO, ANBY}


def test_seth_c6_extra_is_electric_guaranteed_crit_basic_and_scoped_to_child() -> None:
    raw = load_raw_record(load_character_record(str(SETH)))
    definition = compile_seth(SethCompileConfig(cinema_level=6), raw)
    c6_entry = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith("cinema6-basic-shock-extra")
    )
    standalone = next(
        item
        for item in definition.damage_event_templates
        if item.ref.template_id == c6_entry.main_damage_event.template_id
    )
    assert isinstance(standalone, DirectDamageEventTemplate)
    assert standalone.element is Element.ELECTRIC
    assert standalone.ref.skill_group is SkillGroup.BASIC_ATTACK
    assert standalone.ref.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert standalone.move_id is None
    assert standalone.crit_rule.guaranteed is True

    child_templates = tuple(
        item
        for item in definition.damage_event_templates
        if str(item.ref.template_id).startswith("template:character:1271:cinema6:basic-shock-extra:")
    )
    assert len(child_templates) == 2
    assert all(isinstance(item, DirectDamageEventTemplate) for item in child_templates)
    assert all(item.element is Element.ELECTRIC for item in child_templates)
    assert all(item.ref.skill_group is SkillGroup.BASIC_ATTACK for item in child_templates)
    assert all(item.ref.damage_tags == frozenset({DamageTag.BASIC_ATTACK}) for item in child_templates)
    assert all(item.move_id is None and item.crit_rule.guaranteed for item in child_templates)
    assert {
        len(item.derived_damage_events)
        for item in definition.move_entries
        if str(item.entry_id).endswith(("basic-shock-finisher", "basic-shock-full"))
    } == {1}

    c6_rule = next(
        item
        for item in definition.rule_items
        if str(item.rule_id).endswith("cinema6:basic-shock-extra")
    )
    assert c6_rule.eligibility is RuleEligibility.ELIGIBLE
    assert len(c6_rule.effects) == 3
    crit_damage_effect = next(
        item
        for item in c6_rule.effects
        if getattr(item, "result", None) is not None
        and getattr(item.result, "modifier_path", None) is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
    )
    assert crit_damage_effect.rule.owner == SETH
    assert crit_damage_effect.result.value == Resolved(0.60)


def test_seth_basic_shock_full_query_sums_both_source_curves_and_c6_adds_one_child() -> None:
    stage1_response = client.post(
        "/api/v1/moves/calculate",
        json=_seth_api_payload("basic-stage-1-element-unresolved"),
    )
    assert stage1_response.status_code == 200, stage1_response.text
    stage1 = stage1_response.json()
    assert stage1["totals"]["expected"]["complete"] is True
    assert len(stage1["events"]) == 1
    assert stage1["events"][0]["element"] == "physical"
    assert stage1["events"][0]["modes"]["expected"]["calculation_breakdown"]
    assert any(
        item["node"] == "damage.skill-multiplier" and item["value"] == pytest.approx(0.857)
        for item in stage1["events"][0]["modes"]["expected"]["calculation_breakdown"]
    )

    stage4_response = client.post(
        "/api/v1/moves/calculate",
        json=_seth_api_payload("basic-stage-4-element-unresolved"),
    )
    assert stage4_response.status_code == 200, stage4_response.text
    stage4 = stage4_response.json()
    assert stage4["totals"]["expected"]["complete"] is True
    assert len(stage4["events"]) == 1
    assert stage4["events"][0]["element"] == "electric"
    assert all(event["damage_type"] != "anomaly" for event in stage4["events"])

    full = client.post(
        "/api/v1/moves/calculate",
        json=_seth_api_payload("basic-shock-full"),
    )
    assert full.status_code == 200, full.text
    full_result = full.json()
    assert full_result["totals"]["expected"]["complete"] is True
    assert full_result["totals"]["expected"]["value"] == pytest.approx(6050.459227537613)
    assert len(full_result["events"]) == 1
    assert full_result["events"][0]["modes"]["expected"]["calculation_breakdown"]

    c6 = client.post(
        "/api/v1/moves/calculate",
        json=_seth_api_payload(
            "basic-shock-full",
            cinema=6,
            enabled=("rule:character:1271:cinema6:basic-shock-extra",),
        ),
    )
    assert c6.status_code == 200, c6.text
    c6_result = c6.json()
    assert c6_result["totals"]["expected"]["complete"] is True
    assert len(c6_result["events"]) == 2
    assert c6_result["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        full_result["events"][0]["modes"]["expected"]["value"]
    )
    child = c6_result["events"][1]
    assert child["element"] == "electric"
    assert child["crit_capability"] == "standard"

    standalone = client.post(
        "/api/v1/moves/calculate",
        json=_seth_api_payload(
            "cinema6-basic-shock-extra",
            cinema=6,
            enabled=("rule:character:1271:cinema6:basic-shock-extra",),
        ),
    )
    assert standalone.status_code == 200, standalone.text
    assert standalone.json()["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        child["modes"]["expected"]["value"]
    )
