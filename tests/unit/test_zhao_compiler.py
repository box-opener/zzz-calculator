from __future__ import annotations

from pathlib import Path

import pytest

from core.application.characters.zhao import (
    ZHAO_ID,
    ZHAO_REVIEWED_MAPPING,
    ZhaoCompileConfig,
    compile_zhao,
    load_raw_record,
)
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record
from core.presentation.base_stats import (
    character_base_stat_contributions,
    character_base_stats,
)
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    build_registered_build_preview,
    compile_registered_definition,
    registration_for,
)
from core.types import CharacterRole, Element, Unresolved


ZHAO = str(ZHAO_ID)
ASTRA = "character:1311"
YIXUAN = "character:1371"
CORE_CRIT = "rule:character:1341:core:initial-hp-crit-rate"
CORE_HP = "rule:character:1341:core:spring-curtain-team-hp"
CORE_ATTACK = "rule:character:1341:core:spring-curtain-team-attack"
CORE_CHARGE = "rule:character:1341:core:charged-hp-extra"
EXTRA_ABILITY = "rule:character:1341:extra-ability:curtain-team-damage"
C1 = "rule:character:1341:cinema1:team-resistance-ignore"
C2 = "rule:character:1341:cinema2:healing-attack-buffs"
C4 = "rule:character:1341:cinema4:crit-damage-and-decibel"
C6 = "rule:character:1341:cinema6:core-and-charge-multipliers"
SPRING_CURTAIN = "condition:zhao:spring-curtain-active"
CURTAIN_ATTACK = "condition:zhao:spring-curtain-attack-buff-active"
ANY_CURTAIN = "condition:zhao:any-ether-curtain-active"
C1_ACTIVE = "condition:zhao:c1-resistance-ignore-active"
C2_ACTIVE = "condition:zhao:c2-heal-attack-buff-active"
CHARGE_SECONDS = "parameter:zhao:final-judgment-charge-seconds"


def _stats(
    *,
    hp: float = 20_000.0,
    attack: float = 1_000.0,
    element: str = "ice",
    crit_rate: float = 0.20,
    crit_damage: float = 0.50,
    element_bonus: float = 0.20,
) -> dict[str, object]:
    return {
        "hp": hp,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.20,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: element_bonus},
    }


