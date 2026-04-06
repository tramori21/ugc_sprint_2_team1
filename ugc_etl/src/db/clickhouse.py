from clickhouse_driver import Client

from core.config import settings


def get_client() -> Client:
    return Client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_db,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )


def init_db() -> None:
    admin_client = Client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )

    admin_client.execute(f'CREATE DATABASE IF NOT EXISTS {settings.clickhouse_db}')

    db_client = get_client()
    db_client.execute(
        f'''
        CREATE TABLE IF NOT EXISTS {settings.clickhouse_table} (
            event_id String,
            user_id String,
            movie_id String,
            event_type String,
            progress_seconds Nullable(UInt32),
            event_time DateTime,
            request_id String,
            created_at DateTime
        )
        ENGINE = MergeTree
        ORDER BY (movie_id, user_id, event_time)
        '''
    )
