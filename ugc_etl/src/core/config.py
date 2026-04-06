from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = Field('kafka:29092', env='KAFKA_BOOTSTRAP_SERVERS')
    kafka_topic: str = Field('user_actions', env='KAFKA_TOPIC')
    kafka_group_id: str = Field('ugc_etl_group', env='KAFKA_GROUP_ID')
    kafka_batch_size: int = Field(1000, env='KAFKA_BATCH_SIZE')
    kafka_batch_timeout_ms: int = Field(5000, env='KAFKA_BATCH_TIMEOUT_MS')

    clickhouse_host: str = Field('clickhouse', env='CLICKHOUSE_HOST')
    clickhouse_port: int = Field(9000, env='CLICKHOUSE_PORT')
    clickhouse_db: str = Field('ugc', env='CLICKHOUSE_DB')
    clickhouse_user: str = Field('app', env='CLICKHOUSE_USER')
    clickhouse_password: str = Field('app_pass', env='CLICKHOUSE_PASSWORD')
    clickhouse_table: str = Field('views', env='CLICKHOUSE_TABLE')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
