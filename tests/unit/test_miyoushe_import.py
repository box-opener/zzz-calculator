from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from web.miyoushe_import import MiyousheImportError, MiyousheImportService


def _json_response(data, *, headers=None):
    return httpx.Response(
        200,
        json={"retcode": 0, "data": data},
        headers=headers,
    )


def test_official_qr_flow_keeps_credentials_server_side_and_fetches_selected_role():
    requested_paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        if request.url.path.endswith("/app/createQRLogin"):
            return _json_response({
                "ticket": "qr-ticket-secret",
                "url": "https://user.mihoyo.com/qr?ticket=qr-ticket-secret",
            })
        if request.url.path.endswith("/app/queryQRLoginStatus"):
            return _json_response({
                "status": "Confirmed",
                "tokens": [{"token": "stoken-secret"}],
                "user_info": {"mid": "mid-secret", "aid": "account-secret"},
            })
        if request.url.path.endswith("/getCookieAccountInfoBySToken"):
            return _json_response({"uid": "account-secret", "cookie_token": "cookie-secret"})
        if request.url.path.endswith("/getUserGameRolesByCookieToken"):
            return _json_response({
                "list": [{
                    "game_biz": "nap_cn",
                    "game_uid": "123456789",
                    "region": "prod_gf_cn",
                    "nickname": "Test Proxy",
                    "level": 60,
                }],
            })
        if request.url.path.endswith("/common/badge/v1/login/account"):
            return _json_response({}, headers={"set-cookie": "e_nap_token=nap-token-secret; Path=/; HttpOnly"})
        if request.url.path.endswith("/user/avatar_basic_list"):
            return _json_response({"list": [{"unlocked": True, "avatar_id": 1411, "avatar": {"id": 1411}}]})
        if request.url.path.endswith("/user/batch_avatar_detail_v2"):
            return _json_response({"list": [{"avatar": {"id": 1411, "level": 60}, "equip": [], "weapon": None}]})
        return httpx.Response(404, json={"retcode": -1, "message": "unknown"})

    service = MiyousheImportService(transport=httpx.MockTransport(handler))

    async def scenario():
        login = await service.start_login()
        assert set(login) == {"session_id", "qr_url"}
        status = await service.poll_login(login["session_id"])
        assert status["status"] == "Confirmed"
        assert status["roles"] == [{
            "uid": "123456789",
            "nickname": "Test Proxy",
            "level": 60,
            "region": "prod_gf_cn",
            "game_biz": "nap_cn",
        }]
        detail = await service.fetch_avatar_details(login["session_id"], "123456789", 1411)
        assert detail["avatar"]["id"] == 1411
        assert detail["weapon"] is None
        assert "stoken" not in json.dumps(status)
        assert "cookie_token" not in json.dumps(status)
        assert "secret" not in json.dumps(detail)
        with pytest.raises(MiyousheImportError, match="不属于当前米游社账号"):
            await service.fetch_avatar_details(login["session_id"], "000000000", 1411)
        service.logout(login["session_id"])
        with pytest.raises(MiyousheImportError, match="已过期"):
            await service.fetch_avatar_details(login["session_id"], "123456789", 1411)

    asyncio.run(scenario())
    assert "/account/ma-cn-passport/app/createQRLogin" in requested_paths
    assert "/account/ma-cn-passport/app/queryQRLoginStatus" in requested_paths
    assert "/user/avatar_basic_list" in requested_paths
    assert "/user/batch_avatar_detail_v2" in requested_paths
    assert not any("device-fp" in path for path in requested_paths)


def test_upstream_human_verification_is_reported_without_echoing_response_body():
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="private anti-bot challenge payload")

    service = MiyousheImportService(transport=httpx.MockTransport(handler))

    async def scenario():
        with pytest.raises(MiyousheImportError) as captured:
            await service.start_login()
        assert captured.value.code == "human-verification-required"
        assert "不会自动绕过" in str(captured.value)
        assert "private anti-bot challenge payload" not in str(captured.value)

    asyncio.run(scenario())
