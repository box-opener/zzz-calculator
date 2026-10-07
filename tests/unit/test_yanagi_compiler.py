from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.yanagi import (
    YANAGI_ID,
    YanagiCompileConfig,
    compile_yanagi,
    load_raw_record,
)
from core.application.equipment import signature_wengine_id_for
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import compile_registered_definition, config_fields_for
from web.api import app


client = TestClient(app)


def _yanagi_payload(move_entry_id: str, *, cinema_level: int = 0) -> dict:
    payload = {
        "primary_character_id": str(YANAGI_ID),
        "supporting_character_ids": [],
        "team_character_ids": [str(YANAGI_ID)],
        "formation_character_ids": [str(YANAGI_ID)],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(YANAGI_ID): {"core_level": 7, "cinema_level": cinema_level}
        },
        "character_builds": {
            str(YANAGI_ID): {
                "level": 60,
                "build_mode": "equipment-build",
                "drive_discs": [],
            }
        },
        "condition_values": {},
        "parameter_values": {},
        "enabled_rule_item_ids": [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "enemy": {
            "enemy_id": "enemy:yanagi-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "electric": 0.0,
                "ice": 0.0,
                "fire": 0.0,
                "ether": 0.0,
                "wind": 0.0,
                "luminance": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
    }
    return payload


def _calculate(entry_id: str, *, cinema_level: int = 0, payload: dict | None = None):
    request = payload if payload is not None else _yanagi_payload(
        entry_id,
        cinema_level=cinema_level,
    )
    return client.post("/api/v1/moves/calculate", json=request)


def test_yanagi_raw_identity_base_stats_and_signature_mapping() -> None:
    source = load_character_record(str(YANAGI_ID))
    assert source["source_version"] == "3.2"
    assert source["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1221.json"
    assert source["code_name"] == "Yanagi"
    assert source["potential_detail"] == {}

    raw = load_raw_record(source)
    assert raw.name == "柳"
    assert raw.specialty == "异常"
    assert raw.element == "电属性"
    assert raw.rarity == 4
    assert raw.special_element is None
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert raw.potential_details == ()

    stats = character_base_stats(str(YANAGI_ID))
    assert stats.attack.value == pytest.approx(872.574)
    assert stats.hp.value == pytest.approx(7788.6961)
    assert stats.anomaly_mastery.value == pytest.approx(148.0)
    assert stats.anomaly_proficiency.value == pytest.approx(114.0)
    assert str(signature_wengine_id_for(str(YANAGI_ID))) == "wengine:14122"


@pytest.mark.parametrize(
    ("entry_id", "element", "expected"),
    (
        ("move-entry:character:1221:basic-upper-1", "physical", 489.4877469328891),
        ("move-entry:character:1221:basic-upper-3", "electric", 973.8139359016354),
        ("move-entry:character:1221:basic-upper-5", "electric", 2040.9660449881887),
        ("move-entry:character:1221:basic-lower-1", "physical", 973.8139359016354),
        ("move-entry:character:1221:basic-lower-5", "electric", 2342.4870560602053),
    ),
)
def test_yanagi_basic_stance_stages_keep_the_reviewed_element_and_curve(
    entry_id: str,
    element: str,
    expected: float,
) -> None:
    response = _calculate(entry_id)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["damage_type"] == "direct"
    assert event["element"] == element
    assert event["modes"]["expected"]["known_value"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("entry_id", "expected", "damage_type"),
    (
        ("move-entry:character:1221:electric-anomaly", 11959.707477892187, "anomaly"),
        ("move-entry:character:1221:electric-disorder", 16265.202169933375, "disorder"),
    ),
)
def test_yanagi_static_shock_and_disorder_use_their_own_typed_paths(
    entry_id: str,
    expected: float,
    damage_type: str,
) -> None:
    response = _calculate(entry_id)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    event = result["events"][0]
    assert event["damage_type"] == damage_type
    assert event["element"] == "electric"
    assert event["modes"]["expected"]["known_value"] == pytest.approx(expected)


def test_yanagi_ex_special_downfall_is_a_single_child_and_extra_thrusts_are_explicit() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ex-special-moonlit-flow-thrust"
    )
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ex-special:downfall-component",
        "rule:character:1221:ex-special:extra-thrusts",
    ]
    default_result = client.post("/api/v1/moves/calculate", json=payload)
    assert default_result.status_code == 200, default_result.text
    default_events = default_result.json()["events"]
    assert default_result.json()["totals"]["expected"]["complete"] is True
    assert [(item["label"], item["repeat_count"]) for item in default_events] == [
        ("强化特殊技：月华流转（突刺）", 1),
        ("强化特殊技：月华流转（下落攻击）", 1),
    ]

    payload["compile_configs"][str(YANAGI_ID)]["cinema_level"] = 2
    payload["parameter_values"]["parameter:yanagi:ex-special-extra-thrusts"] = 2
    extra_result = client.post("/api/v1/moves/calculate", json=payload)
    assert extra_result.status_code == 200, extra_result.text
    extra_events = extra_result.json()["events"]
    assert extra_result.json()["totals"]["expected"]["complete"] is True
    extra_thrusts = [item for item in extra_events if "额外突刺" in item["label"]]
    downfalls = [item for item in extra_events if "下落攻击" in item["label"]]
    assert len(extra_thrusts) == 1
    assert extra_thrusts[0]["repeat_count"] == 2
    assert len(downfalls) == 1
    assert downfalls[0]["repeat_count"] == 1


