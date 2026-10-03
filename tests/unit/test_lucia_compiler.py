from __future__ import annotations

from pathlib import Path

import pytest

from core.application.characters.lucia import (
    LUCIA_ID,
    LUCIA_REVIEWED_MAPPING,
    LuciaCompileConfig,
    compile_lucia,
    load_raw_record,
)
from core.application.rules import RuleEligibility
from core.application.diagnostics import DiagnosticKind
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    DamageTag,
    DamageType,
    Element,
)


LUCIA = str(LUCIA_ID)
YIXUAN = "character:1371"
ASTRA = "character:1311"
ULTIMATE_ENTRY = "move-entry:character:1451:ultimate-charge-armor-finisher"
EX_CHORUS_ENTRY = "move-entry:character:1451:ex-special-dawn-chorus"
ANOMALY_ENTRY = "move-entry:character:1451:ether-anomaly"
DISORDER_ENTRY = "move-entry:character:1451:ether-disorder"


def _stats(
    element: str = "ether",
    *,
    hp: float = 20000.0,
    attack: float = 600.0,
    crit_rate: float = 0.05,
    crit_damage: float = 0.50,
    element_bonus: float = 0.20,
) -> dict[str, object]:
    return {
        "hp": hp,
        "attack": attack,
        "defense": 500.0,
        "impact": 83.0,
        "anomaly_mastery": 96.0,
        "anomaly_proficiency": 95.0,
        "energy_regen": 1.56,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: element_bonus},
    }


