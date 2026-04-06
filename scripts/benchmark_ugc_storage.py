import argparse
import random
import string
import time
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg import Connection
from pymongo import InsertOne, MongoClient
from pymongo.database import Database


def random_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index}"


def random_text(index: int) -> str:
    return f"review text {index}"


def iter_rows(total_rows: int):
    base_dt = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(total_rows):
        user_id = random_id("user", i % 100000)
        movie_id = random_id("movie", i)
        created_at = base_dt + timedelta(seconds=i)
        updated_at = created_at

        bookmark = {
            "id": random_id("bookmark", i),
            "user_id": user_id,
            "movie_id": movie_id,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        like = {
            "id": random_id("like", i),
            "user_id": user_id,
            "movie_id": movie_id,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        review = {
            "id": random_id("review", i),
            "user_id": user_id,
            "movie_id": movie_id,
            "text": random_text(i),
            "rating": (i % 10) + 1,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        yield {
            "bookmark": bookmark,
            "like": like,
            "review": review,
        }


def measure(func) -> float:
    started = time.perf_counter()
    func()
    return round((time.perf_counter() - started) * 1000, 2)


def prepare_postgres(connection: Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            create table if not exists ugc_bookmarks_bench (
                id text primary key,
                user_id text not null,
                movie_id text not null,
                created_at timestamptz not null,
                updated_at timestamptz not null
            )
            """
        )
        cursor.execute(
            """
            create table if not exists ugc_likes_bench (
                id text primary key,
                user_id text not null,
                movie_id text not null,
                created_at timestamptz not null,
                updated_at timestamptz not null
            )
            """
        )
        cursor.execute(
            """
            create table if not exists ugc_reviews_bench (
                id text primary key,
                user_id text not null,
                movie_id text not null,
                text text not null,
                rating integer not null,
                created_at timestamptz not null,
                updated_at timestamptz not null
            )
            """
        )
        cursor.execute("create index if not exists ix_ugc_bookmarks_bench_user_id on ugc_bookmarks_bench (user_id)")
        cursor.execute("create index if not exists ix_ugc_likes_bench_user_id on ugc_likes_bench (user_id)")
        cursor.execute("create index if not exists ix_ugc_reviews_bench_movie_id on ugc_reviews_bench (movie_id)")
    connection.commit()


def truncate_postgres(connection: Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("truncate table ugc_bookmarks_bench, ugc_likes_bench, ugc_reviews_bench")
    connection.commit()


def insert_postgres(connection: Connection, total_rows: int, chunk_size: int) -> tuple[str, str]:
    bookmarks_batch = []
    likes_batch = []
    reviews_batch = []
    sample_user = ""
    sample_movie = ""
    inserted = 0

    with connection.cursor() as cursor:
        for row in iter_rows(total_rows):
            bookmark = row["bookmark"]
            like = row["like"]
            review = row["review"]

            if not sample_user:
                sample_user = bookmark["user_id"]
                sample_movie = review["movie_id"]

            bookmarks_batch.append(
                (bookmark["id"], bookmark["user_id"], bookmark["movie_id"], bookmark["created_at"], bookmark["updated_at"])
            )
            likes_batch.append(
                (like["id"], like["user_id"], like["movie_id"], like["created_at"], like["updated_at"])
            )
            reviews_batch.append(
                (
                    review["id"],
                    review["user_id"],
                    review["movie_id"],
                    review["text"],
                    review["rating"],
                    review["created_at"],
                    review["updated_at"],
                )
            )

            if len(bookmarks_batch) >= chunk_size:
                cursor.executemany(
                    """
                    insert into ugc_bookmarks_bench (id, user_id, movie_id, created_at, updated_at)
                    values (%s, %s, %s, %s, %s)
                    on conflict (id) do nothing
                    """,
                    bookmarks_batch,
                )
                cursor.executemany(
                    """
                    insert into ugc_likes_bench (id, user_id, movie_id, created_at, updated_at)
                    values (%s, %s, %s, %s, %s)
                    on conflict (id) do nothing
                    """,
                    likes_batch,
                )
                cursor.executemany(
                    """
                    insert into ugc_reviews_bench (id, user_id, movie_id, text, rating, created_at, updated_at)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    on conflict (id) do nothing
                    """,
                    reviews_batch,
                )
                inserted += len(bookmarks_batch)
                connection.commit()
                if inserted % 100000 == 0 or inserted == total_rows:
                    print(f"POSTGRES_PROGRESS={inserted}/{total_rows}", flush=True)
                bookmarks_batch.clear()
                likes_batch.clear()
                reviews_batch.clear()

        if bookmarks_batch:
            cursor.executemany(
                """
                insert into ugc_bookmarks_bench (id, user_id, movie_id, created_at, updated_at)
                values (%s, %s, %s, %s, %s)
                on conflict (id) do nothing
                """,
                bookmarks_batch,
            )
            cursor.executemany(
                """
                insert into ugc_likes_bench (id, user_id, movie_id, created_at, updated_at)
                values (%s, %s, %s, %s, %s)
                on conflict (id) do nothing
                """,
                likes_batch,
            )
            cursor.executemany(
                """
                insert into ugc_reviews_bench (id, user_id, movie_id, text, rating, created_at, updated_at)
                values (%s, %s, %s, %s, %s, %s, %s)
                on conflict (id) do nothing
                """,
                reviews_batch,
            )
            inserted += len(bookmarks_batch)
            connection.commit()
            print(f"POSTGRES_PROGRESS={inserted}/{total_rows}", flush=True)

    return sample_user, sample_movie


def prepare_mongo(database: Database) -> None:
    database.bookmarks_bench.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
    database.likes_bench.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
    database.reviews_bench.create_index([("movie_id", 1), ("created_at", 1)])


def truncate_mongo(database: Database) -> None:
    database.bookmarks_bench.delete_many({})
    database.likes_bench.delete_many({})
    database.reviews_bench.delete_many({})


def insert_mongo(database: Database, total_rows: int, chunk_size: int) -> tuple[str, str]:
    bookmarks_batch = []
    likes_batch = []
    reviews_batch = []
    sample_user = ""
    sample_movie = ""
    inserted = 0

    for row in iter_rows(total_rows):
        if not sample_user:
            sample_user = row["bookmark"]["user_id"]
            sample_movie = row["review"]["movie_id"]

        bookmarks_batch.append(InsertOne(row["bookmark"]))
        likes_batch.append(InsertOne(row["like"]))
        reviews_batch.append(InsertOne(row["review"]))

        if len(bookmarks_batch) >= chunk_size:
            database.bookmarks_bench.bulk_write(bookmarks_batch, ordered=False)
            database.likes_bench.bulk_write(likes_batch, ordered=False)
            database.reviews_bench.bulk_write(reviews_batch, ordered=False)
            inserted += len(bookmarks_batch)
            if inserted % 100000 == 0 or inserted == total_rows:
                print(f"MONGO_PROGRESS={inserted}/{total_rows}", flush=True)
            bookmarks_batch.clear()
            likes_batch.clear()
            reviews_batch.clear()

    if bookmarks_batch:
        database.bookmarks_bench.bulk_write(bookmarks_batch, ordered=False)
        database.likes_bench.bulk_write(likes_batch, ordered=False)
        database.reviews_bench.bulk_write(reviews_batch, ordered=False)
        inserted += len(bookmarks_batch)
        print(f"MONGO_PROGRESS={inserted}/{total_rows}", flush=True)

    return sample_user, sample_movie


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10000000)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--pg-dsn", type=str, default="postgresql://app:123qwe@127.0.0.1:5433/auth")
    parser.add_argument("--mongo-dsn", type=str, default="mongodb://127.0.0.1:27017/")
    args = parser.parse_args()

    pg = psycopg.connect(args.pg_dsn)
    mongo = MongoClient(args.mongo_dsn)
    mongo_db = mongo["ugc"]

    prepare_postgres(pg)
    prepare_mongo(mongo_db)

    truncate_postgres(pg)
    truncate_mongo(mongo_db)

    pg_started = time.perf_counter()
    pg_user, pg_movie = insert_postgres(pg, args.rows, args.chunk_size)
    pg_insert_ms = round((time.perf_counter() - pg_started) * 1000, 2)

    mongo_started = time.perf_counter()
    mongo_user, mongo_movie = insert_mongo(mongo_db, args.rows, args.chunk_size)
    mongo_insert_ms = round((time.perf_counter() - mongo_started) * 1000, 2)

    pg_bookmarks_ms = measure(
        lambda: pg.execute("select movie_id from ugc_bookmarks_bench where user_id = %s", (pg_user,)).fetchall()
    )
    mongo_bookmarks_ms = measure(
        lambda: list(mongo_db.bookmarks_bench.find({"user_id": mongo_user}))
    )

    pg_avg_rating_ms = measure(
        lambda: pg.execute("select avg(rating) from ugc_reviews_bench where movie_id = %s", (pg_movie,)).fetchall()
    )
    mongo_avg_rating_ms = measure(
        lambda: list(
            mongo_db.reviews_bench.aggregate(
                [
                    {"$match": {"movie_id": mongo_movie}},
                    {"$group": {"_id": "$movie_id", "avg_rating": {"$avg": "$rating"}}},
                ]
            )
        )
    )

    print(f"POSTGRES_INSERT_MS={pg_insert_ms}")
    print(f"MONGO_INSERT_MS={mongo_insert_ms}")
    print(f"POSTGRES_USER_BOOKMARKS_MS={pg_bookmarks_ms}")
    print(f"MONGO_USER_BOOKMARKS_MS={mongo_bookmarks_ms}")
    print(f"POSTGRES_MOVIE_AVG_RATING_MS={pg_avg_rating_ms}")
    print(f"MONGO_MOVIE_AVG_RATING_MS={mongo_avg_rating_ms}")


if __name__ == "__main__":
    main()

