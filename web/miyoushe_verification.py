"""User-completed record verification, using the original account/device context."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import secrets
import time
from typing import Any

from .miyoushe import MiyousheError, fetch_profile, upstream_error

TTL = 300
SCHEMA_VERSION = "zzz-miyoushe-verification-v1"


@dataclass
class _Verification:
    uid: str
    cookies: dict[str, str] = field(repr=False)
    transport: Any = field(repr=False)
    expires: float
    qr_session: str | None = field(default=None, repr=False)
    challenge: str | None = field(default=None, repr=False)
    attempts: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    timer: asyncio.TimerHandle | None = field(default=None, repr=False)


class VerificationSessions:
    def __init__(self, *, clock=time.time, capacity=20):
        self.clock, self.capacity = clock, capacity
        self.sessions: dict[str, _Verification] = {}

    def drop(self, key: str):
        session = self.sessions.pop(key, None)
        if session:
            if session.timer:
                session.timer.cancel()
            session.cookies.clear()
            session.challenge = None
            clear = getattr(session.transport, "clear_credentials", None)
            if clear:
                clear()

    def cancel_for_qr(self, qr_session: str):
        for key, session in list(self.sessions.items()):
            if session.qr_session == qr_session:
                self.drop(key)

    def _cleanup(self):
        for key, session in list(self.sessions.items()):
            if session.expires <= self.clock():
                self.drop(key)

    def register(self, uid, cookies, transport, *, qr_session=None):
        self._cleanup()
        if qr_session:
            self.cancel_for_qr(qr_session)
        if len(self.sessions) >= self.capacity:
            raise MiyousheError("待完成的验证过多，请稍后再试。", 429, "verification-capacity")
        key = secrets.token_urlsafe(32)
        session = _Verification(uid, dict(cookies), transport, self.clock() + TTL, qr_session)
        self.sessions[key] = session
        session.timer = asyncio.get_running_loop().call_later(TTL, self.drop, key)
        return {"verification_id": key, "expires_at": datetime.fromtimestamp(session.expires, timezone.utc).isoformat()}

    def _get(self, key: object):
        self._cleanup()
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", key):
            raise MiyousheError("验证会话无效，请重新获取角色。")
        session = self.sessions.get(key)
        if session is None:
            raise MiyousheError("验证已过期或取消，请重新获取角色。", 410, "verification-expired")
        if session.qr_session:
            from .miyoushe_qr import qr_sessions
            qr_sessions.cookie_header(session.qr_session)
        return session

    def _alive(self, key: str, session: _Verification):
        if self._get(key) is not session:
            raise MiyousheError("验证会话已取消。", 410, "verification-expired")

    async def start(self, key: object):
        session = self._get(key)
        async with session.lock:
            self._alive(key, session)
            try:
                async with asyncio.timeout(15):
                    mmt = await session.transport.create_verification()
                self._alive(key, session)
                # Expose only the public challenge inputs, never account cookies/device headers.
                gt, challenge = mmt.get("gt"), mmt.get("challenge")
                if not isinstance(gt, str) or not 1 <= len(gt) <= 128 or not isinstance(challenge, str) or not 1 <= len(challenge) <= 128 or mmt.get("success") != 1:
                    raise ValueError("invalid verification challenge")
                session.challenge = challenge
                return {"schema_version": SCHEMA_VERSION, "gt": gt, "challenge": challenge,
                        "new_captcha": bool(mmt.get("new_captcha")), "success": 1}
            except MiyousheError:
                raise
            except Exception as exc:
                raise upstream_error(exc, stage="verification-create") from None

    async def complete(self, key: object, raw: object):
        session = self._get(key)
        async with session.lock:
            self._alive(key, session)
            if session.challenge is None:
                raise MiyousheError("请先打开安全验证。")
            if not isinstance(raw, dict):
                raise MiyousheError("验证结果格式无效。")
            proof = {k: raw.get(k) for k in ("geetest_challenge", "geetest_validate", "geetest_seccode")}
            if any(not isinstance(v, str) or not 1 <= len(v) <= 2048 or any(ord(c) < 32 or ord(c) == 127 for c in v) for v in proof.values()):
                raise MiyousheError("验证结果缺失或无效，请重新完成验证。")
            # GeeTest v3 may append a two-character suffix to its original challenge.
            if proof["geetest_challenge"][:32] != session.challenge[:32]:
                raise MiyousheError("验证已刷新，请完成当前验证。")
            if session.attempts >= 3:
                self.drop(key)
                raise MiyousheError("验证重试次数过多，请重新获取角色。", 429, "verification-attempts")
            session.attempts += 1
            stage = "verification-submit"
            try:
                async with asyncio.timeout(15):
                    accepted_challenge = await session.transport.verify(proof)
                self._alive(key, session)
                stage = "verification-records"
                payload = {"uid": session.uid, "cookie": "; ".join(f"{k}={v}" for k, v in session.cookies.items())}
                result = await fetch_profile(payload, transport_factory=lambda _: session.transport, retain_verification=False)
                self._alive(key, session)
                if session.qr_session:
                    from .miyoushe_qr import qr_sessions
                    qr_sessions.remember_record_challenge(session.qr_session, accepted_challenge)
                self.drop(key)
                return result
            except asyncio.CancelledError:
                self.drop(key)
                raise
            except MiyousheError as exc:
                if exc.status in {401, 403, 410}:
                    self.drop(key)
                if exc.status == 428:
                    if stage == "verification-records":
                        raise MiyousheError("安全验证已通过，但角色战绩仍要求验证，请重新获取角色以刷新验证上下文。", 428, "record-verification-required") from None
                    raise MiyousheError("米游社未接受本次验证或验证已失效，请重新开始安全验证。", 428, "record-verification-required") from None
                if stage == "verification-records" and exc.status == 502:
                    raise MiyousheError(f"安全验证已通过，但读取角色失败：{exc}", exc.status, exc.code) from None
                raise
            except Exception as exc:
                raise upstream_error(exc, stage=stage) from None

    def cancel(self, key: object):
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", key):
            raise MiyousheError("验证会话无效。")
        self.drop(key)
        return {"schema_version": SCHEMA_VERSION, "status": "cancelled"}


verification_sessions = VerificationSessions()