def _drive_discs():
    def substats(*keys: str):
        return [{"stat": key, "roll_count": 2} for key in keys]

    return [
        {"slot": 1, "set_id": "drive-disc:31000", "main_stat": "hp-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 2, "set_id": "drive-disc:31000", "main_stat": "attack-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 3, "set_id": "drive-disc:31000", "main_stat": "defense-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 4, "set_id": "drive-disc:31000", "main_stat": "attack-percent", "substats": substats("crit-rate", "crit-damage", "anomaly-proficiency-flat", "penetration-flat")},
        {"slot": 5, "set_id": "drive-disc:31000", "main_stat": "ether-damage-bonus", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 6, "set_id": "drive-disc:31000", "main_stat": "hp-percent", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
    ]


def _payload(
    *,
    primary: str = LUCIA,
    supporting: tuple[str, ...] = (),
    move_entry_id: str = "move-entry:character:1451:basic-star-rail-1",
    core_level: int = 1,
    cinema_level: int = 0,
    skill_levels: dict[str, int] | None = None,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    parameter_values: dict[str, int] | None = None,
    initial_defense: float = 1000.0,
    is_stunned: bool = False,
    manual_stats: dict[str, dict[str, object]] | None = None,
    equipment_build: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == LUCIA:
            configs[character_id] = {"core_level": core_level, "cinema_level": cinema_level}
            if skill_levels:
                configs[character_id]["skill_levels"] = skill_levels
            builds[character_id] = (
                {"level": 60, "build_mode": "equipment-build", "drive_discs": _drive_discs()}
                if equipment_build
                else {"level": 60, "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats())}
            )
        elif character_id == YIXUAN:
            configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {"level": 60, "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats(hp=12000.0, attack=1000.0, crit_rate=0.70, crit_damage=1.10, element_bonus=0.40))}
        elif character_id == ASTRA:
            configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {"level": 60, "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats(hp=10000.0, attack=800.0, crit_rate=0.30, crit_damage=0.30, element_bonus=0.0))}
        else:
            raise AssertionError(f"no Lucia test build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:lucia-test",
            "level": 60,
            "initial_defense": initial_defense,
            "damage_resistance": {"ether": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": is_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _event(result, semantic_id: str | None = None):
    events = result["events"]
    return next(item for item in events if item["semantic_id"] == semantic_id) if semantic_id else events[0]


def _breakdown(event, mode: str = "expected"):
    return event["modes"][mode]["calculation_breakdown"]


def _node(event, name: str, mode: str = "expected"):
    return next(item for item in _breakdown(event, mode) if item["node"] == name)


def _modifier(event, effect_id: str):
    return next(
        item
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["effect_id"] == effect_id
    )


def _lucia_raw():
    return load_raw_record(load_character_record(LUCIA))


def test_lucia_live_raw_mapping_base_panel_and_equipment_registration() -> None:
    raw = _lucia_raw()
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1451.json"
    assert raw.character_id == LUCIA_ID
    assert raw.name == "卢西娅"
    assert raw.specialty == "支援"
    assert raw.element == "以太"
    assert raw.rarity == 4
    assert LUCIA in supported_character_ids()

    mapped = {
        (spec.source_name, parameter.parameter_name, parameter.source_skill_id)
        for spec in LUCIA_REVIEWED_MAPPING.moves
        for parameter in spec.parameters
    }
    raw_damage_curves = {
        (move.name, parameter.name, source_skill_id)
        for move in raw.moves
        for parameter in move.parameters
        if parameter.format == "%" and "伤害倍率" in parameter.name
        for source_skill_id, _curve in parameter.source_curves
    }
    from core.application.characters.lucia.reviewed import (
        LUCIA_ADDITIONAL_ATTACK_CURVES,
    )

    unresolved_candidates = {
        (source_name, "追加攻击伤害倍率", source_skill_id)
        for source_name, source_skill_id in LUCIA_ADDITIONAL_ATTACK_CURVES
    }
    derived_curve = {
        ("终结技：进击，大铠甲！", "突进单次撞击伤害倍率", "1451024")
    }
    assert raw_damage_curves == mapped | unresolved_candidates | derived_curve
    assert not any("招架支援：幻梦之声" in item.source_name for item in LUCIA_REVIEWED_MAPPING.moves)

    registration = registration_for(LUCIA)
    assert registration.role.value == "support"
    assert registration.base_element is Element.ETHER
    assert registration.catalog.rarity == "S"
    assert registration.equipment_capabilities.possible_elements == {Element.ETHER}
    assert (Path(__file__).parents[2] / "frontend" / "public" / "characters" / "IconRole50.webp").is_file()

    base = character_base_stats(LUCIA)
    assert base.hp.value == pytest.approx(8477.1696)
    assert base.attack.value == pytest.approx(758.2048)
    assert base.energy_regen.value == pytest.approx(1.56)
    assert base.anomaly_mastery.value == pytest.approx(96.0)
    assert base.anomaly_proficiency.value == pytest.approx(95.0)
    fields = config_fields_for(LUCIA, {"core_level": 6, "cinema_level": 4}, (LUCIA,))
    assert {field.field_id for field in fields} >= {"core_level", "cinema_level", "skill_level:ultimate"}


def test_unmodeled_non_damage_resources_are_diagnosed_without_blocking_damage() -> None:
    definition = compile_lucia(LuciaCompileConfig(cinema_level=6), _lucia_raw())
    rule_diagnostics = {
        str(rule.rule_id): rule.diagnostics for rule in definition.rule_items
    }
    for rule_id in (
        "rule:character:1451:cinema1:dream-song-resistance-ignore",
        "rule:character:1451:cinema4:curtain-decibel",
        "rule:character:1451:ex-special:break-dark-penetration-force",
    ):
        diagnostics = rule_diagnostics[rule_id]
        assert diagnostics
        assert all(not item.blocking for item in diagnostics)
        assert all(item.kind in {DiagnosticKind.UNSUPPORTED_CALCULATOR, DiagnosticKind.MISSING_DATA} for item in diagnostics)


def test_lucia_direct_damage_uses_raw_skill_curve_and_real_crit_modes() -> None:
    result = calculate_payload(_payload())
    event = _event(result)
    assert event["damage_type"] == DamageType.DIRECT.value
    assert _node(event, "damage.skill-multiplier")["value"] == pytest.approx(0.827)
    assert event["modes"]["expected"]["known_value"] is not None
    assert event["modes"]["non-crit"]["known_value"] < event["modes"]["expected"]["known_value"]
    assert event["modes"]["expected"]["known_value"] < event["modes"]["full-crit"]["known_value"]


def test_dream_song_is_a_team_damage_modifier_and_curtain_changes_current_hp() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            core_level=7,
            condition_values={
                "condition:lucia:dream-song-active": True,
                "condition:lucia:spring-curtain-active": True,
            },
            enabled_rule_item_ids=(
                "rule:character:1451:core:dream-song-team-damage",
                "rule:character:1451:core:ether-curtain-team-hp",
            ),
        )
    )
    event = _event(result)
    assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.20)
    assert _node(event, "character.current.max-hp")["value"] == pytest.approx(12600.0)
    assert _node(event, "penetration.force")["value"] == pytest.approx(1510.0)
    assert _modifier(event, "effect:character:1451:core:dream-song-team-damage")["value"] == pytest.approx(0.20)


@pytest.mark.parametrize(("core_level", "expected_bonus"), ((1, 0.10), (4, 0.15), (7, 0.20)))
def test_lucia_core_dream_song_damage_bonus_uses_selected_core_level(
    core_level: int,
    expected_bonus: float,
) -> None:
    result = calculate_payload(
        _payload(
            core_level=core_level,
            condition_values={"condition:lucia:dream-song-active": True},
            enabled_rule_item_ids=("rule:character:1451:core:dream-song-team-damage",),
        )
    )
    assert _node(_event(result), "damage.normal-bonus")["value"] == pytest.approx(expected_bonus)


@pytest.mark.parametrize(
    ("lucia_initial_hp", "expected_force_bonus"),
    ((20000.0, 752.0), (20001.0, 752.037), (24000.0, 900.0), (30000.0, 900.0)),
)
def test_break_dark_penetration_uses_lucia_initial_hp_not_curtain_current_hp(
    lucia_initial_hp: float,
    expected_force_bonus: float,
) -> None:
    manual_stats = {
        YIXUAN: _stats(hp=12000.0, attack=1000.0, crit_rate=0.70, crit_damage=1.10, element_bonus=0.0),
        LUCIA: _stats(hp=lucia_initial_hp, attack=600.0, crit_rate=0.05, crit_damage=0.5, element_bonus=0.0),
    }
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            core_level=7,
            skill_levels={"special-attack": 12},
            condition_values={
                "condition:lucia:spring-curtain-active": True,
                "condition:lucia:break-dark-active": True,
            },
            enabled_rule_item_ids=(
                "rule:character:1451:core:ether-curtain-team-hp",
                "rule:character:1451:ex-special:break-dark-penetration-force",
            ),
            manual_stats=manual_stats,
        )
    )
    event = _event(result)
    assert _node(event, "character.current.max-hp")["value"] == pytest.approx(12600.0)
    assert _node(event, "penetration.force-bonus")["value"] == pytest.approx(expected_force_bonus)
    assert _node(event, "penetration.force")["value"] == pytest.approx(1510.0 + expected_force_bonus)
    assert sum(
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["modifier_path"] == "penetration.force-bonus"
    ) == pytest.approx(expected_force_bonus)


@pytest.mark.parametrize(
    "entry_key",
    (
        "basic-whim-fifth",
        "dodge-counter-whim",
        "special-whim-storm",
        "quick-assist-whim",
    ),
)
def test_whim_variants_do_not_get_chorus_hp_or_cinema_bonuses(entry_key: str) -> None:
    result = calculate_payload(
        _payload(
            move_entry_id=f"move-entry:character:1451:{entry_key}",
            cinema_level=6,
            condition_values={
                "condition:lucia:dream-active": False,
                "condition:lucia:dream-inactive": True,
                "condition:lucia:any-ether-curtain-active": True,
                "condition:lucia:spring-curtain-active": True,
            },
            enabled_rule_item_ids=(
                "rule:character:1451:ex-special:chorus-hp-final-hit",
                "rule:character:1451:cinema2:chorus-damage-in-spring-curtain",
                "rule:character:1451:cinema6:veil-chorus-crit-and-attack",
            ),
        )
    )
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.0)
    assert event["common_application_trace"]["guaranteed_crit_effect_ids"] == []
    assert event["common_application_trace"]["event_stat_modifiers"] == []


@pytest.mark.parametrize(
    ("entry_key", "component_key", "component_effect_id"),
    (
        ("basic-chorus-fifth", "basic-chorus-fifth-hp", "effect:character:1451:chorus-hp-final-hit:basic-chorus-fifth-hp"),
        ("dodge-counter-chorus", "dodge-counter-chorus-hp", "effect:character:1451:chorus-hp-final-hit:dodge-counter-chorus-hp"),
        ("special-chorus-storm", "special-chorus-hp", "effect:character:1451:chorus-hp-final-hit:special-chorus-hp"),
        ("ex-special-dawn-chorus", "ex-special-chorus-hp-final-hit", "effect:character:1451:ex-special:chorus-hp-final-hit"),
        ("chain-gleaming-theater-chorus", "chain-chorus-hp", "effect:character:1451:chorus-hp-final-hit:chain-chorus-hp"),
        ("ultimate-charge-armor-finisher", "ultimate-chorus-hp-finisher", "effect:character:1451:chorus-hp-final-hit:ultimate-chorus-hp-finisher"),
        ("quick-assist-chorus", "quick-assist-chorus-hp", "effect:character:1451:chorus-hp-final-hit:quick-assist-chorus-hp"),
        ("assist-follow-up-chorus", "support-follow-up-chorus-hp", "effect:character:1451:chorus-hp-final-hit:support-follow-up-chorus-hp"),
    ),
)
def test_each_chorus_gets_one_hp_component_with_its_parent_identity(
    entry_key: str,
    component_key: str,
    component_effect_id: str,
) -> None:
    rule_ids = [
        "rule:character:1451:ex-special:chorus-hp-final-hit",
        "rule:character:1451:core:ether-curtain-team-hp",
        "rule:character:1451:cinema2:chorus-damage-in-spring-curtain",
        "rule:character:1451:cinema6:veil-chorus-crit-and-attack",
    ]
    parameters = {}
    result = calculate_payload(
        _payload(
            move_entry_id=f"move-entry:character:1451:{entry_key}",
            cinema_level=6,
            skill_levels={"special-attack": 8},
            condition_values={
                "condition:lucia:dream-active": True,
                "condition:lucia:dream-inactive": False,
                "condition:lucia:any-ether-curtain-active": True,
                "condition:lucia:spring-curtain-active": True,
            },
            enabled_rule_item_ids=tuple(rule_ids),
            parameter_values=parameters,
            manual_stats={LUCIA: _stats(hp=24000.0, attack=600.0)},
        )
    )
    definition = compile_lucia(LuciaCompileConfig(cinema_level=6), _lucia_raw())
    entry = next(item for item in definition.move_entries if str(item.entry_id).endswith(entry_key))
    main_template = next(
        item for item in definition.damage_event_templates
        if item.ref.template_id == entry.main_damage_event.template_id
    )
    component_template = next(
        item for item in definition.damage_event_templates
        if str(item.ref.template_id) == f"template:character:1451:{component_key}"
    )
    assert component_template.move_id == main_template.move_id
    assert component_template.ref.skill_group is main_template.ref.skill_group
    assert component_template.ref.damage_tags == main_template.ref.damage_tags

    assert len(result["events"]) == 2
    hp_children = [
        item for item in result["events"]
        if item["common_application_trace"]["created_by_effect_id"] == component_effect_id
    ]
    assert len(hp_children) == 1
    child = hp_children[0]
    assert _node(child, "character.current.max-hp")["value"] == pytest.approx(25200.0)
    assert _node(child, "damage.skill-multiplier")["value"] == pytest.approx(0.70)
    assert _node(child, "damage.base-value")["value"] == pytest.approx(17640.0)
    for event in result["events"]:
        if event["damage_type"] != "direct":
            continue
        assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.15)
        assert event["common_application_trace"]["guaranteed_crit_effect_ids"] == [
            "effect:character:1451:cinema6:chorus-guaranteed-crit"
        ]
        assert any(
            item["effect_id"] == "effect:character:1451:cinema6:chorus-crit-damage"
            for item in event["common_application_trace"]["event_stat_modifiers"]
        )
    assert result["totals"]["expected"]["complete"] is True


def test_lucia_mindscapes_scope_chorus_resistance_and_penetration_effects() -> None:
    c2_chorus = "rule:character:1451:cinema2:chorus-damage-in-spring-curtain"
    chorus = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1451:basic-chorus-fifth",
            cinema_level=2,
            condition_values={
                "condition:lucia:dream-active": True,
                "condition:lucia:dream-inactive": False,
                "condition:lucia:spring-curtain-active": True,
            },
            enabled_rule_item_ids=(c2_chorus,),
        )
    )
    assert _node(_event(chorus), "damage.normal-bonus")["value"] == pytest.approx(0.15)

    ordinary = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1451:basic-star-rail-1",
            cinema_level=2,
            condition_values={
                "condition:lucia:dream-active": True,
                "condition:lucia:dream-inactive": False,
                "condition:lucia:spring-curtain-active": True,
            },
            enabled_rule_item_ids=(c2_chorus,),
        )
    )
    assert _node(_event(ordinary), "damage.normal-bonus")["value"] == pytest.approx(0.0)

    c1 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1451:basic-star-rail-1",
            cinema_level=1,
            condition_values={"condition:lucia:dream-song-active": True},
            enabled_rule_item_ids=("rule:character:1451:cinema1:dream-song-resistance-ignore",),
        )
    )
    assert _node(_event(c1), "resistance.damage-ignore")["value"] == pytest.approx(0.18)
    assert _node(_event(c1), "resistance.region")["value"] == pytest.approx(0.98)

    yixuan_penetration = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            cinema_level=2,
            condition_values={
                "condition:lucia:spring-curtain-active": True,
                "condition:lucia:break-dark-active": True,
            },
            enabled_rule_item_ids=("rule:character:1451:cinema2:break-dark-penetration-damage",),
        )
    )
    assert _node(_event(yixuan_penetration), "penetration.damage-bonus")["value"] == pytest.approx(0.15)


