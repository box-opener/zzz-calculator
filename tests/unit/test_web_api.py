from __future__ import annotations

from pathlib import Path
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
)
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import registration_for, supported_character_registrations
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineBuildInput, WEngineId
from web.api import app


client = TestClient(app)


def _velina_payload(move_entry_id: str) -> dict:
    payload = _valid_calculation_payload()
    payload.update(
        {
            "primary_character_id": "character:1561",
            "supporting_character_ids": [],
            "team_character_ids": ["character:1561"],
            "formation_character_ids": ["character:1561"],
            "move_entry_id": move_entry_id,
            "compile_configs": {
                "character:1561": {"core_level": 7, "cinema_level": 0}
            },
            "character_builds": {
                "character:1561": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "hp": 7788.6961,
                        "attack": 872.574,
                        "defense": 612.6038,
                        "impact": 86.0,
                        "crit_rate": 0.05,
                        "crit_damage": 0.5,
                        "anomaly_mastery": 112.0,
                        "anomaly_proficiency": 165.0,
                        "energy_regen": 1.2,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"wind": 0.0},
                    },
                }
            },
            "condition_values": {},
            "parameter_values": {},
            "enabled_rule_item_ids": [],
        }
    )
    payload["enemy"].update(
        {
            "enemy_id": "enemy:velina-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "fire": 0.0,
                "ice": 0.0,
                "electric": 0.0,
                "ether": 0.0,
                "wind": 0.0,
                "luminance": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        }
    )
    return payload


def _valid_calculation_payload() -> dict:
    return {
        "primary_character_id": "character:1431",
        "team_character_ids": ["character:1431"],
        "move_entry_id": "move-entry:ye:1431:basic-fast-1",
        "compile_configs": {
            "character:1431": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            }
        },
        "condition_values": {},
        "parameter_values": {},
        "character_builds": {
            "character:1431": {
                "level": 60,
                "out_of_combat_stats": {
                    "attack": 1200.0,
                    "crit_rate": 0.65,
                    "crit_damage": 0.5,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"physical": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:ui",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _anby_calculation_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 6,
    core_level: int = 7,
    enemy_stunned: bool = False,
    charge_count: int | None = None,
    enabled_rule_item_ids: list[str] | None = None,
) -> dict:
    payload = _valid_calculation_payload()
    payload.update(
        {
            "primary_character_id": "character:1011",
            "supporting_character_ids": [],
            "team_character_ids": ["character:1011"],
            "move_entry_id": move_entry_id,
            "compile_configs": {
                "character:1011": {
                    "core_level": core_level,
                    "cinema_level": cinema_level,
                }
            },
            "condition_values": {
                "condition:anby:after-basic-third-active": True,
                "condition:anby:cinema1-energy-efficiency-active": True,
            },
            "character_builds": {
                "character:1011": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "hp": 7500.7134,
                        "attack": 1000.0,
                        "defense": 612.6038,
                        "impact": 136.0,
                        "crit_rate": 0.50,
                        "crit_damage": 0.50,
                        "anomaly_mastery": 94.0,
                        "anomaly_proficiency": 93.0,
                        "energy_regen": 1.2,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"physical": 0.20, "electric": 0.20},
                    },
                }
            },
        }
    )
    payload["enemy"].update(
        {
            "damage_resistance": {"physical": 0.20, "electric": 0.20},
            "is_stunned": enemy_stunned,
        }
    )
    payload["enabled_rule_item_ids"] = enabled_rule_item_ids or []
    payload["rule_stack_counts"] = (
        {"rule:character:1011:cinema6:charge-stacks": charge_count}
        if charge_count is not None
        else {}
    )
    return payload


def _wengine_build(wengine_id: str, refinement: int, *, element: str) -> dict:
    return {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": wengine_id,
        "wengine_level": 60,
        "wengine_refinement": refinement,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.50,
            "crit_damage": 0.50,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {element: 0.0},
        },
        "drive_discs": [],
    }


def _with_supporting_wengine(
    payload: dict,
    support_engines: list[tuple[str, str, int, str]],
) -> dict:
    support_ids = [item[0] for item in support_engines]
    payload["supporting_character_ids"] = support_ids
    payload["team_character_ids"] = [payload["primary_character_id"], *support_ids]
    primary_stats = payload["character_builds"][payload["primary_character_id"]][
        "out_of_combat_stats"
    ]
    primary_stats.setdefault("hp", 10000.0)
    primary_stats.setdefault("defense", 500.0)
    primary_stats.setdefault("impact", 100.0)
    primary_stats.setdefault("anomaly_mastery", 100.0)
    primary_stats.setdefault("anomaly_proficiency", 100.0)
    primary_stats.setdefault("energy_regen", 1.2)
    for owner, wengine_id, refinement, element in support_engines:
        payload["compile_configs"][owner] = {"core_level": 1, "cinema_level": 0}
        payload["character_builds"][owner] = _wengine_build(
            wengine_id,
            refinement,
            element=element,
        )
        payload["enemy"]["damage_resistance"].setdefault(element, 0.2)
    return payload


def _single_wengine_payload(
    character_id: str,
    move_entry_id: str,
    wengine_id: str,
    refinement: int,
    *,
    element: str,
) -> dict:
    payload = _valid_calculation_payload()
    payload["primary_character_id"] = character_id
    payload["team_character_ids"] = [character_id]
    payload["move_entry_id"] = move_entry_id
    compile_config = dict(payload["compile_configs"].get(character_id, {}))
    compile_config.update({"core_level": 1, "cinema_level": 0})
    payload["compile_configs"] = {character_id: compile_config}
    payload["character_builds"] = {
        character_id: _wengine_build(wengine_id, refinement, element=element)
    }
    payload["enemy"]["damage_resistance"] = {element: 0.2}
    return payload


def _ye_primary_astra_support_payload(*, aria: bool) -> dict:
    ye_stats = {
        "hp": 10000.0,
        "attack": 1000.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0},
    }
    astra_stats = {**ye_stats, "element_damage_bonus": {"ether": 0.0}}
    return {
        "primary_character_id": "character:1431",
        "supporting_character_ids": ["character:1311"],
        "team_character_ids": ["character:1431", "character:1311"],
        "move_entry_id": "move-entry:ye:1431:assist-yuanshou",
        "compile_configs": {
            "character:1431": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            },
            "character:1311": {"core_level": 1, "cinema_level": 0},
        },
        # Energy is intentionally explicit here so the comparison isolates
        # ARIA. The trigger actor is also explicit because this is a support
        # entry event, not a free-standing toggle.
        "condition_values": {
            "condition:astra:aria-active": aria,
            "condition:astra:energy-derived-active": True,
        },
        "parameter_values": {},
        "character_builds": {
            "character:1431": {"level": 60, "out_of_combat_stats": ye_stats},
            "character:1311": {"level": 60, "out_of_combat_stats": astra_stats},
        },
        "enemy": {
            "enemy_id": "enemy:ui",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2, "ether": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": (
            ["rule:astra:1311:extra-ability-entry"] if aria else []
        ),
        "selected_trigger_inputs": [
            {
                "input_id": "scenario-trigger:effect:astra:1311:extra-entry-tremolo:actor",
                "actor_id": "character:1431",
            },
            {
                "input_id": "scenario-trigger:effect:astra:1311:extra-entry-cluster:actor",
                "actor_id": "character:1431",
            },
        ]
        if aria
        else [],
        "rule_stack_counts": {},
    }


def _ye_primary_astra_aria_team_buff_payload(*, aria: bool) -> dict:
    """A production-shaped payload with ARIA as its only scenario gate."""

    payload = _ye_primary_astra_support_payload(aria=aria)
    payload["move_entry_id"] = "move-entry:ye:1431:basic-fast-1"
    payload["condition_values"] = {
        "condition:astra:aria-active": aria,
    }
    payload["enabled_rule_item_ids"] = (
        ["rule:astra:1311:aria-team-buff"] if aria else []
    )
    payload["selected_trigger_inputs"] = []
    return payload


def _astra_aria_payload(*, aria: bool, cinema_level: int = 0) -> dict:
    return {
        "primary_character_id": "character:1311",
        "team_character_ids": ["character:1311"],
        "move_entry_id": "move-entry:astra:1311:basic-interlude-1",
        "compile_configs": {
            "character:1311": {
                "core_level": 1,
                "cinema_level": cinema_level,
            }
        },
        "condition_values": {"condition:astra:aria-active": aria},
        "parameter_values": {},
        "character_builds": {
            "character:1311": {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 500.0,
                    "impact": 100.0,
                    "anomaly_mastery": 100.0,
                    "anomaly_proficiency": 100.0,
                    "energy_regen": 1.2,
                    "crit_rate": 0.5,
                    "crit_damage": 0.5,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"ether": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:ui",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"ether": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def test_catalog_uses_production_ids_and_assets() -> None:
    response = client.get("/api/v1/characters")
    assert response.status_code == 200
    payload = response.json()
    assert {item["character_id"] for item in payload} == {
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
        "character:1071",
        "character:1081",
        "character:1101",
        "character:1111",
        "character:1121",
        "character:1131",
        "character:1141",
        "character:1151",
        "character:1161",
        "character:1171",
    }
    assert all(item["image_path"].startswith("/characters/") for item in payload)
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "portrait-placeholder.svg").is_file()
    burnice = next(item for item in payload if item["character_id"] == "character:1171")
    assert burnice["display_name"] == "柏妮思"
    assert burnice["code_name"] == "Burnice"
    assert burnice["rarity"] == "S"
    assert burnice["specialty"] == "anomaly"
    assert burnice["element"] == "fire"
    assert burnice["image_path"] == "/characters/portrait-placeholder.svg"
    anby = next(item for item in payload if item["character_id"] == "character:1011")
    assert anby["rarity"] == "A"
    assert anby["specialty"] == "stun"
    assert anby["image_path"] == "/characters/portrait-placeholder.svg"
    nekomata = next(item for item in payload if item["character_id"] == "character:1021")
    assert nekomata["rarity"] == "S"
    assert nekomata["specialty"] == "attack"
    assert nekomata["element"] == "physical"
    assert nekomata["image_path"] == "/characters/portrait-placeholder.svg"
    corin = next(item for item in payload if item["character_id"] == "character:1061")
    assert corin["display_name"] == "可琳"
    assert corin["code_name"] == "Corin"
    assert corin["rarity"] == "A"
    assert corin["specialty"] == "attack"
    assert corin["element"] == "physical"
    assert corin["image_path"] == "/characters/IconRole09.webp"
    caesar = next(item for item in payload if item["character_id"] == "character:1071")
    assert caesar["display_name"] == "凯撒"
    assert caesar["code_name"] == "Caesar"
    assert caesar["rarity"] == "S"
    assert caesar["specialty"] == "defense"
    assert caesar["element"] == "physical"
    assert caesar["image_path"] == "/characters/IconRole25.webp"
    billy = next(item for item in payload if item["character_id"] == "character:1081")
    assert billy["display_name"] == "比利"
    assert billy["code_name"] == "Billy"
    assert billy["rarity"] == "A"
    assert billy["specialty"] == "attack"
    assert billy["element"] == "physical"
    assert billy["image_path"] == "/characters/portrait-placeholder.svg"
    koleda = next(item for item in payload if item["character_id"] == "character:1101")
    assert koleda["display_name"] == "珂蕾妲"
    assert koleda["code_name"] == "Koleda"
    assert koleda["rarity"] == "S"
    assert koleda["specialty"] == "stun"
    assert koleda["element"] == "fire"
    assert koleda["image_path"] == "/characters/portrait-placeholder.svg"
    anton = next(item for item in payload if item["character_id"] == "character:1111")
    assert anton["display_name"] == "安东"
    assert anton["code_name"] == "Anton"
    assert anton["rarity"] == "A"
    assert anton["specialty"] == "attack"
    assert anton["element"] == "electric"
    assert anton["image_path"] == "/characters/portrait-placeholder.svg"
    ben = next(item for item in payload if item["character_id"] == "character:1121")
    assert ben["display_name"] == "本"
    assert ben["code_name"] == "Ben"
    assert ben["rarity"] == "A"
    assert ben["specialty"] == "defense"
    assert ben["element"] == "fire"
    assert ben["image_path"] == "/characters/portrait-placeholder.svg"
    soukaku = next(item for item in payload if item["character_id"] == "character:1131")
    assert soukaku["display_name"] == "苍角"
    assert soukaku["code_name"] == "Soukaku"
    assert soukaku["rarity"] == "A"
    assert soukaku["specialty"] == "support"
    assert soukaku["element"] == "ice"
    assert soukaku["image_path"] == "/characters/portrait-placeholder.svg"
    lycaon = next(item for item in payload if item["character_id"] == "character:1141")
    assert lycaon["display_name"] == "莱卡恩"
    assert lycaon["code_name"] == "Lycaon"
    assert lycaon["rarity"] == "S"
    assert lycaon["specialty"] == "stun"
    assert lycaon["element"] == "ice"
    assert lycaon["image_path"] == "/characters/portrait-placeholder.svg"
    lucy = next(item for item in payload if item["character_id"] == "character:1151")
    assert lucy["display_name"] == "露西"
    assert lucy["code_name"] == "Lucy"
    assert lucy["rarity"] == "A"
    assert lucy["specialty"] == "support"
    assert lucy["element"] == "fire"
    assert lucy["image_path"] == "/characters/portrait-placeholder.svg"
    lighter = next(item for item in payload if item["character_id"] == "character:1161")
    assert lighter["display_name"] == "莱特"
    assert lighter["code_name"] == "Lighter"
    assert lighter["rarity"] == "S"
    assert lighter["specialty"] == "stun"
    assert lighter["element"] == "fire"
    assert lighter["image_path"] == "/characters/portrait-placeholder.svg"
    nicole = next(item for item in payload if item["character_id"] == "character:1031")
    assert nicole["rarity"] == "A"
    assert nicole["specialty"] == "support"
    assert nicole["element"] == "ether"
    assert nicole["image_path"] == "/characters/portrait-placeholder.svg"
    remielle = next(item for item in payload if item["character_id"] == "character:1581")
    assert remielle["display_name"] == "蕾米埃尔"
    assert remielle["rarity"] == "S"
    assert remielle["specialty"] == "anomaly"
    assert remielle["element"] == "luminance"
    assert remielle["image_path"] == "/characters/portrait-placeholder.svg"
    soldier11 = next(item for item in payload if item["character_id"] == "character:1041")
    assert soldier11["rarity"] == "S"
    assert soldier11["specialty"] == "attack"
    assert soldier11["element"] == "fire"
    assert soldier11["image_path"] == "/characters/portrait-placeholder.svg"
    yidhari = next(item for item in payload if item["character_id"] == "character:1051")
    assert yidhari["rarity"] == "S"
    assert yidhari["specialty"] == "rupture"
    assert yidhari["element"] == "ice"
    assert yidhari["code_name"] == "Yidhari"
    assert yidhari["image_path"] == "/characters/portrait-placeholder.svg"
    assert (asset_root / "IconRole36.webp").is_file()
    assert (asset_root / "IconRole55.webp").is_file()
    assert (asset_root / "IconRole46.webp").is_file()
    assert (asset_root / "IconRole47.webp").is_file()
    assert (asset_root / "IconRole39.webp").is_file()
    assert (asset_root / "IconRole13.webp").is_file()
    assert (asset_root / "IconRole44.webp").is_file()
    assert (asset_root / "IconRole50.webp").is_file()
    assert (asset_root / "IconRole54.webp").is_file()
    assert (asset_root / "IconRole41.webp").is_file()
    assert (asset_root / "IconRole56.webp").is_file()
    assert (asset_root / "IconRole29.webp").is_file()


def test_wengine_catalog_exposes_source_verified_signature_owners() -> None:
    catalog = {
        item["wengine_id"]: item
        for item in client.get("/api/v1/wengines").json()
    }
    expected = {
        "wengine:14109": {
            "name": "霰落星殿",
            "owner": "character:1091",
        },
        "wengine:14137": {
            "name": "青溟笼舍",
            "owner": "character:1371",
        },
        "wengine:14133": {
            "name": "飞鸟星梦",
            "owner": "character:1331",
        },
        "wengine:14125": {
            "name": "玉壶青冰",
            "owner": "character:1251",
        },
        "wengine:14148": {
            "name": "昨夜来电",
            "owner": "character:1481",
        },
        "wengine:14145": {
            "name": "铸梦炉歌",
            "owner": "character:1451",
        },
        "wengine:14134": {
            "name": "半糖雪兔",
            "owner": "character:1341",
        },
    }
    for wengine_id, values in expected.items():
        assert catalog[wengine_id]["display_name"] == values["name"]
        assert catalog[wengine_id]["signature_character_id"] == values["owner"]


def test_vivian_signature_timeline_note_is_tagged_for_calculation_details() -> None:
    response = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14133",
            "equipped_character_id": "character:1331",
            "team_character_ids": ["character:1331"],
            "level": 60,
            "refinement": 1,
        },
    )
    assert response.status_code == 200, response.text
    note = next(
        item
        for item in response.json()["diagnostics"]
        if item["diagnostic_id"] == "wengine:wengine:14133:result-scope"
    )
    assert note["blocking"] is False
    assert note["details_only"] is True
    assert "0.5-second cooldown" in note["message"]


def test_every_supported_character_has_a_signature_for_picker_ordering() -> None:
    registered_ids = {
        registration.character_id
        for registration in supported_character_registrations()
    }
    assert set(SIGNATURE_WENGINE_BY_CHARACTER) == registered_ids


def test_anby_definition_preview_uses_a_rank_defaults_and_exposes_its_actual_rules() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1011",
            "team_character_ids": ["character:1011"],
            "compile_config": {"core_level": 7, "cinema_level": 6},
            "condition_values": {},
        },
    )
    assert response.status_code == 200, response.text
    preview = response.json()
    assert len(preview["moves"]) == 15
    fields = {item["field_id"]: item["value"] for item in preview["compile_config_fields"]}
    assert fields["cinema_level"] == 6
    assert all(fields[f"skill_level:{group}"] == 16 for group in (
        "basic-attack", "dodge", "special-attack", "chain-attack", "assist", "ultimate"
    ))
    rules = {item["rule_id"]: item for item in preview["rule_items"]}
    assert rules["rule:character:1011:extra-ability:counter-energy-restore-source-only"][
        "eligibility"
    ] == "ineligible"
    assert rules["rule:character:1011:cinema6:charge-stacks"]["stack"]["maximum"] == 8


def test_anby_calculate_payload_uses_enemy_stun_state_and_current_charge_layers() -> None:
    c6_stack = "rule:character:1011:cinema6:charge-stacks"
    c6_bonus = "rule:character:1011:cinema6:basic-dash-damage-bonus"
    stack_rules = [c6_stack, c6_bonus]
    base = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            "move-entry:character:1011:basic-volt-assault-1",
            charge_count=0,
            enabled_rule_item_ids=stack_rules,
        ),
    )
    charged = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            "move-entry:character:1011:basic-volt-assault-1",
            charge_count=1,
            enabled_rule_item_ids=stack_rules,
        ),
    )
    assert base.status_code == 200, base.text
    assert charged.status_code == 200, charged.text
    base_result, charged_result = base.json(), charged.json()
    assert base_result["totals"]["expected"]["complete"] is True
    assert charged_result["totals"]["expected"]["complete"] is True
    base_event = base_result["events"][0]
    charged_event = charged_result["events"][0]
    assert _breakdown_value(base_event, "damage.normal-bonus") == pytest.approx(0.0)
    assert _breakdown_value(charged_event, "damage.normal-bonus") == pytest.approx(0.45)
    assert _breakdown_value(base_event, "damage.normal-bonus-region") == pytest.approx(1.20)
    assert _breakdown_value(charged_event, "damage.normal-bonus-region") == pytest.approx(1.65)
    assert charged_event["modes"]["expected"]["value"] == pytest.approx(
        base_event["modes"]["expected"]["value"] * (1.65 / 1.20)
    )

    c2_damage_rule = "rule:character:1011:cinema2:falling-thunder-damage-vs-stunned"
    falling_thunder = "move-entry:character:1011:basic-falling-thunder"
    not_stunned = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            falling_thunder,
            cinema_level=2,
            enemy_stunned=False,
            enabled_rule_item_ids=[c2_damage_rule],
        ),
    )
    stunned = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            falling_thunder,
            cinema_level=2,
            enemy_stunned=True,
            enabled_rule_item_ids=[c2_damage_rule],
        ),
    )
    assert not_stunned.status_code == 200, not_stunned.text
    assert stunned.status_code == 200, stunned.text
    assert _breakdown_value(not_stunned.json()["events"][0], "damage.normal-bonus-region") == pytest.approx(1.20)
    assert _breakdown_value(stunned.json()["events"][0], "damage.normal-bonus-region") == pytest.approx(1.50)

    c2_daze_rule = "rule:character:1011:cinema2:ex-special-daze-vs-not-stunned"
    ex_special = "move-entry:character:1011:ex-special-cobalt-lightning"
    nonstun_ex = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            ex_special,
            cinema_level=2,
            enemy_stunned=False,
            enabled_rule_item_ids=[c2_daze_rule],
        ),
    )
    stunned_ex = client.post(
        "/api/v1/moves/calculate",
        json=_anby_calculation_payload(
            ex_special,
            cinema_level=2,
            enemy_stunned=True,
            enabled_rule_item_ids=[c2_daze_rule],
        ),
    )
    assert nonstun_ex.status_code == 200, nonstun_ex.text
    assert stunned_ex.status_code == 200, stunned_ex.text
    nonstun_event = nonstun_ex.json()["events"][0]
    stunned_event = stunned_ex.json()["events"][0]
    assert any(
        item["modifier_path"] == "daze.outgoing-bonus"
        and item["value"] == pytest.approx(0.10)
        for item in nonstun_event["common_application_trace"]["applied_modifiers"]
    )
    assert not any(
        item["modifier_path"] == "daze.outgoing-bonus"
        for item in stunned_event["common_application_trace"]["applied_modifiers"]
    )