def test_yanagi_current_state_rules_and_additional_ability_eligibility() -> None:
    alone = compile_registered_definition(
        YANAGI_ID,
        {"core_level": 7, "cinema_level": 0},
        (YANAGI_ID,),
        strict=False,
    )
    alone_extra = next(
        item for item in alone.rule_items
        if str(item.rule_id) == "rule:character:1221:extra-ability:basic-electric-buildup"
    )
    assert alone_extra.eligibility is RuleEligibility.INELIGIBLE

    supported = compile_registered_definition(
        YANAGI_ID,
        {"core_level": 7, "cinema_level": 0},
        (YANAGI_ID, "character:1091"),
        strict=False,
    )
    supported_extra = next(
        item for item in supported.rule_items
        if str(item.rule_id) == "rule:character:1221:extra-ability:basic-electric-buildup"
    )
    assert supported_extra.eligibility is RuleEligibility.ELIGIBLE
    assert supported_extra.diagnostics

    c1_definition = compile_yanagi(
        YanagiCompileConfig(cinema_level=1),
        load_raw_record(load_character_record(str(YANAGI_ID))),
    )
    insight = next(
        item for item in c1_definition.scenario_parameters
        if str(item.parameter_id) == "parameter:yanagi:insight-stacks"
    )
    assert insight.value == 3
    assert insight.maximum == 3


def test_yanagi_polar_disorder_adds_ap_after_the_scaled_record_base() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow"
    )
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
        "condition:yanagi:core-disorder-multiplier-active": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
        "rule:character:1221:core:disorder-multiplier",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    polar = next(item for item in result["events"] if item["damage_type"] == "disorder")
    assert polar["damage_subtype"] == "polar-disorder"
    assert polar["element"] == "electric"
    assert polar["modes"]["expected"]["status"] == "calculated"
    assert result["totals"]["expected"]["complete"] is True

    mode = polar["modes"]["expected"]
    breakdown = {item["node"]: item["value"] for item in mode["calculation_breakdown"]}
    strength = mode["anomaly_effect_strength_trace"]["final_strength"]
    current_ap = next(
        item["stats"]["anomaly_proficiency"]
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == str(YANAGI_ID)
    )
    assert breakdown["disorder.base-multiplier"] == pytest.approx(4.5)
    assert breakdown["disorder.time-compensation-multiplier"] == pytest.approx(12.5)
    assert breakdown["disorder.extra-multiplier"] == pytest.approx(2.5)
    assert breakdown["disorder.polar.multiplier"] == pytest.approx(0.15)
    assert breakdown["disorder.polar.ap-coefficient"] == pytest.approx(32.0)
    assert breakdown["character.current.anomaly-proficiency"] == pytest.approx(current_ap)
    expected_base = strength * (4.5 + 12.5 + 2.5) * 0.15 + 32.0 * current_ap
    assert breakdown["damage.base-value"] == pytest.approx(expected_base)
    assert mode["anomaly_record_id"] == "anomaly:static-source:character:1221:electric"