def _payload(
    *,
    move_entry_id: str = "move-entry:character:1341:basic-cold-judgment-1",
    core_level: int = 1,
    cinema_level: int = 0,
    primary: str = ZHAO,
    supporting: tuple[str, ...] = (),
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    character_stats: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    team = (primary, *supporting)
    compile_configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == ZHAO:
            compile_configs[character_id] = {
                "core_level": core_level,
                "cinema_level": cinema_level,
            }
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (character_stats or {}).get(
                    character_id, _stats()
                ),
            }
        elif character_id == ASTRA:
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (character_stats or {}).get(
                    character_id,
                    _stats(hp=8_000.0, attack=800.0, element="ether"),
                ),
            }
        elif character_id == YIXUAN:
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (character_stats or {}).get(
                    character_id,
                    _stats(hp=12_000.0, attack=1_000.0, element="ether"),
                ),
            }
        else:
            raise AssertionError(f"missing Zhao regression build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:zhao-test",
            "level": 60,
            "initial_defense": 1_000.0,
            "damage_resistance": {"ice": 0.20, "ether": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _event(result: dict[str, object], semantic_id: str | None = None):
    events = result["events"]
    assert isinstance(events, list)
    return (
        next(item for item in events if item["semantic_id"] == semantic_id)
        if semantic_id is not None
        else events[0]
    )


def _node(event, node: str, mode: str = "expected") -> float:
    breakdown = event["modes"][mode]["calculation_breakdown"]
    return next(item["value"] for item in breakdown if item["node"] == node)


def _hp_disc():
    return [
        {
            "slot": 6,
            "set_id": "drive-disc:31000",
            "main_stat": "hp-percent",
            "substats": [
                {"stat": "attack-percent", "roll_count": 2},
                {"stat": "crit-rate", "roll_count": 2},
                {"stat": "crit-damage", "roll_count": 2},
                {"stat": "anomaly-proficiency-flat", "roll_count": 2},
            ],
        }
    ]


def test_zhao_raw_source_mapping_preserves_every_reviewed_damage_curve() -> None:
    raw_dict = load_character_record(ZHAO)
    raw = load_raw_record(raw_dict)
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1341.json"
    assert raw.name == "照"
    assert raw.code_name == "Zhao"
    assert raw.element in {"冰", "冰属性"}
    assert raw_dict["rarity"] == 4

    source_ids = {
        spec.source_skill_id
        for move in ZHAO_REVIEWED_MAPPING.moves
        for spec in move.parameters
    }
    assert source_ids == {
        "1341001",
        "1341002",
        "1341003",
        "1341004",
        "1341008",
        "1341009",
        "1341010",
        "1341011",
        "1341012",
        "1341013",
        "1341015",
        "1341016",
        "1341020",
    }

    definition = compile_zhao(
        ZhaoCompileConfig(core_level=1, cinema_level=0), raw
    )
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(entries) == 17  # 13 source moves, two explicit sums, two static paths.
    assert entries["move-entry:character:1341:basic-cold-judgment-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.471)
    assert entries["move-entry:character:1341:basic-cold-judgment-5"].multiplier_variants[0].multiplier.value.value == pytest.approx(7.736)
    assert entries["move-entry:character:1341:ultimate-rabbit-slash"].multiplier_variants[0].multiplier.value.value == pytest.approx(43.752)
    assert "1341005=" in entries["move-entry:character:1341:basic-cold-judgment-5"].original_text
    assert "1341006=" in entries["move-entry:character:1341:basic-cold-judgment-5"].original_text
    assert "1341014=" in entries["move-entry:character:1341:ultimate-rabbit-slash"].original_text
    assert "1341023=" in entries["move-entry:character:1341:ultimate-rabbit-slash"].original_text
    dash = entries["move-entry:character:1341:dash-bouncing-sprint"].multiplier_variants[0].multiplier
    assert isinstance(dash, Unresolved)
    assert dash.candidates == ("Raw combined curve: 173.2%",)
    assert "1341017" not in source_ids  # Defensive Assist has daze only.

    registration = registration_for(ZHAO)
    assert registration.catalog.display_name == "照"
    assert registration.catalog.rarity == "S"
    assert registration.role is CharacterRole.DEFENSE
    assert registration.base_element is Element.ICE
    assert (Path(__file__).parents[2] / "frontend/public/characters/IconRole56.webp").is_file()


def test_zhao_extra_hp_percent_adds_with_equipment_percent_from_white_hp() -> None:
    base = character_base_stats(ZHAO)
    assert base.hp.value == pytest.approx(9_117.4144)
    contributions = character_base_stat_contributions(ZHAO)
    assert len(contributions) == 1
    assert contributions[0].contribution_id.endswith("11102:hp-percent")
    assert contributions[0].value.value == pytest.approx(0.18)

    preview = build_registered_build_preview(ZHAO, level=60, discs=_hp_disc())
    assert preview.complete is True
    assert preview.base_stats["hp"] == pytest.approx(9_117.4144)
    # One 30% HP main stat adds alongside Zhao's raw 18% contribution.
    assert preview.out_of_combat_stats["hp"] == pytest.approx(9_117.4144 * (1 + 0.18 + 0.30))
    hp_sources = [item for item in preview.provenance if item.stat == "hp"]
    assert [(item.layer, item.value) for item in hp_sources] == [
        ("base-value", pytest.approx(9_117.4144)),
        ("out-of-combat-percent", pytest.approx(0.18)),
        ("out-of-combat-percent", pytest.approx(0.30)),
    ]
    assert preview.out_of_combat_stats["hp"] != pytest.approx(
        9_117.4144 * 1.18 * 1.30
    )

    payload = _payload()
    payload["character_builds"][ZHAO] = {
        "level": 60,
        "build_mode": "equipment-build",
        "drive_discs": _hp_disc(),
    }
    calculated = calculate_payload(payload)
    assert calculated["resolved_character_snapshots"][0]["stats"]["hp"] == pytest.approx(
        13_493.773312
    )


def test_core_initial_hp_crit_current_curtain_hp_and_charge_component() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1341:basic-final-judgment",
            core_level=1,
            cinema_level=6,
            condition_values={SPRING_CURTAIN: True},
            parameter_values={CHARGE_SECONDS: 2},
            enabled_rule_item_ids=(CORE_CRIT, CORE_HP, CORE_CHARGE, C4, C6),
        )
    )
    snapshot = result["resolved_character_snapshots"][0]["stats"]
    # Core 1 grants 0.8% per 1000 initial HP; C6 multiplies that by 1.25.
    assert snapshot["crit_rate"] == pytest.approx(0.40)
    assert snapshot["hp"] == pytest.approx(21_000.0)

    main = _event(result, "event:character:1341:basic-final-judgment:main")
    charge = _event(
        result,
        "event:character:1341:charged-hp-extra:basic-final-judgment",
    )
    assert _node(main, "character.current.crit-damage") == pytest.approx(0.90)
    assert charge["repeat_count"] == 2
    # C3/C5 raise Basic input Lv12 to effective Lv16: 0.28 max-HP per
    # second, then Cinema 6 multiplies the added component by 1.4.
    assert _node(charge, "damage.skill-multiplier") == pytest.approx(0.392)
    assert _node(charge, "damage.base-value") == pytest.approx(21_000.0 * 0.392)
    assert _node(charge, "character.current.crit-damage") == pytest.approx(0.90)
    assert charge["common_application_trace"]["created_by_effect_id"] == (
        "effect:character:1341:core:charged-hp-extra:basic-final-judgment"
    )
    assert result["totals"]["expected"]["complete"] is True

    # Cinema 6 is represented by a selectable rule, not by a fixed compile-time bonus.
    without_c6 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1341:basic-final-judgment",
            core_level=1,
            cinema_level=6,
            parameter_values={CHARGE_SECONDS: 2},
            enabled_rule_item_ids=(CORE_CRIT, CORE_CHARGE, C4),
        )
    )
    without_c6_charge = _event(
        without_c6,
        "event:character:1341:charged-hp-extra:basic-final-judgment",
    )
    assert _node(without_c6_charge, "damage.skill-multiplier") == pytest.approx(0.28)
    assert _node(without_c6_charge, "damage.base-value") == pytest.approx(5_600.0)

    zero_charge = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1341:basic-final-judgment",
            parameter_values={CHARGE_SECONDS: 0},
            enabled_rule_item_ids=(CORE_CHARGE,),
        )
    )
    assert [item["semantic_id"] for item in zero_charge["events"]] == [
        "event:character:1341:basic-final-judgment:main"
    ]