def test_anby_signature_equipment_build_uses_demara_battery_and_r5_panel_values() -> None:
    payload = _anby_calculation_payload(
        "move-entry:character:1011:ex-special-cobalt-lightning",
        cinema_level=6,
        core_level=7,
    )
    payload["character_builds"]["character:1011"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:13101",
        "wengine_level": 60,
        "wengine_refinement": 5,
        "drive_discs": [],
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13101:owner:1011:electric-damage",
        "rule:character:1011:cinema1:energy-gain-efficiency-source-only",
        "rule:character:1011:cinema4:backline-electric-energy-source-only",
    ]
    payload["rule_stack_counts"] = {}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    anby = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1011"
    )
    assert anby["stats"]["hp"] == pytest.approx(7500.7134)
    assert anby["stats"]["attack"] == pytest.approx(1282.957)
    assert anby["stats"]["defense"] == pytest.approx(612.6038)
    assert anby["stats"]["impact"] == pytest.approx(156.4)
    assert anby["stats"]["energy_regen"] == pytest.approx(1.2)
    event = result["events"][0]
    assert _breakdown_value(event, "damage.skill-multiplier") == pytest.approx(13.78)
    assert _breakdown_value(event, "damage.base-value") == pytest.approx(17679.14746)
    assert _breakdown_value(event, "damage.normal-bonus-region") == pytest.approx(1.24)
    assert event["modes"]["expected"]["value"] == pytest.approx(7956.0026572)
    assert result["totals"]["expected"]["complete"] is True


def test_calculation_accepts_a_primary_and_two_supporting_characters() -> None:
    payload = _valid_calculation_payload()
    primary = "character:1431"
    supports = ["character:1311", "character:1401"]
    payload["supporting_character_ids"] = supports
    payload["team_character_ids"] = [primary, *supports]
    payload["compile_configs"].update({
        "character:1311": {"core_level": 1, "cinema_level": 0},
        "character:1401": {"core_level": 1, "cinema_level": 0},
    })
    astra_build = deepcopy(payload["character_builds"][primary])
    astra_build["out_of_combat_stats"]["element_damage_bonus"] = {"ether": 0.0}
    alice_build = deepcopy(payload["character_builds"][primary])
    payload["character_builds"].update({
        "character:1311": astra_build,
        "character:1401": alice_build,
    })
    # Alice's mutually-exclusive Star Dance variants are intentionally all
    # false: she is only supporting this Ye calculation and her unselected
    # entry must not block the primary move.
    payload["condition_values"] = {
        "condition:alice:star-dance-charge-1": False,
        "condition:alice:star-dance-charge-2": False,
        "condition:alice:star-dance-charge-3": False,
        "condition:alice:physical-anomaly-active": True,
        "condition:alice:polar-assault-active": False,
        "condition:alice:victory-state-active": False,
    }
    payload["enemy"]["damage_resistance"]["ether"] = 0.2

    for character_id in [primary, *supports]:
        definition_response = client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": character_id,
                "team_character_ids": [primary, *supports],
                "compile_config": payload["compile_configs"][character_id],
            },
        )
        assert definition_response.status_code == 200, definition_response.text
        build_response = client.post(
            "/api/v1/builds/preview",
            json={"character_id": character_id, "level": 60, "drive_discs": []},
        )
        assert build_response.status_code == 200, build_response.text

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["events"]
    assert {item["character_id"] for item in result["resolved_character_snapshots"]} == {
        primary,
        *supports,
    }


def test_alice_attribute_anomaly_exposes_generated_strength_provenance() -> None:
    stats = {
        "hp": 10000.0,
        "attack": 1234.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 234.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.17},
    }
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1401",
            "team_character_ids": ["character:1401"],
            "move_entry_id": "move-entry:alice:1401:physical-anomaly",
            "compile_configs": {"character:1401": {"core_level": 1, "cinema_level": 0}},
            "condition_values": {},
            "parameter_values": {},
            "character_builds": {"character:1401": {"level": 42, "out_of_combat_stats": stats}},
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
            "enabled_rule_item_ids": [],
            "selected_trigger_inputs": [],
            "rule_stack_counts": {},
        },
    )

    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    trace = event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["level"] == 42
    assert trace["attack"] == 1234.0
    assert trace["anomaly_proficiency"] == 234.0
    assert trace["element_bonus"] == 0.17
    assert trace["normal_bonus"] == 0.0
    assert trace["mutation"] == 1.0
    assert trace["final_strength"] == pytest.approx(
        trace["level_coefficient"]
        * trace["anomaly_proficiency_factor"]
        * (1 + trace["element_bonus"] + trace["normal_bonus"])
        * trace["attack"]
        * trace["mutation"]
    )
    factor_labels = {item["source_label"] for item in trace["factors"]}
    assert {
        "角色等级系数",
        "有效异常精通",
        "对应属性增伤",
    } <= factor_labels
    assert any(label.startswith("异化系数（当前实现）") for label in factor_labels)


def test_wengine_catalog_exposes_the_reviewed_wengine_validation_set() -> None:
    response = client.get("/api/v1/wengines")

    assert response.status_code == 200
    catalog = response.json()
    assert {item["wengine_id"] for item in catalog} == {
        "wengine:12001",
        "wengine:12002",
        "wengine:12003",
        "wengine:12004",
        "wengine:12005",
        "wengine:12006",
        "wengine:12007",
        "wengine:12008",
        "wengine:12009",
        "wengine:12010",
        "wengine:12011",
        "wengine:12012",
        "wengine:12013",
        "wengine:12014",
        "wengine:12015",
        "wengine:12016",
        "wengine:13001",
        "wengine:13002",
        "wengine:13003",
        "wengine:13004",
        "wengine:13005",
        "wengine:13006",
        "wengine:13007",
        "wengine:13008",
        "wengine:13009",
        "wengine:13010",
        "wengine:13011",
        "wengine:13012",
        "wengine:13013",
        "wengine:13014",
        "wengine:13015",
        "wengine:13016",
        "wengine:13017",
        "wengine:13018",
        "wengine:13019",
        "wengine:13020",
        "wengine:13021",
        "wengine:13101",
        "wengine:13106",
        "wengine:13108",
        "wengine:13111",
        "wengine:13112",
        "wengine:13113",
        "wengine:13115",
        "wengine:13127",
        "wengine:13128",
        "wengine:13135",
        "wengine:13142",
        "wengine:13144",
        "wengine:14001",
        "wengine:14002",
        "wengine:14003",
        "wengine:13103",
        "wengine:14102",
        "wengine:14104",
        "wengine:14105",
        "wengine:14107",
        "wengine:14109",
        "wengine:14110",
        "wengine:14114",
        "wengine:14116",
        "wengine:14117",
        "wengine:14118",
        "wengine:14119",
        "wengine:14120",
        "wengine:14121",
        "wengine:14122",
        "wengine:14124",
        "wengine:14125",
        "wengine:14126",
        "wengine:14129",
        "wengine:14130",
        "wengine:14132",
        "wengine:14133",
        "wengine:14134",
        "wengine:14137",
        "wengine:14138",
        "wengine:14139",
        "wengine:14131",
        "wengine:14143",
        "wengine:14145",
        "wengine:14149",
        "wengine:14136",
        "wengine:14140",
        "wengine:14141",
        "wengine:14146",
        "wengine:14147",
        "wengine:14148",
        "wengine:14150",
        "wengine:14151",
        "wengine:14152",
        "wengine:14153",
        "wengine:14154",
        "wengine:14155",
        "wengine:14156",
        "wengine:14157",
        "wengine:14158",
        "wengine:14159",
        "wengine:14161",
        "wengine:14162",
    }
    assert {item["specialty"] for item in catalog} == {
        "attack",
        "support",
        "anomaly",
        "stun",
        "defense",
        "rupture",
        "vanguard",
    }
    assert (
        next(item for item in catalog if item["wengine_id"] == "wengine:14131")[
            "signature_character_id"
        ]
        == "character:1311"
    )
    assert all("rule_item_ids" not in item for item in catalog)
    assert all(
        item["signature_character_id"] is None
        for item in catalog
        if item["wengine_id"].startswith("wengine:120")
        and item["wengine_id"] != "wengine:12006"
    )
    assert {
        (item["wengine_id"], item["signature_character_id"])
        for item in catalog
        if item["signature_character_id"] is not None
    } >= {
        ("wengine:13101", "character:1011"),
        ("wengine:14136", "character:1361"),
        ("wengine:14140", "character:1401"),
        ("wengine:14141", "character:1411"),
    }


def test_drive_disc_catalog_and_editor_cover_the_frozen_thirty_sets() -> None:
    catalog_response = client.get("/api/v1/drive-discs")
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert len(catalog) == 30
    assert {item["set_id"] for item in catalog} >= {
        "drive-disc:31000",
        "drive-disc:34100",
        "drive-disc:34200",
    }
    assert all(
        item["two_piece_disposition"]
        in {"static-contribution", "calculation-rule", "ignored-non-damage"}
        and item["four_piece_disposition"] in {"calculation-rule", "ignored-non-damage"}
        for item in catalog
    )
    proto = next(item for item in catalog if item["set_id"] == "drive-disc:31900")
    assert proto["two_piece_disposition"] == "ignored-non-damage"
    assert "护盾" in proto["ignored_two_piece_reason"]
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "drive-discs"
    assert all(
        (asset_root / Path(item["icon_path"]).name).is_file() for item in catalog
    )

    preview = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [],
            "condition_context": {},
        },
    )
    assert preview.status_code == 200
    payload = preview.json()
    assert [item["slot"] for item in payload["slot_schemas"]] == [1, 2, 3, 4, 5, 6]
    attack_flat = next(
        item for item in payload["substat_options"] if item["stat_key"] == "attack-flat"
    )
    assert attack_flat["value_per_roll"] == 19.0


def test_drive_disc_preview_exposes_owner_qualified_four_piece_rules() -> None:
    substats = [
        {"stat": "attack-flat", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    slot_two_substats = [
        {"stat": "attack-percent", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    response = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [
                {
                    "slot": 1,
                    "set_id": "drive-disc:31000",
                    "main_stat": "hp-flat",
                    "substats": substats,
                },
                {
                    "slot": 2,
                    "set_id": "drive-disc:31000",
                    "main_stat": "attack-flat",
                    "substats": slot_two_substats,
                },
                {
                    "slot": 3,
                    "set_id": "drive-disc:31000",
                    "main_stat": "defense-flat",
                    "substats": substats,
                },
                {
                    "slot": 4,
                    "set_id": "drive-disc:31000",
                    "main_stat": "attack-percent",
                    "substats": substats,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["set_counts"] == [{"set_id": "drive-disc:31000", "count": 4}]
    rule = payload["rule_items"][0]
    assert rule["source_type"] == "drive-disc"
    assert "owner:character_1431" in rule["rule_id"]
    assert rule["stack"] == {"default": 3, "minimum": 0, "maximum": 3}


def test_drive_disc_preview_preserves_partial_input_as_a_blocking_diagnostic() -> None:
    response = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [
                {
                    "slot": 4,
                    "set_id": "drive-disc:31000",
                    "main_stat": None,
                    "substats": [],
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["diagnostics"]
    assert all(item["blocking"] for item in payload["diagnostics"])


def test_drive_disc_incomplete_input_blocks_formal_calculation() -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": {
            "hp": 10000.0,
            "attack": 1200.0,
            "defense": 500.0,
            "impact": 100.0,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "crit_rate": 0.65,
            "crit_damage": 0.5,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0},
        },
        "drive_discs": [
            {
                "slot": 4,
                "set_id": "drive-disc:31000",
                "main_stat": None,
                "substats": [],
            }
        ],
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "requires four substats" in response.json()["diagnostics"][0]["message"]


def test_drive_disc_static_and_four_piece_rules_reach_move_execution() -> None:
    payload = _valid_calculation_payload()
    stats = {
        "hp": 10000.0,
        "attack": 1200.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.65,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0},
    }
    substats = [
        {"stat": "attack-flat", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    slot_two_substats = [
        {"stat": "attack-percent", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": stats,
        "drive_discs": [
            {
                "slot": 1,
                "set_id": "drive-disc:31000",
                "main_stat": "hp-flat",
                "substats": substats,
            },
            {
                "slot": 2,
                "set_id": "drive-disc:31000",
                "main_stat": "attack-flat",
                "substats": slot_two_substats,
            },
            {
                "slot": 3,
                "set_id": "drive-disc:31000",
                "main_stat": "defense-flat",
                "substats": substats,
            },
            {
                "slot": 4,
                "set_id": "drive-disc:31000",
                "main_stat": "attack-percent",
                "substats": substats,
            },
        ],
    }
    rule_id = "rule:drive-disc:31000:owner:character_1431:4pc:attack-stacks"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 2}

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    snapshot = result["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == pytest.approx(2433.16)
    assert snapshot["stats"]["crit_rate"] == pytest.approx(0.922)
    assert any(
        item["source_type"] == "drive-disc-set"
        and item["contribution_id"].endswith(":2pc")
        for item in result["build_provenance"]
    )
    assert any(
        item["effect_id"].endswith(":attack") and item["source_type"] == "drive-disc"
        for item in result["panel_traces"]
    )


def test_equipment_calculation_uses_reviewed_character_base_stats_when_omitted() -> (
    None
):
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    stats = response.json()["resolved_character_snapshots"][0]["stats"]
    assert stats["attack"] == pytest.approx(1681.2102)
    assert stats["crit_rate"] == pytest.approx(0.194)
    assert stats["crit_damage"] == pytest.approx(0.98)


def test_wengine_preview_exposes_owner_qualified_rules_for_the_editor() -> None:
    response = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14131",
            "equipped_character_id": "character:1311",
            "team_character_ids": ["character:1431", "character:1311"],
            "level": 60,
            "refinement": 1,
            "condition_values": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["equipped_character_id"] == "character:1311"
    assert payload["rule_items"][0]["rule_id"] == (
        "rule:wengine:14131:owner:1311:team-damage"
    )
    assert payload["rule_items"][0]["source_type"] == "weapon"
    assert payload["scenario_conditions"][0]["editable"] is True


def test_wengine_preview_uses_resolved_external_static_condition_context() -> None:
    def preview(value: bool):
        return client.post(
            "/api/v1/wengines/preview",
            json={
                "wengine_id": "wengine:14143",
                "equipped_character_id": "character:1431",
                "team_character_ids": ["character:1431"],
                "condition_context": {
                    "condition:ye:mingxin-active": value,
                },
            },
        ).json()

    active = preview(True)
    inactive = preview(False)
    active_veil = next(
        item for item in active["rule_items"] if item["rule_id"].endswith(":veil")
    )
    inactive_veil = next(
        item for item in inactive["rule_items"] if item["rule_id"].endswith(":veil")
    )
    assert active_veil["availability"] == "available"
    assert inactive_veil["availability"] == "unavailable"
    assert all(
        item["condition_id"] != "condition:ye:mingxin-active"
        for item in active["scenario_conditions"]
    )


def test_wengine_preview_marks_impossible_owner_mechanics_ineligible() -> None:
    deep_sea = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14119",
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
        },
    ).json()
    dash_rule = next(
        item
        for item in deep_sea["rule_items"]
        if item["rule_id"].endswith(":dash-crit-buff")
    )
    assert dash_rule["eligibility"] == "ineligible"

    dream = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14145",
            "equipped_character_id": "character:1311",
            "team_character_ids": ["character:1311"],
        },
    ).json()
    assert dream["rule_items"][0]["eligibility"] == "ineligible"


def test_definition_preview_returns_versioned_editor_view() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1311",
            "team_character_ids": ["character:1311", "character:1431"],
            "compile_config": {
                "core_level": 1,
                "cinema_level": 6,
            },
            "condition_values": {
                "condition:astra:aria-active": True,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "presentation-v1"
    assert payload["character_id"] == "character:1311"
    assert payload["moves"]
    assert payload["rule_items"]
    field_ids = {item["field_id"] for item in payload["compile_config_fields"]}
    assert {"core_level", "cinema_level"}.issubset(field_ids)
    assert "additional_ability_eligible" not in field_ids


def test_miyabi_and_vivian_independent_damage_entries_are_visible() -> None:
    miyabi_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1091",
            "team_character_ids": ["character:1091"],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert miyabi_preview.status_code == 200, miyabi_preview.text
    frostburn = next(
        item for item in miyabi_preview.json()["moves"]
        if item["entry_id"] == "move-entry:character:1091:frostburn-break"
    )
    assert frostburn["move_id"] is None
    assert frostburn["skill_group"] is None
    assert frostburn["damage_tags"] == []

    vivian_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1331",
            "team_character_ids": ["character:1331"],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert vivian_preview.status_code == 200, vivian_preview.text
    discharge = next(
        item for item in vivian_preview.json()["moves"]
        if item["entry_id"] == "move-entry:character:1331:discharge-current-panel"
    )
    assert discharge["label"] == "异放（薇薇安当前面板）"
    assert discharge["move_id"] is None
    assert discharge["skill_group"] is None
    assert discharge["damage_tags"] == []


def test_astra_finale_tremolo_and_cluster_have_direct_selectable_entries() -> None:
    preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1311",
            "team_character_ids": ["character:1311"],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert preview.status_code == 200, preview.text
    moves = {item["entry_id"]: item for item in preview.json()["moves"]}
    tremolo_id = "move-entry:astra:1311:selectable-finale-tremolo"
    cluster_id = "move-entry:astra:1311:selectable-finale-cluster"
    assert moves[tremolo_id]["move_id"] is None
    assert "tremolo-damage" in moves[tremolo_id]["damage_tags"]
    assert moves[cluster_id]["move_id"] is None
    assert "cluster-damage" in moves[cluster_id]["damage_tags"]

    def payload_for(entry_id: str) -> dict:
        payload = _valid_calculation_payload()
        payload.update(
            {
                "primary_character_id": "character:1311",
                "supporting_character_ids": [],
                "team_character_ids": ["character:1311"],
                "move_entry_id": entry_id,
                "compile_configs": {
                    "character:1311": {"core_level": 1, "cinema_level": 0},
                },
                "condition_values": {
                    "condition:astra:aria-active": True,
                    "condition:astra:energy-derived-active": True,
                },
                "character_builds": {
                    "character:1311": {
                        "level": 60,
                        "out_of_combat_stats": {
                            "hp": 10000.0,
                            "attack": 1000.0,
                            "defense": 500.0,
                            "impact": 100.0,
                            "crit_rate": 0.5,
                            "crit_damage": 0.5,
                            "anomaly_mastery": 100.0,
                            "anomaly_proficiency": 100.0,
                            "energy_regen": 1.2,
                            "penetration_rate": 0.0,
                            "penetration_flat": 0.0,
                            "element_damage_bonus": {"ether": 0.0},
                        },
                    },
                },
                "enemy": {
                    "enemy_id": "enemy:astra-selectable-child",
                    "level": 60,
                    "initial_defense": 1000.0,
                    "damage_resistance": {"ether": 0.2},
                    "damage_reduction": 0.0,
                    "stun_vulnerability_bonus": 0.0,
                    "is_stunned": False,
                },
                "enabled_rule_item_ids": [],
            }
        )
        return payload

    tremolo_response = client.post(
        "/api/v1/moves/calculate", json=payload_for(tremolo_id)
    )
    assert tremolo_response.status_code == 200, tremolo_response.text
    tremolo = tremolo_response.json()
    assert tremolo["totals"]["expected"]["complete"] is True
    assert len(tremolo["events"]) == 1
    assert tremolo["events"][0]["repeat_count"] == 1

    cluster_response = client.post(
        "/api/v1/moves/calculate", json=payload_for(cluster_id)
    )
    assert cluster_response.status_code == 200, cluster_response.text
    cluster = cluster_response.json()
    assert cluster["totals"]["expected"]["complete"] is True
    assert len(cluster["events"]) == 1
    assert cluster["events"][0]["repeat_count"] == 3


def test_other_self_contained_damage_options_appear_in_character_previews() -> None:
    cases = (
        (
            "character:1371",
            ["character:1371", "character:1311"],
            {"core_level": 1, "cinema_level": 1},
            {
                "move-entry:character:1371:extra-ability-lightning-selectable",
                "move-entry:character:1371:cinema1-lightning-selectable",
            },
        ),
        (
            "character:1451",
            ["character:1451"],
            {"core_level": 1, "cinema_level": 6},
            {"move-entry:character:1451:core-additional-attack"},
        ),
        (
            "character:1021",
            ["character:1021"],
            {"core_level": 1, "cinema_level": 0, "potential_level": 1},
            {"move-entry:character:1021:potential-super-furry-mark"},
        ),
        (
            "character:1401",
            ["character:1401"],
            {"core_level": 1, "cinema_level": 6},
            {
                "move-entry:alice:1401:core-periodic-extra",
                "move-entry:alice:1401:cinema6-decisive-extra-attack",
            },
        ),
        (
            "character:1331",
            ["character:1331"],
            {"core_level": 7, "cinema_level": 0},
            {"move-entry:character:1331:core-prophecy-tick"},
        ),
        (
            "character:1361",
            ["character:1361"],
            {"core_level": 1, "cinema_level": 6},
            {
                "move-entry:character:1361:cinema4-severance",
                "move-entry:character:1361:cinema6-armor-piercing-round",
            },
        ),
        (
            "character:1411",
            ["character:1411"],
            {"core_level": 1, "cinema_level": 6},
            {
                "move-entry:character:1411:cinema6-strong-shell",
                "move-entry:character:1411:cinema6-sweet-scare-fireworks",
            },
        ),
    )
    for character_id, team_ids, config, expected_ids in cases:
        response = client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": character_id,
                "team_character_ids": team_ids,
                "compile_config": config,
            },
        )
        assert response.status_code == 200, response.text
        moves = {item["entry_id"]: item for item in response.json()["moves"]}
        assert expected_ids.issubset(moves)

    lucia_response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1451",
            "team_character_ids": ["character:1451"],
            "compile_config": {"core_level": 1, "cinema_level": 6},
        },
    )
    follow_up = next(
        item
        for item in lucia_response.json()["moves"]
        if item["entry_id"] == "move-entry:character:1451:core-additional-attack"
    )
    assert follow_up["move_id"] is None
    assert follow_up["skill_group"] is None
    assert follow_up["damage_tags"] == ["follow-up-attack-damage"]


def test_vivian_discharge_selector_returns_typed_discharge_without_summing_sources() -> None:
    owner = "character:1331"
    teammate = "character:1311"
    discharge_rule = "rule:character:1331:core:anomaly-mutation:ether"

    def payload_for(supporting: tuple[str, ...]) -> dict:
        payload = _valid_calculation_payload()
        team = (owner, *supporting)
        conditions = {}
        if teammate in supporting:
            conditions.update(
                {
                    "condition:vivian:mutation-triggered": True,
                    "condition:astra:core-attack-buff-active": False,
                    "condition:astra:aria-active": False,
                    "condition:astra:energy-derived-active": False,
                }
            )
        payload.update(
            {
                "primary_character_id": owner,
                "supporting_character_ids": list(supporting),
                "team_character_ids": list(team),
                "move_entry_id": "move-entry:character:1331:discharge-current-panel",
                "compile_configs": {
                    character_id: {"core_level": 7, "cinema_level": 0}
                    for character_id in team
                },
                **({"condition_values": conditions} if conditions else {}),
                "character_builds": {
                    character_id: {
                        "level": 60,
                        "build_mode": "equipment-build",
                        "drive_discs": [],
                    }
                    for character_id in team
                },
                "enemy": {
                    "enemy_id": "enemy:ui",
                    "level": 70,
                    "initial_defense": 857.0,
                    "damage_resistance": {},
                    "damage_reduction": 0.0,
                    "stun_vulnerability_bonus": 1.5,
                    "is_stunned": False,
                },
                "selected_trigger_inputs": [],
                "rule_stack_counts": {},
            }
        )
        if supporting:
            payload["enabled_rule_item_ids"] = [discharge_rule]
        else:
            payload.pop("enabled_rule_item_ids", None)
        return payload

    solo_response = client.post(
        "/api/v1/moves/calculate",
        json=payload_for(()),
    )
    assert solo_response.status_code == 200, solo_response.text
    solo = solo_response.json()
    assert solo["totals"]["expected"]["complete"] is True
    assert solo["totals"]["expected"]["value"] > 0.0
    assert len(solo["events"]) == 1
    assert solo["events"][0]["damage_subtype"] == "discharge"
    assert [item["source_character_id"] for item in solo["panel_source_results"]] == [owner]
    assert solo["panel_source_results"][0]["totals"]["expected"]["value"] == pytest.approx(
        solo["totals"]["expected"]["value"]
    )

    team_response = client.post(
        "/api/v1/moves/calculate",
        json=payload_for((teammate,)),
    )
    assert team_response.status_code == 200, team_response.text
    team = team_response.json()
    assert team["totals"]["expected"]["complete"] is True
    assert len(team["events"]) == 1
    assert team["totals"]["expected"]["value"] == pytest.approx(
        team["events"][0]["modes"]["expected"]["known_value"]
    )
    assert [item["source_character_id"] for item in team["panel_source_results"]] == [owner, teammate]
    vivian_result = team["panel_source_results"][0]["totals"]["expected"]
    teammate_result = team["panel_source_results"][1]["totals"]["expected"]
    assert vivian_result["value"] == pytest.approx(team["totals"]["expected"]["value"])
    assert teammate_result["complete"] is True
    assert teammate_result["value"] > 0.0
    assert team["totals"]["expected"]["value"] != pytest.approx(
        vivian_result["value"] + teammate_result["value"]
    )


def test_vivian_discharge_selector_returns_own_event_and_keeps_teammate_group_separate() -> None:
    owner = "character:1331"
    teammate = "character:1311"
    discharge_rule = "rule:character:1331:core:anomaly-mutation:ether"

    def payload_for(supporting: tuple[str, ...]) -> dict:
        payload = _valid_calculation_payload()
        team = (owner, *supporting)
        payload.update(
            {
                "primary_character_id": owner,
                "supporting_character_ids": list(supporting),
                "team_character_ids": list(team),
                "move_entry_id": "move-entry:character:1331:discharge-current-panel",
                "compile_configs": {
                    character_id: {"core_level": 7, "cinema_level": 0}
                    for character_id in team
                },
                "condition_values": {
                    "condition:vivian:mutation-triggered": True,
                    **(
                        {
                            "condition:astra:core-attack-buff-active": False,
                            "condition:astra:aria-active": False,
                            "condition:astra:energy-derived-active": False,
                        }
                        if teammate in supporting
                        else {}
                    ),
                },
                "character_builds": {
                    character_id: {
                        "level": 60,
                        "build_mode": "equipment-build",
                        "drive_discs": [],
                    }
                    for character_id in team
                },
                "enemy": {
                    "enemy_id": "enemy:ui",
                    "level": 70,
                    "initial_defense": 857.0,
                    "damage_resistance": {},
                    "damage_reduction": 0.0,
                    "stun_vulnerability_bonus": 1.5,
                    "is_stunned": False,
                },
                "selected_trigger_inputs": [],
                "rule_stack_counts": {},
            }
        )
        payload["enabled_rule_item_ids"] = [discharge_rule]
        return payload

    solo_response = client.post(
        "/api/v1/moves/calculate",
        json=payload_for(()),
    )
    assert solo_response.status_code == 200, solo_response.text
    solo = solo_response.json()
    assert solo["totals"]["expected"]["complete"] is True
    assert solo["totals"]["expected"]["value"] > 0.0
    assert len(solo["events"]) == 1
    assert solo["events"][0]["damage_subtype"] == "discharge"
    assert [item["source_character_id"] for item in solo["panel_source_results"]] == [owner]
    assert solo["panel_source_results"][0]["totals"]["expected"]["value"] == pytest.approx(
        solo["totals"]["expected"]["value"]
    )

    team_response = client.post(
        "/api/v1/moves/calculate",
        json=payload_for((teammate,)),
    )
    assert team_response.status_code == 200, team_response.text
    team = team_response.json()
    assert team["totals"]["expected"]["value"] == pytest.approx(
        team["events"][0]["modes"]["expected"]["known_value"]
    )
    assert team["totals"]["expected"]["complete"] is True
    assert len(team["events"]) == 1
    assert [item["source_character_id"] for item in team["panel_source_results"]] == [owner, teammate]
    owner_result = team["panel_source_results"][0]["totals"]["expected"]
    assert owner_result["value"] == pytest.approx(team["totals"]["expected"]["value"])
    teammate_result = team["panel_source_results"][1]["totals"]["expected"]
    assert teammate_result["complete"] is True
    assert teammate_result["value"] > 0.0


def test_progress_preview_defaults_core_and_cinema_to_full_core_and_zero_sliders() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1011",
            "team_character_ids": ["character:1011"],
            "compile_config": {},
        },
    )
    assert response.status_code == 200, response.text
    fields = {item["field_id"]: item for item in response.json()["compile_config_fields"]}
    assert fields["core_level"]["value"] == 7
    assert fields["core_level"]["field_type"] == "slider"
    assert fields["cinema_level"]["value"] == 0
    assert fields["cinema_level"]["field_type"] == "slider"

    explicit = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1011",
            "team_character_ids": ["character:1011"],
            "compile_config": {"core_level": 2, "cinema_level": 4},
        },
    )
    assert explicit.status_code == 200, explicit.text
    explicit_fields = {item["field_id"]: item for item in explicit.json()["compile_config_fields"]}
    assert explicit_fields["core_level"]["value"] == 2
    assert explicit_fields["cinema_level"]["value"] == 4


