"""通知および通知設定に関する CRUD 操作を提供するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationCategory,
    NotificationDeliveryStatus,
)
from app.models.notification_setting import NotificationSetting


@dataclass(slots=True)
class NotificationListParams:
    """通知一覧取得のためのフィルタ条件。"""

    user_id: int
    limit: int = 20
    offset: int = 0
    category: NotificationCategory | None = None
    is_read: bool | None = None


@dataclass(slots=True)
class NotificationListResult:
    """通知一覧取得の結果を表すデータ。"""

    items: list[Notification]
    total: int
    unread_count: int
    params: NotificationListParams


@dataclass(slots=True)
class NotificationCreateInput:
    """通知作成時に利用する入力値。"""

    user_id: int
    category: NotificationCategory
    title: str
    message: str
    race_id: int | None = None
    action_url: str | None = None
    metadata: dict[str, Any] | None = None
    status: NotificationDeliveryStatus = NotificationDeliveryStatus.PENDING
    max_retries: int = 3


def _base_query() -> Select[tuple[Notification]]:
    statement = select(Notification).order_by(Notification.created_at.desc(), Notification.id.desc())
    return statement


def _apply_filters(statement: Select[tuple[Notification]], params: NotificationListParams) -> Select[tuple[Notification]]:
    statement = statement.where(Notification.user_id == params.user_id)
    if params.category is not None:
        statement = statement.where(Notification.category == params.category)
    if params.is_read is not None:
        if params.is_read:
            statement = statement.where(Notification.is_read.is_(True))
        else:
            statement = statement.where(Notification.is_read.is_(False))
    return statement


def create_notification(db: Session, payload: NotificationCreateInput) -> Notification:
    """通知を新規作成して永続化する。"""
    notification = Notification(
        user_id=payload.user_id,
        category=payload.category,
        title=payload.title,
        message=payload.message,
        race_id=payload.race_id,
        action_url=payload.action_url,
        metadata=payload.metadata,
        status=payload.status,
        max_retries=payload.max_retries,
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def list_notifications(db: Session, params: NotificationListParams) -> NotificationListResult:
    """指定した条件で通知一覧を取得する。"""
    statement = _apply_filters(_base_query(), params)
    limited_statement = statement.offset(params.offset).limit(params.limit)
    items = db.scalars(limited_statement).all()

    total_statement = _apply_filters(select(func.count(Notification.id)), params)
    total = int(db.scalar(total_statement) or 0)

    unread_statement = select(func.count(Notification.id)).where(
        Notification.user_id == params.user_id,
        Notification.is_read.is_(False),
    )
    unread_count = int(db.scalar(unread_statement) or 0)

    return NotificationListResult(
        items=items,
        total=total,
        unread_count=unread_count,
        params=params,
    )


def get_notification(db: Session, notification_id: int, *, user_id: int) -> Notification | None:
    """ユーザー権限付きで通知を取得する。"""
    statement = _apply_filters(
        _base_query().where(Notification.id == notification_id),
        NotificationListParams(user_id=user_id),
    )
    return db.scalars(statement).first()


def mark_notification_read(
    db: Session,
    notification_id: int,
    *,
    user_id: int,
    read: bool = True,
) -> Notification:
    """通知の既読状態を更新する。"""
    notification = get_notification(db, notification_id, user_id=user_id)
    if notification is None:
        raise ValueError("notification not found")

    if read and not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
    elif not read and notification.is_read:
        notification.is_read = False
        notification.read_at = None

    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def get_or_create_setting(db: Session, *, user_id: int) -> NotificationSetting:
    """通知設定を取得し、存在しない場合はデフォルト値で作成する。"""
    statement = select(NotificationSetting).where(NotificationSetting.user_id == user_id)
    setting = db.scalars(statement).first()
    if setting is None:
        setting = NotificationSetting(user_id=user_id)
        db.add(setting)
        db.flush()
        db.refresh(setting)
    return setting


def update_setting(
    db: Session,
    *,
    user_id: int,
    **changes: Any,
) -> NotificationSetting:
    """通知設定の特定フィールドを更新して返す。"""
    setting = get_or_create_setting(db, user_id=user_id)
    for field, value in changes.items():
        if hasattr(setting, field):
            setattr(setting, field, value)
    db.add(setting)
    db.flush()
    db.refresh(setting)
    return setting


def list_retryable_notifications(
    db: Session,
    *,
    limit: int = 100,
) -> list[Notification]:
    """再送可能な通知を取得する。"""
    statement = (
        select(Notification)
        .where(
            Notification.status.in_(
                [
                    NotificationDeliveryStatus.PENDING,
                    NotificationDeliveryStatus.FAILED,
                ]
            )
        )
        .where(Notification.retry_count < Notification.max_retries)
        .order_by(Notification.created_at.asc(), Notification.id.asc())
        .limit(limit)
    )
    return db.scalars(statement).all()


def update_delivery_status(
    db: Session,
    notification: Notification,
    *,
    status: NotificationDeliveryStatus,
    sent_at: datetime | None = None,
    last_error: str | None = None,
) -> Notification:
    """通知の配信状態を更新する。"""
    notification.status = status
    notification.last_error = last_error
    if sent_at is not None:
        notification.sent_at = sent_at
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def increment_retry_count(
    db: Session,
    notification: Notification,
    *,
    last_error: str | None = None,
) -> Notification:
    """通知のリトライ回数を加算し、失敗状態を更新する。"""
    notification.retry_count += 1
    notification.last_error = last_error
    if notification.retry_count >= notification.max_retries:
        notification.status = NotificationDeliveryStatus.FAILED
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


__all__ = [
    "NotificationCreateInput",
    "NotificationListParams",
    "NotificationListResult",
    "create_notification",
    "get_notification",
    "get_or_create_setting",
    "increment_retry_count",
    "list_notifications",
    "list_retryable_notifications",
    "mark_notification_read",
    "update_delivery_status",
    "update_setting",
]


