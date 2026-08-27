from __future__ import annotations

from fastapi.testclient import TestClient

from web.api import app


client = TestClient(app)


def test_catalog_uses_production_ids_and_assets() -> None:
    response = client.get("/api/v1/characters")
    assert response.status_code == 200
    payload = response.json()
    assert {item["character_id"] for item in payload} == {
        "character:1311",
        "character:1431",
    }
    assert all(item["image_path"].startswith("/characters/") for item in payload)
    assert client.get("/characters/IconRole36.webp").status_code == 200


def test_definition_preview_returns_versioned_editor_view() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1311",
            "team_character_ids": ["character:1311", "character:1431"],
            "cinema_level": 6,
            "additional_ability_eligible": True,
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


def test_invalid_preview_is_structured_and_calculation_is_explicitly_deferred() -> None:
    invalid = client.post("/api/v1/definitions/preview", json={"character_id": "unknown"})
    assert invalid.status_code == 400
    assert invalid.json()["diagnostics"][0]["blocking"] is True

    deferred = client.post("/api/v1/moves/calculate", json={})
    assert deferred.status_code == 501
    assert deferred.json()["diagnostics"][0]["kind"] == "unsupported-calculator"


def test_root_static_mount_does_not_swallow_api_routes() -> None:
    assert client.get("/api/health").json() == {
        "status": "ok",
        "schema_version": "presentation-v1",
    }
