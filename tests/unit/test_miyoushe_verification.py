from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock
from types import SimpleNamespace

from fastapi.testclient import TestClient
from genshin.errors import GeetestError, GenshinException
import pytest

from web.api import app
from web import miyoushe, miyoushe_qr, miyoushe_verification

SECRET = "synthetic-record-cookie"
CHALLENGE = "a" * 32
SERVER_CHALLENGE = "server-issued-record-challenge"
PROOF = {"geetest_challenge": CHALLENGE + "00", "geetest_validate": "valid-user-proof", "geetest_seccode": "valid-user-proof|jordan"}


class Records:
    instances = []
    def __init__(self, cookies, *, device_headers=None):
        self.cookies = dict(cookies)
        self.device_headers = device_headers
        self.verified = bool(device_headers and device_headers.get("x-rpc-challenge") == SERVER_CHALLENGE)
        self.closed = False
        self.verify_error = None
        self.verify_calls = 0
        self.requests = 0
        type(self).instances.append(self)
    async def request(self, endpoint, uid, avatar_id=None):
        self.requests += 1
        assert uid == "12345678" and self.cookies["ltoken_v2"] == SECRET
        if not self.verified:
            raise GeetestError({"retcode": 1034, "message": SECRET})
        return {"avatar_list": []}
    async def create_verification(self):
        return {"gt": "b" * 32, "challenge": CHALLENGE, "success": 1, "new_captcha": 1}
    async def verify(self, proof):
        self.verify_calls += 1
        assert proof == PROOF
        if self.verify_error:
            raise self.verify_error
        self.verified = True
        return SERVER_CHALLENGE
    def clear_credentials(self):
        self.cookies.clear(); self.closed = True


@pytest.fixture
def setup(monkeypatch):
    manager = miyoushe_verification.VerificationSessions()
    monkeypatch.setattr(miyoushe_verification, "verification_sessions", manager)
    Records.instances = []
    monkeypatch.setattr(miyoushe, "MiyousheTransport", Records)
    yield manager
    for key in list(manager.sessions):
        manager.drop(key)


def trigger(client):
    response = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "cookie": "ltoken_v2=" + SECRET})
    assert response.status_code == 428 and SECRET not in response.text
    assert response.json()["diagnostics"][0]["diagnostic_id"] == "api:miyoushe:record-verification-required"
    return response.json()["verification"]["verification_id"]


def test_manual_record_challenge_is_verified_before_retry_and_not_exposed(setup):
    with TestClient(app) as client:
        key = trigger(client)
        response = client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert response.json()["challenge"] == CHALLENGE and SECRET not in response.text
        complete = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF})
        assert complete.status_code == 200 and complete.json()["uid"] == "12345678"
        assert SECRET not in complete.text
        assert key not in setup.sessions
        transport = Records.instances[0]
        assert transport.verified and transport.closed and transport.cookies == {} and transport.requests == 2


@pytest.mark.parametrize("proof", [None, {**PROOF, "geetest_validate": ""}, {**PROOF, "geetest_challenge": "c" * 32}, {**PROOF, "geetest_seccode": "x\nheader"}])
def test_incomplete_or_foreign_proof_does_not_retry_role_request(setup, proof):
    with TestClient(app) as client:
        key = trigger(client)
        client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        response = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": proof})
        assert response.status_code == 400
        assert Records.instances[0].verify_calls == 0 and Records.instances[0].requests == 1


def test_upstream_rejected_proof_keeps_session_and_does_not_fetch_roles(setup):
    with TestClient(app) as client:
        key = trigger(client)
        client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        Records.instances[0].verify_error = GeetestError({"retcode": 1034, "message": SECRET})
        response = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF})
        assert response.status_code == 428 and SECRET not in response.text
        assert key in setup.sessions and Records.instances[0].requests == 1


