from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    project_name: str = Field('auth_service', env='PROJECT_NAME')

    user: str = Field(..., env='POSTGRES_USER')
    password: str = Field(..., env='POSTGRES_PASSWORD')
    host: str = Field(..., env='POSTGRES_HOST')
    port: int = Field(..., env='POSTGRES_PORT')
    db: str = Field(..., env='POSTGRES_DB')

    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')
    redis_db: int = Field(0, env='REDIS_DB')

    mongo_host: str = Field('mongodb', env='MONGO_HOST')
    mongo_port: int = Field(27017, env='MONGO_PORT')
    mongo_db: str = Field('ugc', env='MONGO_DB')
    mongo_user: str = Field('', env='MONGO_USER')
    mongo_password: str = Field('', env='MONGO_PASSWORD')

    jwt_secret: str = Field(..., env='JWT_SECRET')
    jwt_algorithm: str = Field('HS256', env='JWT_ALGORITHM')
    access_token_expire_minutes: int = Field(15, env='ACCESS_TOKEN_EXPIRE_MINUTES')
    refresh_token_expire_days: int = Field(30, env='REFRESH_TOKEN_EXPIRE_DAYS')

    oauth_state_ttl_seconds: int = Field(600, env='OAUTH_STATE_TTL_SECONDS')

    yandex_client_id: str = Field('', env='YANDEX_CLIENT_ID')
    yandex_client_secret: str = Field('', env='YANDEX_CLIENT_SECRET')
    yandex_redirect_uri: str = Field('', env='YANDEX_REDIRECT_URI')

    vk_client_id: str = Field('', env='VK_CLIENT_ID')
    vk_client_secret: str = Field('', env='VK_CLIENT_SECRET')
    vk_redirect_uri: str = Field('', env='VK_REDIRECT_URI')

    google_client_id: str = Field('', env='GOOGLE_CLIENT_ID')
    google_client_secret: str = Field('', env='GOOGLE_CLIENT_SECRET')
    google_redirect_uri: str = Field('', env='GOOGLE_REDIRECT_URI')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
