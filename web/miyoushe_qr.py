"""CN web QR login. Cookies remain in bounded, expiring process memory."""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import re
import secrets
import time
from typing import Any
from urllib.parse import parse_qs, urlparse
import uuid

from .miyoushe import MiyousheError, RECORD_VERIFICATION_HEADERS, SERVER, parsed_cookies, upstream_error, validated_uid

SCHEMA_VERSION = "zzz-miyoushe-qr-v1"
QR_TTL = 180
LOGIN_TTL = 600
POLL_SECONDS = 2
COOKIE_KEYS = ("cookie_token_v2", "account_mid_v2", "account_id_v2", "ltoken_v2", "ltmid_v2", "ltuid_v2")


class QRTransport:
    def __init__(self):
        from genshin.utility.auth import QRCODE_HEADERS
        self.headers = {**QRCODE_HEADERS, "x-rpc-device_id": str(uuid.uuid4())}

    async def _request(self, *, ticket: str | None = None):
        import aiohttp
        from genshin.client.routes import CHECK_QRCODE_URL, CREATE_QRCODE_URL
        route = CREATE_QRCODE_URL if ticket is None else CHECK_QRCODE_URL
        async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(), timeout=aiohttp.ClientTimeout(total=12)) as session:
            async with session.post(route.get_url(), headers=self.headers,
                                    json=None if ticket is None else {"ticket": ticket}, allow_redirects=False) as response:
                response.raise_for_status()
                data = await response.json()
                cookies = {key: morsel.value for key, morsel in response.cookies.items() if key in COOKIE_KEYS}
        if not isinstance(data, Mapping) or not isinstance(data.get("retcode"), int):
            raise ValueError("invalid QR response")
        return data, cookies

    async def create(self) -> Mapping[str, Any]:
        from genshin.errors import raise_for_retcode
        data, _ = await self._request()
        if data["retcode"] != 0:
            raise_for_retcode(data)
        return data["data"]

    async def check(self, ticket: str) -> tuple[str, Mapping[str, str]]:
        from genshin.errors import raise_for_retcode
        data, cookies = await self._request(ticket=ticket)
        if data["retcode"] == -3501:
            return "expired", {}
        if data["retcode"] == -3505:
            return "cancelled", {}
        if data["retcode"] != 0:
            raise_for_retcode(data)
        result = data["data"]
        if not isinstance(result, Mapping):
            raise ValueError("invalid QR state")
        realname = result.get("realname_info")
        if result.get("need_realperson") or (isinstance(realname, Mapping) and realname.get("required")):
            raise MiyousheError("米游社要求实名或身份验证，请先在米游社 App 完成，再重新扫码。", 428, "verification-required")
        status = {"Created": "created", "Scanned": "scanned", "Confirmed": "confirmed"}.get(result.get("status"))
        if status is None:
            raise ValueError("unknown QR state")
        return status, cookies

    async def accounts(self, cookies: Mapping[str, str]) -> list[dict[str, str]]:
        import aiohttp
        import genshin
        client = genshin.Client(cookies=cookies, region=genshin.Region.CHINESE, game=genshin.Game.ZZZ, lang="zh-cn")
        result = await client.request_hoyolab(
            "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie",
            params={"game_biz": "nap_cn"}, region=genshin.Region.CHINESE,
            timeout=aiohttp.ClientTimeout(total=12), allow_redirects=False,
        )
        rows = result.get("list")
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError("invalid game accounts")
        accounts = []
        for row in rows:
            if not isinstance(row, Mapping) or row.get("game_biz") != "nap_cn" or row.get("region") != SERVER:
                continue
            uid = validated_uid(str(row.get("game_uid", "")))
            if not any(a["uid"] == uid for a in accounts):
                accounts.append({"uid": uid, "nickname": str(row.get("nickname") or uid)[:80]})
        return accounts


def qr_image(url: str) -> str:
    import qrcode
    from qrcode.image.svg import SvgPathImage
    output = io.BytesIO()
    qrcode.make(url, image_factory=SvgPathImage, border=4).save(output)
    return "data:image/svg+xml;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def login_cookies(raw: Mapping[str, str]) -> dict[str, str]:
    from genshin.models.auth.cookie import QRLoginResult
    # The published QR model contains only six login-cookie fields.
    result = QRLoginResult(**{k: raw.get(k) for k in COOKIE_KEYS}).to_dict()
    if any(not isinstance(v, str) or not v or len(v) > 8192 or any(ord(c) < 32 for c in v) for v in result.values()):
        raise ValueError("invalid login cookies")
    parsed_cookies("; ".join(f"{key}={value}" for key, value in result.items()))
    return result


