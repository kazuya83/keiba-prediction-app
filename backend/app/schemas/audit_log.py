"""監査ログ関連の Pydantic スキーマを定義する。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """監査ログの出力用スキーマ。"""

    id: int
    action: str
    actor_id: int | None
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """監査ログ一覧レスポンス。"""

    items: list[AuditLogRead]
    total: int
    limit: int
    offset: int


__all__ = ["AuditLogListResponse", "AuditLogRead"]


