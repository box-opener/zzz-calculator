from __future__ import annotations

import asyncio
import base64
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest

from web.api import app
from web import miyoushe, miyoushe_qr

SECRET = "synthetic-qr-login-secret"
COOKIES = {key: ("123" if "uid" in key or "id_v2" in key else SECRET) for key in miyoushe_qr.COOKIE_KEYS}


class Transport:
    def __init__(self, now, states=None):
        self.now = now
        self.states = states or ["created", "scanned", "confirmed"]
        self.check_count = 0
        self.account_error = None

    async def create(self):
        return {"ticket": "synthetic-ticket", "url": f"https://user.mihoyo.com/login-platform/mobile.html?expire={int(self.now[0]) + 120}&tk=synthetic-ticket#/login/qr"}

    async def check(self, ticket):
        assert ticket == "synthetic-ticket"
        self.check_count += 1
        state = self.states.pop(0)
        return state, COOKIES if state == "confirmed" else {}

    async def accounts(self, cookies):
        assert cookies["ltoken_v2"] == SECRET
        if self.account_error:
            raise self.account_error
        return [{"uid": "12345678", "nickname": "测试绳匠"}]


@pytest.fixture
def setup():
    now = [2_000_000_000.0]
    transport = Transport(now)
    manager = miyoushe_qr.QRLoginSessions(transport_factory=lambda: transport, clock=lambda: now[0])
    yield now, transport, manager
    for key in list(manager.sessions):
        manager.drop(key)


def test_login_states_never_return_cookies_and_expire_confirmed_credentials(setup):
    now, transport, manager = setup
    async def scenario():
        created = await manager.start()
        key = created["session_id"]
        image = base64.b64decode(created["qr_image"].split(",", 1)[1])
        assert b"<svg" in image
        assert "ticket" not in created and SECRET not in str(created)
        with pytest.raises(miyoushe.MiyousheError) as error:
            manager.cookie_header(key)
        assert error.value.status == 401
        for expected in ("created", "scanned", "confirmed"):
            result = await manager.status(key)
            assert result["status"] == expected
            assert SECRET not in str(result)
            now[0] += 2
        assert result["accounts"] == [{"uid": "12345678", "nickname": "测试绳匠"}]
        assert SECRET in manager.cookie_header(key)
        await manager.status(key)
        assert transport.check_count == 3
        session = manager.sessions[key]
        now[0] += miyoushe_qr.LOGIN_TTL
        with pytest.raises(miyoushe.MiyousheError) as error:
            manager.cookie_header(key)
        assert error.value.status == 410
        assert session.cookies == {} and session.ticket == ""
    asyncio.run(scenario())


@pytest.mark.parametrize("state", ["expired", "cancelled"])
def test_upstream_terminal_status_removes_local_session(setup, state):
    _, transport, manager = setup
    transport.states = [state]
    async def scenario():
        key = (await manager.start())["session_id"]
        assert (await manager.status(key))["status"] == state
        assert key not in manager.sessions
    asyncio.run(scenario())


def test_fast_parallel_polling_is_serialized_and_throttled(setup):
    _, transport, manager = setup
    async def scenario():
        key = (await manager.start())["session_id"]
        results = await asyncio.gather(*(manager.status(key) for _ in range(8)))
        assert {r["status"] for r in results} == {"created"}
        assert transport.check_count == 1
    asyncio.run(scenario())


def test_cancel_while_confirming_does_not_resurrect_credentials(setup):
    _, transport, manager = setup
    entered = None
    release = None
    async def check(ticket):
        entered.set()
        await release.wait()
        return "confirmed", COOKIES
    transport.check = check
    async def scenario():
        nonlocal entered, release
        entered, release = asyncio.Event(), asyncio.Event()
        key = (await manager.start())["session_id"]
        pending = asyncio.create_task(manager.status(key))
        await entered.wait()
        manager.cancel(key)
        release.set()
        with pytest.raises(miyoushe.MiyousheError) as error:
            await pending
        assert error.value.status == 410
        assert key not in manager.sessions
    asyncio.run(scenario())


def test_capacity_includes_in_flight_creation(setup):
    _, transport, manager = setup
    manager.capacity = 1
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        original = transport.create
        async def create():
            entered.set(); await release.wait(); return await original()
        transport.create = create
        pending = asyncio.create_task(manager.start())
        await entered.wait()
        with pytest.raises(miyoushe.MiyousheError) as error:
            await manager.start()
        assert error.value.status == 429
        release.set(); await pending
        assert manager.starting == 0
    asyncio.run(scenario())