def test_spring_curtain_attack_buff_uses_its_separate_fifty_second_state() -> None:
    result = calculate_payload(
        _payload(
            condition_values={CURTAIN_ATTACK: True},
            enabled_rule_item_ids=(CORE_ATTACK,),
        )
    )
    stats = result["resolved_character_snapshots"][0]["stats"]
    assert stats["hp"] == pytest.approx(20_000.0)
    assert stats["attack"] == pytest.approx(1_100.0)


def test_cinema4_crit_damage_scope_excludes_support_followup() -> None:
    for entry, semantic, expected_cd in (
        (
            "move-entry:character:1341:basic-final-judgment",
            "event:character:1341:basic-final-judgment:main",
            0.90,
        ),
        (
            "move-entry:character:1341:chain-temporary-cooperation",
            "event:character:1341:chain-temporary-cooperation:main",
            0.90,
        ),
        (
            "move-entry:character:1341:ultimate-rabbit-slash",
            "event:character:1341:ultimate-rabbit-slash:main",
            0.90,
        ),
        (
            "move-entry:character:1341:support-afterglow",
            "event:character:1341:support-afterglow:main",
            0.50,
        ),
    ):
        result = calculate_payload(
            _payload(
                move_entry_id=entry,
                cinema_level=4,
                enabled_rule_item_ids=(C4,),
            )
        )
        event = _event(result, semantic)
        assert _node(event, "character.current.crit-damage") == pytest.approx(expected_cd)


def test_cinema2_uses_each_teammates_initial_attack_even_when_zhao_is_support() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=2,
            primary=ASTRA,
            supporting=(ZHAO,),
            condition_values={C2_ACTIVE: True},
            enabled_rule_item_ids=(C2,),
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[ZHAO]["attack"] == pytest.approx(1_200.0)
    assert snapshots[ASTRA]["attack"] == pytest.approx(920.0)
    traces = result["panel_traces"]
    assert {
        (item["recipient_character_id"], item["resolved_value"])
        for item in traces
        if item["rule_item_id"] == C2
    } == {(ZHAO, 200.0), (ASTRA, 120.0)}
    # No Zhao-owned modifier is applied to Astra's attack event itself.
    assert all(
        not item["effect_id"].startswith("effect:character:1341:")
        for item in _event(result)["common_application_trace"]["applied_modifiers"]
    )