def test_cancel_during_upstream_verification_cannot_resume_fetch(setup):
    async def scenario():
        transport = Records({"ltoken_v2": SECRET})
        key = setup.register("12345678", transport.cookies, transport)["verification_id"]
        await setup.start(key)
        entered, release = asyncio.Event(), asyncio.Event()
        async def verify(proof):
            entered.set(); await release.wait()
        transport.verify = verify
        pending = asyncio.create_task(setup.complete(key, PROOF))
        await entered.wait()
        setup.cancel(key); release.set()
        with pytest.raises(miyoushe.MiyousheError) as error:
            await pending
        assert error.value.status == 410 and transport.requests == 0 and transport.closed
    asyncio.run(scenario())


def test_timer_cleans_held_credentials_without_another_request(setup, monkeypatch):
    monkeypatch.setattr(miyoushe_verification, "TTL", 0.02)
    async def scenario():
        transport = Records({"ltoken_v2": SECRET})
        key = setup.register("12345678", transport.cookies, transport)["verification_id"]
        await asyncio.sleep(0.05)
        assert key not in setup.sessions and transport.closed and transport.cookies == {}
    asyncio.run(scenario())


def test_qr_device_identity_and_accepted_challenge_are_retained_until_logout(setup, monkeypatch):
    cookies = {key: ("123" if "uid" in key or "id_v2" in key else SECRET) for key in miyoushe_qr.COOKIE_KEYS}
    class Login:
        headers = {"x-rpc-device_id": "owned-device-id", "x-rpc-device_fp": "owned-fingerprint", "x-rpc-client_type": "4"}
        async def create(self):
            import time
            return {"ticket": "ticket", "url": f"https://user.mihoyo.com/login-platform/mobile.html?tk=ticket&expire={int(time.time())+120}"}
        async def check(self, ticket): return "confirmed", cookies
        async def accounts(self, cookies): return [{"uid": "12345678", "nickname": "test"}]
    login = miyoushe_qr.QRLoginSessions(transport_factory=Login)
    monkeypatch.setattr(miyoushe_qr, "qr_sessions", login)
    with TestClient(app) as client:
        qr = client.post("/api/v1/miyoushe/qr/start").json()["session_id"]
        assert client.post("/api/v1/miyoushe/qr/status", json={"session_id": qr}).json()["status"] == "confirmed"
        response = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "qr_session": qr})
        key = response.json()["verification"]["verification_id"]
        assert response.status_code == 428 and SECRET not in response.text
        assert login.cookie_header(qr)
        assert Records.instances[0].device_headers == {"x-rpc-device_id": "owned-device-id", "x-rpc-device_fp": "owned-fingerprint"}
        client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        assert client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF}).status_code == 200
        assert login.record_device_headers(qr)["x-rpc-challenge"] == SERVER_CHALLENGE
        assert login.record_device_headers(qr)["x-rpc-tool-verison"] == "v1.0.14-zzz"
        assert client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "qr_session": qr}).status_code == 200
        # A challenge can expire upstream before the login session expires.
        login.sessions[qr].record_challenge = None
        key = client.post("/api/v1/miyoushe/characters", json={"uid": "12345678", "qr_session": qr}).json()["verification"]["verification_id"]
        client.post("/api/v1/miyoushe/qr/cancel", json={"session_id": qr})
        assert key not in setup.sessions and Records.instances[-1].closed


