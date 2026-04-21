"""全局配置模块。

这里统一管理环境变量和少量静态配置，避免业务层直接读取 os.environ。
"""

from __future__ import annotations

import functools
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置对象。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="suitme-python", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=9000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    timezone: str = Field(default="Asia/Shanghai", alias="TIMEZONE")

    database_url: str = Field(
        default="mysql+pymysql://root:password@127.0.0.1:3306/suitme?charset=utf8mb4",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="please-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, alias="JWT_EXPIRE_MINUTES")
    jwt_auth_enabled: bool = Field(default=False, alias="JWT_AUTH_ENABLED")

    suitme_ai_base_url: str = Field(default="http://127.0.0.1:9001", alias="SUITME_AI_BASE_URL")
    suitme_ai_auth_token: str | None = Field(default=None, alias="SUITME_AI_AUTH_TOKEN")

    suitme_upload_profile: str = Field(default="./uploads", alias="SUITME_UPLOAD_PROFILE")
    upload_base_uri: str = Field(default="/profile", alias="UPLOAD_BASE_URI")

    oss_endpoint: str | None = Field(default=None, alias="OSS_ENDPOINT")
    oss_bucket_name: str | None = Field(default=None, alias="OSS_BUCKET_NAME")
    oss_access_key_id: str | None = Field(default=None, alias="OSS_ACCESS_KEY_ID")
    oss_access_key_secret: str | None = Field(default=None, alias="OSS_ACCESS_KEY_SECRET")
    oss_public_url: str | None = Field(default=None, alias="OSS_PUBLIC_URL")

    @property
    def upload_profile_path(self) -> Path:
        """返回本地上传目录绝对路径。"""
        return Path(self.suitme_upload_profile).resolve()


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回缓存后的全局配置实例。"""
    return Settings()
