"""通知設定を保持する ORM モデル定義。"""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationSetting(Base):
    """ユーザーごとの通知設定を表すモデル。"""

    __tablename__ = "notification_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_settings_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enable_app: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=func.true(),
    )
    enable_push: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=func.false(),
    )
    allow_prediction: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=func.true(),
    )
    allow_race_result: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=func.true(),
    )
    allow_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=func.true(),
    )
    quiet_hours_start: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    push_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    push_p256dh: Mapped[str | None] = mapped_column(String(255), nullable=True)
    push_auth: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
        back_populates="notification_setting",
    )

    def __repr__(self) -> str:
        return f"NotificationSetting(id={self.id!r}, user_id={self.user_id!r})"

    @property
    def has_push_subscription(self) -> bool:
        """Push 通知の購読情報が揃っているかを返す。"""
        return (
            self.enable_push
            and self.push_endpoint is not None
            and self.push_p256dh is not None
            and self.push_auth is not None
        )


__all__ = ["NotificationSetting"]


