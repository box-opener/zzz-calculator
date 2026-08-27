"""Small same-origin API for the presentation contract.

This module deliberately stops at preview in Stage-017-2.  Calculation request
assembly is completed in Stage-017-3; returning an explicit diagnostic here is
safer than exposing a partial second implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.application.characters.astra import (
    AstraCompileConfig,
    compile_astra,
    load_raw_record as load_astra_raw_record,
)
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.scenario import CalculationScenario
from core.data.loader import load_character_record
from core.presentation import (
    build_character_editor_view,
    supported_character_catalog,
)
from core.presentation.serialization import to_jsonable
from core.types import CharacterId


app = FastAPI(
    title="ZZZ Calculator Presentation API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ASSET_ROOT = _PROJECT_ROOT / "asset"
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"
if _ASSET_ROOT.is_dir():
    app.mount("/asset", StaticFiles(directory=_ASSET_ROOT), name="assets")


@app.get("/api/v1/characters")
def list_characters() -> list[dict[str, Any]]:
    return [to_jsonable(item) for item in supported_character_catalog()]


@app.post("/api/v1/definitions/preview")
def preview_definition(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    try:
        character_id = str(payload.get("character_id", ""))
        definition = _compile_definition(character_id, payload)
        team_ids = tuple(
            CharacterId(str(item))
            for item in payload.get("team_character_ids", (character_id,))
        )
        if len(set(team_ids)) != len(team_ids):
            raise ValueError("team_character_ids must be unique")
        current_operator = CharacterId(str(payload.get("current_operator", team_ids[0])))
        if current_operator not in set(team_ids):
            raise ValueError("current_operator must be a team member")
        scenario = _preview_scenario(definition, payload, team_ids)
        view = build_character_editor_view(
            definition,
            scenario=scenario,
            team_character_ids=team_ids,
        )
        return JSONResponse(to_jsonable(view))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse(
            status_code=400,
            content={
                "schema_version": "presentation-v1",
                "diagnostics": [
                    {
                        "diagnostic_id": "api:preview:invalid-request",
                        "kind": "missing-data",
                        "message": str(exc),
                        "blocking": True,
                    }
                ],
            },
        )


@app.post("/api/v1/moves/calculate")
def calculate_move(_: dict[str, Any] = Body(default={})) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "schema_version": "presentation-v1",
            "diagnostics": [
                {
                    "diagnostic_id": "api:calculate:stage-017-3",
                    "kind": "unsupported-calculator",
                    "message": "Move calculation request assembly is enabled in Stage-017-3",
                    "blocking": True,
                }
            ],
        },
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "schema_version": "presentation-v1"}


# Keep the root static mount after all API routes. Starlette evaluates routes
# in registration order, so mounting ``/`` first would swallow ``/api``.
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")


def _compile_definition(character_id: str, payload: dict[str, Any]):
    if character_id == "character:1311":
        return compile_astra(
            AstraCompileConfig(
                core_level=int(payload.get("core_level", 1)),
                cinema_level=int(payload.get("cinema_level", 0)),
                additional_ability_eligible=bool(
                    payload.get("additional_ability_eligible", False)
                ),
            ),
            load_astra_raw_record(load_character_record(character_id)),
        )
    if character_id == "character:1431":
        return compile_ye_shunguang(
            YeShunguangCompileConfig(
                core_level=int(payload.get("core_level", 1)),
                cinema_level=int(payload.get("cinema_level", 0)),
                mingxin_active=bool(payload.get("mingxin_active", False)),
                entry_move_uses_linren=bool(
                    payload.get("entry_move_uses_linren", False)
                ),
                enemy_stun_vulnerability_bonus=float(
                    payload.get("enemy_stun_vulnerability_bonus", 0.0)
                ),
            ),
            load_ye_raw_record(load_character_record(character_id)),
        )
    raise ValueError(f"unsupported character_id: {character_id}")


def _preview_scenario(definition, payload: dict[str, Any], team_ids):
    condition_values = payload.get("condition_values", {})
    if not isinstance(condition_values, dict):
        raise ValueError("condition_values must be an object")
    conditions = tuple(
        item
        if item.resolution.value == "static"
        else type(item)(
            condition_id=item.condition_id,
            label=item.label,
            original_text=item.original_text,
            resolution=item.resolution,
            value=condition_values.get(str(item.condition_id), item.value),
        )
        for item in definition.scenario_conditions
    )
    return CalculationScenario(
        scenario_id="preview",
        current_operator=CharacterId(str(payload.get("current_operator", team_ids[0]))),
        conditions=conditions,
        parameters=definition.scenario_parameters,
    )


__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.api:app", host="127.0.0.1", port=8000, reload=False)
