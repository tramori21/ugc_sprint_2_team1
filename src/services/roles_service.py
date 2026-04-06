import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.role import Role
from models.user import User
from models.user_role import UserRole


class RolesService:
    @staticmethod
    async def create_role(session: AsyncSession, name: str) -> Role:
        exists = (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
        if exists:
            raise ValueError("Role already exists")

        role = Role(name=name)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role

    @staticmethod
    async def list_roles(session: AsyncSession):
        res = await session.execute(select(Role))
        return res.scalars().all()

    @staticmethod
    async def update_role(
            session: AsyncSession,
            role_id: str,
            name: str) -> Role:
        try:
            rid = uuid.UUID(role_id)
        except ValueError:
            raise ValueError("Role not found")

        role = (await session.execute(select(Role).where(Role.id == rid))).scalar_one_or_none()
        if not role:
            raise ValueError("Role not found")

        exists = (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
        if exists and str(exists.id) != str(role.id):
            raise ValueError("Role already exists")

        role.name = name
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role

    @staticmethod
    async def delete_role(session: AsyncSession, role_id: str):
        try:
            rid = uuid.UUID(role_id)
        except ValueError:
            raise ValueError("Role not found")

        role = (await session.execute(select(Role).where(Role.id == rid))).scalar_one_or_none()
        if not role:
            raise ValueError("Role not found")

        await session.delete(role)
        await session.commit()
        return True

    @staticmethod
    async def assign(session: AsyncSession, user_id: str, role_name: str):
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise ValueError("User not found")

        user = (await session.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
        if not role:
            raise ValueError("Role not found")

        link = (
            await session.execute(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
            )
        ).scalar_one_or_none()
        if link:
            return True

        session.add(UserRole(user_id=user.id, role_id=role.id))
        await session.commit()
        return True

    @staticmethod
    async def revoke(session: AsyncSession, user_id: str, role_name: str):
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise ValueError("User not found")

        role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
        if not role:
            raise ValueError("Role not found")

        link = (
            await session.execute(
                select(UserRole).where(UserRole.user_id == uid, UserRole.role_id == role.id)
            )
        ).scalar_one_or_none()
        if link:
            await session.delete(link)
            await session.commit()

        return True

    @staticmethod
    async def check(
            session: AsyncSession,
            user_id: str,
            role_name: str) -> bool:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return False

        role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
        if not role:
            return False

        link = (
            await session.execute(
                select(UserRole).where(UserRole.user_id == uid, UserRole.role_id == role.id)
            )
        ).scalar_one_or_none()
        return link is not None
