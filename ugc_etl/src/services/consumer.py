import asyncio
import json
from datetime import datetime
from json import JSONDecodeError

from aiokafka import AIOKafkaConsumer
from db.clickhouse import get_client, init_db

from core.config import settings


def _to_dt(value: str) -> datetime:
    normalized = value.replace('Z', '+00:00')
    return datetime.fromisoformat(normalized).replace(tzinfo=None)


def _deserialize(value: bytes) -> dict | None:
    try:
        return json.loads(value.decode('utf-8'))
    except (UnicodeDecodeError, JSONDecodeError):
        return None


def _build_row(data: dict) -> tuple:
    return (
        str(data.get('event_id', '')),
        str(data.get('user_id', '')),
        str(data.get('movie_id', '')),
        str(data.get('event_type', '')),
        data.get('progress_seconds'),
        _to_dt(data['event_time']),
        str(data.get('request_id', '')),
        _to_dt(data['created_at']),
    )


async def wait_clickhouse() -> None:
    last_error = None

    for _ in range(30):
        try:
            init_db()
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(2)

    raise RuntimeError(f'ClickHouse connection failed: {last_error}')


async def wait_topic(consumer: AIOKafkaConsumer) -> None:
    for _ in range(30):
        partitions = consumer.partitions_for_topic(settings.kafka_topic)
        if partitions:
            return
        await asyncio.sleep(2)

    raise RuntimeError(f'Kafka topic not available: {settings.kafka_topic}')


async def consume() -> None:
    await wait_clickhouse()
    client = get_client()

    consumer = None
    last_error = None

    for _ in range(30):
        try:
            consumer = AIOKafkaConsumer(
                settings.kafka_topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                value_deserializer=_deserialize,
            )
            await consumer.start()
            await wait_topic(consumer)
            break
        except Exception as exc:
            last_error = exc
            if consumer is not None:
                try:
                    await consumer.stop()
                except Exception:
                    pass
            consumer = None
            await asyncio.sleep(2)

    if consumer is None:
        raise RuntimeError(f'Kafka consumer connection failed: {last_error}')

    try:
        while True:
            batch = await consumer.getmany(
                timeout_ms=settings.kafka_batch_timeout_ms,
                max_records=settings.kafka_batch_size,
            )

            rows = []

            for _, messages in batch.items():
                for message in messages:
                    data = message.value

                    if not data:
                        continue

                    if data.get('event_type') != 'view':
                        continue

                    rows.append(_build_row(data))

            if rows:
                client.execute(
                    f'''
                    INSERT INTO {settings.clickhouse_table}
                    (event_id, user_id, movie_id, event_type, progress_seconds, event_time, request_id, created_at)
                    VALUES
                    ''',
                    rows,
                )

            await consumer.commit()
    finally:
        await consumer.stop()