def test_calculate_api_accepts_missing_progress_config_with_full_core_defaults() -> None:
    owner = "character:1091"
    payload = _valid_calculation_payload()
    payload.update(
        {
            "primary_character_id": owner,
            "supporting_character_ids": [],
            "team_character_ids": [owner],
            "move_entry_id": "move-entry:character:1091:kazahana-1",
            "compile_configs": {owner: {}},
            "character_builds": {
                owner: {"level": 60, "build_mode": "equipment-build", "drive_discs": []}
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 70,
                "initial_defense": 857.0,
                "damage_resistance": {},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
            "enabled_rule_item_ids": [],
            "selected_trigger_inputs": [],
            "rule_stack_counts": {},
        }
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["totals"]["expected"]["complete"] is True


def test_astra_aria_condition_controls_preview_availability_and_move_execution() -> None:
    previews = {
        aria: client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": "character:1311",
                "team_character_ids": ["character:1311", "character:1431"],
                "compile_config": {"core_level": 1, "cinema_level": 6},
                "condition_values": {"condition:astra:aria-active": aria},
            },
        ).json()
        for aria in (False, True)
    }
    false_rules = {item["rule_id"]: item for item in previews[False]["rule_items"]}
    true_rules = {item["rule_id"]: item for item in previews[True]["rule_items"]}
    aria_rule_ids = {
        "rule:astra:1311:aria-team-buff",
        "rule:astra:1311:finale-derived",
        "rule:astra:1311:extra-ability",
        "rule:astra:1311:extra-ability-entry",
        "rule:astra:1311:cinema2",
        "rule:astra:1311:cinema4",
        "rule:astra:1311:cinema6",
    }
    assert all(false_rules[item]["availability"] == "unavailable" for item in aria_rule_ids)
    assert all(
        true_rules[item]["availability"] == "available"
        for item in {
            "rule:astra:1311:aria-team-buff",
            "rule:astra:1311:cinema2",
            "rule:astra:1311:cinema4",
            "rule:astra:1311:cinema6",
        }
    )
    # ARIA is a separate prerequisite from energy: an ARIA-only RuleItem is
    # available, while an ARIA+energy RuleItem remains blocked until energy is
    # explicitly selected.
    assert true_rules["rule:astra:1311:finale-derived"]["availability"] == "blocked"
    assert true_rules["rule:astra:1311:extra-ability"]["availability"] == "blocked"
    assert true_rules["rule:astra:1311:extra-ability-entry"]["availability"] == "blocked"
    assert all(
        item["condition_id"] == "condition:astra:aria-active"
        for item in previews[True]["scenario_conditions"][:1]
    )

    false_result = client.post(
        "/api/v1/moves/calculate",
        json=_astra_aria_payload(aria=False),
    )
    true_result = client.post(
        "/api/v1/moves/calculate",
        json=_astra_aria_payload(aria=True),
    )
    assert false_result.status_code == true_result.status_code == 200
    assert false_result.json()["events"] == []
    assert true_result.json()["events"][0]["semantic_id"].endswith(
        "basic-interlude-1:main"
    )


def test_astra_aria_calculation_keeps_independent_rule_switch_and_trace_lanes() -> None:
    from core.presentation.calculation_service import _presentation_request, _scenario
    from core.presentation.registry import compile_registered_definition

    payload = _astra_aria_payload(aria=True, cinema_level=6)
    request_view = _presentation_request(payload)
    assert request_view.selected_condition_values["condition:astra:aria-active"] is True
    definition = compile_registered_definition(
        "character:1311",
        {"core_level": 1, "cinema_level": 6},
        ("character:1311",),
    )
    scenario = _scenario(
        payload,
        (definition,),
        definition.character_id,
        (definition.character_id,),
    )
    assert next(
        item for item in scenario.conditions
        if str(item.condition_id) == "condition:astra:aria-active"
    ).value is True

    enabled = "rule:astra:1311:cinema6"
    payload["enabled_rule_item_ids"] = [enabled]
    with_rule = client.post("/api/v1/moves/calculate", json=payload)
    assert with_rule.status_code == 200, with_rule.text
    with_trace = with_rule.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:astra:1311:cinema6:multiplier"
        for item in with_trace["event_multiplier_modifiers"]
    )

    payload["enabled_rule_item_ids"] = []
    without_rule = client.post("/api/v1/moves/calculate", json=payload)
    assert without_rule.status_code == 200, without_rule.text
    without_trace = without_rule.json()["events"][0]["common_application_trace"]
    assert not any(
        item["effect_id"] == "effect:astra:1311:cinema6:multiplier"
        for item in without_trace["event_multiplier_modifiers"]
    )


def test_unrelated_character_preview_does_not_gain_astra_aria_condition() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "compile_config": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            },
            "condition_values": {"condition:astra:aria-active": True},
        },
    )
    assert response.status_code == 200
    assert all(
        item["condition_id"] != "condition:astra:aria-active"
        for item in response.json()["scenario_conditions"]
    )


def test_production_ye_primary_astra_support_aria_changes_entry_trace_and_events() -> None:
    inactive = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_support_payload(aria=False),
    )
    active = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_support_payload(aria=True),
    )
    assert inactive.status_code == active.status_code == 200

    inactive_payload = inactive.json()
    active_payload = active.json()
    assert [item["semantic_id"] for item in inactive_payload["events"]] == [
        "damage:ye:1431:assist-yuanshou:main"
    ]
    assert [item["semantic_id"] for item in active_payload["events"]] == [
        "damage:ye:1431:assist-yuanshou:main",
        "event:astra:1311:entry-tremolo",
        "event:astra:1311:entry-cluster",
    ]
    entry_trace = active_payload["events"][0]["common_application_trace"]
    aria_rule = next(
        item
        for item in entry_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:extra-ability-entry"
    )
    assert aria_rule["status"] == "matched"
    assert {item["status"] for item in aria_rule["effects"]} == {"matched"}
    assert {item["effect_id"] for item in aria_rule["effects"]} == {
        "effect:astra:1311:extra-entry-tremolo",
        "effect:astra:1311:extra-entry-cluster",
    }
    assert active_payload["totals"]["expected"]["value"] != inactive_payload[
        "totals"
    ]["expected"]["value"]


def test_production_ye_primary_astra_aria_team_buff_changes_damage_and_team_crit_panel() -> None:
    inactive = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_aria_team_buff_payload(aria=False),
    )
    active = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_aria_team_buff_payload(aria=True),
    )
    assert inactive.status_code == active.status_code == 200

    inactive_payload = inactive.json()
    active_payload = active.json()
    assert [item["semantic_id"] for item in inactive_payload["events"]] == [
        "damage:ye:1431:basic-fast-1:main"
    ]
    assert [item["semantic_id"] for item in active_payload["events"]] == [
        "damage:ye:1431:basic-fast-1:main"
    ]

    inactive_trace = inactive_payload["events"][0]["common_application_trace"]
    active_trace = active_payload["events"][0]["common_application_trace"]
    inactive_rule = next(
        item
        for item in inactive_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:aria-team-buff"
    )
    active_rule = next(
        item
        for item in active_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:aria-team-buff"
    )
    assert inactive_rule["status"] == "not-matched"
    assert active_rule["status"] == "matched"
    assert {item["status"] for item in active_rule["effects"]} == {"matched"}
    assert {item["effect_id"] for item in active_rule["effects"]} == {
        "effect:astra:1311:aria-team-damage",
        "effect:astra:1311:aria-team-crit-damage",
    }
    damage_modifiers = [
        item
        for item in active_trace["applied_modifiers"]
        if item["effect_id"] == "effect:astra:1311:aria-team-damage"
    ]
    assert len(damage_modifiers) == 1
    assert damage_modifiers[0]["modifier_path"] == "damage.normal-bonus"
    assert damage_modifiers[0]["value"] == pytest.approx(0.20)

    crit_panel_traces = [
        item
        for item in active_payload["panel_traces"]
        if item["effect_id"] == "effect:astra:1311:aria-team-crit-damage"
    ]
    assert {item["recipient_character_id"] for item in crit_panel_traces} == {
        "character:1431",
        "character:1311",
    }
    assert all(
        item["modifier_path"] == "character.current.crit-damage"
        for item in crit_panel_traces
    )
    assert all(
        item["resolved_value"] == pytest.approx(0.25)
        for item in crit_panel_traces
    )

    inactive_snapshots = {
        item["character_id"]: item
        for item in inactive_payload["resolved_character_snapshots"]
    }
    active_snapshots = {
        item["character_id"]: item
        for item in active_payload["resolved_character_snapshots"]
    }
    assert (
        inactive_snapshots["character:1431"]["stats"]["crit_damage"]
        == pytest.approx(0.5)
    )
    assert (
        inactive_snapshots["character:1311"]["stats"]["crit_damage"]
        == pytest.approx(0.5)
    )
    assert (
        active_snapshots["character:1431"]["stats"]["crit_damage"]
        == pytest.approx(0.75)
    )
    assert (
        active_snapshots["character:1311"]["stats"]["crit_damage"]
        == pytest.approx(0.75)
    )
    assert active_payload["totals"]["expected"]["value"] != inactive_payload[
        "totals"
    ]["expected"]["value"]


def test_production_aria_team_buff_rule_switch_is_independent_from_active_state() -> None:
    payload = _ye_primary_astra_aria_team_buff_payload(aria=True)
    enabled = client.post("/api/v1/moves/calculate", json=payload)
    payload["enabled_rule_item_ids"] = []
    disabled = client.post("/api/v1/moves/calculate", json=payload)
    assert enabled.status_code == disabled.status_code == 200
    enabled_payload = enabled.json()
    disabled_payload = disabled.json()
    enabled_trace = enabled_payload["events"][0]["common_application_trace"]
    disabled_trace = disabled_payload["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:astra:1311:aria-team-damage"
        for item in enabled_trace["applied_modifiers"]
    )
    assert not any(
        item["effect_id"] == "effect:astra:1311:aria-team-damage"
        for item in disabled_trace["applied_modifiers"]
    )
    assert not any(
        item["effect_id"] == "effect:astra:1311:aria-team-crit-damage"
        for item in disabled_payload["panel_traces"]
    )
    assert enabled_payload["totals"]["expected"]["value"] != disabled_payload[
        "totals"
    ]["expected"]["value"]


def test_production_aria_trace_explains_missing_trigger_without_faking_a_match() -> None:
    payload = _ye_primary_astra_support_payload(aria=True)
    payload["selected_trigger_inputs"] = []
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    result = response.json()
    trace = result["events"][0]["common_application_trace"]
    aria_rule = next(
        item
        for item in trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:extra-ability-entry"
    )
    assert aria_rule["status"] == "blocked"
    assert all(item["status"] == "blocked" for item in aria_rule["effects"])
    assert any(
        "no scenario trigger fact" in diagnostic["message"]
        for effect in aria_rule["effects"]
        for diagnostic in effect["diagnostics"]
    )


def test_invalid_requests_are_structured() -> None:
    invalid = client.post(
        "/api/v1/definitions/preview", json={"character_id": "unknown"}
    )
    assert invalid.status_code == 400
    assert invalid.json()["diagnostics"][0]["blocking"] is True

    invalid_calculation = client.post("/api/v1/moves/calculate", json={})
    assert invalid_calculation.status_code == 400
    assert invalid_calculation.json()["diagnostics"][0]["blocking"] is True


def test_root_static_mount_does_not_swallow_api_routes() -> None:
    assert client.get("/api/health").json() == {
        "status": "ok",
        "schema_version": "presentation-v1",
    }


def test_move_calculation_executes_all_three_display_modes() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                }
            },
            "character_builds": {
                "character:1431": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1200.0,
                        "crit_rate": 0.65,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"physical": 0.0},
                    },
                }
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2, "ether": 0.2},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
            "enabled_rule_item_ids": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload["totals"]) == {"non-crit", "expected", "full-crit"}
    assert payload["events"]
    assert set(payload["events"][0]["modes"]) == {
        "non-crit",
        "expected",
        "full-crit",
    }
    assert payload["build_provenance"]
    assert all(
        item["source_type"] == "manual-panel" for item in payload["build_provenance"]
    )


