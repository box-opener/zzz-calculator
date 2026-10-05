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
    build_registered_build_preview,
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
        formation_values = payload.get("formation_character_ids")
        if not owner:
            raise ValueError("equipped_character_id is required")
        if not isinstance(discs, (list, tuple)):
            raise ValueError("discs must be an array")
        if not isinstance(conditions, dict):
            raise ValueError("condition_context must be an object")
        if not isinstance(team_values, (list, tuple)):
            raise ValueError("team_character_ids must be an array")
        if formation_values is not None and not isinstance(
            formation_values, (list, tuple)
        ):
            raise ValueError("formation_character_ids must be an ordered array or null")
        team_ids = tuple(str(item) for item in team_values)
        formation_ids = (
            None
            if formation_values is None
            else tuple(str(item) for item in formation_values)
        )
        if formation_ids is not None and (
            len(set(formation_ids)) != len(formation_ids)
            or set(formation_ids) != set(team_ids)
        ):
            raise ValueError(
                "formation_character_ids must contain each active teammate exactly once"
            )
        view = build_registered_drive_disc_editor_view(
            owner,
            tuple(discs),
            team_character_ids=team_ids,
            condition_context=conditions,
            formation_character_ids=formation_ids,
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


@app.post("/api/v1/builds/preview")
def preview_build(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    """Return the authoritative live panel for one equipment build.

    The endpoint accepts partial Drive Disc input and intentionally returns a
    200 response with known static contributions plus blocking diagnostics.
    Formal move calculation keeps its stricter completeness gate.
    """

    try:
        character_id = str(
            payload.get("character_id", payload.get("equipped_character_id", ""))
        )
        if not character_id:
            raise ValueError("character_id is required")
        raw_discs = payload.get("drive_discs", payload.get("discs", ()))
        if not isinstance(raw_discs, (list, tuple)):
            raise ValueError("drive_discs must be an array")
        raw_team = payload.get("team_character_ids", [character_id])
        raw_formation = payload.get("formation_character_ids")
        if not isinstance(raw_team, (list, tuple)):
            raise ValueError("team_character_ids must be an array")
        if raw_formation is not None and not isinstance(raw_formation, (list, tuple)):
            raise ValueError("formation_character_ids must be an ordered array or null")
        team_ids = tuple(str(item) for item in raw_team)
        formation_ids = (
            None
            if raw_formation is None
            else tuple(str(item) for item in raw_formation)
        )
        if formation_ids is not None and (
            len(set(formation_ids)) != len(formation_ids)
            or set(formation_ids) != set(team_ids)
        ):
            raise ValueError(
                "formation_character_ids must contain each active teammate exactly once"
            )
        wengine_id = payload.get("wengine_id")
        if wengine_id is not None and not str(wengine_id).strip():
            wengine_id = None
        view = build_registered_build_preview(
            character_id,
            team_character_ids=team_ids,
            formation_character_ids=formation_ids,
            level=int(payload.get("level", 60)),
            wengine_id=str(wengine_id) if wengine_id is not None else None,
            wengine_level=int(payload.get("wengine_level", 60)),
            wengine_refinement=int(payload.get("wengine_refinement", 1)),
            discs=tuple(item for item in raw_discs if isinstance(item, dict)),
        )
        if len(view.drive_discs) != len(raw_discs):
            raise ValueError("drive_disc must be an object")
        return JSONResponse(to_jsonable(view))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse(
            status_code=400,
            content={
                "schema_version": "presentation-v1",
                "diagnostics": [
                    {
                        "diagnostic_id": "api:build-preview:invalid-request",
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
        formation_values = payload.get("formation_character_ids")
        if not isinstance(team_values, (list, tuple)):
            raise ValueError("team_character_ids must be an array")
        if formation_values is not None and not isinstance(
            formation_values, (list, tuple)
        ):
            raise ValueError("formation_character_ids must be an ordered array or null")
        team_ids = tuple(str(item) for item in team_values)
        formation_ids = (
            None
            if formation_values is None
            else tuple(str(item) for item in formation_values)
        )
        if formation_ids is not None and (
            len(set(formation_ids)) != len(formation_ids)
            or set(formation_ids) != set(team_ids)
        ):
            raise ValueError(
                "formation_character_ids must contain each active teammate exactly once"
            )
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
            tuple(CharacterId(item) for item in team_ids),
            level=int(payload.get("level", 60)),
            refinement=int(payload.get("refinement", 1)),
            condition_context=condition_context,
            formation_character_ids=formation_ids,
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
            primary_character_id=payload.get("primary_character_id"),
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