def test_yanagi_polar_source_selects_one_active_actor_and_preserves_alias_element() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow"
    )
    payload["supporting_character_ids"] = ["character:1091"]
    payload["team_character_ids"] = [str(YANAGI_ID), "character:1091"]
    payload["formation_character_ids"] = [str(YANAGI_ID), "character:1091"]
    payload["character_builds"]["character:1091"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "drive_discs": [],
    }
    payload["compile_configs"]["character:1091"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
    ]
    payload["polarity_anomaly_source"] = {
        "source_character_id": "character:1091",
        "element": "ice:lieshuang",
    }

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    polar = next(
        item for item in response.json()["events"] if item["damage_type"] == "disorder"
    )
    assert polar["element"] == "ice:lieshuang"
    assert polar["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1091:ice-lieshuang"
    )
    assert polar["modes"]["expected"]["anomaly_effect_strength_trace"]["character_id"] == (
        "character:1091"
    )
    payload["polarity_anomaly_source"]["element"] = "luminance"
    invalid = client.post("/api/v1/moves/calculate", json=payload)
    assert invalid.status_code == 400


def test_velina_turbulence_candidate_does_not_treat_polar_disorder_as_regular_disorder() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow"
    )
    payload["supporting_character_ids"] = ["character:1011", "character:1561"]
    payload["team_character_ids"] = [
        str(YANAGI_ID),
        "character:1011",
        "character:1561",
    ]
    payload["formation_character_ids"] = list(payload["team_character_ids"])
    for character_id in ("character:1011", "character:1561"):
        payload["character_builds"][character_id] = {
            "level": 60,
            "build_mode": "equipment-build",
            "drive_discs": [],
        }
        payload["compile_configs"][character_id] = {"core_level": 7, "cinema_level": 0}
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
        "condition:velina:enemy-wind-weathered": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
        "rule:character:1561:core:wind-triggered-turbulence-candidate",
    ]
    payload["polarity_anomaly_source"] = {
        "source_character_id": "character:1011",
        "element": "electric",
    }

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    assert [item["damage_type"] for item in result["events"]] == [
        "direct",
        "disorder",
    ]
    assert result["events"][1]["damage_subtype"] == "polar-disorder"