def test_failed_uid_lookup_does_not_discard_confirmed_login(setup):
    _, transport, manager = setup
    transport.states = ["confirmed"]
    transport.account_error = TimeoutError(SECRET)
    async def scenario():
        key = (await manager.start())["session_id"]
        result = await manager.status(key)
        assert result["status"] == "confirmed" and result["account_warning"] is True
        assert result["accounts"] == [] and SECRET not in str(result)
        assert SECRET in manager.cookie_header(key)
    asyncio.run(scenario())


def test_unexpected_qr_destination_is_rejected_before_rendering(setup):
    _, transport, manager = setup
    transport.create = AsyncMock(return_value={"ticket": "synthetic-ticket", "url": "https://example.com/?tk=synthetic-ticket"})
    with pytest.raises(miyoushe.MiyousheError) as error:
        asyncio.run(manager.start())
    assert error.value.status == 502 and manager.sessions == {}


def test_verified_session_can_fetch_roles_without_browser_cookie_and_manual_still_works(setup, monkeypatch):
    _, transport, manager = setup
    transport.states = ["confirmed"]
    monkeypatch.setattr(miyoushe_qr, "qr_sessions", manager)
    async def fetch(payload, **options):
        assert SECRET in payload["cookie"]
        return {"uid": payload["uid"], "characters": []}
    monkeypatch.setattr(miyoushe, "fetch_profile", fetch)
    with TestClient(app) as client:
        created = client.post("/api/v1/miyoushe/qr/start")
        assert created.status_code == 200 and created.headers["cache-control"] == "no-store"
        key = created.json()["session_id"]
        confirmed = client.post("/api/v1/miyoushe/qr/status", json={"session_id": key})
        assert confirmed.json()["status"] == "confirmed" and SECRET not in confirmed.text
        imported = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "qr_session": key})
        assert imported.status_code == 200 and SECRET not in imported.text
        manual = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "cookie": "ltoken_v2=" + SECRET})
        assert manual.status_code == 200
        assert client.post("/api/v1/miyoushe/qr/cancel", json={"session_id": key}).status_code == 200
        assert client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "qr_session": key}).status_code == 410


@pytest.mark.parametrize("code,state", [(-3501, "expired"), (-3505, "cancelled")])
def test_transport_maps_official_expiry_and_rejection_codes(code, state):
    transport = miyoushe_qr.QRTransport()
    transport._request = AsyncMock(return_value=({"retcode": code}, {}))
    assert asyncio.run(transport.check("synthetic-ticket"))[0] == state


def test_identity_verification_is_reported_without_login_bypass():
    transport = miyoushe_qr.QRTransport()
    transport._request = AsyncMock(return_value=({"retcode": 0, "data": {"status": "Confirmed", "need_realperson": True}}, COOKIES))
    with pytest.raises(miyoushe.MiyousheError) as error:
        asyncio.run(transport.check("synthetic-ticket"))
    assert error.value.status == 428 and SECRET not in str(error.value)


def test_confirmed_cookie_memory_is_cleared_by_timer_without_more_requests(setup, monkeypatch):
    _, transport, manager = setup
    transport.states = ["confirmed"]
    monkeypatch.setattr(miyoushe_qr, "LOGIN_TTL", 0.02)
    async def scenario():
        key = (await manager.start())["session_id"]
        await manager.status(key)
        session = manager.sessions[key]
        assert session.cookies
        await asyncio.sleep(0.05)
        assert key not in manager.sessions and session.cookies == {}
    asyncio.run(scenario())


def test_cookie_expiration_during_uid_lookup_invalidates_login(setup):
    from genshin.errors import InvalidCookies
    _, transport, manager = setup
    transport.states = ["confirmed"]
    transport.account_error = InvalidCookies({"retcode": -100})
    async def scenario():
        key = (await manager.start())["session_id"]
        with pytest.raises(miyoushe.MiyousheError) as error:
            await manager.status(key)
        assert error.value.status == 401 and key not in manager.sessions
    asyncio.run(scenario())


def test_optional_uid_lookup_verification_does_not_drop_confirmed_login(setup):
    from genshin.errors import GeetestError
    _, transport, manager = setup
    transport.states = ["confirmed"]
    transport.account_error = GeetestError({"retcode": 1034})
    async def scenario():
        key = (await manager.start())["session_id"]
        result = await manager.status(key)
        assert result["status"] == "confirmed" and result["account_warning"]
        assert SECRET in manager.cookie_header(key)
    asyncio.run(scenario())


def test_invalid_qr_bodies_and_mixed_auth_do_not_echo_credentials():
    with TestClient(app) as client:
        for path in ("status", "cancel"):
            response = client.post(f"/api/v1/miyoushe/qr/{path}", json=[SECRET])
            assert response.status_code == 400 and SECRET not in response.text
        response = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "cookie": SECRET, "qr_session": "x" * 43})
        assert response.status_code == 400 and SECRET not in response.text
