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
    jwt_secret_key: str = Field(default="dev-secret-key", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        alias="REFRESH_TOKEN_EXPIRE_MINUTES",
    )
    oauth_state_ttl_minutes: int = Field(
        default=10,
        alias="OAUTH_STATE_TTL_MINUTES",
    )
    cache_backend: str = Field(default="inmemory", alias="CACHE_BACKEND")
    cache_prefix: str = Field(default="keiba-cache", alias="CACHE_PREFIX")
    race_cache_ttl_seconds: int = Field(
        default=60,
        alias="RACE_CACHE_TTL_SECONDS",
        ge=0,
    )
    reference_cache_ttl_seconds: int = Field(
        default=300,
        alias="REFERENCE_CACHE_TTL_SECONDS",
        ge=0,
    )
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(
        default=None,
        alias="GOOGLE_CLIENT_SECRET",
    )
    google_redirect_uri: str | None = Field(
        default=None,
        alias="GOOGLE_REDIRECT_URI",
    )
    google_scope: str = Field(
        default="openid email profile",
        alias="GOOGLE_SCOPE",
    )
    google_authorize_url: str = Field(
        default="https://accounts.google.com/o/oauth2/v2/auth",
        alias="GOOGLE_AUTHORIZE_URL",
    )
    google_token_url: str = Field(
        default="https://oauth2.googleapis.com/token",
        alias="GOOGLE_TOKEN_URL",
    )
    google_userinfo_url: str = Field(
        default="https://openidconnect.googleapis.com/v1/userinfo",
        alias="GOOGLE_USERINFO_URL",
    )
    notification_vapid_public_key: str | None = Field(
        default=None,
        alias="NOTIFICATION_VAPID_PUBLIC_KEY",
    )
    notification_vapid_private_key: str | None = Field(
        default=None,
        alias="NOTIFICATION_VAPID_PRIVATE_KEY",
    )
    notification_vapid_subject: str | None = Field(
        default=None,
        alias="NOTIFICATION_VAPID_SUBJECT",
    )
    notification_default_max_retries: int = Field(
        default=3,
        alias="NOTIFICATION_DEFAULT_MAX_RETRIES",
        ge=0,
    )
    ml_inference_base_url: str = Field(
        default="http://ml-inference:8001",
        alias="ML_INFERENCE_BASE_URL",
    )
    ml_inference_timeout_seconds: float = Field(
        default=60.0,
        alias="ML_INFERENCE_TIMEOUT_SECONDS",
        ge=0,
    )
    ml_inference_max_retries: int = Field(
        default=3,
        alias="ML_INFERENCE_MAX_RETRIES",
        ge=0,
    )
    use_ml_inference: bool = Field(
        default=False,
        alias="USE_ML_INFERENCE",
    )
    # スケジューラ設定
    data_update_cron: str = Field(
        default="0 3 * * *",
        alias="DATA_UPDATE_CRON",
        description="データ更新ジョブのcron表現（デフォルト: 毎日3時）",
    )
    data_update_timezone: str = Field(
        default="Asia/Tokyo",
        alias="DATA_UPDATE_TIMEZONE",
        description="データ更新ジョブのタイムゾーン",
    )
    trigger_model_training: bool = Field(
        default=True,
        alias="TRIGGER_MODEL_TRAINING",
        description="データ更新後にモデル再学習をトリガーするか",
    )
    notify_on_success: bool = Field(
        default=False,
        alias="NOTIFY_ON_SUCCESS",
        description="ジョブ成功時も通知を送信するか",
    )
    notify_on_partial: bool = Field(
        default=True,
        alias="NOTIFY_ON_PARTIAL",
        description="ジョブ部分成功時も通知を送信するか",
    )
    notify_on_failure: bool = Field(
        default=True,
        alias="NOTIFY_ON_FAILURE",
        description="ジョブ失敗時も通知を送信するか",
    )


@lru_cache
def get_settings() -> Settings:
    """環境変数から設定を読み込み、キャッシュした Settings を返す。"""
    return Settings.model_validate(dict(os.environ))


__all__ = ["Settings", "get_settings"]