def test_actual_sdk_verification_calls_use_fixed_endpoints_and_only_verified_challenge(monkeypatch):
    # Restore the production transport for this protocol-boundary test.
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET}, device_headers={"x-rpc-device_id": "owned-device", "x-rpc-device_fp": "owned-fp"})
    assert transport.client.device_id == "owned-device" and transport.client.device_fp == "owned-fp"
    assert transport.client.custom_headers["Referer"] == "https://act.mihoyo.com/"
    assert transport.client.custom_headers["x-rpc-app_version"] == miyoushe.MIYOUSHE_APP_VERSION
    result = {"retcode": 0, "data": {"gt": "b" * 32, "challenge": CHALLENGE, "success": 1, "new_captcha": 1}}
    from genshin.errors import DailyGeetestTriggered, check_for_geetest
    with pytest.raises(DailyGeetestTriggered): check_for_geetest(result)
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data=result))
    asyncio.run(transport.create_verification())
    args, kwargs = transport.client.cookie_manager._raw_request.call_args
    assert args == ("GET", miyoushe.RECORD_VERIFICATION_BASE + "createVerification") and kwargs["params"] == {"is_high": "true"}
    assert kwargs["headers"]["x-rpc-challenge_game"] == "8" and kwargs["allow_redirects"] is False
    assert kwargs["headers"]["x-rpc-tool-verison"] == "v1.0.14-zzz"
    assert "x-rpc-tool-version" not in kwargs["headers"]
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data={"retcode": 1034, "message": SECRET}))
    with pytest.raises(GenshinException): asyncio.run(transport.verify(PROOF))
    assert "x-rpc-challenge" not in transport.client.custom_headers
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data={"retcode": 0, "data": None}))
    with pytest.raises(miyoushe.MiyousheError): asyncio.run(transport.verify(PROOF))
    args, kwargs = transport.client.cookie_manager._raw_request.call_args
    assert args == ("POST", miyoushe.RECORD_VERIFICATION_BASE + "verifyVerification") and kwargs["json"] == PROOF
    assert "x-rpc-challenge" not in transport.client.custom_headers
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data={"retcode": 0, "data": {"challenge": SERVER_CHALLENGE}}))
    assert asyncio.run(transport.verify(PROOF)) == SERVER_CHALLENGE
    assert transport.client.custom_headers["x-rpc-challenge"] == SERVER_CHALLENGE
    transport.clear_credentials()
    assert transport.client.cookie_manager.cookies == {}


@pytest.mark.parametrize("data", [None, {}, "accepted", True, {"challenge": SERVER_CHALLENGE}])
@pytest.mark.parametrize("protocol", ["card", "tool"])
def test_verification_acknowledgement_uses_real_sdk_raw_transport(monkeypatch, data, protocol):
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET}, device_headers={"x-rpc-device_id": "owned-device", "x-rpc-device_fp": "owned-fp"})
    transport._verification_protocol = protocol
    calls = []
    class Response:
        content_type = "application/json"
        headers = {}
        cookies = {}
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def json(self): return {"retcode": 0, "data": data}
    class Session:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            return Response()
    monkeypatch.setattr(transport.client.cookie_manager, "create_session", Session)
    # Exercise the actual SDK response parser, not a mock of request_hoyolab.
    if isinstance(data, dict) and data.get("challenge"):
        assert asyncio.run(transport.verify(PROOF)) == SERVER_CHALLENGE
        assert transport.client.custom_headers["x-rpc-challenge"] == SERVER_CHALLENGE
    else:
        with pytest.raises(miyoushe.MiyousheError): asyncio.run(transport.verify(PROOF))
        assert "x-rpc-challenge" not in transport.client.custom_headers
    method, url, kwargs = calls[0]
    assert method == "POST" and url == (miyoushe.TOOL_VERIFICATION_BASE + "verifyGeetest" if protocol == "tool" else miyoushe.RECORD_VERIFICATION_BASE + "verifyVerification")
    assert kwargs["json"] == {**PROOF, **({"app_key": "game_record_zzz"} if protocol == "tool" else {})} and kwargs["cookies"] == {"ltoken_v2": SECRET}
    headers = kwargs["headers"]
    assert headers["x-rpc-app_version"] == miyoushe.MIYOUSHE_APP_VERSION
    assert headers["User-Agent"].endswith("miHoYoBBS/" + miyoushe.MIYOUSHE_APP_VERSION)
    assert headers["x-rpc-device_id"] == "owned-device" and headers["x-rpc-device_fp"] == "owned-fp"
    # DS must be computed from exactly the JSON submitted to verification.
    import hashlib
    from genshin import constants, Region
    import json
    timestamp, random, digest = headers["ds"].split(",")
    expected = f"salt={constants.DS_SALT[Region.CHINESE]}&t={timestamp}&r={random}&b={json.dumps(kwargs['json'])}&q="
    assert hashlib.md5(expected.encode()).hexdigest() == digest
    assert kwargs["allow_redirects"] is False