@pytest.mark.parametrize(
    ("base_proficiency", "expected_damage", "expected_current_ap"),
    (
        (300.0, 9666.505148394912, 375.0),
        (299.9, 7731.665172622653, 374.9),
    ),
)
def test_yanagi_polar_disorder_matches_current_ap_weapon_threshold(
    base_proficiency: float,
    expected_damage: float,
    expected_current_ap: float,
) -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow"
    )
    payload["supporting_character_ids"] = ["character:1011"]
    payload["team_character_ids"] = [str(YANAGI_ID), "character:1011"]
    payload["formation_character_ids"] = list(payload["team_character_ids"])
    payload["compile_configs"]["character:1011"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["character_builds"][str(YANAGI_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": {
            "hp": 10000,
            "attack": 1000,
            "defense": 500,
            "impact": 100,
            "crit_rate": 0,
            "crit_damage": 0.5,
            "anomaly_mastery": 100,
            "anomaly_proficiency": base_proficiency,
            "energy_regen": 1.2,
            "penetration_rate": 0,
            "penetration_flat": 0,
            "element_damage_bonus": {"electric": 0},
        },
        "wengine_id": "wengine:14122",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }
    payload["character_builds"]["character:1011"] = {
        "level": 60,
        "out_of_combat_stats": {
            "attack": 800,
            "crit_rate": 0,
            "crit_damage": 0.5,
            "penetration_rate": 0,
            "penetration_flat": 0,
            "anomaly_mastery": 100,
            "anomaly_proficiency": 100,
            "element_damage_bonus": {"electric": 0},
        },
    }
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
        "condition:wengine:14122:owner:1221:special-hit-anomalous-target-ap-buff-active": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
        "rule:wengine:14122:owner:1221:special-hit-anomalous-target-ap-buff",
        "rule:wengine:14122:owner:1221:over-threshold-disorder-damage",
    ]
    payload["polarity_anomaly_source"] = {
        "source_character_id": "character:1011",
        "element": "electric",
    }

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[str(YANAGI_ID)]["anomaly_proficiency"] == pytest.approx(
        expected_current_ap
    )
    polar = next(item for item in result["events"] if item["damage_type"] == "disorder")
    assert polar["modes"]["expected"]["value"] == pytest.approx(expected_damage)
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("cinema", "extra_thrusts", "enable_c2_polar_rule", "expected_polar_multiplier"),
    (
        (2, 2, False, 0.15),
        (2, 2, True, 0.50),
        (6, 4, False, 0.15),
        (6, 4, True, 0.80),
        (2, 7, True, 0.50),
        (6, 7, True, 0.80),
    ),
)
def test_yanagi_ex_polarity_uses_rule_state_and_cinema_cap(
    cinema: int,
    extra_thrusts: int,
    enable_c2_polar_rule: bool,
    expected_polar_multiplier: float,
) -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ex-special-moonlit-flow-thrust",
        cinema_level=cinema,
    )
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
    }
    payload["parameter_values"] = {
        "parameter:yanagi:ex-special-extra-thrusts": extra_thrusts,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ex-special:downfall-component",
        "rule:character:1221:ex-special:polarity-disorder",
        "rule:character:1221:ex-special:extra-thrusts",
        *(
            ["rule:character:1221:cinema2:ex-polarity-multiplier"]
            if enable_c2_polar_rule
            else []
        ),
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    polar = next(item for item in result["events"] if item["damage_type"] == "disorder")
    assert sum(item["damage_type"] == "disorder" for item in result["events"]) == 1
    if extra_thrusts == 7:
        extra = next(item for item in result["events"] if "额外突刺" in item["label"])
        assert extra["repeat_count"] == 7
    breakdown = {
        item["node"]: item["value"]
        for item in polar["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["disorder.polar.multiplier"] == pytest.approx(
        expected_polar_multiplier
    )
    assert result["totals"]["expected"]["complete"] is True


def test_yanagi_cinema3_and5_raise_ultimate_skill_and_polar_cal_level() -> None:
    raw = load_raw_record(load_character_record(str(YANAGI_ID)))
    expected_ratio = {0: 30.243, 3: 32.993, 5: 35.743}
    expected_cal = {0: 32.0, 3: 36.5, 5: 41.0}
    for cinema in (0, 3, 5):
        definition = compile_yanagi(
            YanagiCompileConfig(cinema_level=cinema),
            raw,
        )
        ultimate = next(
            item for item in definition.move_entries
            if str(item.entry_id).endswith("ultimate-thunder-shadow")
        )
        assert ultimate.multiplier_variants[0].multiplier.value.value == pytest.approx(
            expected_ratio[cinema]
        )
        template = next(
            item for item in definition.damage_event_templates
            if str(item.ref.template_id) == "template:character:1221:ultimate:polarity-disorder"
        )
        assert template.anomaly_proficiency_coefficient == pytest.approx(expected_cal[cinema])


def test_yanagi_skill_level_controls_are_labeled_as_base_levels() -> None:
    fields = {
        item.field_id: item
        for item in config_fields_for(
            YANAGI_ID,
            {"cinema_level": 3, "skill_levels": {"ultimate": 12}},
            (YANAGI_ID,),
        )
    }
    ultimate = fields["skill_level:ultimate"]
    assert ultimate.value == 12
    assert ultimate.label == "终结技基础等级（不含3/5影）"
    assert ultimate.help_text == "基础等级；3影、5影各提升2级后用于计算，实际等级最高16。"


def test_yanagi_without_active_target_anomaly_keeps_the_ultimate_direct_only() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow"
    )
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["events"]) == 1
    assert result["events"][0]["damage_type"] == "direct"
    assert result["totals"]["expected"]["complete"] is True


def test_yanagi_ultimate_polarity_keeps_base_factor_at_cinema6() -> None:
    payload = _yanagi_payload(
        "move-entry:character:1221:ultimate-thunder-shadow",
        cinema_level=6,
    )
    payload["condition_values"] = {
        "condition:yanagi:target-has-active-anomaly": True,
    }
    payload["parameter_values"] = {
        "parameter:yanagi:ex-special-extra-thrusts": 4,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1221:ultimate:polarity-disorder",
        "rule:character:1221:cinema2:ex-polarity-multiplier",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    polar = next(item for item in response.json()["events"] if item["damage_type"] == "disorder")
    breakdown = {
        item["node"]: item["value"]
        for item in polar["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["disorder.polar.multiplier"] == pytest.approx(0.15)
    assert breakdown["disorder.polar.ap-coefficient"] == pytest.approx(41.0)
