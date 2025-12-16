# app/core/config.py
from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ全体で使う設定値。

    - .env の値
    - 環境変数
    を一元管理する。
    """

    env: Literal["local", "dev", "prod"] = "local"

    # SQLite / Postgres など、汎用的に使えるように str にしておく
    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
    )


settings = Settings()
