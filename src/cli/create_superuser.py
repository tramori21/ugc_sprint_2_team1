import argparse
import asyncio

from sqlalchemy import select

from core.security import hash_password
from db.postgres import async_session
from models.user import User


async def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update superuser")
    parser.add_argument("--login", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.login == args.login))).scalar_one_or_none()
        if user:
            user.password = hash_password(args.password)
            if hasattr(user, "is_active"):
                user.is_active = True
            if hasattr(user, "is_superuser"):
                user.is_superuser = True
            session.add(user)
            await session.commit()
            print("OK: superuser updated:", args.login)
            return 0

        user = User(login=args.login, password=hash_password(args.password))
        if hasattr(user, "is_active"):
            user.is_active = True
        if hasattr(user, "is_superuser"):
            user.is_superuser = True

        session.add(user)
        await session.commit()
        print("OK: superuser created:", args.login)
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
