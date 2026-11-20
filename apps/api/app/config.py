from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://hearback:hearback@localhost:5432/hearback"
    environment: str = "local"
    jwt_secret: str = "local-dev-secret-not-for-production-use"
    jwt_audience: str = "hearback-api"


settings = Settings()
