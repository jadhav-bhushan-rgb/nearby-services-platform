from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: str = "development"
    DEBUG: bool = False
    APP_NAME: str = "Nearby Services Platform"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = Field(min_length=16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000"
    TRUST_PROXY_HEADERS: bool = False

    ADMIN_EMAIL: str = "admin@nearby.local"
    ADMIN_PASSWORD: str = "ChangeMe123!"
    ADMIN_NAME: str = "Platform Admin"
    SEED_SAMPLE_DATA: bool = True

    RATE_LIMIT_PUBLIC_PER_MIN: int = 60
    RATE_LIMIT_SEARCH_PER_MIN: int = 30
    RATE_LIMIT_LOGIN_PER_MIN: int = 5

    CACHE_TTL_LIST_SECONDS: int = 60
    CACHE_TTL_NEARBY_SECONDS: int = 45
    CACHE_TTL_DETAIL_SECONDS: int = 120
    CACHE_TTL_MAP_SECONDS: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def production_guards(self) -> "Settings":
        if self.ENV == "production":
            if self.SECRET_KEY.startswith("dev-"):
                raise ValueError("Set a unique SECRET_KEY before running in production")
            if self.ADMIN_PASSWORD == "ChangeMe123!":
                raise ValueError("Change ADMIN_PASSWORD before running in production")
        return self


settings = Settings()
