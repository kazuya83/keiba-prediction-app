"""通知機能に関する Pydantic スキーマ定義。"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.notification import NotificationCategory, NotificationDeliveryStatus


class NotificationRead(BaseModel):
    """通知一覧/詳細で返却するスキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category: NotificationCategory
    title: str
    message: str
    race_id: int | None = None
    action_url: str | None = None
    metadata: dict[str, Any] | None = None
    is_read: bool
    read_at: datetime | None = None
    sent_at: datetime | None = None
    status: NotificationDeliveryStatus
    retry_count: int
    max_retries: int
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """通知一覧 API のレスポンス。"""

    items: list[NotificationRead]
    total: int
    limit: int
    offset: int
    unread_count: int


class NotificationReadRequest(BaseModel):
    """通知の既読状態を更新するためのリクエスト。"""

    read: bool = Field(default=True, description="既読にする場合は True、未読に戻す場合は False。")


class NotificationSettingRead(BaseModel):
    """通知設定のレスポンススキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    enable_app: bool
    enable_push: bool
    allow_prediction: bool
    allow_race_result: bool
    allow_system: bool
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
    push_endpoint: str | None = None
    push_p256dh: str | None = None
    push_auth: str | None = None
    vapid_public_key: str | None = None


class NotificationSettingUpdate(BaseModel):
    """通知設定更新リクエスト。"""

    enable_app: bool | None = Field(default=None, description="アプリ内通知の有効/無効を設定する。")
    enable_push: bool | None = Field(default=None, description="ブラウザ Push 通知の有効/無効を設定する。")
    allow_prediction: bool | None = Field(default=None, description="予測完了通知の受信設定。")
    allow_race_result: bool | None = Field(default=None, description="レース結果通知の受信設定。")
    allow_system: bool | None = Field(default=None, description="システム通知の受信設定。")
    quiet_hours_start: time | None = Field(
        default=None,
        description="通知を抑制するサイレントタイムの開始時刻 (HH:MM)。",
    )
    quiet_hours_end: time | None = Field(
        default=None,
        description="通知を抑制するサイレントタイムの終了時刻 (HH:MM)。",
    )
    push_endpoint: str | None = Field(
        default=None,
        description="ブラウザ Push 購読情報のエンドポイント URL。",
    )
    push_p256dh: str | None = Field(
        default=None,
        description="Web Push の p256dh キー。",
    )
    push_auth: str | None = Field(
        default=None,
        description="Web Push の auth シークレット。",
    )

    @field_validator("push_endpoint")
    @classmethod
    def _strip_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_quiet_hours(self) -> "NotificationSettingUpdate":
        """静かな時間帯の整合性を検証する。"""
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        if start is not None and end is not None and start >= end:
            raise ValueError("quiet_hours_end は quiet_hours_start より後の時刻を指定してください。")
        return self


__all__ = [
    "NotificationListResponse",
    "NotificationRead",
    "NotificationReadRequest",
    "NotificationSettingRead",
    "NotificationSettingUpdate",
]


