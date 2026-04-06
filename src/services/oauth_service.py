import json
import os
import uuid
from typing import Dict, Optional, Tuple, cast

import httpx
import redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.social_account import SocialAccount
from models.user import User
from services.auth_service import AuthService


class OAuthNotConfiguredError(ValueError):
    pass


class OAuthProviderError(ValueError):
    pass


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _provider_cfg(provider: str) -> Dict[str, str]:
    if provider == "yandex":
        return {
            "client_id": _env("YANDEX_CLIENT_ID"),
            "client_secret": _env("YANDEX_CLIENT_SECRET"),
            "redirect_uri": _env("YANDEX_REDIRECT_URI"),
        }
    if provider == "vk":
        return {
            "client_id": _env("VK_CLIENT_ID"),
            "client_secret": _env("VK_CLIENT_SECRET"),
            "redirect_uri": _env("VK_REDIRECT_URI"),
        }
    if provider == "google":
        return {
            "client_id": _env("GOOGLE_CLIENT_ID"),
            "client_secret": _env("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": _env("GOOGLE_REDIRECT_URI"),
        }
    raise OAuthProviderError("Unknown provider")


def _ensure_configured(cfg: Dict[str, str]) -> None:
    if not cfg.get("client_id") or not cfg.get("client_secret") or not cfg.get("redirect_uri"):
        raise OAuthNotConfiguredError("OAuth provider not configured (env is empty)")


def _redis_conn() -> redis.Redis:
    host = _env("REDIS_HOST", "127.0.0.1")
    port = int(_env("REDIS_PORT", "6380"))
    db = int(_env("REDIS_DB", "0"))
    return redis.Redis(host=host, port=port, db=db)


def _state_prefix() -> str:
    return _env("OAUTH_STATE_PREFIX", "oauth_state")


def _state_ttl() -> int:
    try:
        return int(_env("OAUTH_STATE_TTL_SECONDS", "600"))
    except ValueError:
        return 600


def _state_key(state: str) -> str:
    return f"{_state_prefix()}:{state}"


class OAuthService:
    @staticmethod
    def build_login_redirect(provider: str) -> str:
        cfg = _provider_cfg(provider)
        _ensure_configured(cfg)

        state = uuid.uuid4().hex
        payload = {"provider": provider}
        r = _redis_conn()
        r.setex(_state_key(state), _state_ttl(), json.dumps(payload))

        if provider == "yandex":
            return (
                "https://oauth.yandex.ru/authorize"
                f"?response_type=code&client_id={cfg['client_id']}"
                f"&redirect_uri={cfg['redirect_uri']}"
                f"&state={state}"
            )

        if provider == "vk":
            return (
                "https://oauth.vk.com/authorize"
                f"?client_id={cfg['client_id']}"
                f"&display=page"
                f"&redirect_uri={cfg['redirect_uri']}"
                f"&scope=email"
                f"&response_type=code"
                f"&v=5.131"
                f"&state={state}"
            )

        if provider == "google":
            scope = "openid%20email%20profile"
            return (
                "https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={cfg['client_id']}"
                f"&redirect_uri={cfg['redirect_uri']}"
                f"&response_type=code"
                f"&scope={scope}"
                f"&state={state}"
            )

        raise OAuthProviderError("Unknown provider")

    @staticmethod
    def _consume_state(provider: str, state: str) -> None:
        if not state:
            raise OAuthProviderError("State is required")

        r = _redis_conn()
        raw = r.get(_state_key(state))
        if not raw:
            raise OAuthProviderError("Invalid or expired state")

        r.delete(_state_key(state))
        raw_bytes = cast(bytes, raw)
        payload = json.loads(raw_bytes.decode("utf-8"))
        if payload.get("provider") != provider:
            raise OAuthProviderError("State provider mismatch")

    @staticmethod
    async def _fetch_yandex(code: str) -> Tuple[str, Optional[str]]:
        cfg = _provider_cfg("yandex")
        _ensure_configured(cfg)

        async with httpx.AsyncClient(timeout=10) as client:
            token = await client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token.status_code != 200:
                raise OAuthProviderError("Yandex token exchange failed")
            access_token = token.json().get("access_token")
            if not access_token:
                raise OAuthProviderError("Yandex access_token missing")

            info = await client.get(
                "https://login.yandex.ru/info?format=json",
                headers={"Authorization": f"OAuth {access_token}"},
            )
            if info.status_code != 200:
                raise OAuthProviderError("Yandex userinfo failed")
            data = info.json()
            social_id = str(data.get("id") or "")
            email = data.get("default_email")
            if not social_id:
                raise OAuthProviderError("Yandex user id missing")
            return social_id, email

    @staticmethod
    async def _fetch_vk(code: str) -> Tuple[str, Optional[str]]:
        cfg = _provider_cfg("vk")
        _ensure_configured(cfg)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://oauth.vk.com/access_token",
                params={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "redirect_uri": cfg["redirect_uri"],
                    "code": code,
                },
            )
            if resp.status_code != 200:
                raise OAuthProviderError("VK token exchange failed")
            data = resp.json()
            social_id = str(data.get("user_id") or "")
            email = data.get("email")
            if not social_id:
                raise OAuthProviderError("VK user id missing")
            return social_id, email

    @staticmethod
    async def _fetch_google(code: str) -> Tuple[str, Optional[str]]:
        cfg = _provider_cfg("google")
        _ensure_configured(cfg)

        async with httpx.AsyncClient(timeout=10) as client:
            token = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "code": code,
                    "redirect_uri": cfg["redirect_uri"],
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token.status_code != 200:
                raise OAuthProviderError("Google token exchange failed")
            access_token = token.json().get("access_token")
            if not access_token:
                raise OAuthProviderError("Google access_token missing")

            info = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if info.status_code != 200:
                raise OAuthProviderError("Google userinfo failed")
            data = info.json()
            social_id = str(data.get("sub") or "")
            email = data.get("email")
            if not social_id:
                raise OAuthProviderError("Google user id missing")
            return social_id, email

    @staticmethod
    async def finish(provider: str, code: str, state: str, session: AsyncSession):
        if not code:
            raise OAuthProviderError("Code is required")

        OAuthService._consume_state(provider, state)

        if provider == "yandex":
            social_id, email = await OAuthService._fetch_yandex(code)
        elif provider == "vk":
            social_id, email = await OAuthService._fetch_vk(code)
        elif provider == "google":
            social_id, email = await OAuthService._fetch_google(code)
        else:
            raise OAuthProviderError("Unknown provider")

        social = (
            await session.execute(
                select(SocialAccount).where(
                    SocialAccount.provider == provider,
                    SocialAccount.social_id == social_id,
                )
            )
        ).scalar_one_or_none()

        if social:
            user = (await session.execute(select(User).where(User.id == social.user_id))).scalar_one()
            return await AuthService._issue_tokens(session, user)

        base_login = (email or f"{provider}_{social_id}@oauth.local").lower()
        login = base_login

        exists = (await session.execute(select(User).where(User.login == login))).scalar_one_or_none()
        if exists:
            login = f"{provider}_{social_id}"

        user = User(login=login, password=hash_password(uuid.uuid4().hex), is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        session.add(SocialAccount(user_id=user.id, provider=provider, social_id=social_id))
        await session.commit()

        return await AuthService._issue_tokens(session, user)

    @staticmethod
    async def unlink(provider: str, user: User, session: AsyncSession) -> bool:
        social = (
            await session.execute(
                select(SocialAccount).where(
                    SocialAccount.provider == provider,
                    SocialAccount.user_id == user.id,
                )
            )
        ).scalar_one_or_none()

        if not social:
            return False

        await session.delete(social)
        await session.commit()
        return True