@pytest.mark.parametrize(("spring_curtain", "expected_current_hp", "expected_final_hit"), ((False, 24000.0, 16800.0), (True, 25200.0, 17640.0)))
def test_ex_chorus_hp_component_uses_full_current_max_hp_fraction(
    spring_curtain: bool,
    expected_current_hp: float,
    expected_final_hit: float,
) -> None:
    manual_stats = {
        LUCIA: _stats(hp=24000.0, attack=600.0),
    }
    enabled_rules = ["rule:character:1451:ex-special:chorus-hp-final-hit"]
    if spring_curtain:
        enabled_rules.append("rule:character:1451:core:ether-curtain-team-hp")
    result = calculate_payload(
        _payload(
            move_entry_id=EX_CHORUS_ENTRY,
            skill_levels={"special-attack": 12},
            condition_values={"condition:lucia:spring-curtain-active": spring_curtain},
            enabled_rule_item_ids=tuple(enabled_rules),
            manual_stats=manual_stats,
        )
    )
    main, extra = result["events"]
    assert _node(main, "character.current.attack")["value"] == pytest.approx(600.0)
    assert _node(extra, "character.current.max-hp")["value"] == pytest.approx(expected_current_hp)
    assert _node(extra, "damage.skill-multiplier")["value"] == pytest.approx(0.70)
    assert _node(extra, "damage.base-value")["value"] == pytest.approx(expected_final_hit)


