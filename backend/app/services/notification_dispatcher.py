"""通知配信とバックグラウンドジョブ処理を担うサービス。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, Callable, Protocol

from sqlalchemy.orm import Session

from app.crud import notification as notification_crud
from app.models.notification import (
    Notification,
    NotificationCategory,
    NotificationDeliveryStatus,
)
from app.models.notification_setting import NotificationSetting

logger = logging.getLogger(__name__)

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover - optional dependency
    WebPushException = None
    webpush = None


class PushDeliveryError(RuntimeError):
    """Push 通知配信時のエラーを表す例外。"""


@dataclass(slots=True)
class NotificationEvent:
    """通知生成の元となるイベント情報。"""

    user_id: int
    category: NotificationCategory
    title: str
    message: str
    race_id: int | None = None
    action_url: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class PushSubscription:
    """Web Push 購読情報。"""

    endpoint: str
    p256dh: str
    auth: str


class PushNotificationSender(Protocol):
    """Push 通知送信の実装契約。"""

    def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> None:
        """購読情報に対して Push 通知を配信する。"""


class PyWebPushSender:
    """pywebpush を利用して通知を送信する実装。"""

    def __init__(self, vapid_private_key: str, vapid_public_key: str, subject: str) -> None:
        if webpush is None:
            raise PushDeliveryError("pywebpush がインストールされていないため Push を利用できません。")
        self._private_key = vapid_private_key
        self._public_key = vapid_public_key
        self._subject = subject

    def send(self, subscription: PushSubscription, payload: dict[str, Any]) -> None:
        assert webpush is not None  # for type checker
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self._private_key,
                vapid_claims={"sub": self._subject},
            )
        except WebPushException as exc:  # pragma: no cover - depends on external service
            raise PushDeliveryError(str(exc)) from exc


class NotificationSuppressedError(RuntimeError):
    """ユーザー設定により通知が作成されなかった場合の例外。"""


class NotificationDispatcher:
    """通知生成と配信を扱うサービスクラス。"""

    def __init__(
        self,
        db: Session,
        *,
        push_sender: PushNotificationSender | None = None,
        default_max_retries: int = 3,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._db = db
        self._push_sender = push_sender
        self._default_max_retries = default_max_retries
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def dispatch_event(self, event: NotificationEvent) -> Notification | None:
        """イベントに基づいて通知を生成し、必要に応じて Push 配信を試みる。"""
        settings = notification_crud.get_or_create_setting(self._db, user_id=event.user_id)
        if not self._should_create_notification(settings, event.category):
            logger.info(
                "Notification suppressed by user preference",
                extra={"user_id": event.user_id, "category": event.category.value},
            )
            raise NotificationSuppressedError("notification suppressed by user preference")

        created_at = event.created_at or self._now()
        notification = notification_crud.create_notification(
            self._db,
            notification_crud.NotificationCreateInput(
                user_id=event.user_id,
                category=event.category,
                title=event.title,
                message=event.message,
                race_id=event.race_id,
                action_url=event.action_url,
                metadata=event.metadata,
                status=NotificationDeliveryStatus.PENDING,
                max_retries=self._default_max_retries,
            ),
        )
        notification.created_at = created_at
        notification.updated_at = created_at
        self._db.add(notification)
        self._db.flush()
        self._db.refresh(notification)

        if self._can_send_push_now(settings):
            self._deliver_push(notification, settings)
        else:
            if settings.enable_push and not settings.has_push_subscription:
                logger.warning(
                    "Push notification disabled due to missing subscription.",
                    extra={"user_id": settings.user_id},
                )
            if settings.enable_push and self._is_within_quiet_hours(settings):
                logger.debug(
                    "Notification deferred due to quiet hours.",
                    extra={"user_id": settings.user_id, "notification_id": notification.id},
                )
        return notification

    def retry_pending_notifications(self, *, limit: int = 100) -> list[Notification]:
        """再送可能な通知に対して Push 配信を再試行する。"""
        retry_targets = notification_crud.list_retryable_notifications(self._db, limit=limit)
        delivered: list[Notification] = []
        for notification in retry_targets:
            settings = notification_crud.get_or_create_setting(self._db, user_id=notification.user_id)
            if not self._can_send_push_now(settings):
                continue
            self._deliver_push(notification, settings)
            delivered.append(notification)
        return delivered

    def _deliver_push(self, notification: Notification, settings: NotificationSetting) -> None:
        subscription = self._to_subscription(settings)
        if subscription is None:
            if settings.enable_push:
                notification_crud.update_delivery_status(
                    self._db,
                    notification,
                    status=NotificationDeliveryStatus.SUPPRESSED,
                    last_error="Missing push subscription",
                )
            return

        payload = self._build_push_payload(notification)
        if self._push_sender is None:
            logger.warning(
                "Push sender is not configured; skipping push delivery.",
                extra={"notification_id": notification.id},
            )
            if not settings.enable_app:
                notification_crud.update_delivery_status(
                    self._db,
                    notification,
                    status=NotificationDeliveryStatus.SUPPRESSED,
                    last_error="Push sender not configured",
                )
            return

        try:
            self._push_sender.send(subscription, payload)
        except PushDeliveryError as exc:
            logger.error(
                "Failed to deliver push notification",
                extra={
                    "notification_id": notification.id,
                    "user_id": notification.user_id,
                },
                exc_info=exc,
            )
            notification_crud.increment_retry_count(
                self._db,
                notification,
                last_error=str(exc),
            )
            return

        notification_crud.update_delivery_status(
            self._db,
            notification,
            status=NotificationDeliveryStatus.SENT,
            sent_at=self._now(),
        )

    def _should_create_notification(
        self,
        settings: NotificationSetting,
        category: NotificationCategory,
    ) -> bool:
        if not settings.enable_app and not settings.enable_push:
            return False
        if category == NotificationCategory.PREDICTION and not settings.allow_prediction:
            return False
        if category == NotificationCategory.RESULT and not settings.allow_race_result:
            return False
        if category == NotificationCategory.SYSTEM and not settings.allow_system:
            return False
        return True

    def _can_send_push_now(self, settings: NotificationSetting) -> bool:
        if not settings.enable_push or not settings.has_push_subscription:
            return False
        if self._push_sender is None:
            return False
        if self._is_within_quiet_hours(settings):
            return False
        return True

    def _is_within_quiet_hours(self, settings: NotificationSetting) -> bool:
        start = settings.quiet_hours_start
        end = settings.quiet_hours_end
        if start is None or end is None:
            return False
        now_time = self._now().time()
        if start < end:
            return start <= now_time < end
        # サイレント時間が日付を跨ぐケース (例: 23:00-06:00) を考慮
        return now_time >= start or now_time < end

    def _to_subscription(self, settings: NotificationSetting) -> PushSubscription | None:
        if not settings.has_push_subscription:
            return None
        assert settings.push_endpoint is not None
        assert settings.push_p256dh is not None
        assert settings.push_auth is not None
        return PushSubscription(
            endpoint=settings.push_endpoint,
            p256dh=settings.push_p256dh,
            auth=settings.push_auth,
        )

    def _build_push_payload(self, notification: Notification) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": notification.title,
            "body": notification.message,
            "category": notification.category.value,
            "notificationId": notification.id,
        }
        if notification.action_url:
            payload["actionUrl"] = notification.action_url
        if notification.metadata:
            payload["metadata"] = notification.metadata
        return payload

    def _now(self) -> datetime:
        current = self._now_provider()
        if current.tzinfo is None:
            return current.replace(tzinfo=timezone.utc)
        return current


__all__ = [
    "NotificationDispatcher",
    "NotificationEvent",
    "NotificationSuppressedError",
    "PushDeliveryError",
    "PushNotificationSender",
    "PyWebPushSender",
    "PushSubscription",
]


