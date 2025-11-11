"""管理APIで利用する Pydantic スキーマ定義。"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminUserSummary(BaseModel):
    """管理画面で表示するユーザー情報。"""

    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """ユーザー一覧レスポンス。"""

    items: list[AdminUserSummary]
    total: int
    limit: int
    offset: int


class AdminUserUpdateRequest(BaseModel):
    """ユーザー管理の更新リクエスト。"""

    is_active: bool | None = None
    is_superuser: bool | None = None
    reason: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class AdminUserUpdateResponse(AdminUserSummary):
    """ユーザー更新後のレスポンス。"""

    pass


class LogLevel(StrEnum):
    """取得対象のログレベル。"""

    ERROR = "error"
    WARNING = "warning"
    CRITICAL = "critical"


class AdminErrorLogEntry(BaseModel):
    """管理者向けのエラーログ表示用スキーマ。"""

    id: int
    level: str
    message: str
    logger_name: str
    pathname: str
    lineno: int
    timestamp: datetime
    context: dict[str, Any]
    exception: str | None


class AdminErrorLogListResponse(BaseModel):
    """エラーログ一覧レスポンス。"""

    items: list[AdminErrorLogEntry]
    limit: int
    total: int


class ModelTrainingStatus(StrEnum):
    """モデル再学習ジョブの状態。"""

    QUEUED = "queued"


class ModelTrainingRequest(BaseModel):
    """モデル再学習APIの入力。"""

    model_id: str | None = Field(default=None, max_length=128)
    parameters: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class ModelTrainingResponse(BaseModel):
    """モデル再学習APIのレスポンス。"""

    job_id: str
    status: ModelTrainingStatus
    queued_at: datetime


__all__ = [
    "AdminErrorLogEntry",
    "AdminErrorLogListResponse",
    "AdminUserListResponse",
    "AdminUserSummary",
    "AdminUserUpdateRequest",
    "AdminUserUpdateResponse",
    "LogLevel",
    "ModelTrainingRequest",
    "ModelTrainingResponse",
    "ModelTrainingStatus",
]


