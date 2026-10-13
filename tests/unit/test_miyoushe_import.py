from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest

from web.api import app
from web import miyoushe


COOKIE = "ltuid_v2=123; ltoken_v2=test-private-token"


def avatar():
    return {
        "id": 1381, "name_mi18n": "零号·安比", "level": 60, "rank": 6,
        "skills": [{"skill_type": t, "level": 7 if t == 5 else 16} for t in (0, 1, 2, 3, 5, 6)],
        "skill_awaken": {"awaken_level": 2},
        "weapon": {"id": 14138, "level": 60, "star": 3, "rarity": "S", "name": "牺牲洁纯"},
        "equip": [{"equipment_type": 1, "rarity": "S", "level": 15,
                   "equip_suit": {"suit_id": 31000},
                   "main_properties": [{"property_id": 11103, "base": "2200"}],
                   "properties": [{"property_id": 12103, "base": "95", "add": 4},
                                  {"property_id": 20103, "base": "4.8%", "add": 1},
                                  {"property_id": 21103, "base": "4.8%", "add": 0},
                                  {"property_id": 31203, "base": "9", "add": 0}]}],
        "properties": [{"property_id": 2, "base": "999", "final": "3500"}],
        "cookie": COOKIE,
    }


def test_real_equipment_and_effective_skill_levels_round_trip_without_double_cinema():
    record = miyoushe.normalize_character(avatar())
    assert record["issues"] == []
    config = record["configuration"]
    assert config["compile_config"]["core_level"] == 7
    assert config["compile_config"]["cinema_level"] == 6
    assert config["compile_config"]["potential_level"] == 2
    assert set(config["compile_config"]["skill_levels"].values()) == {12}
    assert config["wengine"] == {"id": "wengine:14138", "level": 60, "refinement": 3}
    assert config["drive_discs"][0]["substats"][0] == {"stat": "attack-flat", "roll_count": 5}
    assert config["drive_discs"][0]["substats"][1]["roll_count"] == 2
    assert config["manual_panel_stats"] is None
    assert COOKIE not in str(record)
    # The source's final panel is retained for reference, never added as gear stats.
    assert record["source_data"]["properties"][0]["final"] == "3500"
    assert record["source_data"]["skill_awaken"] == {"awaken_level": 2}


@pytest.mark.parametrize("change, issue", [
    (lambda a: a.update(level=50), "60级"),
    (lambda a: a["weapon"].update(level=50), "音擎"),
    (lambda a: a["equip"][0].update(level=12), "15级"),
    (lambda a: a["equip"][0]["properties"][0].update(add=0), "不一致"),
    (lambda a: a.update(id=1611), "尚未接入"),
    (lambda a: a["skills"][-2].update(level=6), "满核心"),
])
def test_unsupported_actual_build_is_saved_but_never_replaced_by_max_level(change, issue):
    raw = avatar(); change(raw)
    record = miyoushe.normalize_character(raw)
    assert record["configuration"] is None
    assert issue in " ".join(record["issues"])
    assert record["source_data"]["level"] == raw["level"]


def test_explicitly_unequipped_weapon_and_empty_discs_are_preserved():
    raw = avatar(); raw.update(weapon=None, equip=[])
    record = miyoushe.normalize_character(raw)
    assert record["configuration"]["wengine"] is None
    assert record["configuration"]["drive_discs"] == []


@pytest.mark.parametrize("count", [0, 37])
def test_official_effective_disc_stat_count_is_preserved_without_arbitrary_plan_data(count):
    raw = avatar()
    raw["equip_plan_info"] = {"valid_property_cnt": count, "cookie": COOKIE, "custom_info": {"token": COOKIE}}
    record = miyoushe.normalize_character(raw)
    assert record["source_data"]["equip_plan_info"] == {"valid_property_cnt": count, "effective_substats": None}
    assert COOKIE not in str(record)


@pytest.mark.parametrize("plan", [None, {}, {"valid_property_cnt": -1}, {"valid_property_cnt": True}, {"valid_property_cnt": "37"}])
def test_missing_or_invalid_effective_stat_count_is_not_invented(plan):
    raw = avatar()
    raw["equip_plan_info"] = plan
    assert miyoushe.normalize_character(raw)["source_data"]["equip_plan_info"] is None


def test_official_effective_scheme_uses_ids_and_respects_an_explicit_empty_selection():
    raw=avatar()
    raw['equip_plan_info']={'valid_property_cnt':8,'plan_effective_property_list':[
        {'id':2,'name':'ignored display text','is_select':True},{'id':20103,'is_select':True},
        {'id':21103,'is_select':False},{'id':999999,'is_select':True}]}
    plan=miyoushe.normalize_character(raw)['source_data']['equip_plan_info']
    assert plan=={'valid_property_cnt':8,'effective_substats':['attack-percent','crit-rate']}
    raw['equip_plan_info']['plan_effective_property_list']=[]
    assert miyoushe.normalize_character(raw)['source_data']['equip_plan_info']['effective_substats']==[]


def test_disc_valid_flags_supply_the_scheme_when_the_plan_list_is_not_returned():
    raw=avatar();raw['equip'][0]['properties'][1]['valid']=True;raw['equip'][0]['properties'][2]['valid']=False
    assert miyoushe.normalize_character(raw)['source_data']['equip_plan_info']['effective_substats']==['crit-rate']


