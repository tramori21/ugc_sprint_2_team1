from datetime import datetime
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, ReturnDocument


class UGCService:
    @staticmethod
    async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
        await db.bookmarks.create_index(
            [('user_id', ASCENDING), ('movie_id', ASCENDING)],
            unique=True,
            name='bookmarks_user_movie_uq',
        )
        await db.likes.create_index(
            [('user_id', ASCENDING), ('movie_id', ASCENDING)],
            unique=True,
            name='likes_user_movie_uq',
        )
        await db.reviews.create_index(
            [('user_id', ASCENDING), ('movie_id', ASCENDING), ('created_at', ASCENDING)],
            name='reviews_user_movie_created_idx',
        )
        await db.reviews.create_index(
            [('movie_id', ASCENDING), ('created_at', ASCENDING)],
            name='reviews_movie_created_idx',
        )

    @staticmethod
    async def upsert_bookmark(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> dict:
        now = datetime.utcnow()
        document = await db.bookmarks.find_one_and_update(
            {'user_id': user_id, 'movie_id': movie_id},
            {
                '$set': {
                    'updated_at': now,
                },
                '$setOnInsert': {
                    'id': str(uuid4()),
                    'user_id': user_id,
                    'movie_id': movie_id,
                    'created_at': now,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        document.pop('_id', None)
        return document

    @staticmethod
    async def list_bookmarks(db: AsyncIOMotorDatabase, user_id: str) -> list[dict]:
        items = []
        async for document in db.bookmarks.find({'user_id': user_id}).sort('created_at', ASCENDING):
            document.pop('_id', None)
            items.append(document)
        return items

    @staticmethod
    async def get_bookmark(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> dict | None:
        document = await db.bookmarks.find_one({'user_id': user_id, 'movie_id': movie_id})
        if document:
            document.pop('_id', None)
        return document

    @staticmethod
    async def delete_bookmark(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> bool:
        result = await db.bookmarks.delete_one({'user_id': user_id, 'movie_id': movie_id})
        return result.deleted_count > 0

    @staticmethod
    async def upsert_like(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> dict:
        now = datetime.utcnow()
        document = await db.likes.find_one_and_update(
            {'user_id': user_id, 'movie_id': movie_id},
            {
                '$set': {
                    'updated_at': now,
                },
                '$setOnInsert': {
                    'id': str(uuid4()),
                    'user_id': user_id,
                    'movie_id': movie_id,
                    'created_at': now,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        document.pop('_id', None)
        return document

    @staticmethod
    async def list_likes(db: AsyncIOMotorDatabase, user_id: str) -> list[dict]:
        items = []
        async for document in db.likes.find({'user_id': user_id}).sort('created_at', ASCENDING):
            document.pop('_id', None)
            items.append(document)
        return items

    @staticmethod
    async def get_like(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> dict | None:
        document = await db.likes.find_one({'user_id': user_id, 'movie_id': movie_id})
        if document:
            document.pop('_id', None)
        return document

    @staticmethod
    async def delete_like(db: AsyncIOMotorDatabase, user_id: str, movie_id: str) -> bool:
        result = await db.likes.delete_one({'user_id': user_id, 'movie_id': movie_id})
        return result.deleted_count > 0

    @staticmethod
    async def create_review(
        db: AsyncIOMotorDatabase,
        user_id: str,
        movie_id: str,
        text: str,
        rating: int,
    ) -> dict:
        now = datetime.utcnow()
        document = {
            'id': str(uuid4()),
            'user_id': user_id,
            'movie_id': movie_id,
            'text': text,
            'rating': rating,
            'created_at': now,
            'updated_at': now,
        }
        await db.reviews.insert_one(document)
        return document

    @staticmethod
    async def list_reviews(
        db: AsyncIOMotorDatabase,
        user_id: str,
        movie_id: str | None = None,
    ) -> list[dict]:
        query = {'user_id': user_id}
        if movie_id:
            query['movie_id'] = movie_id

        items = []
        async for document in db.reviews.find(query).sort('created_at', ASCENDING):
            document.pop('_id', None)
            items.append(document)
        return items

    @staticmethod
    async def get_review(db: AsyncIOMotorDatabase, user_id: str, review_id: str) -> dict | None:
        document = await db.reviews.find_one({'user_id': user_id, 'id': review_id})
        if document:
            document.pop('_id', None)
        return document

    @staticmethod
    async def update_review(
        db: AsyncIOMotorDatabase,
        user_id: str,
        review_id: str,
        text: str,
        rating: int,
    ) -> dict | None:
        document = await db.reviews.find_one_and_update(
            {'user_id': user_id, 'id': review_id},
            {
                '$set': {
                    'text': text,
                    'rating': rating,
                    'updated_at': datetime.utcnow(),
                },
            },
            return_document=ReturnDocument.AFTER,
        )
        if document:
            document.pop('_id', None)
        return document

    @staticmethod
    async def delete_review(db: AsyncIOMotorDatabase, user_id: str, review_id: str) -> bool:
        result = await db.reviews.delete_one({'user_id': user_id, 'id': review_id})
        return result.deleted_count > 0