def test_lucia_additional_attack_requires_current_operator_attack_and_excludes_lucia() -> None:
    rule_id = "rule:character:1451:core:additional-attack"
    core_followup_template = next(
        item for item in compile_lucia(LuciaCompileConfig(), load_raw_record(load_character_record(LUCIA))).damage_event_templates
        if str(item.ref.template_id) == "template:character:1451:core:additional-attack"
    )
    assert core_followup_template.damage_dealer == LUCIA
    assert core_followup_template.element is Element.ETHER
    assert core_followup_template.move_id is None
    assert core_followup_template.ref.skill_group is None
    assert core_followup_template.ref.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})
    active_conditions = {
        "condition:lucia:dream-active": True,
        "condition:lucia:dream-inactive": False,
        "condition:lucia:additional-attack-ready": True,
    }
    for primary, supporting, move_entry_id in (
        (YIXUAN, (LUCIA,), "move-entry:character:1371:basic-xiaoyun-jin-1"),
        (ASTRA, (LUCIA,), "move-entry:astra:1311:basic-rhapsody-1"),
    ):
        result = calculate_payload(
            _payload(
                primary=primary,
                supporting=supporting,
                move_entry_id=move_entry_id,
                condition_values=active_conditions,
                enabled_rule_item_ids=(rule_id,),
            )
        )
        assert len(result["events"]) == 2
        rule_match = next(
            item
            for item in result["events"][0]["common_application_trace"]["rule_matches"]
            if item["rule_id"] == rule_id
        )
        assert rule_match["effects"][0]["status"] == "matched"
        assert result["totals"]["expected"]["complete"] is True
        child = result["events"][1]
        assert child["damage_type"] == "direct"
        assert _node(child, "damage.skill-multiplier")["value"] == pytest.approx(11.0)

    lucia_own_attack = calculate_payload(
        _payload(
            primary=LUCIA,
            supporting=(YIXUAN,),
            move_entry_id="move-entry:character:1451:basic-star-rail-1",
            condition_values=active_conditions,
            enabled_rule_item_ids=(rule_id,),
        )
    )
    own_rule_match = next(
        item
        for item in lucia_own_attack["events"][0]["common_application_trace"]["rule_matches"]
        if item["rule_id"] == rule_id
    )
    assert own_rule_match["effects"][0]["status"] == "not-matched"
    assert lucia_own_attack["totals"]["expected"]["complete"] is True
    assert not any(
        item["diagnostic_id"].endswith(":unresolved-template")
        for item in lucia_own_attack["totals"]["expected"]["diagnostics"]
    )


