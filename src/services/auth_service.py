import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.refresh_token import RefreshToken
from models.role import Role
from models.user import User
from models.user_role import UserRole


class AuthService:
    @staticmethod
    async def _issue_tokens(session: AsyncSession, user: User):
        access = create_access_token({"sub": str(user.id)})
        refresh = create_refresh_token({"sub": str(user.id)})

        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        session.add(
            RefreshToken(
                user_id=user.id,
                token=refresh,
                expires_at=expires_at,
                is_revoked=False,
            )
        )
        await session.commit()
        return access, refresh, user
    @staticmethod
    async def register(session: AsyncSession, login: str, password: str):
        res = await session.execute(select(User).where(User.login == login))
        if res.scalar_one_or_none():
            raise ValueError("User already exists")

        user = User(
            login=login,
            password=hash_password(password),
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        default_role = (
            await session.execute(select(Role).where(Role.name == "subscriber"))
        ).scalar_one_or_none()
        if not default_role:
            default_role = Role(name="subscriber")
            session.add(default_role)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                default_role = (
                    await session.execute(select(Role).where(Role.name == "subscriber"))
                ).scalar_one_or_none()
            else:
                await session.refresh(default_role)

        if default_role:
            session.add(UserRole(user_id=user.id, role_id=default_role.id))
            await session.commit()

        return await AuthService._issue_tokens(session, user)

    @staticmethod
    async def login(session: AsyncSession, login: str, password: str):
        res = await session.execute(select(User).where(User.login == login))
        user = res.scalar_one_or_none()
        if not user or not verify_password(password, user.password):
            raise ValueError("Invalid credentials")

        return await AuthService._issue_tokens(session, user)

    @staticmethod
    async def refresh(session: AsyncSession, refresh_token: str):
        if not refresh_token:
            raise ValueError("Invalid refresh token")

        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise ValueError("Invalid refresh token")

        sub = payload.get("sub")
        if not sub:
            raise ValueError("Invalid refresh token")

        try:
            user_id = uuid.UUID(sub)
        except ValueError:
            raise ValueError("Invalid refresh token")

        token_obj = (
            await session.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        ).scalar_one_or_none()
        if (not token_obj) or token_obj.is_revoked or (
                token_obj.expires_at < datetime.utcnow()):
            raise ValueError("Refresh token expired or revoked")

        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user or not user.is_active:
            raise ValueError("User inactive")

        token_obj.is_revoked = True
        await session.commit()

        return await AuthService._issue_tokens(session, user)

    @staticmethod
    async def logout(session: AsyncSession, refresh_token: str):
        if not refresh_token:
            return True

        token_obj = (
            await session.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        ).scalar_one_or_none()
        if token_obj and not token_obj.is_revoked:
            token_obj.is_revoked = True
            await session.commit()

        return True