@dataclass
class _Session:
    transport: Any = field(repr=False)
    ticket: str = field(repr=False)
    expires: float
    status: str = "created"
    next_poll: float = 0
    cookies: dict[str, str] = field(default_factory=dict, repr=False)
    accounts: list[dict[str, str]] = field(default_factory=list)
    account_warning: bool = False
    record_challenge: str | None = field(default=None, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    timer: asyncio.TimerHandle | None = field(default=None, repr=False)


class QRLoginSessions:
    def __init__(self, *, transport_factory=None, clock=time.time, capacity=20):
        self.transport_factory = transport_factory
        self.clock = clock
        self.capacity = capacity
        self.sessions: dict[str, _Session] = {}
        self.starting = 0

    def drop(self, session_id: str):
        from .miyoushe_verification import verification_sessions
        verification_sessions.cancel_for_qr(session_id)
        session = self.sessions.pop(session_id, None)
        if session:
            if session.timer:
                session.timer.cancel()
            session.cookies.clear()
            session.ticket = ""
            session.record_challenge = None

    def _cleanup(self):
        for key, session in list(self.sessions.items()):
            if session.expires <= self.clock():
                self.drop(key)

    def _arm_expiry(self, session_id: str, session: _Session):
        if session.timer:
            session.timer.cancel()
        session.timer = asyncio.get_running_loop().call_later(max(0, session.expires - self.clock()), self.drop, session_id)

    def _get(self, value: object) -> tuple[str, _Session]:
        self._cleanup()
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
            raise MiyousheError("扫码登录会话无效，请重新生成二维码。", 400, "invalid-qr-session")
        session = self.sessions.get(value)
        if session is None:
            raise MiyousheError("扫码登录已过期或结束，请重新扫码。", 410, "qr-expired")
        return value, session

    def _ensure_alive(self, session_id: str, session: _Session):
        if self.sessions.get(session_id) is not session or session.expires <= self.clock():
            self.drop(session_id)
            raise MiyousheError("扫码登录已过期或取消，请重新扫码。", 410, "qr-expired")

    def _snapshot(self, session: _Session) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "status": session.status,
                "expires_at": datetime.fromtimestamp(session.expires, timezone.utc).isoformat(),
                "poll_after_ms": POLL_SECONDS * 1000, "accounts": session.accounts,
                "account_warning": session.account_warning}

    async def start(self) -> dict[str, Any]:
        self._cleanup()
        if len(self.sessions) + self.starting >= self.capacity:
            raise MiyousheError("正在等待的扫码登录过多，请稍后再试。", 429, "qr-capacity")
        self.starting += 1
        try:
            transport = (self.transport_factory or QRTransport)()
            async with asyncio.timeout(15):
                created = await transport.create()
            ticket, url = created["ticket"], created["url"]
            if not isinstance(ticket, str) or not 1 <= len(ticket) <= 200 or not isinstance(url, str) or len(url) > 2048:
                raise ValueError("invalid QR creation")
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            if parsed.scheme != "https" or parsed.hostname not in {"user.mihoyo.com", "user.miyoushe.com"} or parsed.username or parsed.password or parsed.port not in {None, 443} or query.get("tk") != [ticket]:
                raise ValueError("unexpected QR destination")
            expires = min(float(query.get("expire", [self.clock() + QR_TTL])[0]), self.clock() + QR_TTL)
            if expires <= self.clock() or not expires < float("inf"):
                raise ValueError("expired QR creation")
            image = qr_image(url)
            session_id = secrets.token_urlsafe(32)
            session = _Session(transport, ticket, expires)
            self.sessions[session_id] = session
            self._arm_expiry(session_id, session)
            return {**self._snapshot(session), "session_id": session_id, "qr_image": image}
        except MiyousheError:
            raise
        except Exception as exc:
            raise upstream_error(exc) from None
        finally:
            self.starting -= 1

    async def status(self, value: object) -> dict[str, Any]:
        session_id, session = self._get(value)
        async with session.lock:
            self._ensure_alive(session_id, session)
            if session.status == "confirmed" or session.next_poll > self.clock():
                return self._snapshot(session)
            session.next_poll = self.clock() + POLL_SECONDS
            try:
                async with asyncio.timeout(15):
                    status, cookies = await session.transport.check(session.ticket)
                self._ensure_alive(session_id, session)
                if status in {"expired", "cancelled"}:
                    self.drop(session_id)
                    return {**self._snapshot(session), "status": status}
                if status not in {"created", "scanned", "confirmed"}:
                    raise ValueError("invalid QR status")
                if status == "confirmed":
                    session.cookies = login_cookies(cookies)
                    session.expires = self.clock() + LOGIN_TTL
                    session.ticket = ""
                    self._arm_expiry(session_id, session)
                    try:
                        async with asyncio.timeout(15):
                            session.accounts = await session.transport.accounts(dict(session.cookies))
                    except Exception as exc:
                        error = upstream_error(exc)
                        if error.status == 401:
                            raise error from None
                        session.account_warning = True
                    self._ensure_alive(session_id, session)
                session.status = status
                return self._snapshot(session)
            except asyncio.CancelledError:
                self.drop(session_id)
                raise
            except MiyousheError as exc:
                if exc.status in {401, 403, 410, 428}:
                    self.drop(session_id)
                raise
            except Exception as exc:
                raise upstream_error(exc) from None

    def cookie_header(self, value: object) -> str:
        _, session = self._get(value)
        if session.status != "confirmed" or not session.cookies:
            raise MiyousheError("请先在米游社 App 确认扫码登录。", 401, "qr-not-confirmed")
        return "; ".join(f"{key}={value}" for key, value in session.cookies.items())

    def record_device_headers(self, value: object) -> dict[str, str]:
        self.cookie_header(value)
        _, session = self._get(value)
        headers = {k: v for k, v in getattr(session.transport, "headers", {}).items() if k in {"x-rpc-device_id", "x-rpc-device_fp"}}
        if session.record_challenge:
            headers.update({"x-rpc-challenge": session.record_challenge, **RECORD_VERIFICATION_HEADERS})
        return headers

    def remember_record_challenge(self, value: object, challenge: str | None):
        self.cookie_header(value)
        _, session = self._get(value)
        session.record_challenge = challenge

    def cancel(self, value: object) -> dict[str, str]:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
            raise MiyousheError("扫码登录会话无效。")
        self.drop(value)
        return {"schema_version": SCHEMA_VERSION, "status": "cancelled"}


qr_sessions = QRLoginSessions()
