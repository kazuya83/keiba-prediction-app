"""アプリケーション設定を管理するモジュール。"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()


class Settings(BaseModel):
    """環境変数から読み込まれるアプリケーション設定を表す。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    environment: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Keiba Prediction API", alias="APP_NAME")
    app_description: str = Field(
        default="競馬予測アプリケーションのバックエンド API",
        alias="APP_DESCRIPTION",
    )
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    debug: bool = Field(default=False, alias="DEBUG")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    """環境変数から設定を読み込み、キャッシュした Settings を返す。"""
    return Settings.model_validate(dict(os.environ))


__all__ = ["Settings", "get_settings"]


