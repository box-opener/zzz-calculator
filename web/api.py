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
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"


def _miyoushe_failure(exc) -> JSONResponse:
    return JSONResponse(status_code=exc.status, headers={"Cache-Control": "no-store"}, content={
        "schema_version": "presentation-v1",
        **({"verification": exc.verification} if exc.verification else {}),
        "diagnostics": [{"diagnostic_id": f"api:miyoushe:{exc.code}", "kind": "missing-data",
                         "message": str(exc), "blocking": True}],
    })


@app.post("/api/v1/miyoushe/qr/start")
async def start_miyoushe_qr() -> JSONResponse:
    from .miyoushe import MiyousheError
    from .miyoushe_qr import qr_sessions
    try:
        return JSONResponse(await qr_sessions.start(), headers={"Cache-Control": "no-store"})
    except MiyousheError as exc:
        return _miyoushe_failure(exc)


@app.post("/api/v1/miyoushe/qr/status")
async def poll_miyoushe_qr(payload: Any = Body(default={})) -> JSONResponse:
    from .miyoushe import MiyousheError
    from .miyoushe_qr import qr_sessions
    try:
        if not isinstance(payload, dict):
            raise MiyousheError("扫码请求格式无效。")
        return JSONResponse(await qr_sessions.status(payload.get("session_id")), headers={"Cache-Control": "no-store"})
    except MiyousheError as exc:
        return _miyoushe_failure(exc)


@app.post("/api/v1/miyoushe/qr/cancel")
async def cancel_miyoushe_qr(payload: Any = Body(default={})) -> JSONResponse:
    from .miyoushe import MiyousheError
    from .miyoushe_qr import qr_sessions
    try:
        if not isinstance(payload, dict):
            raise MiyousheError("扫码请求格式无效。")
        return JSONResponse(qr_sessions.cancel(payload.get("session_id")), headers={"Cache-Control": "no-store"})
    except MiyousheError as exc:
        return _miyoushe_failure(exc)


@app.post("/api/v1/miyoushe/characters")
async def import_miyoushe_characters(payload: Any = Body(default={})) -> JSONResponse:
    from .miyoushe import MiyousheError, fetch_profile
    try:
        if not isinstance(payload, dict):
            raise MiyousheError("请求必须包含 UID 和 Cookie 字段。")
        device_headers = None
        qr_session = None
        if "qr_session" in payload:
            from .miyoushe_qr import qr_sessions
            if "cookie" in payload:
                raise MiyousheError("请选择扫码登录或手动 Cookie 中的一种方式。")
            payload = {**payload, "cookie": qr_sessions.cookie_header(payload["qr_session"])}
            device_headers = qr_sessions.record_device_headers(payload["qr_session"])
            qr_session = payload["qr_session"]
        options = {"device_headers": device_headers, "qr_session": qr_session} if qr_session else {}
        return JSONResponse(await fetch_profile(payload, **options), headers={"Cache-Control": "no-store"})
    except MiyousheError as exc:
        return _miyoushe_failure(exc)


@app.post("/api/v1/miyoushe/verification/{action}")
async def miyoushe_verification(action: str, payload: Any = Body(default={})) -> JSONResponse:
    from .miyoushe import MiyousheError
    from .miyoushe_verification import verification_sessions
    try:
        if not isinstance(payload, dict):
            raise MiyousheError("验证请求格式无效。")
        key = payload.get("verification_id")
        if action == "start":
            data = await verification_sessions.start(key)
        elif action == "complete":
            data = await verification_sessions.complete(key, payload.get("proof"))
        elif action == "cancel":
            data = verification_sessions.cancel(key)
        else:
            raise MiyousheError("验证请求不存在。", 404, "unknown-verification-action")
        return JSONResponse(data, headers={"Cache-Control": "no-store"})
    except MiyousheError as exc:
        return _miyoushe_failure(exc)


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
        from core.presentation.substat_analysis import calculate_with_substat_gains

        return JSONResponse(content=calculate_with_substat_gains(payload))
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


@app.get("/api/v1/enemies")
def list_enemies() -> JSONResponse:
    from core.presentation.enemy_catalog import enemy_catalog
    return JSONResponse(enemy_catalog())


@app.get('/api/v1/endgame/seasons')
def endgame_seasons(mode: str) -> JSONResponse:
    from core.data.endgame.loader import seasons
    try:
        return JSONResponse(seasons(mode))
    except ValueError as exc:
        return JSONResponse({'diagnostics': [{'message': str(exc)}]}, status_code=400)


@app.get('/api/v1/endgame/seasons/{mode}/{season_id}')
def endgame_season(mode: str, season_id: str) -> JSONResponse:
    from core.data.endgame.loader import season_detail
    try:
        return JSONResponse(season_detail(mode, season_id))
    except ValueError as exc:
        return JSONResponse({'diagnostics': [{'message': str(exc)}]}, status_code=400)


@app.post('/api/v1/endgame/editor')
def endgame_editor(payload: dict[str, Any] = Body(default={})) -> JSONResponse:
    from core.presentation.endgame import editor_payload
    from core.presentation.calculation_service import _compile_definitions
    try:
        return JSONResponse(editor_payload(payload['endgame_selection'], _compile_definitions(payload)))
    except (TypeError, ValueError, KeyError) as exc:
        return JSONResponse({'diagnostics': [{'message': str(exc)}]}, status_code=400)


# Keep the root static mount after all API routes. Starlette evaluates routes
# in registration order, so mounting ``/`` first would swallow ``/api``.
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")


__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.api:app", host="127.0.0.1", port=8000, reload=False)
