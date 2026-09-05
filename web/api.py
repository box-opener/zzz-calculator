"""Small same-origin API for the presentation contract.

This module exposes the thin transport boundary. Calculation request assembly
lives in ``calculation_adapter`` so HTTP parsing never becomes a second rules
engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.presentation import (
    build_registered_editor_view,
    build_registered_drive_disc_editor_view,
    build_registered_wengine_editor_view,
    supported_character_catalog,
    supported_drive_disc_catalog,
    supported_wengine_catalog,
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
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"


@app.get("/api/v1/characters")
def list_characters() -> list[dict[str, Any]]:
    return [to_jsonable(item) for item in supported_character_catalog()]


@app.get("/api/v1/wengines")
def list_wengines() -> list[dict[str, Any]]:
    return [to_jsonable(item) for item in supported_wengine_catalog()]


@app.get("/api/v1/drive-discs")
def list_drive_discs() -> list[dict[str, Any]]:
    return [to_jsonable(item) for item in supported_drive_disc_catalog()]


@app.post("/api/v1/drive-discs/preview")
def preview_drive_discs(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    try:
        owner = str(payload.get("equipped_character_id", ""))
        discs = payload.get("discs", ())
        conditions = payload.get("condition_context", {})
        team_values = payload.get("team_character_ids", [owner])
        if not owner:
            raise ValueError("equipped_character_id is required")
        if not isinstance(discs, (list, tuple)):
            raise ValueError("discs must be an array")
        if not isinstance(conditions, dict):
            raise ValueError("condition_context must be an object")
        if not isinstance(team_values, (list, tuple)):
            raise ValueError("team_character_ids must be an array")
        view = build_registered_drive_disc_editor_view(
            owner,
            tuple(discs),
            team_character_ids=tuple(str(item) for item in team_values),
            condition_context=conditions,
        )
        return JSONResponse(to_jsonable(view))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse(
            status_code=400,
            content={
                "schema_version": "presentation-v1",
                "diagnostics": [
                    {
                        "diagnostic_id": "api:drive-disc-preview:invalid-request",
                        "kind": "missing-data",
                        "message": str(exc),
                        "blocking": True,
                    }
                ],
            },
        )


@app.post("/api/v1/wengines/preview")
def preview_wengine(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    """Return rules for one equipped W-Engine instance.

    The catalog endpoint only exposes model metadata.  This endpoint is the
    owner-aware editor contract used by the UI and by calculation requests.
    """

    try:
        wengine_id = str(payload.get("wengine_id", ""))
        equipped_character_id = str(payload.get("equipped_character_id", ""))
        if not wengine_id or not equipped_character_id:
            raise ValueError("wengine_id and equipped_character_id are required")
        team_values = payload.get("team_character_ids", [equipped_character_id])
        if not isinstance(team_values, (list, tuple)):
            raise ValueError("team_character_ids must be an array")
        if (
            "condition_context" in payload
            and "condition_values" in payload
            and payload["condition_context"] != payload["condition_values"]
        ):
            raise ValueError("condition_context and condition_values disagree")
        condition_context = payload.get(
            "condition_context",
            payload.get("condition_values", {}),
        )
        if not isinstance(condition_context, dict):
            raise ValueError("condition_context must be an object")
        view = build_registered_wengine_editor_view(
            wengine_id,
            equipped_character_id,
            tuple(CharacterId(str(item)) for item in team_values),
            level=int(payload.get("level", 60)),
            refinement=int(payload.get("refinement", 1)),
            condition_context=condition_context,
        )
        return JSONResponse(to_jsonable(view))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse(
            status_code=400,
            content={
                "schema_version": "presentation-v1",
                "diagnostics": [
                    {
                        "diagnostic_id": "api:wengine-preview:invalid-request",
                        "kind": "missing-data",
                        "message": str(exc),
                        "blocking": True,
                    }
                ],
            },
        )


@app.post("/api/v1/definitions/preview")
def preview_definition(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    try:
        character_id = str(payload.get("character_id", ""))
        team_ids = tuple(
            CharacterId(str(item))
            for item in payload.get("team_character_ids", (character_id,))
        )
        if len(set(team_ids)) != len(team_ids):
            raise ValueError("team_character_ids must be unique")
        config_values = payload.get("compile_config", {})
        if not isinstance(config_values, dict):
            raise ValueError("compile_config must be an object")
        view = build_registered_editor_view(
            character_id,
            config_values,
            team_ids,
            condition_values=payload.get("condition_values", {}),
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
def calculate_move(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    try:
        from core.presentation.calculation_service import calculate_payload

        return JSONResponse(content=calculate_payload(payload))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse(
            status_code=400,
            content={
                "schema_version": "presentation-v1",
                "diagnostics": [
                    {
                        "diagnostic_id": "api:calculate:invalid-request",
                        "kind": "missing-data",
                        "message": str(exc),
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


__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.api:app", host="127.0.0.1", port=8000, reload=False)