def test_lucia_c6_applies_to_off_operator_chorus_followup_without_skill_group() -> None:
    c6_rule = "rule:character:1451:cinema6:veil-chorus-crit-and-attack"
    core_rule = "rule:character:1451:core:additional-attack"
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            cinema_level=6,
            condition_values={
                "condition:lucia:dream-active": True,
                "condition:lucia:dream-inactive": False,
                "condition:lucia:additional-attack-ready": True,
                "condition:lucia:any-ether-curtain-active": True,
            },
            enabled_rule_item_ids=(core_rule, c6_rule),
        )
    )
    assert result["totals"]["expected"]["complete"] is True
    child = result["events"][1]
    trace = child["common_application_trace"]
    assert trace["guaranteed_crit_effect_ids"] == [
        "effect:character:1451:cinema6:chorus-guaranteed-crit"
    ]
    assert any(
        item["effect_id"] == "effect:character:1451:cinema6:chorus-crit-damage"
        and item["value"] == pytest.approx(0.30)
        for item in trace["event_stat_modifiers"]
    )
    modes = child["modes"]
    assert modes["expected"]["value"] == pytest.approx(modes["full-crit"]["value"])
    assert modes["non-crit"]["value"] == pytest.approx(modes["expected"]["value"])


def test_lucia_followup_instances_are_unique_per_source_hit() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xuanmo-array",
            condition_values={
                "condition:lucia:dream-active": True,
                "condition:lucia:dream-inactive": False,
                "condition:lucia:additional-attack-ready": True,
            },
            enabled_rule_item_ids=(
                "rule:character:1371:followup:basic-array-qingming-shock",
                "rule:character:1451:core:additional-attack",
            ),
        )
    )
    assert result["totals"]["expected"]["complete"] is True
    followups = [
        item for item in result["events"]
        if item["semantic_id"].startswith(
            "event:character:1451:core:additional-attack:source:"
        )
    ]
    assert len(followups) == 2
    assert followups[0]["semantic_id"] != followups[1]["semantic_id"]