@pytest.mark.parametrize("retcode", [1034, 10035])
def test_real_sdk_response_pipeline_binds_protocol_trace_and_server_record_token(monkeypatch, retcode):
    manager = miyoushe_verification.VerificationSessions()
    monkeypatch.setattr(miyoushe_verification, "verification_sessions", manager)
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET})
    calls = []
    class Response:
        content_type = "application/json"
        headers = {"x-trace-id": "synthetic-original-request-trace"}
        cookies = {}
        def __init__(self, envelope): self.envelope = envelope
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def json(self): return self.envelope
    class Session:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def request(self, method, url, **kwargs):
            path = str(url)
            calls.append(path)
            assert kwargs["headers"]["x-rpc-app_version"] == miyoushe.MIYOUSHE_APP_VERSION
            assert kwargs["headers"]["User-Agent"].endswith("miHoYoBBS/" + miyoushe.MIYOUSHE_APP_VERSION)
            if path.endswith(("/createVerification", "/createGeetest")):
                if retcode == 10035:
                    assert path == miyoushe.TOOL_VERIFICATION_BASE + "createGeetest"
                    assert kwargs["params"] == {"is_high": "true", "app_key": "game_record_zzz"}
                else:
                    assert path == miyoushe.RECORD_VERIFICATION_BASE + "createVerification"
                    assert kwargs["params"] == {"is_high": "true"}
                envelope = {"retcode": 0, "data": {"gt": "b" * 32, "challenge": CHALLENGE, "new_captcha": 1, "success": 1}}
            elif path.endswith(("/verifyVerification", "/verifyGeetest")):
                assert kwargs["json"] == {**PROOF, **({"app_key": "game_record_zzz"} if retcode == 10035 else {})}
                assert path == (miyoushe.TOOL_VERIFICATION_BASE + "verifyGeetest" if retcode == 10035 else miyoushe.RECORD_VERIFICATION_BASE + "verifyVerification")
                envelope = {"retcode": 0, "data": {"challenge": SERVER_CHALLENGE}}
            else:
                assert path.endswith("/avatar/basic")
                envelope = {"retcode": 0, "data": {"avatar_list": []}} if kwargs["headers"].get("x-rpc-challenge") == SERVER_CHALLENGE else {"retcode": retcode, "message": SECRET}
            if not path.endswith("/avatar/basic"):
                assert kwargs["headers"]["x-rpc-challenge_path"] == miyoushe.API_BASE + "avatar/basic"
                assert kwargs["headers"]["x-rpc-challenge_trace"] == "synthetic-original-request-trace"
                assert kwargs["headers"]["x-rpc-challenge_game"] == "8"
            return Response(envelope)
    monkeypatch.setattr(transport.client.cookie_manager, "create_session", Session)
    # Keep all SDK request methods and response parsing in the recovery pipeline.
    monkeypatch.setattr(miyoushe, "MiyousheTransport", lambda _: transport)
    with TestClient(app) as client:
        key = trigger(client)
        assert client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key}).status_code == 200
        result = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF})
        assert result.status_code == 200 and result.json()["characters"] == []
        assert SECRET not in result.text and key not in manager.sessions
    middle = ["createGeetest", "verifyGeetest"] if retcode == 10035 else ["createVerification", "verifyVerification"]
    assert [url.rsplit("/", 1)[-1] for url in calls] == ["basic", *middle, "basic"]
    assert transport.client.cookie_manager.cookies == {}


