from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.core.schemas.api.db_config import DatabaseURL


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TESTING: bool = False
    DEBUG: bool = False
    PROJECT_NAME: str = "backend"
    DATA_PATH: str = f"/tmp/{PROJECT_NAME}/"

    DB_NAME: str = "backend"
    DB_USER: Optional[str] = "mysql"
    DB_PASSWORD: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306

    BACKEND_URL: str = "redis://192.168.5.146:6379"

    DB_ECHO_LOG: bool = False
    DB_ECHO_LEVEL: str = "error"
    CRYPT_SCHEMA: str = "bcrypt"

    TOKEN_URL: str = "/token"
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 60 * 240

    # CORS & Session
    SAME_SITE: Optional[str] = None
    ALLOWED_HOSTS: str | List[str] = Field(default_factory=list)  # type: ignore

    SECRET_KEY: Optional[str] = Field(default_factory=str)

    @property
    def DATABASE_CONFIG(self) -> DatabaseURL:  # noqa
        return DatabaseURL(
            driver="mysql+aiomysql",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            url=None,
        )

    @property
    def ALEMBIC_CONFIG(self) -> DatabaseURL:  # noqa
        return DatabaseURL(
            driver="mysql+pymysql",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            url=None,
        )

    @field_validator("ALLOWED_HOSTS", mode="before")
    def CommaSeparatedStrings(cls, v: Optional[str]) -> List[str]:  # noqa
        if not v:
            return []
        return [item.strip() for item in v.split(",")]  # pragma: no cover


settings = Settings()
