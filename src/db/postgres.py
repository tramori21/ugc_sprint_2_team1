from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from core.config import settings

Base = declarative_base()

dsn = (
    f"postgresql+asyncpg://{settings.user}:{settings.password}"
    f"@{settings.host}:{settings.port}/{settings.db}"
)

engine = create_async_engine(dsn, echo=False, future=True)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

from models import login_history, refresh_token, role, user, user_role  # noqa: F401,E402


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
