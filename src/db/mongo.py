from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings


def _build_dsn() -> str:
    if settings.mongo_user and settings.mongo_password:
        return (
            f'mongodb://{settings.mongo_user}:{settings.mongo_password}'
            f'@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}'
            '?authSource=admin'
        )

    return f'mongodb://{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}'


@lru_cache()
def get_mongo_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(_build_dsn())


def get_database() -> AsyncIOMotorDatabase:
    return get_mongo_client()[settings.mongo_db]


def close_mongo() -> None:
    try:
        get_mongo_client().close()
    finally:
        get_mongo_client.cache_clear()