def test_lucia_additional_ability_eligibility_and_team_break_dark_panel_buff() -> None:
    values = {"core_level": 1, "cinema_level": 0}
    solo = compile_registered_definition(LUCIA, values, (LUCIA,))
    with_rupture = compile_registered_definition(LUCIA, values, (LUCIA, YIXUAN))
    rule_id = "rule:character:1451:extra-ability:break-dark-team-crit-damage"
    solo_rule = next(item for item in solo.rule_items if str(item.rule_id) == rule_id)
    eligible_rule = next(item for item in with_rupture.rule_items if str(item.rule_id) == rule_id)
    assert solo_rule.eligibility is RuleEligibility.INELIGIBLE
    assert eligible_rule.eligibility is RuleEligibility.ELIGIBLE

    with_break_dark = calculate_payload(
        _payload(
            supporting=(YIXUAN,),
            condition_values={"condition:lucia:break-dark-active": True},
            enabled_rule_item_ids=(rule_id,),
        )
    )
    snapshots = {
        item["character_id"]: item["stats"]
        for item in with_break_dark["resolved_character_snapshots"]
    }
    assert snapshots[LUCIA]["crit_damage"] == pytest.approx(0.80)
    assert snapshots[YIXUAN]["crit_damage"] == pytest.approx(1.40)
    assert {item["recipient_character_id"] for item in with_break_dark["panel_traces"] if item["effect_id"] == "effect:character:1451:extra-ability:break-dark-team-crit-damage"} == {LUCIA, YIXUAN}


