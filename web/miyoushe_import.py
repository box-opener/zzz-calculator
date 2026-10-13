"""Server-only access to the official CN MiHoYo account and ZZZ record APIs.

Authentication material is kept in process memory and is never returned by
these methods. The browser receives only a short-lived session handle, the
official QR link needed for the user to scan, and non-secret role metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import secrets
import time
import uuid
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx


PASSPORT_BASE = "https://passport-api.mihoyo.com"
API_TAKUMI_BASE = "https://api-takumi.mihoyo.com"
ACT_TAKUMI_BASE = "https://act-api-takumi.mihoyo.com"
NAP_CULTIVATE_BASE = f"{ACT_TAKUMI_BASE}/event/nap_cultivate_tool"

CREATE_QR_URL = f"{PASSPORT_BASE}/account/ma-cn-passport/app/createQRLogin"
QUERY_QR_URL = f"{PASSPORT_BASE}/account/ma-cn-passport/app/queryQRLoginStatus"
COOKIE_TOKEN_URL = f"{PASSPORT_BASE}/account/auth/api/getCookieAccountInfoBySToken"
GAME_ROLES_URL = f"{PASSPORT_BASE}/binding/api/getUserGameRolesByCookieToken"
NAP_BOOTSTRAP_URL = f"{API_TAKUMI_BASE}/common/badge/v1/login/account"
QR_APP_ID = "ddxf5dufpuyo"
QR_USER_AGENT = "HYPContainer/1.3.3.182"
QR_EXPIRED_RETCODE = -106
SESSION_TTL_SECONDS = 60 * 60
HTTP_TIMEOUT = httpx.Timeout(12.0, connect=4.0)


class MiyousheImportError(ValueError):
    """A safe-to-display import error which never includes upstream payloads."""

    def __init__(self, message: str, *, code: str = "miyoushe-import-error") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class MiyousheRole:
    uid: str
    nickname: str
    level: int | None
    region: str
    game_biz: str

    def to_json(self) -> dict[str, object]:
        return {
            "uid": self.uid,
            "nickname": self.nickname,
            "level": self.level,
            "region": self.region,
            "game_biz": self.game_biz,
        }


@dataclass(slots=True)
class _Session:
    session_id: str
    device_id: str
    ticket: str
    qr_url: str
    created_at: float
    status: str = "Created"
    stoken: str | None = None
    mid: str | None = None
    stuid: str | None = None
    cookie_token: str | None = None
    account_id: str | None = None
    roles: tuple[MiyousheRole, ...] = ()
    nap_tokens: dict[str, str] = field(default_factory=dict)


def _new_device() -> str:
    # The official QR protocol requires a client-generated device ID. Keep it
    # ephemeral; do not fabricate a device fingerprint or claim a false OS.
    return str(uuid.uuid4())


class MiyousheImportService:
    """Small in-memory official-account session manager for this local app."""

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport
        self._sessions: dict[str, _Session] = {}

    def _prune(self) -> None:
        cutoff = time.time() - SESSION_TTL_SECONDS
        for session_id in tuple(self._sessions):
            if self._sessions[session_id].created_at < cutoff:
                del self._sessions[session_id]

    def _session(self, session_id: str) -> _Session:
        self._prune()
        session = self._sessions.get(session_id)
        if session is None:
            raise MiyousheImportError("登录状态已过期，请重新扫码。", code="session-expired")
        return session

    @staticmethod
    def _safe_official_qr_url(value: object) -> str:
        if not isinstance(value, str):
            raise MiyousheImportError("米游社没有返回有效二维码，请重试。", code="qr-invalid")
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host == "mihoyo.com"
            or host.endswith(".mihoyo.com")
            or host == "miyoushe.com"
            or host.endswith(".miyoushe.com")
        ):
            raise MiyousheImportError("米游社返回的二维码域名无效。", code="qr-invalid")
        return value

    @staticmethod
    def _payload(response: httpx.Response, context: str) -> dict[str, Any]:
        if response.status_code in {403, 429}:
            raise MiyousheImportError(
                "米游社要求官方验证或限制了请求；不会自动绕过。请先在米游社官方页面完成验证后重试。",
                code="human-verification-required",
            )
        try:
            raw = response.json()
        except ValueError as exc:
            raise MiyousheImportError(
                "米游社没有返回可读取的数据；如官方页面要求验证，请先在官方页面完成人工验证后重试。",
                code="human-verification-required",
            ) from exc
        if not isinstance(raw, dict):
            raise MiyousheImportError(f"{context}返回了无法识别的数据。", code="upstream-invalid")
        if response.status_code >= 400:
            raise MiyousheImportError(f"{context}请求失败（HTTP {response.status_code}）。", code="upstream-http")
        return raw

    @classmethod
    def _data(cls, response: httpx.Response, context: str) -> dict[str, Any]:
        raw = cls._payload(response, context)
        retcode = raw.get("retcode")
        if retcode != 0:
            if retcode == QR_EXPIRED_RETCODE:
                raise MiyousheImportError("二维码已过期，请刷新后重试。", code="qr-expired")
            if retcode in {-100, 10001, 10002, 10101, -3101}:
                raise MiyousheImportError("米游社会话已失效，请重新扫码。", code="auth-expired")
            raise MiyousheImportError(
                f"{context}失败（官方错误码 {retcode}）。请检查米游社官方页面是否要求人工验证后重试。",
                code="upstream-error",
            )
        data = raw.get("data")
        if not isinstance(data, dict):
            raise MiyousheImportError(f"{context}没有返回数据。", code="upstream-invalid")
        return data

    async def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=HTTP_TIMEOUT, transport=self._transport)

    async def _request(self, client: httpx.AsyncClient, method: str, url: str, *, context: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise MiyousheImportError("连接米游社超时，请稍后重试。", code="upstream-timeout") from exc
        except httpx.RequestError as exc:
            raise MiyousheImportError("暂时无法连接米游社，请检查网络后重试。", code="upstream-network") from exc
        return self._data(response, context)

    @staticmethod
    def _qr_headers(device_id: str) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": QR_USER_AGENT,
            "x-rpc-app_id": QR_APP_ID,
            "x-rpc-client_type": "3",
            "x-rpc-device_id": device_id,
            "Content-Type": "application/json",
        }

    async def _create_qr(self, client: httpx.AsyncClient, session: _Session) -> None:
        data = await self._request(
            client,
            "POST",
            CREATE_QR_URL,
            context="创建米游社二维码",
            headers=self._qr_headers(session.device_id),
            json={},
        )
        ticket = data.get("ticket")
        qr_url = data.get("url")
        if not isinstance(ticket, str) or not ticket or qr_url is None:
            raise MiyousheImportError("米游社二维码响应缺少必要字段。", code="qr-invalid")
        session.ticket = ticket
        session.qr_url = self._safe_official_qr_url(qr_url)
        session.status = "Created"

    async def start_login(self) -> dict[str, str]:
        self._prune()
        device_id = _new_device()
        session = _Session(
            session_id=secrets.token_urlsafe(24),
            device_id=device_id,
            ticket="",
            qr_url="",
            created_at=time.time(),
        )
        async with await self._client() as client:
            await self._create_qr(client, session)
        self._sessions[session.session_id] = session
        return {"session_id": session.session_id, "qr_url": session.qr_url}

    @staticmethod
    def _cookie_header(values: Mapping[str, str | None]) -> str:
        return "; ".join(f"{key}={value}" for key, value in values.items() if value)

    async def _exchange_cookie_token(self, client: httpx.AsyncClient, session: _Session) -> None:
        assert session.stoken and session.mid
        url = f"{COOKIE_TOKEN_URL}?stoken={session.stoken}"
        headers = {"Cookie": self._cookie_header({"mid": session.mid, "stoken": session.stoken})}
        try:
            response = await client.get(url, headers=headers)
        except httpx.TimeoutException as exc:
            raise MiyousheImportError("获取米游社会话超时，请重新扫码。", code="upstream-timeout") from exc
        except httpx.RequestError as exc:
            raise MiyousheImportError("无法验证米游社会话，请重新扫码。", code="upstream-network") from exc
        data = self._data(response, "验证米游社会话")
        cookie_token = data.get("cookie_token") or response.cookies.get("cookie_token")
        account_id = response.cookies.get("account_id") or data.get("uid") or session.stuid
        if not isinstance(cookie_token, str) or not cookie_token or account_id is None:
            raise MiyousheImportError("米游社没有返回可用的账号授权。", code="auth-incomplete")
        session.cookie_token = cookie_token
        session.account_id = str(account_id)

    async def _load_roles(self, client: httpx.AsyncClient, session: _Session) -> tuple[MiyousheRole, ...]:
        assert session.cookie_token and session.account_id
        url = f"{GAME_ROLES_URL}?game_biz=nap_cn"
        cookie = self._cookie_header({"account_id": session.account_id, "cookie_token": session.cookie_token})
        data = await self._request(client, "GET", url, context="读取绝区零账号角色", headers={"Cookie": cookie})
        raw_list = data.get("list")
        if not isinstance(raw_list, list):
            raise MiyousheImportError("米游社没有返回绝区零角色列表。", code="roles-invalid")
        roles = []
        for raw in raw_list:
            if not isinstance(raw, dict) or raw.get("game_biz") not in {None, "nap_cn"}:
                continue
            uid = raw.get("game_uid")
            region = raw.get("region")
            nickname = raw.get("nickname", "")
            level = raw.get("level")
            if uid is None or not isinstance(region, str) or not region:
                continue
            roles.append(
                MiyousheRole(
                    uid=str(uid),
                    nickname=str(nickname),
                    level=level if isinstance(level, int) and not isinstance(level, bool) else None,
                    region=region,
                    game_biz="nap_cn",
                )
            )
        session.roles = tuple(roles)
        if not roles:
            raise MiyousheImportError("这个米游社账号没有绑定绝区零国服角色。", code="roles-empty")
        return session.roles

    async def poll_login(self, session_id: str) -> dict[str, object]:
        session = self._session(session_id)
        if session.roles:
            return {"status": "Confirmed", "roles": [role.to_json() for role in session.roles]}
        async with await self._client() as client:
            try:
                data = await self._request(
                    client,
                    "POST",
                    QUERY_QR_URL,
                    context="查询米游社扫码状态",
                    headers=self._qr_headers(session.device_id),
                    json={"ticket": session.ticket},
                )
            except MiyousheImportError as exc:
                if exc.code != "qr-expired":
                    raise
                await self._create_qr(client, session)
                return {"status": "Created", "qr_url": session.qr_url, "refreshed": True}
            status = data.get("status")
            if status not in {"Created", "Scanned", "Confirmed"}:
                raise MiyousheImportError("米游社返回了无法识别的扫码状态。", code="qr-status-invalid")
            session.status = status
            if status != "Confirmed":
                return {"status": status}
            user_info = data.get("user_info")
            tokens = data.get("tokens")
            token = tokens[0].get("token") if isinstance(tokens, list) and tokens and isinstance(tokens[0], dict) else None
            mid = user_info.get("mid") if isinstance(user_info, dict) else None
            aid = user_info.get("aid") if isinstance(user_info, dict) else None
            if not isinstance(token, str) or not token or not isinstance(mid, str) or not mid:
                raise MiyousheImportError("扫码已确认，但米游社未返回完整授权。", code="auth-incomplete")
            session.stoken = token
            session.mid = mid
            session.stuid = str(aid) if aid is not None else None
            await self._exchange_cookie_token(client, session)
            roles = await self._load_roles(client, session)
            return {"status": "Confirmed", "roles": [role.to_json() for role in roles]}

    def roles(self, session_id: str) -> list[dict[str, object]]:
        session = self._session(session_id)
        if not session.roles:
            raise MiyousheImportError("请先完成米游社扫码登录。", code="login-required")
        return [role.to_json() for role in session.roles]

    async def _role(self, session: _Session, role_uid: str) -> MiyousheRole:
        if not session.roles:
            raise MiyousheImportError("请先完成米游社扫码登录。", code="login-required")
        for role in session.roles:
            if role.uid == role_uid:
                return role
        raise MiyousheImportError("所选 UID 不属于当前米游社账号。", code="role-unknown")

    async def _ensure_nap_token(self, client: httpx.AsyncClient, session: _Session, role: MiyousheRole) -> str:
        existing = session.nap_tokens.get(role.uid)
        if existing:
            return existing
        assert session.cookie_token and session.account_id
        cookie = self._cookie_header({"account_id": session.account_id, "cookie_token": session.cookie_token})
        body = {
            "game_biz": role.game_biz,
            "lang": "zh-cn",
            "region": role.region,
            "uid": role.uid,
        }
        try:
            response = await client.post(
                NAP_BOOTSTRAP_URL,
                json=body,
                headers={"Cookie": cookie, "Content-Type": "application/json"},
            )
        except httpx.TimeoutException as exc:
            raise MiyousheImportError("初始化绝区零数据会话超时，请重试。", code="upstream-timeout") from exc
        except httpx.RequestError as exc:
            raise MiyousheImportError("无法初始化绝区零数据会话，请重试。", code="upstream-network") from exc
        self._data(response, "初始化绝区零数据会话")
        token = response.cookies.get("e_nap_token")
        if not token:
            raise MiyousheImportError("米游社没有建立绝区零数据会话。", code="nap-token-missing")
        session.nap_tokens[role.uid] = token
        return token

    async def fetch_avatar_details(self, session_id: str, role_uid: str, avatar_id: int) -> dict[str, Any]:
        session = self._session(session_id)
        role = await self._role(session, role_uid)
        async with await self._client() as client:
            e_nap_token = await self._ensure_nap_token(client, session, role)
            headers = {
                "Cookie": self._cookie_header({"e_nap_token": e_nap_token}),
                "x-rpc-device_id": session.device_id,
                "Referer": "https://act.mihoyo.com/zzz/gt/character-builder-h/index.html",
            }
            basics_url = f"{NAP_CULTIVATE_BASE}/user/avatar_basic_list"
            basics = await self._request(
                client,
                "GET",
                basics_url,
                context="读取绝区零角色列表",
                params={"uid": role.uid, "region": role.region},
                headers=headers,
            )
            basic_list = basics.get("list")
            if not isinstance(basic_list, list):
                raise MiyousheImportError("米游社角色列表格式无法识别。", code="avatar-list-invalid")
            selected = []
            for item in basic_list:
                if not isinstance(item, dict) or item.get("unlocked") is not True:
                    continue
                avatar = item.get("avatar")
                raw_id = avatar.get("id") if isinstance(avatar, dict) else item.get("avatar_id")
                if raw_id == avatar_id:
                    selected.append(item)
            if len(selected) != 1:
                raise MiyousheImportError(
                    "所选角色未在此账号的米游社展示数据中找到。",
                    code="avatar-not-found",
                )
            detail_url = f"{NAP_CULTIVATE_BASE}/user/batch_avatar_detail_v2"
            details = await self._request(
                client,
                "POST",
                detail_url,
                context="读取绝区零角色实装详情",
                params={"uid": role.uid, "region": role.region},
                headers={**headers, "Content-Type": "application/json"},
                json={"avatar_list": selected},
            )
            detail_list = details.get("list")
            if not isinstance(detail_list, list):
                raise MiyousheImportError("米游社角色详情格式无法识别。", code="avatar-detail-invalid")
            matches = []
            for detail in detail_list:
                if not isinstance(detail, dict):
                    continue
                avatar = detail.get("avatar")
                if isinstance(avatar, dict) and avatar.get("id") == avatar_id:
                    matches.append(detail)
            if len(matches) != 1:
                raise MiyousheImportError("米游社未返回所选角色的唯一详情。", code="avatar-detail-invalid")
            return matches[0]

    def logout(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


__all__ = ["MiyousheImportError", "MiyousheImportService", "MiyousheRole"]