def test_unselected_move_variant_returns_structured_blocking_diagnostic() -> None:
    payload = _valid_calculation_payload()
    payload["move_entry_id"] = "move-entry:ye:1431:basic-mingxin-zhanliuguang-mie"
    payload["compile_configs"]["character:1431"]["mingxin_active"] = True
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert all(item["complete"] is False for item in result["totals"].values())
    messages = [item["message"] for item in result["diagnostics"]]
    assert any("明心境·斩流光 灭" in message for message in messages)
    assert any("condition:ye:variant:mingxin-zhanliuguang-mie" in message for message in messages)
    assert all(item["blocking"] is True for item in result["diagnostics"])


def test_move_calculation_accepts_astra_as_cross_character_support() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1431",
            "supporting_character_ids": ["character:1311"],
            "team_character_ids": ["character:1431", "character:1311"],
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                },
                "character:1311": {
                    "core_level": 1,
                    "cinema_level": 0,
                },
            },
            "condition_values": {
                "condition:astra:core-attack-buff-active": True,
            },
            "character_builds": {
                "character:1431": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1200.0,
                        "crit_rate": 0.5,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"physical": 0.0},
                    },
                },
                "character:1311": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1500.0,
                        "crit_rate": 0.5,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"ether": 0.0},
                    },
                },
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2, "ether": 0.2},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
            "enabled_rule_item_ids": [
                "rule:astra:1311:core-passive-self",
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recipients = {item["recipient_character_id"] for item in payload["panel_traces"]}
    assert recipients == {"character:1431", "character:1311"}
    core_traces = [
        item
        for item in payload["panel_traces"]
        if item["effect_id"] == "effect:astra:1311:core-self-attack"
    ]
    assert len(core_traces) == 2
    assert payload["resolved_character_snapshots"]


def test_calculation_api_does_not_fill_missing_formal_inputs() -> None:
    import copy

    missing_enemy_state = _valid_calculation_payload()
    del missing_enemy_state["enemy"]["is_stunned"]
    response = client.post("/api/v1/moves/calculate", json=missing_enemy_state)
    assert response.status_code == 400
    assert "is_stunned" in response.json()["diagnostics"][0]["message"]

    missing_attack = _valid_calculation_payload()
    del missing_attack["character_builds"]["character:1431"]["out_of_combat_stats"][
        "attack"
    ]
    response = client.post("/api/v1/moves/calculate", json=missing_attack)
    assert response.status_code == 400
    assert "attack" in response.json()["diagnostics"][0]["message"]

    mismatched_operator = copy.deepcopy(_valid_calculation_payload())
    mismatched_operator["current_operator"] = "character:1311"
    response = client.post("/api/v1/moves/calculate", json=mismatched_operator)
    assert response.status_code == 400
    assert "primary_character_id" in response.json()["diagnostics"][0]["message"]


def test_optional_element_bonus_defaults_to_zero_in_legacy_panel_api() -> None:
    payload = _valid_calculation_payload()
    del payload["character_builds"]["character:1431"]["out_of_combat_stats"][
        "element_damage_bonus"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert result["resolved_character_snapshots"][0]["stats"][
        "element_damage_bonus"
    ]["physical"] == pytest.approx(0.0)


def test_bare_ice_equipment_build_calculates_without_bonus_map_or_enemy_resistance() -> None:
    owner = "character:1091"
    payload = _valid_calculation_payload()
    payload.update(
        {
            "primary_character_id": owner,
            "supporting_character_ids": [],
            "team_character_ids": [owner],
            "move_entry_id": "move-entry:character:1091:kazahana-1",
            "compile_configs": {owner: {"core_level": 1, "cinema_level": 0}},
            "condition_values": {},
            "character_builds": {
                owner: {"level": 60, "build_mode": "equipment-build", "drive_discs": []}
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 70,
                "initial_defense": 857.0,
                "damage_resistance": {},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
            "enabled_rule_item_ids": [],
            "selected_trigger_inputs": [],
            "rule_stack_counts": {},
        }
    )

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    assert _breakdown_value(result["events"][0], "resistance.region") == pytest.approx(1.0)
    snapshot = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    assert snapshot["stats"]["element_damage_bonus"]["ice"] == pytest.approx(0.0)
    assert all(item["source_type"] not in {"weapon", "drive-disc"} for item in result["build_provenance"])


@pytest.mark.parametrize(
    ("owner", "move_entry_id", "compile_config", "resistance_key", "alias_key", "resistance", "expected_region"),
    (
        (
            "character:1091",
            "move-entry:character:1091:lieshuang-anomaly",
            {"core_level": 7, "cinema_level": 0},
            "ice",
            "ice:lieshuang",
            0.20,
            0.80,
        ),
        (
            "character:1371",
            "move-entry:character:1371:basic-xiaoyun-jin-1",
            {"core_level": 7, "cinema_level": 0},
            "ether",
            "ether:xuanmo",
            0.25,
            0.75,
        ),
        (
            "character:1431",
            "move-entry:ye:1431:assist-zhaoying",
            {
                "core_level": 7,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": True,
            },
            "physical",
            "physical:linren",
            0.30,
            0.70,
        ),
    ),
)
def test_alias_enemy_resistance_uses_base_element_pool(
    owner: str,
    move_entry_id: str,
    compile_config: dict[str, object],
    resistance_key: str,
    alias_key: str,
    resistance: float,
    expected_region: float,
) -> None:
    for input_key in (resistance_key, alias_key):
        payload = _valid_calculation_payload()
        payload.update(
            {
                "primary_character_id": owner,
                "supporting_character_ids": [],
                "team_character_ids": [owner],
                "move_entry_id": move_entry_id,
                "compile_configs": {owner: compile_config},
                "character_builds": {
                    owner: {"level": 60, "build_mode": "equipment-build", "drive_discs": []}
                },
                "enemy": {
                    "enemy_id": "enemy:ui",
                    "level": 70,
                    "initial_defense": 857.0,
                    "damage_resistance": {input_key: resistance},
                    "damage_reduction": 0.0,
                    "stun_vulnerability_bonus": 1.5,
                    "is_stunned": False,
                },
                "enabled_rule_item_ids": [],
                "selected_trigger_inputs": [],
                "rule_stack_counts": {},
            }
        )
        response = client.post("/api/v1/moves/calculate", json=payload)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["totals"]["expected"]["complete"] is True
        assert _breakdown_value(
            result["events"][0], "resistance.enemy-initial-region"
        ) == pytest.approx(expected_region)


def test_enemy_resistance_snapshot_has_all_base_elements_and_shared_alias_pools() -> None:
    from core.presentation.calculation_service import _enemy_inputs
    from core.presentation.requests import EnemyInput
    from core.types import Element, Resolved

    def snapshot_for(resistances: dict[str, float]):
        return _enemy_inputs(
            EnemyInput(
                enemy_id="enemy:unit-test",
                level=70,
                initial_defense=857.0,
                damage_resistance=resistances,
            )
        )[0]

    defaults = snapshot_for({})
    assert set(defaults.damage_resistance) == set(Element)
    assert all(value == Resolved(0.0) for value in defaults.damage_resistance.values())

    supplied = snapshot_for(
        {
            "physical": 0.11,
            "fire": 0.12,
            "ice:lieshuang": 0.13,
            "electric": 0.14,
            "ether:xuanmo": 0.15,
            "wind": 0.16,
            "luminance": 0.17,
            "physical:linren": 0.11,
        }
    )
    assert supplied.damage_resistance[Element.ICE] == Resolved(0.13)
    assert supplied.damage_resistance[Element.LIESHUANG] == Resolved(0.13)
    assert supplied.damage_resistance[Element.ETHER] == Resolved(0.15)
    assert supplied.damage_resistance[Element.XUANMO] == Resolved(0.15)
    assert supplied.damage_resistance[Element.PHYSICAL] == Resolved(0.11)
    assert supplied.damage_resistance[Element.LINREN] == Resolved(0.11)
    assert supplied.damage_resistance[Element.FIRE] == Resolved(0.12)
    assert supplied.damage_resistance[Element.ELECTRIC] == Resolved(0.14)
    assert supplied.damage_resistance[Element.WIND] == Resolved(0.16)
    assert supplied.damage_resistance[Element.LUMINANCE] == Resolved(0.17)


@pytest.mark.parametrize("required_source", ("attack", "hp"))
def test_equipment_build_does_not_invent_missing_required_attack_or_hp(
    required_source: str,
) -> None:
    owner = "character:1091"
    payload = _valid_calculation_payload()
    base_stats = {
        "hp": 10000.0,
        "attack": 1000.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "energy_regen": 1.2,
        "element_damage_bonus": {"ice": 0.0},
    }
    del base_stats[required_source]
    payload.update(
        {
            "primary_character_id": owner,
            "supporting_character_ids": [],
            "team_character_ids": [owner],
            "move_entry_id": "move-entry:character:1091:kazahana-1",
            "compile_configs": {owner: {"core_level": 1, "cinema_level": 0}},
            "character_builds": {
                owner: {
                    "level": 60,
                    "build_mode": "equipment-build",
                    "base_stats": base_stats,
                    "drive_discs": [],
                }
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 70,
                "initial_defense": 857.0,
                "damage_resistance": {},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
            },
        }
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert required_source in response.json()["diagnostics"][0]["message"]


def test_cross_specialty_wengine_keeps_static_stats_but_disables_all_talents() -> None:
    owner = "character:1371"
    passive = f"rule:wengine:14001:owner:1371:attack-percent"
    proc = f"rule:wengine:14001:owner:1371:crit-triggered-extra-damage"
    condition = "condition:wengine:14001:owner:1371:crit-triggered-extra-damage-current-hit"
    payload = _single_wengine_payload(
        owner,
        "move-entry:character:1371:basic-xiaoyun-jin-1",
        "wengine:14001",
        5,
        element="ether",
    )
    payload["condition_values"] = {condition: True}
    payload["enabled_rule_item_ids"] = [passive, proc]

    preview = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14001",
            "equipped_character_id": owner,
            "team_character_ids": [owner],
            "level": 60,
            "refinement": 5,
        },
    )
    assert preview.status_code == 200, preview.text
    assert all(item["eligibility"] == "ineligible" for item in preview.json()["rule_items"])

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    snapshot = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    assert snapshot["stats"]["attack"] == pytest.approx(1594.0)
    assert snapshot["stats"]["crit_rate"] == pytest.approx(0.70)
    assert any(
        item["source_type"] == "w-engine"
        and item["stat"] == "attack"
        and item["value"] == pytest.approx(594.0)
        for item in result["build_provenance"]
    )
    assert not any(
        trace["source_type"] == "weapon"
        for trace in result["panel_traces"]
    )


def test_cross_specialty_support_wengine_keeps_advanced_stat_but_not_owner_or_team_effects() -> None:
    owner = "character:1431"
    payload = _single_wengine_payload(
        owner,
        "move-entry:ye:1431:basic-fast-1",
        "wengine:13103",
        5,
        element="physical",
    )
    payload["supporting_character_ids"] = ["character:1311"]
    payload["team_character_ids"] = [owner, "character:1311"]
    payload["compile_configs"]["character:1311"] = {"core_level": 1, "cinema_level": 0}
    payload["character_builds"]["character:1311"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "drive_discs": [],
    }
    passive_ids = [
        f"rule:wengine:13103:owner:1431:{suffix}"
        for suffix in ("all-damage-buff", "energy-regen-flat")
    ]
    payload["enabled_rule_item_ids"] = passive_ids

    preview = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:13103",
            "equipped_character_id": owner,
            "team_character_ids": [owner, "character:1311"],
            "level": 60,
            "refinement": 5,
        },
    )
    assert preview.status_code == 200, preview.text
    assert all(item["eligibility"] == "ineligible" for item in preview.json()["rule_items"])

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    panels = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert panels[owner]["attack"] == pytest.approx(1624.0)
    assert panels[owner]["energy_regen"] == pytest.approx(1.8)
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.0)
    assert not any(trace["source_type"] == "weapon" for trace in result["panel_traces"])


def test_skill_level_and_integer_parameter_inputs_reach_compiler_and_scenario() -> None:
    payload = _valid_calculation_payload()
    payload["move_entry_id"] = "move-entry:ye:1431:basic-cloud"
    payload["compile_configs"]["character:1431"]["skill_levels"] = {
        "basic-attack": 14,
    }
    payload["parameter_values"] = {
        "parameter:ye:flowing-cloud-sword-count": 5,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200


def test_wengine_equipment_build_reaches_build_assembly_and_execution() -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14143:owner:1431:resistance-ignore",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    snapshot = response.json()["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == 1743.0
    assert snapshot["stats"]["crit_damage"] == 0.98
    provenance = response.json()["build_provenance"]
    assert any(
        item["source_id"] == "wengine:14143"
        and item["stat"] == "attack"
        and item["layer"] == "white-value"
        for item in provenance
    )
    payload["enabled_rule_item_ids"] = []
    disabled_response = client.post("/api/v1/moves/calculate", json=payload)
    assert disabled_response.status_code == 200
    disabled_payload = disabled_response.json()
    assert (
        disabled_payload["resolved_character_snapshots"][0]["stats"]["attack"] == 1743.0
    )
    assert not any(
        item["effect_id"].endswith("resistance-ignore")
        for item in disabled_payload["events"][0]["common_application_trace"][
            "applied_modifiers"
        ]
    )


def test_first_remaining_wengine_flows_from_equipment_build_to_owner_direct_damage() -> None:
    expected_bonus = {1: 0.12, 5: 0.20}
    for refinement, bonus in expected_bonus.items():
        payload = _valid_calculation_payload()
        payload["character_builds"]["character:1431"] = {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:12001",
            "wengine_level": 60,
            "wengine_refinement": refinement,
            "base_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.50,
                "crit_damage": 0.50,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "energy_regen": 1.2,
                "element_damage_bonus": {"physical": 0.0},
            },
            "drive_discs": [],
        }
        payload["enabled_rule_item_ids"] = [
            "rule:wengine:12001:owner:1431:basic-dash-counter-damage"
        ]
        response = client.post("/api/v1/moves/calculate", json=payload)

        assert response.status_code == 200, response.text
        result = response.json()
        snapshot = result["resolved_character_snapshots"][0]
        assert snapshot["stats"]["attack"] == pytest.approx(1_770.0)
        event = result["events"][0]
        assert event["damage_type"] == "direct"
        assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(bonus)
        assert _breakdown_value(event, "damage.normal-bonus-region") == pytest.approx(1 + bonus)
        assert any(
            item["effect_id"] == "effect:wengine:12001:owner:1431:basic-dash-counter-damage"
            and item["value"] == pytest.approx(bonus)
            for item in event["common_application_trace"]["applied_modifiers"]
        )
        assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(("refinement", "expected_bonus"), ((1, 0.15), (5, 0.25)))
def test_lunar_decrescent_state_bonus_only_applies_to_its_equipped_damage_dealer(
    refinement: int,
    expected_bonus: float,
) -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = _wengine_build(
        "wengine:12002", refinement, element="physical"
    )
    rule_id = "rule:wengine:12002:owner:1431:damage-buff"
    condition_id = "condition:wengine:12002:owner:1431:damage-buff-active"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["condition_values"] = {condition_id: True}

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert result["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(
        1_770.0
    )
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(
        expected_bonus
    )
    assert result["totals"]["expected"]["complete"] is True

    payload["condition_values"][condition_id] = False
    disabled = client.post("/api/v1/moves/calculate", json=payload).json()
    assert _breakdown_value(disabled["events"][0], "damage.normal-bonus") == 0.0


def test_reverb_support_engines_apply_panel_stats_to_the_active_team() -> None:
    for wengine_id, refinement, suffix, condition_suffix, stat_key, amount in (
        ("wengine:12004", 1, "team-impact", "team-impact-active", "impact", 0.08),
        (
            "wengine:12005",
            5,
            "team-anomaly-stats",
            "team-anomaly-stats-active",
            "anomaly_mastery",
            16.0,
        ),
    ):
        payload = _with_supporting_wengine(
            _valid_calculation_payload(),
            [("character:1311", wengine_id, refinement, "ether")],
        )
        baseline = client.post("/api/v1/moves/calculate", json=payload).json()
        rule_id = f"rule:{wengine_id}:owner:1311:{suffix}"
        condition_id = f"condition:{wengine_id}:owner:1311:{condition_suffix}"
        payload["enabled_rule_item_ids"] = [rule_id]
        payload["condition_values"] = {condition_id: True}
        active_response = client.post("/api/v1/moves/calculate", json=payload)
        assert active_response.status_code == 200, active_response.text
        active = active_response.json()
        before = {
            item["character_id"]: item["stats"]
            for item in baseline["resolved_character_snapshots"]
        }
        after = {
            item["character_id"]: item["stats"]
            for item in active["resolved_character_snapshots"]
        }
        for character_id in ("character:1431", "character:1311"):
            if stat_key == "impact":
                assert after[character_id][stat_key] == pytest.approx(
                    before[character_id][stat_key] * (1 + amount)
                )
            else:
                assert after[character_id][stat_key] == pytest.approx(
                    before[character_id][stat_key] + amount
                )