@pytest.mark.parametrize("envelope", [{}, {"retcode": None}, {"retcode": False}, {"retcode": "0"}, {"retcode": -201, "message": SECRET}, []])
def test_unconfirmed_verification_envelope_never_enables_role_retry(envelope):
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET})
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data=envelope))
    with pytest.raises((miyoushe.MiyousheError, GenshinException)):
        asyncio.run(transport.verify(PROOF))
    assert "x-rpc-challenge" not in transport.client.custom_headers


@pytest.mark.parametrize("challenge", [[], True, " ", "injected\nheader", "x" * 2049])
def test_invalid_server_challenge_is_not_forwarded_to_record_requests(challenge):
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET})
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data={"retcode": 0, "data": {"challenge": challenge}}))
    with pytest.raises(miyoushe.MiyousheError) as error:
        asyncio.run(transport.verify(PROOF))
    assert error.value.code == "verification-response-invalid"
    assert "x-rpc-challenge" not in transport.client.custom_headers


@pytest.mark.parametrize("trace", ["synthetic-detail-trace", "injected\nheader", "x" * 129])
def test_detail_verification_binds_failed_path_and_only_valid_trace(trace):
    transport = miyoushe.MiyousheTransport({"ltoken_v2": SECRET})
    raw = AsyncMock(return_value=SimpleNamespace(data={"retcode": 10041, "message": SECRET}, headers={"x-trace-id": trace}))
    transport.client.cookie_manager._raw_request = raw
    with pytest.raises(GenshinException): asyncio.run(transport.request("avatar/info", "12345678", 1381))
    raw.return_value = SimpleNamespace(data={"retcode": 0, "data": {"gt": "b" * 32, "challenge": CHALLENGE, "success": 1, "new_captcha": 1}})
    asyncio.run(transport.create_verification())
    headers = raw.call_args.kwargs["headers"]
    assert headers["x-rpc-challenge_path"] == miyoushe.API_BASE + "avatar/info"
    assert headers.get("x-rpc-challenge_trace") == (trace if trace == "synthetic-detail-trace" else None)
    raw.return_value = SimpleNamespace(data={"retcode": 0, "data": {"challenge": SERVER_CHALLENGE}})
    asyncio.run(transport.verify(PROOF))
    assert raw.call_args.kwargs["headers"]["x-rpc-challenge_path"] == headers["x-rpc-challenge_path"]
    assert raw.call_args.kwargs["headers"].get("x-rpc-challenge_trace") == headers.get("x-rpc-challenge_trace")
    transport.clear_credentials()
    assert transport._verification_context == {}


def test_unknown_verification_rejection_has_safe_stage_and_numeric_code(setup, caplog):
    with TestClient(app) as client:
        key = trigger(client)
        client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        Records.instances[0].verify_error = GenshinException({"retcode": -201, "message": SECRET + str(PROOF)})
        response = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF})
        assert response.status_code == 502 and "错误码 -201" in response.text
        assert "api:miyoushe:verification-upstream-rejected" in response.text
        assert "stage=verification-submit" in caplog.text and "retcode=-201" in caplog.text
        assert SECRET not in response.text + caplog.text and PROOF["geetest_validate"] not in response.text + caplog.text
        assert key in setup.sessions and Records.instances[0].requests == 1


def test_failed_post_verification_record_read_is_distinguished_from_rejected_proof(setup):
    with TestClient(app) as client:
        key = trigger(client)
        client.post("/api/v1/miyoushe/verification/start", json={"verification_id": key})
        Records.instances[0].request = AsyncMock(side_effect=ValueError(SECRET))
        response = client.post("/api/v1/miyoushe/verification/complete", json={"verification_id": key, "proof": PROOF})
        assert response.status_code == 502 and "安全验证已通过，但读取角色失败" in response.text
        assert SECRET not in response.text and Records.instances[0].verified
