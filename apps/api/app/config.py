import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DataInsight AI API"
    debug: bool = False

    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/datainsight"
    redis_url: str = "redis://redis:6379/0"
    storage_bucket: str = "datasets"

    cors_origins: str = "http://localhost:3000"

    def get_cors_origins(self) -> list[str]:
        v = self.cors_origins.strip()
        if not v:
            return ["http://localhost:3000"]
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    @field_validator("database_url", mode="before")
    @classmethod
    def normalise_db_url(cls, v: object) -> object:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        return v


settings = Settings()