def test_lucia_c6_attack_panel_applies_in_any_curtain_even_as_support() -> None:
    manual_stats = {
        YIXUAN: _stats(hp=12000.0, attack=800.0, crit_rate=0.70, crit_damage=1.10),
        LUCIA: _stats(hp=20000.0, attack=600.0, crit_rate=0.05, crit_damage=0.50),
    }
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(LUCIA,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            cinema_level=6,
            condition_values={
                "condition:lucia:any-ether-curtain-active": True,
                "condition:lucia:spring-curtain-active": False,
            },
            enabled_rule_item_ids=("rule:character:1451:cinema6:veil-chorus-crit-and-attack",),
            manual_stats=manual_stats,
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[LUCIA]["attack"] == pytest.approx(1000.0)
    assert snapshots[YIXUAN]["attack"] == pytest.approx(800.0)
    assert result["events"][0]["common_application_trace"]["guaranteed_crit_effect_ids"] == []


def test_lucia_c6_uses_initial_hp_attack_and_scene_controlled_guaranteed_crit() -> None:
    c6_rule = "rule:character:1451:cinema6:veil-chorus-crit-and-attack"
    active = calculate_payload(
        _payload(
            move_entry_id=EX_CHORUS_ENTRY,
            cinema_level=6,
            condition_values={
                "condition:lucia:any-ether-curtain-active": True,
                "condition:lucia:spring-curtain-active": True,
            },
            skill_levels={"special-attack": 12},
            enabled_rule_item_ids=(
                c6_rule,
                "rule:character:1451:core:ether-curtain-team-hp",
                "rule:character:1451:ex-special:chorus-hp-final-hit",
            ),
        )
    )
    ex_event = _event(active)
    child = active["events"][1]
    lucia_snapshot = next(item for item in active["resolved_character_snapshots"] if item["character_id"] == LUCIA)
    assert lucia_snapshot["stats"]["hp"] == pytest.approx(21000.0)
    assert lucia_snapshot["stats"]["attack"] == pytest.approx(1000.0)
    assert _node(child, "character.current.max-hp")["value"] == pytest.approx(21000.0)
    assert _node(child, "damage.skill-multiplier")["value"] == pytest.approx(0.82)
    assert _node(child, "damage.base-value")["value"] == pytest.approx(17220.0)
    assert ex_event["common_application_trace"]["guaranteed_crit_effect_ids"] == [
        "effect:character:1451:cinema6:chorus-guaranteed-crit"
    ]
    assert ex_event["common_application_trace"]["event_stat_modifiers"][0]["effect_id"] == (
        "effect:character:1451:cinema6:chorus-crit-damage"
    )
    assert ex_event["modes"]["non-crit"]["known_value"] == pytest.approx(
        ex_event["modes"]["expected"]["known_value"]
    )
    assert ex_event["modes"]["expected"]["known_value"] == pytest.approx(
        ex_event["modes"]["full-crit"]["known_value"]
    )

    curtain_off = calculate_payload(
        _payload(
            move_entry_id=EX_CHORUS_ENTRY,
            cinema_level=6,
            condition_values={"condition:lucia:any-ether-curtain-active": False},
            enabled_rule_item_ids=(c6_rule,),
        )
    )
    assert _event(curtain_off)["common_application_trace"]["guaranteed_crit_effect_ids"] == []
    assert _event(curtain_off)["modes"]["non-crit"]["known_value"] < _event(curtain_off)["modes"]["expected"]["known_value"]

    c6_off = calculate_payload(
        _payload(
            move_entry_id=EX_CHORUS_ENTRY,
            cinema_level=6,
            condition_values={"condition:lucia:any-ether-curtain-active": True},
            enabled_rule_item_ids=(),
        )
    )
    assert _event(c6_off)["common_application_trace"]["guaranteed_crit_effect_ids"] == []

    whim = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1451:basic-whim-fifth",
            cinema_level=6,
            condition_values={
                "condition:lucia:any-ether-curtain-active": True,
                "condition:lucia:dream-inactive": True,
                "condition:lucia:dream-active": False,
            },
            enabled_rule_item_ids=(c6_rule,),
        )
    )
    assert _event(whim)["common_application_trace"]["guaranteed_crit_effect_ids"] == []


