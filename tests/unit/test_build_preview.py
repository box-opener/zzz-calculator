from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.presentation.base_stats import character_base_stats
from core.presentation.registry import build_registered_build_preview
from web.api import app


client = TestClient(app)


def test_ye_level_60_base_stats_are_normalized_from_fixed_nanoka_record() -> None:
    stats = character_base_stats("character:1431")

    assert stats.hp.value == pytest.approx(7673.7042)
    assert stats.attack.value == pytest.approx(938.2102)
    assert stats.defense.value == pytest.approx(606.5977)
    assert stats.impact.value == 83
    assert stats.crit_rate.value == pytest.approx(0.194)
    assert stats.crit_damage.value == pytest.approx(0.50)
    assert stats.anomaly_mastery.value == 93
    assert stats.anomaly_proficiency.value == 94
    assert stats.energy_regen.value == pytest.approx(1.2)


def test_live_build_preview_returns_real_base_and_current_panel() -> None:
    response = client.post(
        "/api/v1/builds/preview",
        json={
            "character_id": "character:1431",
            "level": 60,
            "wengine_id": "wengine:14143",
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["complete"] is True
    assert payload["base_stats"]["attack"] == pytest.approx(938.2102)
    assert payload["base_stats"]["crit_rate"] == pytest.approx(0.194)
    # 938.2102 character attack + 743 W-Engine white attack.
    assert payload["out_of_combat_stats"]["attack"] == pytest.approx(1681.2102)
    assert any(
        item["source_type"] == "character" and item["source_label"] == "叶瞬光·角色基础"
        for item in payload["provenance"]
    )
    assert any(
        item["source_type"] == "w-engine" and item["stat"] == "attack"
        for item in payload["provenance"]
    )


def test_partial_drive_disc_preview_preserves_known_values_and_display_metadata() -> (
    None
):
    response = client.post(
        "/api/v1/builds/preview",
        json={
            "character_id": "character:1431",
            "level": 60,
            "drive_discs": [
                {
                    "slot": 4,
                    "set_id": "drive-disc:31000",
                    "main_stat": None,
                    "substats": [
                        {"stat": "crit-rate", "roll_count": 1},
                        {"stat": "attack-flat", "roll_count": 2},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["complete"] is False
    assert payload["out_of_combat_stats"]["crit_rate"] == pytest.approx(0.218)
    disc = payload["drive_discs"][0]
    assert disc["main_stat"] is None
    assert disc["complete"] is False
    crit = next(item for item in disc["substats"] if item["stat_key"] == "crit-rate")
    assert crit["label"] == "暴击率"
    assert crit["value_per_roll"] == pytest.approx(0.024)
    assert crit["display_value_per_roll"] == "2.4%"
    assert crit["roll_count"] == 1
    assert crit["total_value"] == pytest.approx(0.024)
    assert crit["display_total_value"] == "2.4%"
    assert any(item["blocking"] for item in payload["diagnostics"])


def test_build_preview_and_non_max_level_are_explicit() -> None:
    response = client.post(
        "/api/v1/builds/preview",
        json={"character_id": "character:1311", "level": 60},
    )
    assert response.status_code == 200
    assert response.json()["base_stats"]["attack"] == pytest.approx(715.77)

    with pytest.raises(ValueError, match="only available at level 60"):
        build_registered_build_preview("character:1431", level=59)
