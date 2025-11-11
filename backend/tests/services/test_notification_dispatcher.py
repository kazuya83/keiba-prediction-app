from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.crud import notification as notification_crud
from app.models.notification import NotificationCategory, NotificationDeliveryStatus
from app.models.user import User
from app.services.notification_dispatcher import (
    NotificationDispatcher,
    NotificationEvent,
    NotificationSuppressedError,
    PushDeliveryError,
    PushNotificationSender,
    PushSubscription,
)


class StubPushSender(PushNotificationSender):
    """テスト用の Push 送信スタブ。"""

    def __init__(self) -> None:
        self.sent_payloads: list[dict[str, Any]] = []
        self.raise_error: bool = False

    def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> None:
        if self.raise_error:
            raise PushDeliveryError("stub error")
        self.sent_payloads.append({"subscription": subscription, "payload": payload})


def _create_user(db_session: Session, email: str = "dispatcher@example.com") -> User:
    user = User(
        email=email,
        hashed_password="hashed-password",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _now() -> datetime:
    return datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)


def test_dispatch_event_creates_notification_when_enabled(db_session: Session) -> None:
    user = _create_user(db_session)
    dispatcher = NotificationDispatcher(db_session, now_provider=_now)

    event = NotificationEvent(
        user_id=user.id,
        category=NotificationCategory.SYSTEM,
        title="システムアップデート",
        message="新しいバージョンがリリースされました。",
    )

    notification = dispatcher.dispatch_event(event)
    assert notification is not None
    assert notification.title == event.title
    assert notification.category == NotificationCategory.SYSTEM
    assert notification.status == NotificationDeliveryStatus.PENDING


def test_dispatch_event_respects_category_preferences(db_session: Session) -> None:
    user = _create_user(db_session, email="suppress@example.com")
    notification_crud.update_setting(
        db_session,
        user_id=user.id,
        allow_prediction=False,
    )
    dispatcher = NotificationDispatcher(db_session, now_provider=_now)

    event = NotificationEvent(
        user_id=user.id,
        category=NotificationCategory.PREDICTION,
        title="予測完了",
        message="通知は抑制されるはずです。",
    )

    with pytest.raises(NotificationSuppressedError):
        dispatcher.dispatch_event(event)


def test_dispatch_event_sends_push_when_subscription_available(db_session: Session) -> None:
    user = _create_user(db_session, email="push@example.com")
    notification_crud.update_setting(
        db_session,
        user_id=user.id,
        enable_push=True,
        push_endpoint="https://example.com/push",
        push_p256dh="p256dh-key",
        push_auth="auth-secret",
    )
    push_sender = StubPushSender()
    dispatcher = NotificationDispatcher(
        db_session,
        push_sender=push_sender,
        now_provider=_now,
    )

    event = NotificationEvent(
        user_id=user.id,
        category=NotificationCategory.RESULT,
        title="レース結果確定",
        message="結果が確定しました。",
    )

    notification = dispatcher.dispatch_event(event)
    assert notification is not None
    assert push_sender.sent_payloads, "Push 通知が送信されるべきです。"
    refreshed = notification_crud.get_notification(db_session, notification.id, user_id=user.id)
    assert refreshed is not None
    assert refreshed.status == NotificationDeliveryStatus.SENT
    assert refreshed.sent_at is not None


def test_retry_pending_notifications_retries_failed_delivery(db_session: Session) -> None:
    user = _create_user(db_session, email="retry@example.com")
    notification_crud.update_setting(
        db_session,
        user_id=user.id,
        enable_push=True,
        push_endpoint="https://example.com/push",
        push_p256dh="p256dh-key",
        push_auth="auth-secret",
    )
    notification = notification_crud.create_notification(
        db_session,
        notification_crud.NotificationCreateInput(
            user_id=user.id,
            category=NotificationCategory.SYSTEM,
            title="リトライ対象",
            message="最初は失敗して再送されます。",
        ),
    )

    push_sender = StubPushSender()
    dispatcher = NotificationDispatcher(
        db_session,
        push_sender=push_sender,
        now_provider=_now,
    )

    # 1回目はエラーを発生させる
    push_sender.raise_error = True
    dispatcher.retry_pending_notifications()
    refreshed = notification_crud.get_notification(db_session, notification.id, user_id=user.id)
    assert refreshed is not None
    assert refreshed.retry_count == 1
    assert refreshed.status in (NotificationDeliveryStatus.PENDING, NotificationDeliveryStatus.FAILED)

    # 2回目は成功させる
    push_sender.raise_error = False
    dispatcher.retry_pending_notifications()
    refreshed_final = notification_crud.get_notification(db_session, notification.id, user_id=user.id)
    assert refreshed_final is not None
    assert refreshed_final.status == NotificationDeliveryStatus.SENT
    assert refreshed_final.retry_count >= 1

