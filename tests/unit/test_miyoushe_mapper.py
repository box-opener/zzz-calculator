from __future__ import annotations

from web.miyoushe_mapper import map_miyoushe_avatar_detail


def _avatar_detail():
    return {
        "avatar": {
            "id": 1051,
            "name_mi18n": "伊德海莉",
            "level": 60,
            "rank": 3,
            "properties": [
                {"property_id": 11101, "base": 99999, "final": 99999},
                {"property_id": 12101, "base": 9999, "final": 9999},
            ],
            "skills": [
                {"skill_type": 0, "level": 14},
                {"skill_type": 1, "level": 12},
                {"skill_type": 2, "level": 11},
                {"skill_type": 3, "level": 13},
                {"skill_type": 5, "level": 8},
                {"skill_type": 6, "level": 12},
            ],
        },
        "weapon": None,
        "equip": [{
            "equipment_type": 1,
            "level": 15,
            "equip_suit": {"suit_id": 31000, "name": "啄木鸟电音"},
            "main_properties": [{"property_id": 11101, "base": 2200, "valid": True}],
            "properties": [
                {"property_id": 12101, "base": 19, "valid": True},
                {"property_id": 20101, "base": 2.4, "valid": True},
                {"property_id": 21101, "base": 4.8, "valid": True},
                {"property_id": 23201, "base": 9, "valid": True},
            ],
        }],
    }


def test_maps_registered_character_progress_and_exact_disc_values_without_final_panel():
    mapped = map_miyoushe_avatar_detail(_avatar_detail(), "character:1051")

    assert mapped["character_id"] == "character:1051"
    assert mapped["display_name"] == "伊德海莉"
    assert mapped["character_level"] == 60
    assert mapped["compile_config"] == {"cinema_level": 3}
    assert mapped["wengine_present"] is True
    assert mapped["wengine_explicit_null"] is True
    assert mapped["drive_discs"] == [{
        "slot": 1,
        "set_id": "drive-disc:31000",
        "main_stat": "hp-flat",
        "main_stat_value": 2200.0,
        "level": 15,
        "substats": [
            {"stat": "attack-flat", "value": 19.0},
            {"stat": "crit-rate", "value": 0.024},
            {"stat": "crit-damage", "value": 0.048},
            {"stat": "penetration-flat", "value": 9.0},
        ],
    }]
    assert mapped["can_apply"] is True
    assert "manual_panel_stats" not in mapped
    assert any(item["code"] == "skills-semantics-unverified" for item in mapped["diagnostics"])


def test_unknown_disc_property_blocks_apply_instead_of_silent_zero_or_wrong_mapping():
    detail = _avatar_detail()
    detail["equip"][0]["properties"][0]["property_id"] = 999999

    mapped = map_miyoushe_avatar_detail(detail, "character:1051")

    assert mapped["can_apply"] is False
    assert any(
        diagnostic["code"] == "drive-disc-substat-unsupported"
        and diagnostic["blocking"] is True
        for diagnostic in mapped["diagnostics"]
    )


def test_unknown_drive_disc_id_blocks_apply():
    detail = _avatar_detail()
    detail["equip"][0]["equip_suit"]["suit_id"] = 999999

    mapped = map_miyoushe_avatar_detail(detail, "character:1051")

    assert mapped["can_apply"] is False
    assert any(diagnostic["code"] == "drive-disc-set-unknown" for diagnostic in mapped["diagnostics"])


def test_local_character_without_source_level_curve_keeps_existing_level():
    detail = _avatar_detail()
    detail["avatar"]["id"] = 1311
    detail["avatar"]["level"] = 50
    mapped = map_miyoushe_avatar_detail(detail, "character:1311")

    assert mapped["character_level"] is None
    assert mapped["can_apply"] is True
    assert any(diagnostic["code"] == "character-level-unavailable" for diagnostic in mapped["diagnostics"])


def test_imports_level_when_local_character_growth_curve_is_available():
    detail = _avatar_detail()
    detail["avatar"]["level"] = 50

    mapped = map_miyoushe_avatar_detail(detail, "character:1051")

    assert mapped["character_level"] == 50
    assert not any(diagnostic["code"] == "character-level-unavailable" for diagnostic in mapped["diagnostics"])


def test_explicitly_empty_equipment_clears_only_the_imported_owner():
    detail = _avatar_detail()
    detail["equip"] = None
    mapped = map_miyoushe_avatar_detail(detail, "character:1051")

    assert mapped["drive_discs"] == []
    assert mapped["drive_discs_present"] is False
    assert mapped["drive_discs_explicit_null"] is True


def test_maps_registered_wengine_only_with_explicit_refinement_and_source_values():
    detail = _avatar_detail()
    detail["weapon"] = {
        "id": 14131,
        "level": 50,
        "refinement": 2,
        "main_properties": [{"property_id": 12101, "base": 321}],
        "properties": [{"property_id": 12102, "base": 12}],
    }

    mapped = map_miyoushe_avatar_detail(detail, "character:1051")

    assert mapped["wengine"] == {
        "id": "wengine:14131",
        "level": 50,
        "refinement": 2,
        "source_base_value": 321.0,
        "source_advanced_stat_value": 0.12,
    }

    detail["weapon"].pop("refinement")
    mapped_without_refinement = map_miyoushe_avatar_detail(detail, "character:1051")
    assert mapped_without_refinement["wengine"] is None
    assert any(
        diagnostic["code"] == "wengine-refinement-missing"
        for diagnostic in mapped_without_refinement["diagnostics"]
    )