def test_lucia_ultimate_instant_damage_and_single_collision_are_separate_entries() -> None:
    collision_entry = "move-entry:character:1451:ultimate-charge-armor-single-collision"
    instant = calculate_payload(_payload(move_entry_id=ULTIMATE_ENTRY))
    collision = calculate_payload(_payload(move_entry_id=collision_entry))
    assert len(instant["events"]) == len(collision["events"]) == 1
    assert instant["totals"]["expected"]["complete"] is True
    assert collision["totals"]["expected"]["complete"] is True
    instant_event = _event(instant)
    collision_event = _event(collision)
    assert instant_event["semantic_id"] == "event:character:1451:ultimate-charge-armor-finisher:main"
    assert collision_event["semantic_id"] == "event:character:1451:ultimate-rush-hit"
    assert instant_event["repeat_count"] == collision_event["repeat_count"] == 1
    assert _node(instant_event, "damage.skill-multiplier")["value"] == pytest.approx(38.057)
    assert _node(collision_event, "damage.skill-multiplier")["value"] == pytest.approx(1.865)

    hp_rule = "rule:character:1451:ex-special:chorus-hp-final-hit"
    instant_with_hp = calculate_payload(
        _payload(move_entry_id=ULTIMATE_ENTRY, enabled_rule_item_ids=(hp_rule,))
    )
    collision_with_hp = calculate_payload(
        _payload(move_entry_id=collision_entry, enabled_rule_item_ids=(hp_rule,))
    )
    assert len(instant_with_hp["events"]) == 2
    assert len(collision_with_hp["events"]) == 1
    assert collision_with_hp["totals"]["expected"]["complete"] is True
    definition = compile_lucia(LuciaCompileConfig(), _lucia_raw())
    collision_template = next(
        item
        for item in definition.damage_event_templates
        if str(item.ref.template_id) == "template:character:1451:ultimate-rush-hit"
    )
    assert str(collision_template.move_id) == "move:lucia:ultimate-charge-armor-chorus"
    assert collision_template.ref.damage_tags


def test_lucia_static_ether_anomaly_and_disorder_are_not_penetration_damage() -> None:
    anomaly = calculate_payload(_payload(move_entry_id=ANOMALY_ENTRY))
    disorder = calculate_payload(_payload(move_entry_id=DISORDER_ENTRY))
    anomaly_event = _event(anomaly)
    disorder_event = _event(disorder)
    assert anomaly_event["damage_type"] == "anomaly"
    assert anomaly_event["repeat_count"] == 20
    assert _node(anomaly_event, "anomaly.attribute.multiplier")["value"] == pytest.approx(0.625)
    assert _node(disorder_event, "disorder.total-multiplier")["value"] == pytest.approx(17.0)
    assert anomaly_event["modes"]["expected"]["anomaly_effect_strength_trace"]["element"] == "ether"
    for event in (anomaly_event, disorder_event):
        assert not any(item["node"].startswith("penetration.") for item in _breakdown(event))
    assert anomaly["totals"]["expected"]["complete"] is True
    assert disorder["totals"]["expected"]["complete"] is True


def test_lucia_actual_equipment_build_has_level_60_base_energy_panel() -> None:
    result = calculate_payload(_payload(equipment_build=True))
    snapshot = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == LUCIA)
    assert snapshot["stats"]["hp"] > 8477.1696
    assert snapshot["stats"]["attack"] > 758.2048
    assert snapshot["stats"]["energy_regen"] == pytest.approx(1.56)
    assert result["totals"]["expected"]["complete"] is True