def test_reverb_mark_ii_mixed_refinements_select_max_for_each_team_stat_path() -> None:
    owners = (
        ("character:1311", "wengine:12005", 1, "ether"),
        ("character:1411", "wengine:12005", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    rule_ids = [
        "rule:wengine:12005:owner:1311:team-anomaly-stats",
        "rule:wengine:12005:owner:1411:team-anomaly-stats",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["condition_values"] = {
        "condition:wengine:12005:owner:1311:team-anomaly-stats-active": True,
        "condition:wengine:12005:owner:1411:team-anomaly-stats-active": True,
    }
    baseline_payload = deepcopy(payload)
    baseline_payload["enabled_rule_item_ids"] = []
    baseline_payload["condition_values"] = {}
    baseline = client.post("/api/v1/moves/calculate", json=baseline_payload)
    assert baseline.status_code == 200, baseline.text
    baseline_stats = {
        item["character_id"]: item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    after_stats = {
        item["character_id"]: item["stats"]
        for item in result["resolved_character_snapshots"]
    }
    for character_id in payload["team_character_ids"]:
        assert after_stats[character_id]["anomaly_mastery"] == pytest.approx(
            baseline_stats[character_id]["anomaly_mastery"] + 16.0
        )
        assert after_stats[character_id]["anomaly_proficiency"] == pytest.approx(
            baseline_stats[character_id]["anomaly_proficiency"] + 16.0
        )
    winner_effect_ids = {
        item["effect_id"] for item in result["panel_traces"]
    }
    assert any(item.startswith("effect:wengine:12005:owner:1411:") for item in winner_effect_ids)
    assert not any(item.startswith("effect:wengine:12005:owner:1311:") for item in winner_effect_ids)


def test_treasure_chest_team_unique_uses_max_while_each_wearer_keeps_self_energy() -> None:
    owners = (
        ("character:1311", "wengine:13103", 1, "ether"),
        ("character:1411", "wengine:13103", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13103:owner:1311:all-damage-buff",
        "rule:wengine:13103:owner:1311:energy-regen-flat",
        "rule:wengine:13103:owner:1411:all-damage-buff",
        "rule:wengine:13103:owner:1411:energy-regen-flat",
    ]
    payload["condition_values"] = {
        "condition:wengine:13103:owner:1311:ether-triggered-buff-active": True,
        "condition:wengine:13103:owner:1411:ether-triggered-buff-active": True,
    }
    baseline_payload = deepcopy(payload)
    baseline_payload["enabled_rule_item_ids"] = []
    baseline_payload["condition_values"] = {}
    baseline = client.post("/api/v1/moves/calculate", json=baseline_payload)
    assert baseline.status_code == 200, baseline.text
    before = {
        item["character_id"]: item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    after = {
        item["character_id"]: item["stats"]
        for item in result["resolved_character_snapshots"]
    }
    assert after["character:1311"]["energy_regen"] == pytest.approx(
        before["character:1311"]["energy_regen"] + 0.5
    )
    assert after["character:1411"]["energy_regen"] == pytest.approx(
        before["character:1411"]["energy_regen"] + 0.8
    )
    event = result["events"][0]
    team_bonus = [
        item
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["modifier_path"] == "damage.normal-bonus"
        and item["effect_id"].startswith("effect:wengine:13103:owner:")
    ]
    assert len(team_bonus) == 1
    assert team_bonus[0]["value"] == pytest.approx(0.24)


@pytest.mark.parametrize(
    ("r1_layers", "r5_layers", "expected_bonus", "winner_owner"),
    (
        (4, 1, 0.10, "1311"),
        (1, 4, 0.16, "1411"),
        (0, 1, 0.04, "1411"),
    ),
)
def test_friendly_cannon_mixed_refinements_maximizes_effective_attack_layers(
    r1_layers: int,
    r5_layers: int,
    expected_bonus: float,
    winner_owner: str,
) -> None:
    owners = (
        ("character:1311", "wengine:13115", 1, "ether"),
        ("character:1411", "wengine:13115", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    rule_ids = [
        "rule:wengine:13115:owner:1311:team-attack-per-ally-stack",
        "rule:wengine:13115:owner:1411:team-attack-per-ally-stack",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["rule_stack_counts"] = {
        rule_ids[0]: r1_layers,
        rule_ids[1]: r5_layers,
    }
    baseline_payload = deepcopy(payload)
    baseline_payload["enabled_rule_item_ids"] = []
    baseline_payload["rule_stack_counts"] = {}
    baseline = client.post("/api/v1/moves/calculate", json=baseline_payload)
    assert baseline.status_code == 200, baseline.text
    before_attack = {
        item["character_id"]: item["stats"]["attack"]
        for item in baseline.json()["resolved_character_snapshots"]
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    after_attack = {
        item["character_id"]: item["stats"]["attack"]
        for item in result["resolved_character_snapshots"]
    }
    for character_id in payload["team_character_ids"]:
        assert after_attack[character_id] == pytest.approx(
            before_attack[character_id] * (1 + expected_bonus)
        )
    active_effects = {
        item["effect_id"] for item in result["panel_traces"]
        if item["effect_id"].startswith("effect:wengine:13115:owner:")
    }
    assert active_effects == {
        f"effect:wengine:13115:owner:{winner_owner}:team-attack-per-ally-stack"
    }


def test_friendly_cannon_defaults_to_four_layers_without_inferring_from_unit_count() -> None:
    rule_id = "rule:wengine:13115:owner:1311:team-attack-per-ally-stack"
    payload = _with_supporting_wengine(
        _valid_calculation_payload(),
        [("character:1311", "wengine:13115", 5, "ether")],
    )
    payload["enabled_rule_item_ids"] = [rule_id]

    def ye_attack(selected: int | None) -> tuple[float, int | None]:
        current = deepcopy(payload)
        if selected is not None:
            current["rule_stack_counts"] = {rule_id: selected}
        response = client.post("/api/v1/moves/calculate", json=current)
        assert response.status_code == 200, response.text
        result = response.json()
        snapshot = next(
            item for item in result["resolved_character_snapshots"]
            if item["character_id"] == "character:1431"
        )
        traces = [
            item for item in result["panel_traces"]
            if item["effect_id"] == "effect:wengine:13115:owner:1311:team-attack-per-ally-stack"
        ]
        return snapshot["stats"]["attack"], traces[0]["stack_count"] if traces else None

    default_attack, default_stack = ye_attack(None)
    zero_attack, zero_stack = ye_attack(0)
    middle_attack, middle_stack = ye_attack(2)
    assert default_stack == 4
    assert zero_stack is None
    assert middle_stack == 2
    assert default_attack == pytest.approx(1200.0 * 1.16)
    assert zero_attack == pytest.approx(1200.0)
    assert middle_attack == pytest.approx(1200.0 * 1.08)


@pytest.mark.parametrize(
    ("refinements", "expected_delta"),
    (((1, 1), 0.08), ((1, 5), 0.12)),
)
def test_duplicate_reverb_tidal_buffs_select_maximum_refinement(
    refinements: tuple[int, int],
    expected_delta: float,
) -> None:
    payload = _with_supporting_wengine(
        _valid_calculation_payload(),
        [
            ("character:1311", "wengine:12004", refinements[0], "ether"),
            ("character:1411", "wengine:12004", refinements[1], "physical"),
        ],
    )
    baseline = client.post("/api/v1/moves/calculate", json=payload).json()
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:12004:owner:1311:team-impact",
        "rule:wengine:12004:owner:1411:team-impact",
    ]
    payload["condition_values"] = {
        "condition:wengine:12004:owner:1311:team-impact-active": True,
        "condition:wengine:12004:owner:1411:team-impact-active": True,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    before = {
        item["character_id"]: item["stats"]["impact"]
        for item in baseline["resolved_character_snapshots"]
    }
    after = {
        item["character_id"]: item["stats"]["impact"]
        for item in result["resolved_character_snapshots"]
    }
    for character_id in payload["team_character_ids"]:
        assert after[character_id] == pytest.approx(
            before[character_id] * (1 + expected_delta)
        )


@pytest.mark.parametrize(
    ("wengine_id", "suffix", "expected_bonus"),
    (
        ("wengine:12007", "ex-daze", 0.16),
        ("wengine:12008", "primary-target-daze", 0.12),
    ),
)
def test_turbulence_daze_rules_match_source_scope_without_changing_damage(
    wengine_id: str,
    suffix: str,
    expected_bonus: float,
) -> None:
    payload = _single_wengine_payload(
        "character:1251",
        "move-entry:character:1251:ex-special-moon-over-sea-begonia",
        wengine_id,
        5,
        element="electric",
    )
    disabled = client.post("/api/v1/moves/calculate", json=payload).json()
    payload["enabled_rule_item_ids"] = [
        f"rule:{wengine_id}:owner:1251:{suffix}"
    ]
    enabled = client.post("/api/v1/moves/calculate", json=payload).json()
    event = enabled["events"][0]
    daze_modifier = next(
        item
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["modifier_path"] == "daze.outgoing-bonus"
    )
    assert daze_modifier["value"] == pytest.approx(expected_bonus)
    assert event["modes"]["expected"]["value"] == pytest.approx(
        disabled["events"][0]["modes"]["expected"]["value"]
    )
    assert any(
        not item["blocking"] and "does not calculate Daze" in item["message"]
        for item in enabled["diagnostics"]
    )


def test_lunar_noviluna_keeps_energy_restore_as_a_scoped_result_diagnostic() -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = _wengine_build(
        "wengine:12003", 5, element="physical"
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:12003:owner:1431:energy-restore"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert result["resolved_character_snapshots"][0]["stats"]["energy_regen"] == pytest.approx(
        1.2
    )
    assert any(
        not item["blocking"]
        and "Energy resource result" in item["message"]
        and "回复<color=#2BAD00>5</color>点" in item["original_text"]
        for item in result["diagnostics"]
    )


@pytest.mark.parametrize(
    (
        "character_id",
        "entry",
        "wengine_id",
        "refinement",
        "suffix",
        "condition_suffix",
        "stat",
        "expected",
    ),
    (
        (
            "character:1251",
            "move-entry:character:1251:ex-special-moon-over-sea-begonia",
            "wengine:12009",
            5,
            "impact",
            "impact-active",
            "impact",
            113.0,
        ),
        (
            "character:1401",
            "move-entry:alice:1401:physical-anomaly",
            "wengine:12010",
            5,
            "anomaly-mastery",
            "anomaly-mastery-active",
            "anomaly_mastery",
            140.0,
        ),
        (
            "character:1401",
            "move-entry:alice:1401:physical-anomaly",
            "wengine:12011",
            1,
            "anomaly-proficiency",
            "anomaly-proficiency-active",
            "anomaly_proficiency",
            185.0,
        ),
        (
            "character:1401",
            "move-entry:alice:1401:physical-anomaly",
            "wengine:12011",
            5,
            "anomaly-proficiency",
            "anomaly-proficiency-active",
            "anomaly_proficiency",
            200.0,
        ),
    ),
)
def test_equipped_panel_buffs_use_their_declared_live_stat_nodes(
    character_id: str,
    entry: str,
    wengine_id: str,
    refinement: int,
    suffix: str,
    condition_suffix: str,
    stat: str,
    expected: float,
) -> None:
    payload = _single_wengine_payload(
        character_id,
        entry,
        wengine_id,
        refinement,
        element="electric" if character_id == "character:1251" else "physical",
    )
    baseline = client.post("/api/v1/moves/calculate", json=payload).json()
    payload["enabled_rule_item_ids"] = [
        f"rule:{wengine_id}:owner:{character_id.split(':')[-1]}:{suffix}"
    ]
    payload["condition_values"] = {
        f"condition:{wengine_id}:owner:{character_id.split(':')[-1]}:{condition_suffix}": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"][stat] == pytest.approx(
        expected
    )
    if wengine_id == "wengine:12011":
        assert result["events"][0]["modes"]["expected"]["value"] > baseline["events"][0][
            "modes"
        ]["expected"]["value"]
    elif wengine_id == "wengine:12010":
        assert result["events"][0]["modes"]["expected"]["value"] == pytest.approx(
            baseline["events"][0]["modes"]["expected"]["value"]
        )


@pytest.mark.parametrize(
    (
        "owner",
        "wengine_id",
        "refinement",
        "element",
        "rule_suffix",
        "condition_suffix",
        "stat",
        "amount",
        "stack_count",
    ),
    (
        (
            "character:1341",
            "wengine:12013",
            5,
            "ice",
            "defense",
            "defense-active",
            "defense",
            0.32,
            None,
        ),
        (
            "character:1371",
            "wengine:12015",
            5,
            "ether",
            "attack",
            "attack-active",
            "attack",
            0.115,
            None,
        ),
        (
            "character:1401",
            "wengine:13003",
            5,
            "physical",
            "attack-per-energy-stack",
            None,
            "attack",
            0.08,
            2,
        ),
        (
            "character:1431",
            "wengine:13004",
            5,
            "physical",
            "attack",
            "attack-active",
            "attack",
            0.192,
            None,
        ),
        (
            "character:1361",
            "wengine:13005",
            5,
            "electric",
            "impact-per-energy-tier",
            None,
            "impact",
            0.096,
            3,
        ),
    ),
)
def test_second_batch_panel_effects_use_current_owner_stat_and_explicit_layers(
    owner: str,
    wengine_id: str,
    refinement: int,
    element: str,
    rule_suffix: str,
    condition_suffix: str | None,
    stat: str,
    amount: float,
    stack_count: int | None,
) -> None:
    if owner == "character:1431":
        payload = _single_wengine_payload(
            owner,
            "move-entry:ye:1431:basic-fast-1",
            wengine_id,
            refinement,
            element=element,
        )
    else:
        payload = _with_supporting_wengine(
            _valid_calculation_payload(),
            [(owner, wengine_id, refinement, element)],
        )
    baseline = client.post("/api/v1/moves/calculate", json=payload).json()
    rule_id = f"rule:{wengine_id}:owner:{owner.split(':')[-1]}:{rule_suffix}"
    payload["enabled_rule_item_ids"] = [rule_id]
    if condition_suffix is not None:
        payload["condition_values"] = {
            f"condition:{wengine_id}:owner:{owner.split(':')[-1]}:{condition_suffix}": True
        }
    if stack_count is not None:
        payload["rule_stack_counts"] = {rule_id: stack_count}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    active = response.json()
    before = {
        item["character_id"]: item["stats"]
        for item in baseline["resolved_character_snapshots"]
    }
    after = {
        item["character_id"]: item["stats"]
        for item in active["resolved_character_snapshots"]
    }
    assert after[owner][stat] == pytest.approx(before[owner][stat] * (1 + amount))
    if wengine_id == "wengine:13003":
        assert before[owner]["anomaly_proficiency"] == pytest.approx(175.0)
    if owner != "character:1431":
        assert after["character:1431"][stat] == pytest.approx(
            before["character:1431"][stat]
        )


def test_street_superstar_uses_explicit_current_charge_count_on_ultimate_only() -> None:
    rule_id = "rule:wengine:13001:owner:1431:ultimate-damage-per-charge"
    payload = _single_wengine_payload(
        "character:1431",
        "move-entry:ye:1431:ultimate-zhuyunjingting",
        "wengine:13001",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 3}
    ultimate = client.post("/api/v1/moves/calculate", json=payload)
    assert ultimate.status_code == 200, ultimate.text
    assert _breakdown_value(ultimate.json()["events"][0], "damage.normal-bonus") == pytest.approx(
        0.72
    )

    payload["move_entry_id"] = "move-entry:ye:1431:basic-fast-1"
    basic = client.post("/api/v1/moves/calculate", json=payload)
    assert basic.status_code == 200, basic.text
    assert _breakdown_value(basic.json()["events"][0], "damage.normal-bonus") == 0.0


@pytest.mark.parametrize(
    ("owner", "wengine_id", "element", "rule_suffix", "source_fragment", "damage_change_expected"),
    (
        (
            "character:1401",
            "wengine:12012",
            "physical",
            "anomaly-energy-restore",
            "回复<color=#2BAD00>5.5</color>点能量",
            False,
        ),
        (
            "character:1341",
            "wengine:12014",
            "ice",
            "enemy-outgoing-damage-reduction",
            "造成的伤害降低<color=#2BAD00>10%</color>",
            False,
        ),
        (
            "character:1311",
            "wengine:13002",
            "ether",
            "resource-gains",
            "喧响值",
            False,
        ),
        (
            "character:1341",
            "wengine:13011",
            "ice",
            "incoming-damage-and-resource-effects",
            "能量获得效率提升",
            False,
        ),
        (
            "character:1341",
            "wengine:13016",
            "ice",
            "incoming-damage-and-malaise-reduction",
            "秽息浸染",
            False,
        ),
        (
            "character:1341",
            "wengine:13112",
            "ice",
            "incoming-damage-reduction",
            "受到的伤害降低",
            False,
        ),
        (
            "character:1341",
            "wengine:13142",
            "ice",
            "team-energy-restore",
            "回复<color=#2BAD00>3.2</color>点能量",
            False,
        ),
        (
            "character:1311",
            "wengine:13115",
            "ether",
            "team-attack-per-ally-stack",
            "每名友方单位最多提供1层增益效果",
            True,
        ),
    ),
)
def test_result_only_weapon_effects_keep_scoped_nonblocking_diagnostics(
    owner: str,
    wengine_id: str,
    element: str,
    rule_suffix: str,
    source_fragment: str,
    damage_change_expected: bool,
) -> None:
    payload = _with_supporting_wengine(
        _valid_calculation_payload(), [(owner, wengine_id, 5, element)]
    )
    baseline = client.post("/api/v1/moves/calculate", json=payload).json()
    payload["enabled_rule_item_ids"] = [
        f"rule:{wengine_id}:owner:{owner.split(':')[-1]}:{rule_suffix}"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    diagnostic = next(
        item for item in result["diagnostics"] if source_fragment in (item["original_text"] or "")
    )
    assert diagnostic["blocking"] is False
    if damage_change_expected:
        assert result["events"][0]["modes"]["expected"]["value"] > baseline["events"][0]["modes"]["expected"]["value"]
    else:
        assert result["events"][0]["modes"]["expected"]["value"] == pytest.approx(
            baseline["events"][0]["modes"]["expected"]["value"]
        )


def test_electric_lip_gloss_field_anomaly_state_applies_owner_and_any_target_bonus() -> None:
    field_id = "condition:wengine:13009:owner:1401:anomaly-in-field-active"
    attack_rule = "rule:wengine:13009:owner:1401:field-anomaly-attack"
    target_rule = "rule:wengine:13009:owner:1401:target-anomaly-damage"
    payload = _single_wengine_payload(
        "character:1401",
        "move-entry:alice:1401:physical-anomaly",
        "wengine:13009",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [attack_rule, target_rule]
    default_active = client.post("/api/v1/moves/calculate", json=payload)
    assert default_active.status_code == 200, default_active.text
    assert default_active.json()["events"][0]["modes"]["expected"][
        "anomaly_effect_strength_trace"
    ]["normal_bonus"] == pytest.approx(0.25)
    payload["condition_values"] = {field_id: False}
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    base_attack = baseline.json()["resolved_character_snapshots"][0]["stats"]["attack"]

    # The field state is the only anomaly prerequisite. The current target is
    # not given a separate anomaly flag, so the target bonus applies normally.
    payload["condition_values"] = {field_id: True}
    active_response = client.post("/api/v1/moves/calculate", json=payload)
    assert active_response.status_code == 200, active_response.text
    active = active_response.json()
    assert active["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(
        base_attack * 1.16
    )
    assert active["totals"]["expected"]["complete"] is True
    assert active["events"][0]["modes"]["expected"][
        "anomaly_effect_strength_trace"
    ]["normal_bonus"] == pytest.approx(0.25)
    assert active["events"][0]["modes"]["expected"]["value"] > baseline.json()["events"][0]["modes"]["expected"]["value"]


@pytest.mark.parametrize(("refinement", "multiplier"), ((1, 6.0), (5, 9.6)))
def test_big_cylinder_extra_hit_uses_owner_defense_crit_and_native_element(
    refinement: int,
    multiplier: float,
) -> None:
    owner = "character:1341"
    rule_id = f"rule:wengine:13112:owner:1341:defense-counter-extra-damage"
    condition_id = f"condition:wengine:13112:owner:1341:defense-counter-damage-ready"
    payload = _single_wengine_payload(
        owner,
        "move-entry:character:1341:basic-cold-judgment-1",
        "wengine:13112",
        refinement,
        element="ice",
    )
    payload["character_builds"][owner]["base_stats"]["defense"] = 1000.0
    payload["character_builds"][owner]["base_stats"]["element_damage_bonus"] = {
        "physical": 0.0,
        "ice": 0.0,
    }
    payload["enemy"]["damage_resistance"] = {"physical": 0.1, "ice": 0.5}
    payload["condition_values"] = {condition_id: True}
    payload["enabled_rule_item_ids"] = [rule_id]

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    child = next(
        event for event in result["events"]
        if event["common_application_trace"]["created_by_effect_id"] == (
            "effect:wengine:13112:owner:1341:defense-counter-extra-damage"
        )
    )
    main = next(event for event in result["events"] if event is not child)
    assert _breakdown_value(main, "resistance.region") == pytest.approx(0.9)
    current_defense = result["resolved_character_snapshots"][0]["stats"]["defense"]
    assert _breakdown_value(child, "character.current.defense") == pytest.approx(current_defense)
    assert _breakdown_value(child, "damage.base-value") == pytest.approx(current_defense * multiplier)
    assert _breakdown_value(child, "resistance.region") == pytest.approx(0.5)
    assert _breakdown_value(child, "character.current.crit-rate") == pytest.approx(1.0)
    assert child["modes"]["non-crit"]["value"] == pytest.approx(
        child["modes"]["full-crit"]["value"]
    )


def test_cannon_rotor_extra_hit_uses_wearer_attack_and_does_not_recurse() -> None:
    owner = "character:1431"
    rule_id = "rule:wengine:14001:owner:1431:crit-triggered-extra-damage"
    condition_id = "condition:wengine:14001:owner:1431:crit-triggered-extra-damage-current-hit"
    payload = _single_wengine_payload(
        owner,
        "move-entry:ye:1431:basic-fast-1",
        "wengine:14001",
        5,
        element="physical",
    )
    payload["condition_values"] = {condition_id: True}
    payload["enabled_rule_item_ids"] = [
        rule_id,
        "rule:wengine:14001:owner:1431:attack-percent",
    ]

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    child = next(
        event for event in result["events"]
        if event["common_application_trace"]["created_by_effect_id"] == (
            "effect:wengine:14001:owner:1431:crit-triggered-extra-damage"
        )
    )
    owner_attack = result["resolved_character_snapshots"][0]["stats"]["attack"]
    assert _breakdown_value(child, "damage.base-value") == pytest.approx(
        owner_attack * 2.0
    )
    assert _breakdown_value(child, "character.current.crit-rate") == pytest.approx(
        result["resolved_character_snapshots"][0]["stats"]["crit_rate"]
    )
    assert child["common_application_trace"]["created_by_effect_id"] == (
        "effect:wengine:14001:owner:1431:crit-triggered-extra-damage"
    )


def test_precious_fossil_uses_both_hp_thresholds_in_the_daze_lane() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:basic-concerto-sniping",
        "wengine:13006",
        5,
        element="electric",
    )
    base_condition = "condition:wengine:13006:owner:1361:target-hp-at-least-50-percent"
    extra_condition = "condition:wengine:13006:owner:1361:target-hp-at-least-75-percent"
    rule_ids = [
        "rule:wengine:13006:owner:1361:daze-bonus-at-50",
        "rule:wengine:13006:owner:1361:daze-extra-bonus-at-75",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["condition_values"] = {
        "condition:trigger:follow-up-active": True,
        base_condition: True,
        extra_condition: False,
    }
    at_50 = client.post("/api/v1/moves/calculate", json=payload)
    assert at_50.status_code == 200, at_50.text
    at_50_result = at_50.json()
    daze_values = [
        item["value"]
        for item in at_50_result["events"][0]["common_application_trace"][
            "applied_modifiers"
        ]
        if item["modifier_path"] == "daze.outgoing-bonus"
        and item["source_type"] == "weapon"
    ]
    assert daze_values == [pytest.approx(0.16)]
    assert at_50_result["totals"]["expected"]["complete"] is True

    payload["condition_values"][extra_condition] = True
    at_75 = client.post("/api/v1/moves/calculate", json=payload)
    assert at_75.status_code == 200, at_75.text
    at_75_values = [
        item["value"]
        for item in at_75.json()["events"][0]["common_application_trace"][
            "applied_modifiers"
        ]
        if item["modifier_path"] == "daze.outgoing-bonus"
        and item["source_type"] == "weapon"
    ]
    assert at_75_values == [pytest.approx(0.16), pytest.approx(0.16)]


def test_precise_transformer_after_hit_impact_and_twin_crying_stars_current_ap_stacks() -> None:
    owner = "character:1341"
    payload = _with_supporting_wengine(
        _valid_calculation_payload(), [(owner, "wengine:13007", 5, "ice")]
    )
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    before = next(
        item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13007:owner:1341:impact-after-hit"
    ]
    payload["condition_values"] = {
        "condition:wengine:13007:owner:1341:impact-buff-after-hit-active": True
    }
    after_hit = client.post("/api/v1/moves/calculate", json=payload)
    assert after_hit.status_code == 200, after_hit.text
    after = next(
        item["stats"]
        for item in after_hit.json()["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    assert after["impact"] == pytest.approx(before["impact"] * 1.16)

    anomaly_owner = "character:1401"
    stacks_payload = _with_supporting_wengine(
        _valid_calculation_payload(), [(anomaly_owner, "wengine:13008", 5, "physical")]
    )
    stacks = client.post("/api/v1/moves/calculate", json=stacks_payload).json()
    before_stacks = next(
        item["stats"]
        for item in stacks["resolved_character_snapshots"]
        if item["character_id"] == anomaly_owner
    )
    ap_rule = "rule:wengine:13008:owner:1401:anomaly-proficiency-per-stack"
    stacks_payload["enabled_rule_item_ids"] = [ap_rule]
    stacks_payload["rule_stack_counts"] = {ap_rule: 4}
    with_stacks = client.post("/api/v1/moves/calculate", json=stacks_payload)
    assert with_stacks.status_code == 200, with_stacks.text
    after_stacks = next(
        item["stats"]
        for item in with_stacks.json()["resolved_character_snapshots"]
        if item["character_id"] == anomaly_owner
    )
    assert after_stacks["anomaly_proficiency"] == pytest.approx(
        before_stacks["anomaly_proficiency"] + 4 * 48
    )
    assert after_stacks["anomaly_mastery"] == pytest.approx(
        before_stacks["anomaly_mastery"]
    )


def test_bunny_band_shield_state_changes_attack_without_changing_its_hp_build() -> None:
    owner = "character:1341"
    payload = _with_supporting_wengine(
        _valid_calculation_payload(), [(owner, "wengine:13010", 5, "ice")]
    )
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    before = next(
        item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    payload["enabled_rule_item_ids"] = ["rule:wengine:13010:owner:1341:shield-stat"]
    payload["condition_values"] = {
        "condition:wengine:13010:owner:1341:shield-active": True
    }
    shielded = client.post("/api/v1/moves/calculate", json=payload)
    assert shielded.status_code == 200, shielded.text
    after = next(
        item["stats"]
        for item in shielded.json()["resolved_character_snapshots"]
        if item["character_id"] == owner
    )
    assert after["attack"] == pytest.approx(before["attack"] * 1.16)
    assert after["hp"] == pytest.approx(before["hp"])


def test_fantasy_cube_low_hp_bonus_is_ex_special_scoped_and_crit_damage_is_panel_state() -> None:
    payload = _single_wengine_payload(
        "character:1371",
        "move-entry:character:1371:ex-condense-cloud-technique",
        "wengine:13012",
        5,
        element="ether",
    )
    low_hp_rule = "rule:wengine:13012:owner:1371:ex-special-low-hp-damage"
    crit_rule = "rule:wengine:13012:owner:1371:ex-special-crit-damage-buff"
    payload["enabled_rule_item_ids"] = [low_hp_rule, crit_rule]
    payload["condition_values"] = {
        "condition:wengine:13012:owner:1371:target-hp-below-50-percent": True,
        "condition:wengine:13012:owner:1371:ex-special-crit-damage-active": True,
    }
    ex_special = client.post("/api/v1/moves/calculate", json=payload)
    assert ex_special.status_code == 200, ex_special.text
    ex_result = ex_special.json()
    assert _breakdown_value(ex_result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.32
    )
    yixuan_stats = ex_result["resolved_character_snapshots"][0]["stats"]
    assert yixuan_stats["crit_damage"] == pytest.approx(0.756)

    payload["move_entry_id"] = "move-entry:character:1371:basic-xiaoyun-jin-1"
    basic = client.post("/api/v1/moves/calculate", json=payload)
    assert basic.status_code == 200, basic.text
    assert _breakdown_value(basic.json()["events"][0], "damage.normal-bonus") == 0.0


def test_gilded_blossom_attack_is_panel_and_extra_damage_is_ex_special_scoped() -> None:
    payload = _single_wengine_payload(
        "character:1431",
        "move-entry:ye:1431:special-dingfengbo",
        "wengine:13013",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13013:owner:1431:attack-percent",
        "rule:wengine:13013:owner:1431:ex-special-damage",
    ]
    special = client.post("/api/v1/moves/calculate", json=payload)
    assert special.status_code == 200, special.text
    special_result = special.json()
    assert _breakdown_value(special_result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.24
    )
    attack_with_weapon = special_result["resolved_character_snapshots"][0]["stats"][
        "attack"
    ]

    payload["move_entry_id"] = "move-entry:ye:1431:basic-fast-1"
    basic = client.post("/api/v1/moves/calculate", json=payload)
    assert basic.status_code == 200, basic.text
    assert _breakdown_value(basic.json()["events"][0], "damage.normal-bonus") == 0.0
    assert basic.json()["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(
        attack_with_weapon
    )


def test_radio_wave_walk_current_stacks_add_penetration_force_only() -> None:
    rule_id = "rule:wengine:13014:owner:1371:penetration-force-per-stack"
    payload = _single_wengine_payload(
        "character:1371",
        "move-entry:character:1371:basic-xiaoyun-jin-1",
        "wengine:13014",
        5,
        element="ether",
    )
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 3}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    assert _breakdown_value(event, "penetration.force-bonus") == pytest.approx(384.0)
    assert _breakdown_value(event, "penetration.force") == pytest.approx(2112.2)


def test_strong_enough_attack_buffs_are_two_independent_current_states() -> None:
    first_rule = "rule:wengine:13015:owner:1431:attack-buff"
    extra_rule = "rule:wengine:13015:owner:1431:anomalous-target-extra-attack-buff"
    first_condition = "condition:wengine:13015:owner:1431:ex-special-or-chain-attack-buff-active"
    extra_condition = "condition:wengine:13015:owner:1431:anomalous-target-attack-bonus-active"
    payload = _single_wengine_payload(
        "character:1431",
        "move-entry:ye:1431:basic-fast-1",
        "wengine:13015",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [first_rule, extra_rule]
    payload["condition_values"] = {first_condition: True, extra_condition: False}
    first = client.post("/api/v1/moves/calculate", json=payload)
    assert first.status_code == 200, first.text
    first_attack = first.json()["resolved_character_snapshots"][0]["stats"]["attack"]

    payload["condition_values"][extra_condition] = True
    extra = client.post("/api/v1/moves/calculate", json=payload)
    assert extra.status_code == 200, extra.text
    extra_attack = extra.json()["resolved_character_snapshots"][0]["stats"]["attack"]
    assert extra_attack == pytest.approx(first_attack + (first_attack / 1.096) * 0.096)


def test_boisterous_echoes_keeps_anomaly_target_damage_separate_from_energy_restore() -> None:
    payload = _single_wengine_payload(
        "character:1401",
        "move-entry:alice:1401:basic-star-opera-1",
        "wengine:13018",
        5,
        element="physical",
    )
    rule_id = "rule:wengine:13018:owner:1401:anomalous-target-damage"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["condition_values"] = {
        "condition:wengine:13018:owner:1401:target-anomaly-active": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.184
    )
    energy_diagnostic = next(
        item for item in result["diagnostics"] if "no Energy resource result" in item["message"]
    )
    assert energy_diagnostic["blocking"] is False


def test_cauldron_of_clarity_uses_one_stack_selection_for_damage_and_full_stack_crit() -> None:
    damage_rule = "rule:wengine:13019:owner:1371:ex-special-damage-per-stack"
    crit_rule = "rule:wengine:13019:owner:1371:crit-rate-at-max-stacks"
    payload = _single_wengine_payload(
        "character:1371",
        "move-entry:character:1371:basic-xiaoyun-jin-1",
        "wengine:13019",
        5,
        element="ether",
    )
    payload["enabled_rule_item_ids"] = [damage_rule, crit_rule]
    payload["rule_stack_counts"] = {damage_rule: 3}
    full = client.post("/api/v1/moves/calculate", json=payload)
    assert full.status_code == 200, full.text
    full_result = full.json()
    assert _breakdown_value(full_result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.192
    )
    assert full_result["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(
        0.604
    )

    payload["rule_stack_counts"][damage_rule] = 2
    partial = client.post("/api/v1/moves/calculate", json=payload)
    assert partial.status_code == 200, partial.text
    partial_result = partial.json()
    assert _breakdown_value(partial_result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.128
    )
    assert partial_result["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(
        0.5
    )


def test_simmering_pot_assist_buff_affects_wearer_damage_and_keeps_daze_in_its_node() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:basic-concerto-sniping",
        "wengine:13020",
        5,
        element="electric",
    )
    payload["condition_values"] = {
        "condition:trigger:follow-up-active": True,
        "condition:wengine:13020:owner:1361:assist-attack-buffs-active": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13020:owner:1361:assist-attack-buffs"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(
        0.115
    )
    daze_modifiers = [
        item
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["modifier_path"] == "daze.outgoing-bonus"
        and item["source_type"] == "weapon"
    ]
    assert [item["value"] for item in daze_modifiers] == [pytest.approx(0.115)]
    assert response.json()["totals"]["expected"]["complete"] is True


def test_demara_battery_electric_bonus_is_element_scoped_energy_efficiency_is_source_only() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:basic-concerto-sniping",
        "wengine:13101",
        5,
        element="electric",
    )
    payload["condition_values"] = {
        "condition:trigger:follow-up-active": True,
        "condition:wengine:13101:owner:1361:energy-recovery-efficiency-active": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13101:owner:1361:electric-damage",
        "rule:wengine:13101:owner:1361:energy-recovery-efficiency",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(
        0.24
    )
    assert result["totals"]["expected"]["complete"] is True
    energy_diagnostic = next(
        item for item in result["diagnostics"] if "Energy resource result" in item["message"]
    )
    assert energy_diagnostic["blocking"] is False


def test_housekeeper_current_backline_energy_and_physical_stack_inputs() -> None:
    primary = "character:1401"
    ye = "character:1431"
    payload = _valid_calculation_payload()
    payload["primary_character_id"] = primary
    payload["team_character_ids"] = [primary]
    payload["move_entry_id"] = "move-entry:alice:1401:basic-star-opera-1"
    payload["compile_configs"] = {primary: {"core_level": 1, "cinema_level": 0}}
    payload["character_builds"] = {
        primary: {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.5,
                "crit_damage": 0.5,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "energy_regen": 1.2,
                "element_damage_bonus": {"physical": 0.0},
            },
        }
    }
    payload = _with_supporting_wengine(payload, [(ye, "wengine:13106", 5, "physical")])
    payload["compile_configs"][ye] = {
        "core_level": 1,
        "cinema_level": 0,
        "mingxin_active": False,
        "entry_move_uses_linren": False,
    }
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    before = next(
        item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
        if item["character_id"] == ye
    )
    regen_rule = "rule:wengine:13106:owner:1431:backline-energy-regeneration"
    payload["enabled_rule_item_ids"] = [regen_rule]
    backline = client.post("/api/v1/moves/calculate", json=payload)
    assert backline.status_code == 200, backline.text
    after = next(
        item["stats"]
        for item in backline.json()["resolved_character_snapshots"]
        if item["character_id"] == ye
    )
    assert after["energy_regen"] == pytest.approx(before["energy_regen"] + 0.72)

    on_field = _single_wengine_payload(
        ye,
        "move-entry:ye:1431:basic-fast-1",
        "wengine:13106",
        5,
        element="physical",
    )
    on_field["enabled_rule_item_ids"] = [regen_rule]
    active_owner = client.post("/api/v1/moves/calculate", json=on_field)
    assert active_owner.status_code == 200, active_owner.text
    assert active_owner.json()["resolved_character_snapshots"][0]["stats"][
        "energy_regen"
    ] == pytest.approx(1.2)
    on_field["condition_values"] = {
        "condition:wengine:13106:owner:1431:wearer-in-backline": True
    }
    fabricated_backline = client.post("/api/v1/moves/calculate", json=on_field)
    assert fabricated_backline.status_code == 400
    assert "unknown scenario conditions" in fabricated_backline.text

    physical = _single_wengine_payload(
        ye,
        "move-entry:ye:1431:basic-fast-1",
        "wengine:13106",
        5,
        element="physical",
    )
    stack_rule = "rule:wengine:13106:owner:1431:physical-damage-per-stack"
    physical["enabled_rule_item_ids"] = [stack_rule]
    for selected_stacks, expected_bonus in ((None, 0.72), (0, 0.0), (5, 0.24), (15, 0.72)):
        physical["rule_stack_counts"] = (
            {} if selected_stacks is None else {stack_rule: selected_stacks}
        )
        stack_result = client.post("/api/v1/moves/calculate", json=physical)
        assert stack_result.status_code == 200, stack_result.text
        assert _breakdown_value(
            stack_result.json()["events"][0], "damage.normal-bonus"
        ) == pytest.approx(expected_bonus)


def test_starlight_replica_trigger_state_applies_to_later_physical_moves() -> None:
    payload = _single_wengine_payload(
        "character:1431",
        "move-entry:ye:1431:basic-fast-1",
        "wengine:13108",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13108:owner:1431:distant-physical-damage"
    ]
    payload["condition_values"] = {
        "condition:wengine:13108:owner:1431:distant-physical-hit-buff-active": True
    }
    for move in (
        "move-entry:ye:1431:basic-fast-1",
        "move-entry:ye:1431:special-dingfengbo",
    ):
        payload["move_entry_id"] = move
        response = client.post("/api/v1/moves/calculate", json=payload)
        assert response.status_code == 200, response.text
        assert _breakdown_value(response.json()["events"][0], "damage.normal-bonus") == pytest.approx(
            0.575
        )


def test_unfettered_game_ball_applies_target_crit_in_event_lane_to_all_attackers_once() -> None:
    owners = (
        ("character:1311", "wengine:14002", 5, "ether"),
        ("character:1411", "wengine:14002", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    rule_ids = [
        "rule:wengine:14002:owner:1311:target-crit-rate",
        "rule:wengine:14002:owner:1411:target-crit-rate",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["condition_values"] = {
        "condition:wengine:14002:owner:1311:attribute-counter-target-crit-buff-active": True,
        "condition:wengine:14002:owner:1411:attribute-counter-target-crit-buff-active": True,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    event_stats = event["common_application_trace"]["event_stat_modifiers"]
    assert len(event_stats) == 1
    assert event_stats[0]["modifier_path"] == "character.current.crit-rate"
    assert event_stats[0]["recipient_character_id"] == "character:1431"
    assert event_stats[0]["value"] == pytest.approx(0.20)
    assert _breakdown_value(event, "character.current.crit-rate") == pytest.approx(
        0.85
    )
    formal_crit_rates = {
        item["character_id"]: item["stats"]["crit_rate"]
        for item in result["resolved_character_snapshots"]
    }
    assert formal_crit_rates["character:1431"] == pytest.approx(0.65)
    assert formal_crit_rates["character:1311"] == pytest.approx(0.50)


def test_unfettered_game_ball_mixed_refinements_select_maximum_target_crit_rate() -> None:
    owners = (
        ("character:1311", "wengine:14002", 1, "ether"),
        ("character:1411", "wengine:14002", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14002:owner:1311:target-crit-rate",
        "rule:wengine:14002:owner:1411:target-crit-rate",
    ]
    payload["condition_values"] = {
        "condition:wengine:14002:owner:1311:attribute-counter-target-crit-buff-active": True,
        "condition:wengine:14002:owner:1411:attribute-counter-target-crit-buff-active": True,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert result["totals"]["expected"]["complete"] is True
    assert len(event["common_application_trace"]["event_stat_modifiers"]) == 1
    assert event["common_application_trace"]["event_stat_modifiers"][0]["value"] == pytest.approx(0.20)

    # Only currently matching conditions enter MAX comparison. With the R5
    # state inactive, the lower R1 value is the sole effective candidate.
    payload["condition_values"][
        "condition:wengine:14002:owner:1411:attribute-counter-target-crit-buff-active"
    ] = False
    lower_refinement = client.post("/api/v1/moves/calculate", json=payload)
    assert lower_refinement.status_code == 200, lower_refinement.text
    lower = lower_refinement.json()
    assert lower["totals"]["expected"]["complete"] is True
    assert len(lower["events"][0]["common_application_trace"]["event_stat_modifiers"]) == 1
    assert lower["events"][0]["common_application_trace"]["event_stat_modifiers"][0][
        "value"
    ] == pytest.approx(0.12)


def test_unfettered_game_ball_target_crit_does_not_touch_no_crit_anomaly_events() -> None:
    payload = _valid_calculation_payload()
    payload["primary_character_id"] = "character:1401"
    payload["team_character_ids"] = ["character:1401"]
    payload["move_entry_id"] = "move-entry:alice:1401:physical-anomaly"
    payload["compile_configs"] = {"character:1401": {"core_level": 1, "cinema_level": 0}}
    payload["character_builds"] = {
        "character:1401": {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.5,
                "crit_damage": 0.5,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "energy_regen": 1.2,
                "element_damage_bonus": {"physical": 0.0},
            },
        }
    }
    payload = _with_supporting_wengine(
        payload,
        [
            ("character:1311", "wengine:14002", 5, "ether"),
            ("character:1411", "wengine:14002", 1, "physical"),
        ],
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14002:owner:1311:target-crit-rate",
        "rule:wengine:14002:owner:1411:target-crit-rate",
    ]
    payload["condition_values"] = {
        "condition:wengine:14002:owner:1311:attribute-counter-target-crit-buff-active": True,
        "condition:wengine:14002:owner:1411:attribute-counter-target-crit-buff-active": True,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert result["events"][0]["common_application_trace"]["event_stat_modifiers"] == []


def test_krakens_cradle_keeps_ice_penetration_bonus_separate_from_half_hp_crit() -> None:
    payload = _single_wengine_payload(
        "character:1371",
        "move-entry:character:1371:basic-xiaoyun-jin-1",
        "wengine:14105",
        5,
        element="ether",
    )
    stack_rule = "rule:wengine:14105:owner:1371:ice-penetration-damage-per-stack"
    crit_rule = "rule:wengine:14105:owner:1371:crit-rate-at-half-hp"
    payload["enabled_rule_item_ids"] = [stack_rule, crit_rule]
    payload["rule_stack_counts"] = {stack_rule: 3}
    payload["condition_values"] = {
        "condition:wengine:14105:owner:1371:owner-hp-at-or-below-half": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    yixuan = result["resolved_character_snapshots"][0]["stats"]
    assert yixuan["crit_rate"] == pytest.approx(0.82)
    weapon_modifiers = [
        item
        for item in result["events"][0]["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
    ]
    assert weapon_modifiers == []
    assert result["totals"]["expected"]["complete"] is True


def test_six_shooter_charge_stack_only_changes_ex_special_daze_node() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:special-ghost-bloom",
        "wengine:14003",
        5,
        element="electric",
    )
    rule_id = "rule:wengine:14003:owner:1361:ex-special-daze-per-charge"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 6}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    weapon_daze = [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "daze.outgoing-bonus"
    ]
    assert weapon_daze == [pytest.approx(0.384)]
    assert _breakdown_value(event, "damage.normal-bonus") == 0.0
    assert result["totals"]["expected"]["complete"] is True
    assert any(
        "does not calculate Daze" in item["message"] and not item["blocking"]
        for item in result["diagnostics"]
    )


def test_hailstorm_shrine_keeps_crit_panel_when_registered_owner_lacks_ice() -> None:
    payload = _single_wengine_payload(
        "character:1401",
        "move-entry:alice:1401:basic-star-opera-1",
        "wengine:14109",
        5,
        element="physical",
    )
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14109:owner:1401:crit-damage",
        "rule:wengine:14109:owner:1401:ice-damage-per-stack",
    ]
    payload["rule_stack_counts"] = {
        "rule:wengine:14109:owner:1401:ice-damage-per-stack": 2
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"][
        "crit_damage"
    ] == pytest.approx(1.3)
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.0)
    assert result["totals"]["expected"]["complete"] is True


def test_tusks_of_fury_applies_active_team_damage_and_keeps_daze_in_its_node() -> None:
    payload = _with_supporting_wengine(
        _valid_calculation_payload(),
        [("character:1341", "wengine:14107", 5, "ice")],
    )
    rule_id = "rule:wengine:14107:owner:1341:team-parry-perfect-dodge-buff"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["condition_values"] = {
        "condition:wengine:14107:owner:1341:team-parry-perfect-dodge-buffs-active": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(0.36)
    weapon_daze = [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "daze.outgoing-bonus"
    ]
    assert weapon_daze == [pytest.approx(0.24)]
    assert result["totals"]["expected"]["complete"] is True


def test_restrained_uses_current_basic_stack_count_for_damage_and_daze() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:basic-concerto-sniping",
        "wengine:14114",
        5,
        element="electric",
    )
    rule_id = "rule:wengine:14114:owner:1361:basic-damage-daze-per-stack"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 3}
    payload["condition_values"] = {"condition:trigger:follow-up-active": True}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(0.36)
    weapon_daze = [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "daze.outgoing-bonus"
    ]
    assert weapon_daze == [pytest.approx(0.36)]
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("refinements", "expected_bonus"),
    (((1, 1), 0.30), ((1, 5), 0.48)),
)
def test_blazing_laurel_applies_depression_as_event_crit_damage_without_panel_leak(
    refinements: tuple[int, int],
    expected_bonus: float,
) -> None:
    payload = _valid_calculation_payload()
    primary = "character:1091"
    payload["primary_character_id"] = primary
    payload["team_character_ids"] = [primary]
    payload["move_entry_id"] = "move-entry:character:1091:kazahana-3"
    payload["compile_configs"] = {primary: {"core_level": 1, "cinema_level": 0}}
    payload["character_builds"] = {
        primary: {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.5,
                "crit_damage": 0.5,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"ice": 0.2},
            },
        }
    }
    payload["enemy"]["damage_resistance"] = {"ice": 0.2}
    payload = _with_supporting_wengine(
        payload,
        [
            ("character:1361", "wengine:14116", refinements[0], "electric"),
            ("character:1251", "wengine:14116", refinements[1], "electric"),
        ],
    )
    rule_ids = [
        "rule:wengine:14116:owner:1361:depression-target-stacks",
        "rule:wengine:14116:owner:1251:depression-target-stacks",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["rule_stack_counts"] = {rule_id: 20 for rule_id in rule_ids}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    modifiers = event["common_application_trace"]["event_stat_modifiers"]
    assert len(modifiers) == 1
    assert modifiers[0]["modifier_path"] == "character.current.crit-damage"
    assert modifiers[0]["recipient_character_id"] == primary
    assert modifiers[0]["value"] == pytest.approx(expected_bonus)
    formal_crit_damage = {
        item["character_id"]: item["stats"]["crit_damage"]
        for item in result["resolved_character_snapshots"]
    }
    assert formal_crit_damage[primary] == pytest.approx(0.5)
    assert formal_crit_damage["character:1361"] == pytest.approx(0.5)
    crit_damage_values = [
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-damage"
    ]
    assert crit_damage_values == [pytest.approx(0.5 + expected_bonus)]
    assert result["totals"]["expected"]["complete"] is True


def test_flamemaker_shaker_ap_buff_has_its_own_current_state_not_a_live_stack_threshold() -> None:
    owner = "character:1401"
    payload = _single_wengine_payload(
        owner,
        "move-entry:alice:1401:basic-star-opera-1",
        "wengine:14117",
        5,
        element="physical",
    )
    damage_rule = "rule:wengine:14117:owner:1401:ex-assist-damage-per-stack"
    ap_rule = "rule:wengine:14117:owner:1401:anomaly-proficiency-at-five-stacks"
    ap_condition = "condition:wengine:14117:owner:1401:anomaly-proficiency-buff-active"
    payload["enabled_rule_item_ids"] = [damage_rule, ap_rule]
    payload["rule_stack_counts"] = {damage_rule: 2}
    payload["condition_values"] = {ap_condition: True}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    stats = result["resolved_character_snapshots"][0]["stats"]
    assert stats["anomaly_proficiency"] == pytest.approx(200.0)
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.14)

    payload["condition_values"][ap_condition] = False
    inactive = client.post("/api/v1/moves/calculate", json=payload)
    assert inactive.status_code == 200, inactive.text
    assert inactive.json()["resolved_character_snapshots"][0]["stats"][
        "anomaly_proficiency"
    ] == pytest.approx(100.0)


def test_timeweaver_ap_state_uses_current_panel_value_and_electric_buildup_is_capability_gated() -> None:
    owner = "character:1401"
    payload = _single_wengine_payload(
        owner,
        "move-entry:alice:1401:physical-anomaly",
        "wengine:14122",
        5,
        element="physical",
    )
    payload["character_builds"][owner]["base_stats"]["anomaly_proficiency"] = 300.0
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14122:owner:1401:special-hit-anomalous-target-ap-buff",
        "rule:wengine:14122:owner:1401:electric-buildup-efficiency",
    ]
    payload["condition_values"] = {
        "condition:wengine:14122:owner:1401:special-hit-anomalous-target-ap-buff-active": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"][
        "anomaly_proficiency"
    ] == pytest.approx(415.0)
    assert result["totals"]["expected"]["complete"] is True


def test_jade_tea_stacks_and_qualifying_team_buff_are_independent_current_states() -> None:
    payload = _with_supporting_wengine(
        _valid_calculation_payload(),
        [("character:1361", "wengine:14125", 5, "electric")],
    )
    impact_rule = "rule:wengine:14125:owner:1361:impact-per-tea-stack"
    team_rule = "rule:wengine:14125:owner:1361:tea-threshold-team-damage"
    team_condition = "condition:wengine:14125:owner:1361:tea-threshold-team-damage-active"
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    before_impact = next(
        item["stats"]["impact"]
        for item in baseline.json()["resolved_character_snapshots"]
        if item["character_id"] == "character:1361"
    )

    payload["enabled_rule_item_ids"] = [impact_rule, team_rule]
    payload["rule_stack_counts"] = {impact_rule: 10}
    payload["condition_values"] = {team_condition: True}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    trigger_stats = next(
        item["stats"]
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1361"
    )
    assert trigger_stats["impact"] == pytest.approx(before_impact * 1.14)
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.32)
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("refinements", "expected_bonus"),
    (((1, 1), 0.20), ((1, 5), 0.32)),
)
def test_jade_tea_team_unique_bonus_selects_maximum_refinement(
    refinements: tuple[int, int],
    expected_bonus: float,
) -> None:
    owners = (
        ("character:1361", "wengine:14125", refinements[0], "electric"),
        ("character:1251", "wengine:14125", refinements[1], "electric"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    rule_ids = [
        "rule:wengine:14125:owner:1361:tea-threshold-team-damage",
        "rule:wengine:14125:owner:1251:tea-threshold-team-damage",
    ]
    payload["enabled_rule_item_ids"] = rule_ids
    payload["condition_values"] = {
        "condition:wengine:14125:owner:1361:tea-threshold-team-damage-active": True,
        "condition:wengine:14125:owner:1251:tea-threshold-team-damage-active": True,
    }
    baseline_payload = deepcopy(payload)
    baseline_payload["enabled_rule_item_ids"] = []
    baseline_payload["condition_values"] = {}
    baseline_response = client.post("/api/v1/moves/calculate", json=baseline_payload)
    assert baseline_response.status_code == 200, baseline_response.text
    baseline_region = _breakdown_value(
        baseline_response.json()["events"][0], "damage.normal-bonus-region"
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert result["totals"]["expected"]["complete"] is True
    assert _breakdown_value(event, "damage.normal-bonus-region") == pytest.approx(
        baseline_region + expected_bonus
    )


def test_stinging_razor_current_stacks_apply_physical_damage_and_max_stack_buildup() -> None:
    owner = "character:1401"
    payload = _single_wengine_payload(
        owner,
        "move-entry:alice:1401:basic-star-opera-1",
        "wengine:14126",
        5,
        element="physical",
    )
    damage_rule = "rule:wengine:14126:owner:1401:physical-damage-per-hunter-intent"
    buildup_rule = "rule:wengine:14126:owner:1401:buildup-efficiency-at-max-hunter-intent"
    payload["enabled_rule_item_ids"] = [damage_rule, buildup_rule]
    payload["rule_stack_counts"] = {damage_rule: 3}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(0.72)
    buildup_values = [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "anomaly-buildup.efficiency"
    ]
    assert buildup_values == [pytest.approx(0.80)]
    assert result["totals"]["expected"]["complete"] is True


def test_bird_dream_buildup_applies_to_wearer_while_ether_stacks_change_formal_ap() -> None:
    owner = "character:1331"
    payload = _single_wengine_payload(
        owner,
        "move-entry:character:1331:basic-lady-dance",
        "wengine:14133",
        5,
        element="ether",
    )
    efficiency_rule = "rule:wengine:14133:owner:1331:anomaly-buildup-efficiency"
    ap_rule = "rule:wengine:14133:owner:1331:anomaly-proficiency-per-ether-stack"
    payload["enabled_rule_item_ids"] = [efficiency_rule, ap_rule]
    payload["rule_stack_counts"] = {ap_rule: 6}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    stats = result["resolved_character_snapshots"][0]["stats"]
    assert stats["anomaly_proficiency"] == pytest.approx(382.0)
    buildup_values = [
        item["value"]
        for item in result["events"][0]["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "anomaly-buildup.efficiency"
    ]
    assert buildup_values == [pytest.approx(0.64)]
    assert result["totals"]["expected"]["complete"] is True


def test_sweetbunny_team_stats_and_ether_curtain_crit_state_have_separate_scopes() -> None:
    payload = _with_supporting_wengine(
        _valid_calculation_payload(),
        [("character:1341", "wengine:14134", 5, "ice")],
    )
    team_rule = "rule:wengine:14134:owner:1341:team-attack-hp"
    veil_rule = "rule:wengine:14134:owner:1341:team-crit-damage-after-ether-veil"
    energy_rule = "rule:wengine:14134:owner:1341:energy-regen-flat"
    veil_condition = "condition:wengine:14134:owner:1341:ether-veil-team-crit-damage-active"
    baseline = client.post("/api/v1/moves/calculate", json=payload)
    assert baseline.status_code == 200, baseline.text
    before = {
        item["character_id"]: item["stats"]
        for item in baseline.json()["resolved_character_snapshots"]
    }
    assert before["character:1341"]["hp"] == pytest.approx(14800.0)
    assert before["character:1341"]["energy_regen"] == pytest.approx(1.2)
    payload["enabled_rule_item_ids"] = [energy_rule, team_rule, veil_rule]
    payload["condition_values"] = {veil_condition: True}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    after = {
        item["character_id"]: item["stats"]
        for item in result["resolved_character_snapshots"]
    }
    for character_id in ("character:1431", "character:1341"):
        assert after[character_id]["attack"] == pytest.approx(before[character_id]["attack"] * 1.16)
        assert after[character_id]["hp"] == pytest.approx(before[character_id]["hp"] * 1.16)
        assert after[character_id]["crit_damage"] == pytest.approx(
            before[character_id]["crit_damage"] + 0.48
        )
    assert after["character:1341"]["energy_regen"] == pytest.approx(1.94)
    assert after["character:1341"]["hp"] == pytest.approx(17168.0)
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("move_entry_id", "expected_damage_bonus", "expected_pen_bonus"),
    (
        ("move-entry:character:1371:basic-xiaoyun-jin-1", 0.256, 0.0),
        ("move-entry:character:1371:ex-qingming-shock-break", 0.256, 0.32),
    ),
)
def test_cyan_cage_keeps_ether_damage_and_ultimate_ex_penetration_lanes_separate(
    move_entry_id: str,
    expected_damage_bonus: float,
    expected_pen_bonus: float,
) -> None:
    payload = _single_wengine_payload(
        "character:1371",
        move_entry_id,
        "wengine:14137",
        5,
        element="ether",
    )
    rule_id = "rule:wengine:14137:owner:1371:ether-damage-per-cyan-journey-stack"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 2}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(
        expected_damage_bonus
    )
    penetration_events = [
        item for item in result["events"] if item["damage_type"] == "penetration"
    ]
    if expected_pen_bonus:
        assert penetration_events
        penetration_modifiers = [
            item["value"]
            for event in penetration_events
            for item in event["common_application_trace"]["applied_modifiers"]
            if item["source_type"] == "weapon"
            and item["modifier_path"] == "penetration.damage-bonus"
        ]
        assert penetration_modifiers == [pytest.approx(expected_pen_bonus)]
    else:
        assert not any(
            item["source_type"] == "weapon"
            and item["modifier_path"] == "penetration.damage-bonus"
            for event in penetration_events
            for item in event["common_application_trace"]["applied_modifiers"]
        )
    assert result["totals"]["expected"]["complete"] is True


def test_fuyuan_clean_stacks_change_crit_damage_but_not_ineligible_electric_damage() -> None:
    payload = _single_wengine_payload(
        "character:1431",
        "move-entry:ye:1431:basic-fast-1",
        "wengine:14138",
        5,
        element="physical",
    )
    stack_rule = "rule:wengine:14138:owner:1431:crit-damage-per-hit-category-stack"
    electric_rule = "rule:wengine:14138:owner:1431:electric-damage-at-three-stacks"
    payload["enabled_rule_item_ids"] = [stack_rule, electric_rule]
    payload["rule_stack_counts"] = {stack_rule: 3}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"][
        "crit_damage"
    ] == pytest.approx(1.46)
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.0)
    assert result["totals"]["expected"]["complete"] is True


def test_fox_furnace_applies_tagged_daze_without_inventing_fire_team_buff() -> None:
    payload = _single_wengine_payload(
        "character:1361",
        "move-entry:trigger:1361:special-ghost-bloom",
        "wengine:14139",
        5,
        element="electric",
    )
    daze_rule = "rule:wengine:14139:owner:1361:ex-chain-ultimate-daze"
    team_rule = "rule:wengine:14139:owner:1361:team-damage-per-fire-chain-ultimate-stack"
    payload["enabled_rule_item_ids"] = [daze_rule, team_rule]
    payload["rule_stack_counts"] = {team_rule: 2}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    daze_values = [
        item["value"]
        for item in result["events"][0]["common_application_trace"]["applied_modifiers"]
        if item["source_type"] == "weapon"
        and item["modifier_path"] == "daze.outgoing-bonus"
    ]
    assert daze_values == [pytest.approx(0.448)]
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == pytest.approx(0.0)
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("owner", "move", "wengine_id", "element", "rule_suffix", "condition_suffix"),
    (
        (
            "character:1341",
            "move-entry:character:1341:basic-cold-judgment-1",
            "wengine:13112",
            "ice",
            "defense-counter-extra-damage",
            "defense-counter-damage-ready",
        ),
        (
            "character:1431",
            "move-entry:ye:1431:basic-fast-1",
            "wengine:14001",
            "physical",
            "crit-triggered-extra-damage",
            "crit-triggered-extra-damage-current-hit",
        ),
    ),
)
def test_resolved_extra_damage_events_are_created_only_when_proc_state_is_selected(
    owner: str,
    move: str,
    wengine_id: str,
    element: str,
    rule_suffix: str,
    condition_suffix: str,
) -> None:
    owner_number = owner.split(":")[-1]
    rule_id = f"rule:{wengine_id}:owner:{owner_number}:{rule_suffix}"
    condition_id = f"condition:{wengine_id}:owner:{owner_number}:{condition_suffix}"
    payload = _single_wengine_payload(
        owner,
        move,
        wengine_id,
        5,
        element=element,
    )
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["condition_values"] = {condition_id: False}
    off = client.post("/api/v1/moves/calculate", json=payload)
    assert off.status_code == 200, off.text
    assert off.json()["totals"]["expected"]["complete"] is True

    payload["condition_values"][condition_id] = True
    on = client.post("/api/v1/moves/calculate", json=payload)
    assert on.status_code == 200, on.text
    result = on.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    assert any(
        event["common_application_trace"]["created_by_effect_id"]
        == f"effect:{wengine_id}:owner:{owner_number}:{rule_suffix}"
        for event in result["events"]
    )


def test_bashful_demon_and_kaboom_cannon_apply_team_attack_from_support_owners() -> None:
    owners = (
        ("character:1311", "wengine:13113", 5, "ether"),
        ("character:1411", "wengine:13113", 5, "physical"),
    )
    payload = _with_supporting_wengine(_valid_calculation_payload(), list(owners))
    base_ids = [
        "rule:wengine:13113:owner:1311:team-attack-per-stack",
        "rule:wengine:13113:owner:1411:team-attack-per-stack",
    ]
    payload["enabled_rule_item_ids"] = base_ids
    payload["condition_values"] = {
        "condition:wengine:13113:owner:1311:ex-special-team-attack-buff-active": True,
        "condition:wengine:13113:owner:1411:ex-special-team-attack-buff-active": True,
    }
    payload["rule_stack_counts"] = {rule_id: 4 for rule_id in base_ids}
    bashful = client.post("/api/v1/moves/calculate", json=payload)
    assert bashful.status_code == 200, bashful.text
    bashful_result = bashful.json()
    ye_stats = next(
        item["stats"]
        for item in bashful_result["resolved_character_snapshots"]
        if item["character_id"] == "character:1431"
    )
    assert ye_stats["attack"] == pytest.approx(1353.6)
    assert bashful_result["totals"]["expected"]["complete"] is True

    cannon_payload = _with_supporting_wengine(
        _valid_calculation_payload(), [("character:1311", "wengine:13115", 5, "ether")]
    )
    cannon_rule = "rule:wengine:13115:owner:1311:team-attack-per-ally-stack"
    cannon_payload["enabled_rule_item_ids"] = [cannon_rule]
    cannon_payload["rule_stack_counts"] = {cannon_rule: 3}
    cannon = client.post("/api/v1/moves/calculate", json=cannon_payload)
    assert cannon.status_code == 200, cannon.text
    cannon_result = cannon.json()
    assert cannon_result["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(
        1344.0
    )
    assert cannon_result["totals"]["expected"]["complete"] is True
    energy_diagnostic = next(
        item for item in cannon_result["diagnostics"] if "Energy resource result" in item["message"]
    )
    assert energy_diagnostic["blocking"] is False


def test_peacekeeper_shield_energy_regen_and_buildup_modifier_use_separate_scopes() -> None:
    shield_rule = "rule:wengine:13127:owner:1341:shielded-energy-regeneration"
    payload = _single_wengine_payload(
        "character:1341",
        "move-entry:character:1341:basic-final-judgment",
        "wengine:13127",
        5,
        element="ice",
    )
    payload["enabled_rule_item_ids"] = [shield_rule]
    payload["condition_values"] = {
        "condition:wengine:13127:owner:1341:shield-active": True
    }
    shield = client.post("/api/v1/moves/calculate", json=payload)
    assert shield.status_code == 200, shield.text
    assert shield.json()["resolved_character_snapshots"][0]["stats"][
        "energy_regen"
    ] == pytest.approx(1.84)

    buildup_rule = "rule:wengine:13127:owner:1341:ex-assist-anomaly-buildup"
    payload["enabled_rule_item_ids"] = [buildup_rule]
    payload["move_entry_id"] = "move-entry:character:1341:support-afterglow"
    buildup = client.post("/api/v1/moves/calculate", json=payload)
    assert buildup.status_code == 200, buildup.text
    modifiers = buildup.json()["events"][0]["common_application_trace"]["applied_modifiers"]
    assert any(
        item["modifier_path"] == "anomaly-buildup.efficiency"
        and item["value"] == pytest.approx(0.55)
        for item in modifiers
    )


def test_roaring_ride_random_effect_states_are_independent_and_use_anomaly_proficiency() -> None:
    payload = _single_wengine_payload(
        "character:1401",
        "move-entry:alice:1401:basic-star-opera-1",
        "wengine:13128",
        5,
        element="physical",
    )
    rule = "rule:wengine:13128:owner:1401:random-anomaly-proficiency-buff"
    payload["enabled_rule_item_ids"] = [rule]
    payload["condition_values"] = {
        "condition:wengine:13128:owner:1401:random-anomaly-proficiency-buff-active": True
    }
    result = client.post("/api/v1/moves/calculate", json=payload)
    assert result.status_code == 200, result.text
    stats = result.json()["resolved_character_snapshots"][0]["stats"]
    assert stats["anomaly_proficiency"] == pytest.approx(164.0)
    assert stats["anomaly_mastery"] == pytest.approx(100.0)
    assert stats["attack"] == pytest.approx(2030.0)


def test_box_cutter_followup_state_applies_physical_damage_and_daze_without_current_followup_filter() -> None:
    payload = _single_wengine_payload(
        "character:1251",
        "move-entry:character:1251:dash-entry",
        "wengine:13135",
        5,
        element="electric",
    )
    payload["character_builds"]["character:1251"]["base_stats"][
        "element_damage_bonus"
    ]["physical"] = 0.0
    payload["character_builds"]["character:1251"]["base_stats"][
        "element_damage_bonus"
    ]["electric"] = 0.0
    payload["enemy"]["damage_resistance"]["physical"] = 0.2
    payload["enemy"]["damage_resistance"]["electric"] = 0.2
    rule = "rule:wengine:13135:owner:1251:follow-up-attack-damage-daze"
    payload["enabled_rule_item_ids"] = [rule]
    payload["condition_values"] = {
        "condition:wengine:13135:owner:1251:follow-up-attack-buffs-active": True
    }
    result = client.post("/api/v1/moves/calculate", json=payload)
    assert result.status_code == 200, result.text
    event = result.json()["events"][0]
    assert _breakdown_value(event, "damage.normal-bonus") == pytest.approx(0.24)
    assert any(
        item["modifier_path"] == "daze.outgoing-bonus" and item["value"] == pytest.approx(0.16)
        for item in event["common_application_trace"]["applied_modifiers"]
    )


def test_tremor_trigram_bonus_is_ex_and_ultimate_only() -> None:
    payload = _single_wengine_payload(
        "character:1341",
        "move-entry:character:1341:ultimate-rabbit-slash",
        "wengine:13142",
        5,
        element="ice",
    )
    damage_rule = "rule:wengine:13142:owner:1341:ex-ultimate-damage"
    energy_rule = "rule:wengine:13142:owner:1341:team-energy-restore"
    payload["enabled_rule_item_ids"] = [damage_rule, energy_rule]
    ultimate = client.post("/api/v1/moves/calculate", json=payload)
    assert ultimate.status_code == 200, ultimate.text
    assert _breakdown_value(ultimate.json()["events"][0], "damage.normal-bonus") == pytest.approx(
        0.40
    )
    assert ultimate.json()["totals"]["expected"]["complete"] is True

    payload["move_entry_id"] = "move-entry:character:1341:basic-cold-judgment-1"
    basic = client.post("/api/v1/moves/calculate", json=payload)
    assert basic.status_code == 200, basic.text
    assert _breakdown_value(basic.json()["events"][0], "damage.normal-bonus") == 0.0


def test_grill_owisp_fire_bonus_and_hp_loss_crit_state_keep_distinct_scopes() -> None:
    payload = _single_wengine_payload(
        "character:1371",
        "move-entry:character:1371:basic-xiaoyun-jin-1",
        "wengine:13144",
        5,
        element="ether",
    )
    crit_rule = "rule:wengine:13144:owner:1371:crit-rate-after-hp-loss"
    payload["enabled_rule_item_ids"] = [crit_rule]
    payload["condition_values"] = {
        "condition:wengine:13144:owner:1371:owner-hp-lowered-crit-buff-active": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(
        0.74
    )
    assert _breakdown_value(result["events"][0], "damage.normal-bonus") == 0.0
    fire_rule = "rule:wengine:13144:owner:1371:fire-damage"
    fire_match = next(
        item
        for item in result["events"][0]["common_application_trace"]["rule_matches"]
        if item["rule_id"] == fire_rule
    )
    assert fire_match["status"] == "not-matched"
    assert not any(
        item["modifier_path"] == "damage.normal-bonus"
        for item in result["events"][0]["common_application_trace"]["applied_modifiers"]
    )


def _breakdown_value(event: dict[str, object], node: str) -> float:
    breakdown = event["modes"]["expected"]["calculation_breakdown"]
    return next(item["value"] for item in breakdown if item["node"] == node)


def test_astra_signature_wengine_adds_team_damage_from_equipment_build() -> None:
    payload = _valid_calculation_payload()
    payload["supporting_character_ids"] = ["character:1311"]
    payload["team_character_ids"] = ["character:1431", "character:1311"]
    payload["compile_configs"]["character:1311"] = {
        "core_level": 1,
        "cinema_level": 0,
    }
    payload["character_builds"]["character:1311"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14131",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"ether": 0.0},
        },
    }
    payload["enemy"]["damage_resistance"]["ether"] = 0.2
    payload["condition_values"] = {
        "condition:wengine:14131:owner:1311:damage-buff-active": True,
    }
    payload["enabled_rule_item_ids"] = ["rule:wengine:14131:owner:1311:team-damage"]
    payload["rule_stack_counts"] = {"rule:wengine:14131:owner:1311:team-damage": 2}

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    event_trace = response.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:wengine:14131:owner:1311:team-damage"
        and item["value"] == 0.2
        for item in event_trace["applied_modifiers"]
    )


def test_ye_signature_wengine_uses_the_existing_mingxin_condition_for_veil_effects() -> (
    None
):
    payload = _valid_calculation_payload()
    payload["compile_configs"]["character:1431"]["mingxin_active"] = True
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14143:owner:1431:resistance-ignore",
        "rule:wengine:14143:owner:1431:veil",
    ]

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    event_trace = response.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:wengine:14143:owner:1431:veil-damage"
        for item in event_trace["applied_modifiers"]
    )
    assert any(
        item["effect_id"] == "effect:wengine:14143:owner:1431:veil-crit-damage"
        for item in response.json()["panel_traces"]
    )
    assert all(
        item["source_type"] == "weapon"
        for item in response.json()["panel_traces"]
        if item["effect_id"].startswith("effect:wengine:14143:")
    )


def test_team_ids_must_match_compiled_primary_and_supporting_definitions() -> None:
    payload = _valid_calculation_payload()
    payload["supporting_character_ids"] = ["character:1311"]
    payload["compile_configs"]["character:1311"] = {
        "core_level": 1,
        "cinema_level": 0,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "exactly equal" in response.json()["diagnostics"][0]["message"]


def test_unspecified_trigger_is_omitted_not_encoded_as_empty_actor() -> None:
    payload = _valid_calculation_payload()
    payload["selected_trigger_inputs"] = [
        {
            "input_id": "scenario-trigger:effect:test:actor",
            "actor_id": "",
        }
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "unspecified trigger" in response.json()["diagnostics"][0]["message"]


def test_velina_raw_panel_signature_and_wind_or_infused_cyclone_mapping() -> None:
    raw = load_character_record("character:1561")
    assert raw["source_version"] == "3.2"
    assert raw["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1561.json"
    assert raw["code_name"] == "Velina"
    assert raw["potential_detail"] == {}
    panel = character_base_stats("character:1561")
    assert panel.hp.value == pytest.approx(7788.6961)
    assert panel.attack.value == pytest.approx(872.574)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.anomaly_mastery.value == pytest.approx(112.0)
    assert panel.anomaly_proficiency.value == pytest.approx(165.0)
    assert panel.energy_regen.value == pytest.approx(1.2)
    assert str(SIGNATURE_WENGINE_BY_CHARACTER[CharacterId("character:1561")]) == "wengine:14156"

    registration = registration_for("character:1561")
    assert registration.equipment_capabilities.can_produce_damage_scope(
        element=Element.WIND,
        skill_groups=(SkillGroup.SPECIAL_ATTACK,),
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    assert not registration.equipment_capabilities.can_produce_damage_scope(
        element=Element.WIND,
        skill_groups=(SkillGroup.SPECIAL_ATTACK,),
        tags=(DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
    )
    wind = registration.compile_definition(
        {"core_level": 7, "cinema_level": 0},
        (CharacterId("character:1561"),),
        True,
    )
    entries = {str(item.entry_id): item for item in wind.move_entries}
    broad_wind = entries["move-entry:character:1561:broad-cyclone-wind"]
    assert broad_wind.multiplier_variants[0].multiplier.value.value == pytest.approx(0.786)
    assert broad_wind.multiplier_variants[0].repeat_count == 10
    assert entries["move-entry:character:1561:micro-cyclone"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.655)
    weathering = entries["move-entry:character:1561:wind-weathering"]
    assert weathering.multiplier_variants[0].multiplier.value.value == pytest.approx(17.5)

    coloured = registration.compile_definition(
        {"core_level": 7, "cinema_level": 0, "current_coloured_element": 5},
        (CharacterId("character:1561"),),
        True,
    )
    coloured_entry = next(
        item
        for item in coloured.move_entries
        if str(item.entry_id) == "move-entry:character:1561:broad-cyclone-coloured-ether"
    )
    assert coloured_entry.multiplier_variants[0].multiplier.value.value == pytest.approx(0.3908)
    assert coloured_entry.multiplier_variants[0].repeat_count == 10
    assert coloured_entry.main_damage_event.element.value == "ether"


def test_velina_wind_weathering_bonus_is_special_independent_and_not_normal_bonus() -> None:
    payload = _velina_payload("move-entry:character:1561:micro-cyclone")
    payload["condition_values"] = {"condition:velina:enemy-wind-weathered": True}
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:wind-weathered:direct-and-penetration-damage"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    event = response.json()["events"][0]
    assert event["modes"]["expected"]["value"] == pytest.approx(309.90854276374927)
    breakdown = {
        item["node"]: item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["damage.normal-bonus-region"] == pytest.approx(1.0)
    assert breakdown["damage.special-independent-region"] == pytest.approx(1.1)

    # An existing 50% Wind bonus remains in the normal region and multiplies
    # independently by the Winded state's special 1.1 factor.
    payload["character_builds"]["character:1561"]["out_of_combat_stats"]["element_damage_bonus"] = {"wind": 0.5}
    boosted = client.post("/api/v1/moves/calculate", json=payload).json()["events"][0]
    boosted_breakdown = {
        item["node"]: item["value"]
        for item in boosted["modes"]["expected"]["calculation_breakdown"]
    }
    assert boosted_breakdown["damage.normal-bonus-region"] == pytest.approx(1.5)
    assert boosted_breakdown["damage.special-independent-region"] == pytest.approx(1.1)


def test_velina_micro_cyclone_dissipation_is_a_separate_discharge_child() -> None:
    payload = _velina_payload("move-entry:character:1561:micro-cyclone")
    payload["condition_values"] = {
        "condition:velina:enemy-wind-weathered": True,
        "condition:velina:micro-cyclone-dissipating": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:wind-weathered:direct-and-penetration-damage",
        "rule:character:1561:core:micro-cyclone-dissipation",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert result["totals"]["expected"]["value"] == pytest.approx(
        2317.8804824730164
    )
    assert [item["damage_subtype"] for item in result["events"]] == [None, "discharge"]
    assert result["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        309.90854276374927
    )
    assert result["events"][1]["modes"]["expected"]["value"] == pytest.approx(
        2007.9719397092672
    )


def test_velina_14156_initial_energy_threshold_uses_initial_equipment_panel() -> None:
    payload = _single_wengine_payload(
        "character:1561",
        "move-entry:character:1561:micro-cyclone",
        "wengine:14156",
        1,
        element="wind",
    )
    payload["compile_configs"]["character:1561"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:core:initial-energy-regeneration-passive"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    stats = result["resolved_character_snapshots"][0]["stats"]
    assert stats["energy_regen"] == pytest.approx(1.92)
    assert stats["anomaly_mastery"] == pytest.approx(136.0)
    breakdown = {
        item["node"]: item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["damage.normal-bonus"] == pytest.approx(0.1512)
    capabilities = registration_for("character:1561").equipment_capabilities
    weapon = compile_wengine(
        WEngineBuildInput(
            WEngineId("wengine:14156"),
            CharacterId("character:1561"),
            level=60,
            refinement=1,
        ),
        owner_capabilities=capabilities,
    )
    stack_rule = next(
        item
        for item in weapon.rule_items
        if str(item.rule_id).endswith("turbulence-weathering-damage-per-stack")
    )
    assert stack_rule.stack_count == 2
    assert stack_rule.stack_max == 2


def test_velina_initial_energy_derived_bonuses_use_continuous_excess() -> None:
    payload = _velina_payload("move-entry:character:1561:wind-weathering")
    payload["character_builds"]["character:1561"]["out_of_combat_stats"][
        "energy_regen"
    ] = 1.205
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:core:initial-energy-regeneration-passive"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()

    snapshot = result["resolved_character_snapshots"][0]
    assert snapshot["stats"]["energy_regen"] == pytest.approx(1.205)
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(112.25)
    trace = result["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["normal_bonus"] == pytest.approx(0.00105)


def test_velina_cinema4_attack_buff_is_owner_panel_state_independent_of_operator() -> None:
    payload = _velina_payload("move-entry:ye:1431:basic-fast-1")
    payload["primary_character_id"] = "character:1431"
    payload["supporting_character_ids"] = ["character:1561"]
    payload["team_character_ids"] = ["character:1431", "character:1561"]
    payload["formation_character_ids"] = ["character:1431", "character:1561"]
    payload["compile_configs"]["character:1431"] = {
        "core_level": 1,
        "cinema_level": 0,
        "mingxin_active": False,
        "entry_move_uses_linren": False,
    }
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 10000.0,
            "attack": 1200.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.65,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    payload["compile_configs"]["character:1561"]["cinema_level"] = 4
    payload["condition_values"] = {"condition:velina:cinema4-attack-active": True}
    payload["enabled_rule_item_ids"] = ["rule:character:1561:cinema4:attack-buff"]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    snapshot = next(
        item
        for item in response.json()["resolved_character_snapshots"]
        if item["character_id"] == "character:1561"
    )
    assert snapshot["character_id"] == "character:1561"
    assert snapshot["stats"]["attack"] == pytest.approx(872.574 * 1.15)


def test_velina_extra_ability_and_cinema6_damage_bonus_keep_separate_conditions() -> None:
    payload = _velina_payload("move-entry:character:1561:wind-weathering")
    payload["supporting_character_ids"] = ["character:1091"]
    payload["team_character_ids"] = ["character:1561", "character:1091"]
    payload["formation_character_ids"] = ["character:1561", "character:1091"]
    payload["compile_configs"]["character:1561"]["cinema_level"] = 6
    payload["compile_configs"]["character:1091"] = {"core_level": 7, "cinema_level": 0}
    payload["character_builds"]["character:1091"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.05,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"ice": 0.0},
        },
    }
    payload["condition_values"] = {"condition:velina:enemy-wind-weathered": True}
    payload["parameter_values"] = {"parameter:velina:wind-weathering-remaining-seconds": 8}
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:extra-ability:wind-weathering-and-turbulence-damage",
        "rule:character:1561:cinema2:extra-ability-damage-increase",
        "rule:character:1561:cinema6:weathering-remaining-time-damage",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    event = response.json()["events"][0]
    assert event["damage_type"] == "anomaly"
    assert event["damage_subtype"] == "attribute-anomaly"
    assert event["modes"]["non-crit"]["status"] == "calculated"
    breakdown = {
        item["node"]: item["value"]
        for item in event["modes"]["non-crit"]["calculation_breakdown"]
    }
    assert breakdown["anomaly.attribute.damage-bonus-region"] == pytest.approx(1.45)

    payload["parameter_values"]["parameter:velina:wind-weathering-remaining-seconds"] = 0
    zero_time = client.post("/api/v1/moves/calculate", json=payload).json()["events"][0]
    zero_breakdown = {
        item["node"]: item["value"]
        for item in zero_time["modes"]["non-crit"]["calculation_breakdown"]
    }
    assert zero_breakdown["anomaly.attribute.damage-bonus-region"] == pytest.approx(1.25)


def test_velina_turbulence_replaces_disorder_and_uses_the_nonwind_source_element() -> None:
    payload = _anby_calculation_payload(
        "move-entry:character:1011:electric-disorder",
        cinema_level=0,
        core_level=7,
        enabled_rule_item_ids=[
            "rule:character:1561:core:wind-triggered-turbulence-candidate"
        ],
    )
    payload["supporting_character_ids"] = ["character:1561"]
    payload["team_character_ids"] = ["character:1011", "character:1561"]
    payload["compile_configs"]["character:1561"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["character_builds"]["character:1561"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 7788.6961,
            "attack": 872.574,
            "defense": 612.6038,
            "impact": 86.0,
            "crit_rate": 0.05,
            "crit_damage": 0.5,
            "anomaly_mastery": 112.0,
            "anomaly_proficiency": 165.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"wind": 0.0},
        },
    }
    payload["condition_values"]["condition:velina:enemy-wind-weathered"] = True
    payload["enemy"]["damage_resistance"] = {"electric": 0.2, "wind": 0.0}
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    event = next(item for item in result["events"] if item["damage_subtype"] == "turbulence")
    assert event["damage_subtype"] == "turbulence"
    assert event["element"] == "electric"
    assert event["modes"]["expected"]["value"] == pytest.approx(
        16200.786622073581
    )
    cyclone = next(item for item in result["events"] if item["damage_type"] == "direct")
    assert cyclone["element"] == "wind"
    assert cyclone["repeat_count"] == 10
    assert cyclone["modes"]["expected"]["known_value"] == pytest.approx(
        3111.3347771538456
    )

    payload["parameter_values"]["parameter:velina:wind-erosion-stacks"] = 1
    micro_result = client.post("/api/v1/moves/calculate", json=payload).json()
    micro_cyclone = next(
        item for item in micro_result["events"] if item["damage_type"] == "direct"
    )
    assert micro_cyclone["repeat_count"] == 1
    assert micro_cyclone["modes"]["expected"]["known_value"] == pytest.approx(
        micro_cyclone["modes"]["expected"]["value"]
    )

    # Without a current Winded state, the same non-Wind event remains ordinary Disorder.
    payload["condition_values"]["condition:velina:enemy-wind-weathered"] = False
    payload["parameter_values"].pop("parameter:velina:wind-erosion-stacks", None)
    without_weathering = client.post("/api/v1/moves/calculate", json=payload).json()
    assert len(without_weathering["events"]) == 1
    assert without_weathering["events"][0]["damage_type"] == "disorder"


def test_velina_ultimate_wind_discharge_is_one_no_move_child_event() -> None:
    payload = _velina_payload("move-entry:character:1561:ultimate-hear-the-wind")
    payload["supporting_character_ids"] = ["character:1091"]
    payload["team_character_ids"] = ["character:1561", "character:1091"]
    payload["formation_character_ids"] = ["character:1561", "character:1091"]
    payload["compile_configs"]["character:1091"] = {"core_level": 7, "cinema_level": 0}
    payload["character_builds"]["character:1091"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.05,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"ice": 0.0},
        },
    }
    payload["condition_values"] = {"condition:velina:enemy-wind-weathered": True}
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:extra-ability:ultimate-wind-discharge"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert len(result["events"]) == 2
    direct, discharge = result["events"]
    assert direct["damage_type"] == "direct"
    assert discharge["damage_type"] == "anomaly"
    assert discharge["damage_subtype"] == "discharge"
    assert discharge["repeat_count"] == 1
    multiplier = next(
        item["value"]
        for item in discharge["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "anomaly.discharge.original-anomaly-multiplier"
    )
    assert multiplier == pytest.approx(6.8)
    assert result["totals"]["expected"]["complete"] is True


@pytest.mark.parametrize(
    ("coloured_element", "broad_element", "broad_unit_multiplier"),
    ((0, "wind", 0.786), (5, "ether", 0.3908)),
)
def test_velina_storm_eye_summons_exactly_one_broad_cyclone_variant(
    coloured_element: int,
    broad_element: str,
    broad_unit_multiplier: float,
) -> None:
    payload = _velina_payload("move-entry:character:1561:ex-storm-eye")
    payload["compile_configs"]["character:1561"]["current_coloured_element"] = coloured_element
    payload["condition_values"] = {"condition:velina:enemy-wind-weathered": False}
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:special:storm-eye-broad-cyclone"
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert len(result["events"]) == 2
    body = next(item for item in result["events"] if "风暴眼" in item["label"])
    broad = next(item for item in result["events"] if "广域气旋" in item["label"])
    assert body["element"] == "wind"
    assert body["modes"]["expected"]["calculation_breakdown"][1]["value"] == pytest.approx(4.334)
    assert broad["element"] == broad_element
    assert broad["repeat_count"] == 10
    assert broad["modes"]["expected"]["calculation_breakdown"][1]["value"] == pytest.approx(broad_unit_multiplier)


@pytest.mark.parametrize(
    ("coloured_element", "broad_element"), ((0, "wind"), (5, "ether"))
)
def test_velina_storm_eye_broad_cyclone_can_dissipate_once(
    coloured_element: int,
    broad_element: str,
) -> None:
    payload = _velina_payload("move-entry:character:1561:ex-storm-eye")
    payload["compile_configs"]["character:1561"]["current_coloured_element"] = coloured_element
    payload["condition_values"] = {
        "condition:velina:enemy-wind-weathered": True,
        "condition:velina:broad-cyclone-dissipating": True,
    }
    payload["enabled_rule_item_ids"] = [
        "rule:character:1561:special:storm-eye-broad-cyclone",
        "rule:character:1561:core:broad-cyclone-dissipation",
    ]

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 3
    broad = next(item for item in result["events"] if "广域气旋" in item["label"])
    discharge = next(item for item in result["events"] if item["damage_subtype"] == "discharge")
    assert broad["element"] == broad_element
    assert broad["repeat_count"] == 10
    assert broad["modes"]["expected"]["known_value"] == pytest.approx(
        broad["modes"]["expected"]["value"] * 10
    )
    assert discharge["repeat_count"] == 1
    assert discharge["damage_subtype"] == "discharge"
    discharge_multiplier = next(
        item["value"]
        for item in discharge["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "anomaly.discharge.original-anomaly-multiplier"
    )
    assert discharge_multiplier == pytest.approx(2.55)
    assert result["totals"]["expected"]["value"] == pytest.approx(
        sum(item["modes"]["expected"]["known_value"] for item in result["events"])
    )


def test_stale_frostbite_state_is_ignored_when_active_team_has_no_ice_element() -> None:
    baseline = _valid_calculation_payload()
    baseline_response = client.post("/api/v1/moves/calculate", json=baseline)
    assert baseline_response.status_code == 200, baseline_response.text

    stale = deepcopy(baseline)
    stale["condition_values"] = {
        "condition:enemy:frostbite-crit-damage-active:primary:character:1431": True
    }
    stale["enabled_rule_item_ids"] = [
        "rule:enemy:frostbite-crit-damage:primary:character:1431"
    ]
    response = client.post("/api/v1/moves/calculate", json=stale)
    assert response.status_code == 200, response.text
    result = response.json()
    baseline_result = baseline_response.json()
    assert result["totals"] == baseline_result["totals"]
    assert result["totals"]["expected"]["complete"] is True
    assert not any(
        item["effect_id"] == "effect:enemy:frostbite-crit-damage:primary:character:1431"
        for item in result["events"][0]["common_application_trace"]["event_stat_modifiers"]
    )