@pytest.mark.parametrize("uid", ["https://example.com", "../12345678", True, 12345678, "00000000"])
def test_invalid_uid_is_rejected_before_any_transport(uid):
    factory = AsyncMock()
    with pytest.raises(miyoushe.MiyousheError):
        asyncio.run(miyoushe.fetch_profile({"uid": uid, "cookie": COOKIE}, transport_factory=factory))
    factory.assert_not_called()


def test_cookie_validation_does_not_echo_secret():
    for cookie in ["private-cookie-with-no-token", "ltoken=private\nheader=evil", ""]:
        with pytest.raises(miyoushe.MiyousheError) as error:
            miyoushe.parsed_cookies(cookie)
        assert cookie not in str(error.value) or not cookie


def test_sdk_transport_uses_only_fixed_cn_endpoint_and_explicit_uid():
    from types import SimpleNamespace
    transport = miyoushe.MiyousheTransport(miyoushe.parsed_cookies(COOKIE))
    transport.client.cookie_manager._raw_request = AsyncMock(return_value=SimpleNamespace(data={"retcode": 0, "data": {"avatar_list": []}}, headers={}))
    asyncio.run(transport.request("avatar/info", "12345678", 1381))
    args, kwargs = transport.client.cookie_manager._raw_request.call_args
    assert args == ("GET", miyoushe.API_BASE + "avatar/info")
    assert kwargs["params"] == {"role_id": "12345678", "server": "prod_gf_cn", "id_list[]": 1381}
    assert kwargs["allow_redirects"] is False


def test_http_import_fetches_details_and_returns_only_sanitized_snapshot(monkeypatch):
    class Transport:
        def __init__(self, cookies):
            assert cookies["ltoken_v2"] == "test-private-token"
        async def request(self, endpoint, uid, avatar_id=None):
            assert uid == "12345678"
            if endpoint == "avatar/basic":
                return {"avatar_list": [{"id": 1381}]}
            assert avatar_id == 1381
            return {"avatar_list": [avatar()]}
    monkeypatch.setattr(miyoushe, "MiyousheTransport", Transport)
    response = TestClient(app).post("/api/v1/miyoushe/characters", json={"uid": "12345678", "cookie": COOKIE})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "test-private-token" not in response.text
    assert response.json()["characters"][0]["configuration"]["compile_config"]["potential_level"] == 2


@pytest.mark.parametrize("code,status", [(-100, 401), (10102, 403), (1034, 428), (10101, 429)])
def test_upstream_auth_privacy_verification_and_rate_errors_are_safe(monkeypatch, code, status):
    class Upstream(Exception):
        retcode = code
    class Transport:
        def __init__(self, cookies): pass
        async def request(self, *args):
            raise Upstream(COOKIE)
    monkeypatch.setattr(miyoushe, "MiyousheTransport", Transport)
    response = TestClient(app).post("/api/v1/miyoushe/characters", json={"uid": "12345678", "cookie": COOKIE})
    assert response.status_code == status
    assert "test-private-token" not in response.text


def test_sdk_privacy_and_rate_limit_exception_mapping_matches_protocol():
    from genshin.errors import DataNotPublic, TooManyRequests, VisitsTooFrequently

    for kind, code, status in [(DataNotPublic, 10102, 403), (TooManyRequests, 10101, 429), (VisitsTooFrequently, -110, 429)]:
        assert miyoushe.upstream_error(kind({"retcode": code})).status == status


@pytest.mark.parametrize("change", [
    lambda a: a.update(skills=None),
    lambda a: a.update(equip=None),
    lambda a: a["equip"][0].update(equip_suit=None),
    lambda a: a["skills"].append(a["skills"][0]),
])
def test_malformed_role_still_preserves_source_and_does_not_block_other_roles(change):
    raw = avatar(); change(raw)
    row = miyoushe.normalize_character(raw)
    assert row["configuration"] is None
    assert row["issues"]
    assert row["source_data"]["skill_awaken"] == {"awaken_level": 2}
    assert COOKIE not in str(row)


def test_copied_cookie_header_is_case_insensitive():
    assert miyoushe.parsed_cookies("cookie: " + COOKIE)["ltoken_v2"] == "test-private-token"


def test_failed_detail_cancels_remaining_requests():
    cancelled = []
    class Transport:
        def __init__(self, cookies): pass
        async def request(self, endpoint, uid, avatar_id=None):
            if endpoint == "avatar/basic":
                return {"avatar_list": [{"id": i} for i in (1381, 1391, 1351)]}
            if avatar_id == 1381:
                await asyncio.sleep(0.01)
                raise TimeoutError(COOKIE)
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled.append(avatar_id)
                raise
    with pytest.raises(miyoushe.MiyousheError) as error:
        asyncio.run(miyoushe.fetch_profile({"uid": "12345678", "cookie": COOKIE}, transport_factory=Transport))
    assert error.value.status == 504
    assert set(cancelled) == {1391, 1351}


def test_bad_body_is_safe_even_when_it_contains_cookie():
    response = TestClient(app).post("/api/v1/miyoushe/characters", json=[COOKIE])
    assert response.status_code == 400
    assert "test-private-token" not in response.text
