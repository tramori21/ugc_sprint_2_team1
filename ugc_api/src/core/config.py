from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    project_name: str = Field('ugc_api', env='PROJECT_NAME')
    app_port: int = Field(8010, env='APP_PORT')

    jwt_secret: str = Field(..., env='JWT_SECRET')
    jwt_algorithm: str = Field('HS256', env='JWT_ALGORITHM')

    kafka_bootstrap_servers: str = Field('kafka:29092', env='KAFKA_BOOTSTRAP_SERVERS')
    kafka_topic: str = Field('user_actions', env='KAFKA_TOPIC')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