def test_solo_cinema2_keeps_self_buff_and_treats_other_team_as_empty_noop() -> None:
    result = calculate_payload(
        _payload(
            cinema_level=2,
            condition_values={C2_ACTIVE: True},
            enabled_rule_item_ids=(C2,),
        )
    )
    stats = result["resolved_character_snapshots"][0]["stats"]
    assert stats["attack"] == pytest.approx(1_200.0)
    assert result["totals"]["expected"]["complete"] is True
    assert not any(item["blocking"] for item in result["diagnostics"])
    panel_effect_ids = {item["effect_id"] for item in result["panel_traces"]}
    assert "effect:character:1341:cinema2:zhao-attack-bonus-after-heal" in panel_effect_ids
    assert "effect:character:1341:cinema2:other-team-attack-bonus-after-heal" not in panel_effect_ids


def test_extra_ability_initial_hp_and_resistance_ignore_work_on_zhao_team() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            core_level=1,
            cinema_level=1,
            primary=ASTRA,
            supporting=(ZHAO,),
            condition_values={
                SPRING_CURTAIN: True,
                ANY_CURTAIN: True,
                C1_ACTIVE: True,
            },
            enabled_rule_item_ids=(CORE_HP, EXTRA_ABILITY, C1),
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[ZHAO]["hp"] == pytest.approx(21_000.0)
    event = _event(result)
    # The bonus is 10% + 1% for each 400 initial HP over 15,000: 22.5% at 20,000.
    assert _node(event, "damage.normal-bonus") == pytest.approx(0.225)
    assert _node(event, "resistance.damage-ignore") == pytest.approx(0.15)
    applied = event["common_application_trace"]["applied_modifiers"]
    assert any(item["effect_id"] == "effect:character:1341:extra-ability:curtain-team-damage-base" for item in applied)
    assert result["totals"]["expected"]["complete"] is True

    capped = calculate_payload(
        _payload(
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            primary=ASTRA,
            supporting=(ZHAO,),
            condition_values={ANY_CURTAIN: True},
            enabled_rule_item_ids=(EXTRA_ABILITY,),
            character_stats={ZHAO: _stats(hp=40_000.0)},
        )
    )
    assert _node(_event(capped), "damage.normal-bonus") == pytest.approx(0.40)


def test_static_ice_anomaly_and_disorder_are_no_crit_and_use_full_duration() -> None:
    anomaly = calculate_payload(
        _payload(move_entry_id="move-entry:character:1341:ice-shatter")
    )
    anomaly_event = _event(anomaly)
    assert anomaly_event["damage_type"] == "anomaly"
    assert anomaly["totals"]["non-crit"]["value"] == pytest.approx(
        anomaly["totals"]["full-crit"]["value"]
    )
    strength = anomaly_event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert strength["final_strength"] == pytest.approx(2_400.0)
    assert _node(anomaly_event, "anomaly.attribute.multiplier") == pytest.approx(5.0)

    disorder = calculate_payload(
        _payload(move_entry_id="move-entry:character:1341:ice-disorder")
    )
    disorder_event = _event(disorder)
    assert disorder_event["damage_type"] == "disorder"
    assert _node(disorder_event, "disorder.total-multiplier") == pytest.approx(13.75)
    assert disorder["totals"]["non-crit"]["value"] == pytest.approx(
        disorder["totals"]["expected"]["value"]
    )


def test_zhao_additional_ability_eligibility_is_derived_from_team_roles() -> None:
    solo = compile_registered_definition(ZHAO, {"core_level": 1, "cinema_level": 0}, (ZHAO,))
    with_support = compile_registered_definition(
        ZHAO,
        {"core_level": 1, "cinema_level": 0},
        (ZHAO, ASTRA),
    )
    with_rupture = compile_registered_definition(
        ZHAO,
        {"core_level": 1, "cinema_level": 0},
        (ZHAO, YIXUAN),
    )
    rule_id = "rule:character:1341:extra-ability:curtain-team-damage"
    assert next(item for item in solo.rule_items if str(item.rule_id) == rule_id).eligibility is RuleEligibility.INELIGIBLE
    assert next(item for item in with_support.rule_items if str(item.rule_id) == rule_id).eligibility is RuleEligibility.ELIGIBLE
    assert next(item for item in with_rupture.rule_items if str(item.rule_id) == rule_id).eligibility is RuleEligibility.INELIGIBLE
