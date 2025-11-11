"""通知エンティティの ORM モデル定義。"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.race import Race
    from app.models.user import User


class NotificationCategory(StrEnum):
    """通知の分類を表す列挙型。"""

    PREDICTION = "prediction"
    RESULT = "result"
    SYSTEM = "system"


class NotificationDeliveryStatus(StrEnum):
    """通知の配信状態を管理する列挙型。"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class Notification(Base):
    """ユーザーへ配信される通知の本体を表すモデル。"""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    race_id: Mapped[int | None] = mapped_column(
        ForeignKey("races.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, name="notification_category"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    _metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=func.false(),
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[NotificationDeliveryStatus] = mapped_column(
        Enum(NotificationDeliveryStatus, name="notification_status"),
        nullable=False,
        default=NotificationDeliveryStatus.PENDING,
        server_default=NotificationDeliveryStatus.PENDING.value,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    max_retries: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=3,
        server_default="3",
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )
    race: Mapped["Race | None"] = relationship(
        "Race",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return (
            f"Notification(id={self.id!r}, user_id={self.user_id!r}, "
            f"category={self.category!r}, status={self.status!r})"
        )

    @property
    def is_retryable(self) -> bool:
        """通知の再送対象かを判定する。"""
        if self.status == NotificationDeliveryStatus.SENT:
            return False
        return self.retry_count < self.max_retries

    @property
    def metadata(self) -> dict[str, Any] | None:
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict[str, Any] | None) -> None:
        self._metadata = value


__all__ = [
    "Notification",
    "NotificationCategory",
    "NotificationDeliveryStatus",
]


