import asyncio
import json

from aiokafka import AIOKafkaProducer

from core.config import settings


class KafkaProducer:
    producer: AIOKafkaProducer | None = None

    @classmethod
    async def connect(cls) -> None:
        if cls.producer is not None:
            return

        last_error = None

        for _ in range(30):
            producer = None
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=lambda value: json.dumps(value).encode('utf-8'),
                )
                await producer.start()
                cls.producer = producer
                return
            except Exception as exc:
                last_error = exc
                if producer is not None:
                    try:
                        await producer.stop()
                    except Exception:
                        pass
                await asyncio.sleep(2)

        raise RuntimeError(f'Kafka producer connection failed: {last_error}')

    @classmethod
    async def disconnect(cls) -> None:
        if cls.producer is not None:
            await cls.producer.stop()
            cls.producer = None

    @classmethod
    async def send(cls, message: dict) -> None:
        if cls.producer is None:
            raise RuntimeError('Kafka producer is not connected')

        await cls.producer.send_and_wait(settings.kafka_topic, message)
