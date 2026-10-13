"""Authenticated CN game-record import; calculation semantics stay in core.

The SDK owns the changing DS/cookie protocol. Only sanitized character data
leaves this adapter; credentials never enter the returned browser snapshot.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from http.cookies import SimpleCookie, CookieError
import math
import logging
import re
import uuid
from typing import Any

from core.data.loader import supported_character_ids
from core.data.drive_discs.loader import DRIVE_DISC_SET_IDS
from core.presentation.catalog import supported_wengine_catalog
from core.presentation.registry import registration_for
from core.types import (
    DRIVE_DISC_MAIN_STATS_BY_SLOT, DRIVE_DISC_MAIN_STAT_VALUES,
    DRIVE_DISC_SUBSTAT_VALUES, DriveDiscStatKey, DriveDiscSlot,
    EquippedDriveDisc, DriveDiscSetId, DriveDiscSubstatRoll,
)


SCHEMA_VERSION = "zzz-miyoushe-profile-v1"
API_BASE = "https://api-takumi-record.mihoyo.com/event/game_record_zzz/api/zzz/"
RECORD_VERIFICATION_BASE = "https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/"
TOOL_VERIFICATION_BASE = "https://api-takumi.mihoyo.com/event/toolcomsrv/risk/"
ZZZ_RECORD_APP_KEY = "game_record_zzz"
SERVER = "prod_gf_cn"
# CN WebView context used by the current reference record implementation.
MIYOUSHE_APP_VERSION = "2.102.1"
RECORD_CLIENT_HEADERS = {
    "x-rpc-app_version": MIYOUSHE_APP_VERSION,
    "x-rpc-client_type": "5",
    "X-Requested-With": "com.mihoyo.hyperion",
    "User-Agent": ("Mozilla/5.0 (Linux; Android 13; PHK110 Build/SKQ1.221119.001; wv)"
                   "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/"
                   f"126.0.6478.133 Mobile Safari/537.36 miHoYoBBS/{MIYOUSHE_APP_VERSION}"),
}
# The record protocol intentionally spells this wire header "verison".
RECORD_VERIFICATION_HEADERS = {"x-rpc-challenge_game": "8", "x-rpc-tool-verison": "v1.0.14-zzz"}
_LOGGER = logging.getLogger(__name__)
_UPSTREAM_REASONS = {
    "系统繁忙": "service-busy", "系统错误": "service-error", "internal error": "service-error",
    "验证码错误": "invalid-captcha", "验证失败": "verification-rejected", "verify failed": "verification-rejected",
    "参数错误": "invalid-parameters", "invalid parameters": "invalid-parameters",
}
SKILL_GROUPS = {0: "basic-attack", 2: "dodge", 6: "assist", 1: "special-attack", 3: "chain-attack"}
# Game-record property IDs, not names or equipment array order.
PROPERTY_STATS = {
    11103: "hp-flat", 12103: "attack-flat", 13103: "defense-flat",
    23203: "penetration-flat", 31203: "anomaly-proficiency-flat",
    20103: "crit-rate", 21103: "crit-damage", 11102: "hp-percent",
    12102: "attack-percent", 13102: "defense-percent", 12202: "impact-percent",
    31402: "anomaly-mastery-percent", 30502: "energy-regen-percent",
    23103: "penetration-rate", 31503: "physical-damage-bonus",
    31603: "fire-damage-bonus", 31703: "ice-damage-bonus",
    31803: "electric-damage-bonus", 31903: "ether-damage-bonus", 32303: "wind-damage-bonus",
}


class MiyousheError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "invalid-request"):
        super().__init__(message)
        self.status = status
        self.code = code
        self.verification = None


def validated_uid(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{5,8}", value.strip()):
        raise MiyousheError("请输入国服绝区零游戏 UID（6–9 位数字），不是米游社账号 ID。")
    return value.strip()


def parsed_cookies(value: object) -> dict[str, str]:
    if not isinstance(value, str) or not value.strip() or len(value) > 16384:
        raise MiyousheError("请提供已登录米游社的 Cookie。", 401, "authentication-required")
    text = re.sub(r"^cookie:\s*", "", value.strip(), flags=re.IGNORECASE)
    if any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise MiyousheError("Cookie 必须是单行请求头内容。")
    jar: SimpleCookie = SimpleCookie()
    try:
        jar.load(text)
    except CookieError:
        raise MiyousheError("Cookie 格式无效。") from None
    cookies = {key: item.value for key, item in jar.items()}
    if not any(cookies.get(k) for k in ("ltoken", "ltoken_v2", "cookie_token", "cookie_token_v2")):
        raise MiyousheError("Cookie 中缺少米游社登录令牌，请重新复制登录后的 Cookie。", 401, "authentication-required")
    return cookies


def upstream_error(exc: Exception, *, stage: str = "records") -> MiyousheError:
    # Do not echo upstream messages/exception repr: they may contain credentials.
    code = getattr(exc, "retcode", None)
    code = code if type(code) is int and -1_000_000 <= code <= 1_000_000 else None
    kind = type(exc).__name__
    # Never log exception messages, traceback locals, URLs, UID, Cookie or proof.
    original = getattr(exc, "original", None)
    reason = _UPSTREAM_REASONS.get(original.strip().lower(), "unclassified") if isinstance(original, str) else "unclassified"
    _LOGGER.warning("Miyoushe request failed: stage=%s exception=%s retcode=%s reason=%s", stage, kind, code, reason)
    if code in {-100, -101, 10001, 10002} or kind == "InvalidCookies":
        return MiyousheError("米游社登录已过期或 Cookie 无效，请登录后重新获取。", 401, "login-expired")
    if code == 10102 or kind == "DataNotPublic":
        return MiyousheError("角色战绩未公开，或当前账号无权读取该 UID；请检查战绩隐私设置和账号。", 403, "private-record")
    if code in {1034, 10035, 10041, 5003, -3102} or kind in {"GeetestError", "GeetestFailed", "DailyGeetestTriggered"}:
        return MiyousheError("米游社要求验证码验证，请先在米游社完成验证，再重新获取。", 428, "verification-required")
    if code in {10101, -110, 1028} or kind in {"TooManyRequests", "VisitsTooFrequently"} or getattr(exc, "status", None) == 429:
        return MiyousheError("米游社查询次数已达限制，请稍后再试。", 429, "rate-limited")
    if kind == "AccountNotFound" or code in {1008, 1009}:
        return MiyousheError("未找到对应国服游戏账号，请检查 UID。", 404, "account-not-found")
    if isinstance(exc, TimeoutError):
        return MiyousheError("米游社请求超时，请稍后重试；已保存的资料仍可加载。", 504, "timeout")
    if stage == "verification-submit":
        if code is not None:
            return MiyousheError(f"米游社未接受安全验证（错误码 {code}），请重新打开验证后重试。", 502, "verification-upstream-rejected")
        return MiyousheError("安全验证提交失败，请重新打开验证后重试。", 502, "verification-submit-unavailable")
    suffix = f"（错误码 {code}）" if code is not None else ""
    return MiyousheError(f"米游社暂时不可用或返回格式已变化{suffix}，请稍后重试。", 502, "upstream-unavailable")


class MiyousheTransport:
    def __init__(self, cookies: Mapping[str, str], *, device_headers: Mapping[str, str] | None = None):
        import genshin
        # Keep the QR login's device identity for record requests and their challenge.
        identity = {k: v for k, v in (device_headers or {}).items() if k in {"x-rpc-device_id", "x-rpc-device_fp", "x-rpc-challenge", "x-rpc-challenge_game", "x-rpc-tool-verison"}}
        identity.setdefault("x-rpc-device_id", str(uuid.uuid4()))
        self.client = genshin.Client(cookies=cookies, region=genshin.Region.CHINESE, game=genshin.Game.ZZZ, lang="zh-cn", headers={
            "Referer": "https://act.mihoyo.com/", "Origin": "https://act.mihoyo.com",
            "x-rpc-platform": "2", "x-rpc-page": "v1.0.14_#/zzz", **RECORD_CLIENT_HEADERS, **identity,
        })
        self._verification_context = {"x-rpc-challenge_path": API_BASE + "avatar/basic"}
        self._verification_protocol = "card"

    def clear_credentials(self):
        self.client.cookie_manager.cookies.clear()
        self.client.custom_headers.pop("x-rpc-challenge", None)
        self._verification_context.clear()
        self._verification_protocol = None

    async def _verification_request(self, *, proof: Mapping[str, str] | None = None) -> Any:
        import aiohttp
        import genshin
        from genshin.utility.ds import get_ds_headers
        tool = self._verification_protocol == "tool"
        params = {"is_high": "true", **({"app_key": ZZZ_RECORD_APP_KEY} if tool else {})} if proof is None else None
        body = dict(proof) if proof is not None else None
        if body is not None and tool:
            body["app_key"] = ZZZ_RECORD_APP_KEY
        # Record verification must bind to the actual rejected record request;
        # community verification clears a different risk scope.
        action = ("createGeetest" if proof is None else "verifyGeetest") if tool else ("createVerification" if proof is None else "verifyVerification")
        # Auth responses are envelopes, not game records. Like SDK create_mmt /
        # verify_mmt, check retcode ourselves: the generic record checker assumes
        # data is a mapping and can reject a successful acknowledgement.
        response = await self.client.cookie_manager._raw_request(
            "GET" if proof is None else "POST",
            (TOOL_VERIFICATION_BASE if tool else RECORD_VERIFICATION_BASE) + action,
            params=params, json=body, cookies=self.client.cookie_manager.cookies,
            headers={**get_ds_headers(genshin.Region.CHINESE, params=params, data=body), **self.client.custom_headers,
                     **RECORD_VERIFICATION_HEADERS, **self._verification_context},
            timeout=aiohttp.ClientTimeout(total=12), allow_redirects=False,
        )
        envelope = response.data
        if not isinstance(envelope, Mapping) or type(envelope.get("retcode")) is not int:
            raise MiyousheError("米游社安全验证响应格式无效，请稍后重试。", 502, "verification-response-invalid")
        if envelope["retcode"] != 0:
            genshin.errors.raise_for_retcode(envelope)
        return envelope.get("data")

    async def create_verification(self) -> dict[str, Any]:
        from genshin.models.auth.geetest import MMT
        self.client.custom_headers.pop("x-rpc-challenge", None)
        data = await self._verification_request()
        if not isinstance(data, Mapping):
            raise MiyousheError("米游社安全验证响应格式无效，请稍后重试。", 502, "verification-response-invalid")
        mmt = MMT(**data)
        if not 1 <= len(mmt.gt) <= 128 or not 1 <= len(mmt.challenge) <= 128 or mmt.success != 1:
            raise MiyousheError("安全验证暂不可用，请稍后重试。", 502, "verification-unavailable")
        return mmt.model_dump()

    async def verify(self, proof: Mapping[str, str]):
        # Resume only after the upstream envelope explicitly contains integer 0.
        data = await self._verification_request(proof=proof)
        challenge = data.get("challenge") if isinstance(data, Mapping) else None
        if not isinstance(challenge, str) or not 1 <= len(challenge) <= 2048 or any(not 33 <= ord(c) <= 126 for c in challenge):
            raise MiyousheError("米游社返回的验证令牌格式无效，请重新验证。", 502, "verification-response-invalid")
        self.client.custom_headers.pop("x-rpc-challenge", None)
        # Use only the server-issued record token, never the GeeTest challenge.
        self.client.custom_headers.update({"x-rpc-challenge": challenge, **RECORD_VERIFICATION_HEADERS})
        return challenge

    async def request(self, endpoint: str, uid: str, avatar_id: int | None = None) -> Mapping[str, Any]:
        import aiohttp
        import genshin
        from genshin.utility.ds import get_ds_headers
        if endpoint not in {"avatar/basic", "avatar/info"}:
            raise ValueError("unsupported record endpoint")
        params: dict[str, object] = {"role_id": uid, "server": SERVER}
        if avatar_id is not None:
            params["id_list[]"] = avatar_id
        url = API_BASE + endpoint
        response = await self.client.cookie_manager._raw_request(
            "GET", url, params=params, cookies=self.client.cookie_manager.cookies,
            headers={**get_ds_headers(genshin.Region.CHINESE, params=params), **self.client.custom_headers},
            timeout=aiohttp.ClientTimeout(total=12), allow_redirects=False,
        )
        envelope = response.data
        if not isinstance(envelope, Mapping) or type(envelope.get("retcode")) is not int:
            raise ValueError("invalid record response")
        try:
            if envelope["retcode"] != 0:
                genshin.errors.check_for_geetest({"retcode": envelope["retcode"]})
                genshin.errors.raise_for_retcode(envelope)
            data = envelope.get("data")
            if not isinstance(data, Mapping):
                raise ValueError("invalid record data")
            genshin.errors.check_for_geetest(envelope)
        except genshin.errors.GenshinException as exc:
            if exc.retcode in {1034, 10035, 10041, 5003} or isinstance(exc, genshin.errors.DailyGeetestTriggered):
                self._verification_protocol = "tool" if exc.retcode == 10035 else "card"
                context = {"x-rpc-challenge_path": url}
                trace = response.headers.get("x-trace-id")
                if isinstance(trace, str) and 1 <= len(trace) <= 128 and all(33 <= ord(c) <= 126 for c in trace):
                    context["x-rpc-challenge_trace"] = trace
                self._verification_context = context
            raise
        return data


def integer(value: object, minimum: int, maximum: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{label}缺失或超出支持范围")
    return value


def stat_value(value: object) -> float:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError("词条数值缺失")
    text = str(value).strip().replace(",", "").replace("％", "%")
    try:
        result = float(text.removesuffix("%")) / (100 if text.endswith("%") else 1)
    except ValueError:
        raise ValueError("词条数值无法解析") from None
    if not math.isfinite(result) or result < 0:
        raise ValueError("词条数值无效")
    return result


def import_disc(raw: Mapping[str, Any]) -> dict[str, Any]:
    slot = DriveDiscSlot(integer(raw.get("equipment_type"), 1, 6, "驱动盘槽位"))
    if raw.get("rarity") != "S" or raw.get("level") != 15:
        raise ValueError(f"{slot.value}号驱动盘尚不是 S 级15级，当前装备模型不支持按满级代替")
    suit = raw.get("equip_suit", {})
    set_id = str(suit.get("suit_id")) if isinstance(suit, Mapping) else ""
    if set_id not in DRIVE_DISC_SET_IDS:
        raise ValueError(f"{slot.value}号驱动盘套装暂未支持")
    mains = raw.get("main_properties", [])
    if not isinstance(mains, list) or len(mains) != 1:
        raise ValueError(f"{slot.value}号驱动盘主词条缺失")
    stat = DriveDiscStatKey(PROPERTY_STATS.get(mains[0].get("property_id"), "unknown"))
    if stat not in DRIVE_DISC_MAIN_STATS_BY_SLOT[slot] or not math.isclose(stat_value(mains[0].get("base")), DRIVE_DISC_MAIN_STAT_VALUES[stat], abs_tol=1e-6):
        raise ValueError(f"{slot.value}号驱动盘主词条值与当前模型不符")
    subs = []
    for prop in raw.get("properties", []):
        key = DriveDiscStatKey(PROPERTY_STATS.get(prop.get("property_id"), "unknown"))
        per_roll = DRIVE_DISC_SUBSTAT_VALUES.get(key)
        if per_roll is None:
            raise ValueError("驱动盘副词条类型暂不支持")
        amount = stat_value(prop.get("base"))
        count = round(amount / per_roll)
        if not math.isclose(amount, count * per_roll, abs_tol=1e-6):
            raise ValueError("驱动盘副词条值无法准确换算为当前词条次数")
        if "add" in prop and integer(prop["add"], 0, 5, "副词条强化次数") + 1 != count:
            raise ValueError("驱动盘副词条总值与强化次数不一致")
        subs.append(DriveDiscSubstatRoll(key, count))
    disc = EquippedDriveDisc(slot, DriveDiscSetId(f"drive-disc:{set_id}"), stat, tuple(subs))
    if not disc.complete:
        raise ValueError(f"{slot.value}号驱动盘词条信息不完整")
    return {"slot": slot.value, "set_id": str(disc.set_id), "main_stat": stat.value,
            "substats": [{"stat": s.stat.value, "roll_count": s.roll_count} for s in subs]}


def source_summary(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve useful source fields, rather than persisting arbitrary payloads."""
    def items(value: object, limit: int) -> list[Mapping[str, Any]]:
        return [item for item in value[:limit] if isinstance(item, Mapping)] if isinstance(value, list) else []

    def fields(value: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
        return {key: (value[key][:200] if isinstance(value[key], str) else value[key])
                for key in keys if key in value and isinstance(value[key], (str, int, float, bool))}

    def properties(items: object) -> list[dict[str, Any]]:
        if not isinstance(items, list):
            return []
        return [fields(p, ("property_id", "base", "final", "add", "level", "valid"))
                for p in items[:30] if isinstance(p, Mapping)]
    weapon = raw.get("weapon")
    awakened = raw.get("skill_awaken")
    plan = raw.get("equip_plan_info")
    count = plan.get("valid_property_cnt") if isinstance(plan, Mapping) else None
    valid_count = count if isinstance(count, int) and not isinstance(count, bool) and 0 <= count <= 2**53 - 1 else None
    selected_stats = None
    effective_list = plan.get("plan_effective_property_list") if isinstance(plan, Mapping) else None
    if isinstance(effective_list, list):
        short_ids = {1: "hp-percent", 2: "attack-percent", 3: "defense-percent", 5: "crit-rate", 6: "crit-damage", 8: "anomaly-proficiency-flat", 10: "penetration-flat"}
        selected_stats = sorted({stat for row in items(effective_list, 30)
            if row.get("is_select") is not False
            and type(row.get("id")) is int
            and (stat := PROPERTY_STATS.get(row["id"], short_ids.get(row["id"]))) in {s.value for s in DRIVE_DISC_SUBSTAT_VALUES}})
    else:
        flagged = [p for disc in items(raw.get("equip"), 6) for p in items(disc.get("properties"), 4) if type(p.get("valid")) is bool]
        if flagged:
            selected_stats = sorted({stat for p in flagged if p["valid"] and type(p.get("property_id")) is int and (stat := PROPERTY_STATS.get(p["property_id"])) in {s.value for s in DRIVE_DISC_SUBSTAT_VALUES}})
    return {
        **fields(raw, ("level", "rank")),
        "skills": [fields(s, ("skill_type", "level")) for s in items(raw.get("skills"), 7)],
        "skill_awaken": fields(awakened, ("awaken_level",)) if isinstance(awakened, Mapping) else None,
        "properties": properties(raw.get("properties")),
        "equip_plan_info": {"valid_property_cnt": valid_count, "effective_substats": selected_stats} if valid_count is not None or selected_stats is not None else None,
        "weapon": fields(weapon, ("id", "name", "level", "star", "rarity")) if isinstance(weapon, Mapping) else None,
        "discs": [{**fields(d, ("equipment_type", "level", "rarity")),
                   "set": fields(d["equip_suit"], ("suit_id",)) if isinstance(d.get("equip_suit"), Mapping) else None,
                   "main_properties": properties(d.get("main_properties")), "properties": properties(d.get("properties"))}
                  for d in items(raw.get("equip"), 6)],
    }


def normalize_character(raw: Mapping[str, Any]) -> dict[str, Any]:
    avatar_id = integer(raw.get("id"), 1, 99999, "角色ID")
    cid = f"character:{avatar_id}"
    issues: list[str] = []
    config = None
    if cid not in supported_character_ids():
        issues.append("该角色尚未接入计算器，资料已保留。")
    else:
        try:
            level = integer(raw.get("level"), 1, 60, "角色等级")
            if level != 60:
                raise ValueError("当前角色基础面板仅支持60级，真实等级已保存")
            cinema = integer(raw.get("rank"), 0, 6, "影画")
            skill_rows = raw.get("skills", [])
            if not isinstance(skill_rows, list) or len(skill_rows) > 7:
                raise ValueError("角色技能资料格式无效")
            skills = {integer(s.get("skill_type"), 0, 6, "技能类型"): integer(s.get("level"), 1, 16, "技能等级") for s in skill_rows}
            if len(skills) != len(skill_rows):
                raise ValueError("角色技能类型重复")
            if not {0, 1, 2, 3, 5, 6}.issubset(skills):
                raise ValueError("角色技能资料不完整")
            core = integer(skills[5], 1, 7, "核心技能等级")
            if core != 7:
                raise ValueError("当前基础面板固定满核心突破，未满核心的真实资料已保存")
            bonus = (2 if cinema >= 3 else 0) + (2 if cinema >= 5 else 0)
            base_skills = {group: integer(skills[t] - bonus, 1, 12, "基础技能等级") for t, group in SKILL_GROUPS.items()}
            base_skills["ultimate"] = base_skills["chain-attack"]
            compile_config: dict[str, Any] = {"core_level": core, "cinema_level": cinema, "skill_levels": base_skills}
            fields = registration_for(cid).config_fields(compile_config, ())
            if any(f.field_id == "potential_level" for f in fields):
                awakened = raw.get("skill_awaken")
                if not isinstance(awakened, Mapping):
                    raise ValueError("该角色的潜能资料缺失")
                compile_config["potential_level"] = integer(awakened.get("awaken_level"), 0, 6, "潜能等级")
            weapon = raw.get("weapon")
            wengine = None
            if weapon is not None:
                wid = f"wengine:{integer(weapon.get('id'), 1, 99999, '音擎ID')}"
                if wid not in {w.wengine_id for w in supported_wengine_catalog()}:
                    raise ValueError("该音擎暂未接入计算器")
                if weapon.get("level") != 60:
                    raise ValueError("当前音擎面板仅支持60级，真实等级已保存")
                wengine = {"id": wid, "level": 60, "refinement": integer(weapon.get("star"), 1, 5, "音擎精炼")}
            discs = [import_disc(d) for d in raw.get("equip", [])]
            if len({d["slot"] for d in discs}) != len(discs):
                raise ValueError("驱动盘槽位重复")
            # Validate real config against the registered role (e.g. unavailable Cinema).
            registration_for(cid).compile_definition(compile_config, (cid,), False)
            config = {"schema_version": "zzz-character-config-v2", "character_id": cid,
                      "character_level": level, "build_mode": "equipment-build",
                      "compile_config": compile_config, "wengine": wengine,
                      "drive_discs": discs, "manual_panel_stats": None}
        except ValueError as exc:
            issues.append(str(exc)[:180])
        except (TypeError, KeyError, AttributeError):
            issues.append("角色或装备资料不符合当前计算模型，请检查等级、技能、套装与词条。")
    return {"character_id": cid, "display_name": str(raw.get("name_mi18n") or raw.get("name") or cid)[:80],
            "level": raw.get("level"), "cinema": raw.get("rank"),
            "configuration": config, "issues": issues, "source_data": source_summary(raw)}


async def fetch_profile(payload: Mapping[str, Any], *, transport_factory=None, device_headers=None,
                        qr_session: str | None = None, retain_verification=True) -> dict[str, Any]:
    uid = validated_uid(payload.get("uid"))
    cookies = parsed_cookies(payload.get("cookie"))
    tasks: list[asyncio.Task] = []
    transport = None
    stage = "record-init"
    try:
        if transport_factory is not None:
            transport = transport_factory(cookies)
        elif device_headers is None:
            transport = MiyousheTransport(cookies)
        else:
            transport = MiyousheTransport(cookies, device_headers=device_headers)
        async with asyncio.timeout(60):
            stage = "record-list"
            data = await transport.request("avatar/basic", uid)
            avatars = data.get("avatar_list")
            if not isinstance(avatars, list) or len(avatars) > 100:
                raise ValueError("invalid avatar list")
            ids = [integer(a.get("id"), 1, 99999, "角色ID") for a in avatars]
            if len(set(ids)) != len(ids):
                raise ValueError("duplicate avatar IDs")
            semaphore = asyncio.Semaphore(3)
            async def detail(avatar_id: int):
                async with semaphore:
                    result = await transport.request("avatar/info", uid, avatar_id)
                rows = result.get("avatar_list")
                if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != avatar_id:
                    raise ValueError("wrong avatar detail")
                return normalize_character(rows[0])
            stage = "record-detail"
            tasks = [asyncio.create_task(detail(i)) for i in ids]
            characters = await asyncio.gather(*tasks)
        return {"schema_version": SCHEMA_VERSION, "provider": "miyoushe", "uid": uid,
                "server": SERVER, "fetched_at": datetime.now(timezone.utc).isoformat(), "characters": characters}
    except BaseException as exc:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if isinstance(exc, asyncio.CancelledError):
            raise
        if not isinstance(exc, Exception):
            raise
        if isinstance(exc, MiyousheError):
            raise
        error = upstream_error(exc, stage=stage)
        if error.status == 428 and transport is not None and retain_verification:
            from .miyoushe_verification import verification_sessions
            error = MiyousheError("米游社角色战绩需要安全验证，请在当前页面完成验证后继续获取。", 428, "record-verification-required")
            error.verification = verification_sessions.register(uid, cookies, transport, qr_session=qr_session)
        raise error from None
