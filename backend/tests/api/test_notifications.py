from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import notification as notification_crud
from app.models.notification import NotificationCategory


def _register_and_get_token(
    client: TestClient,
    email: str = "notify@example.com",
    password: str = "securepass123",
) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _get_auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _get_current_user_id(client: TestClient, token: str) -> int:
    response = client.get("/api/users/me", headers=_get_auth_headers(token))
    assert response.status_code == 200
    return response.json()["id"]


def test_list_notifications_returns_created_notifications(
    test_client: TestClient,
    db_session: Session,
) -> None:
    token = _register_and_get_token(test_client)
    user_id = _get_current_user_id(test_client, token)

    notification_crud.create_notification(
        db_session,
        notification_crud.NotificationCreateInput(
            user_id=user_id,
            category=NotificationCategory.PREDICTION,
            title="予測が完了しました",
            message="京都11Rの予測が完了しました。",
            metadata={"raceId": 101},
        ),
    )
    notification_crud.create_notification(
        db_session,
        notification_crud.NotificationCreateInput(
            user_id=user_id,
            category=NotificationCategory.RESULT,
            title="結果が確定しました",
            message="京都11Rの結果が確定しました。",
            metadata={"raceId": 101, "result": "win"},
        ),
    )

    response = test_client.get(
        "/api/notifications",
        headers=_get_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["unread_count"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "結果が確定しました"
    assert body["items"][1]["title"] == "予測が完了しました"


def test_mark_notification_read_updates_state(
    test_client: TestClient,
    db_session: Session,
) -> None:
    token = _register_and_get_token(test_client, email="notify2@example.com")
    user_id = _get_current_user_id(test_client, token)
    notification = notification_crud.create_notification(
        db_session,
        notification_crud.NotificationCreateInput(
            user_id=user_id,
            category=NotificationCategory.SYSTEM,
            title="システムメンテナンス",
            message="深夜2時にメンテナンスを実施します。",
        ),
    )

    response = test_client.put(
        f"/api/notifications/{notification.id}/read",
        json={"read": True},
        headers=_get_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_read"] is True
    assert body["read_at"] is not None

    refreshed = notification_crud.get_notification(db_session, notification.id, user_id=user_id)
    assert refreshed is not None
    assert refreshed.is_read is True
    assert refreshed.read_at is not None


def test_update_notification_settings_requires_subscription_for_push(
    test_client: TestClient,
    db_session: Session,
) -> None:
    token = _register_and_get_token(test_client, email="notify3@example.com")

    response = test_client.post(
        "/api/notifications/settings",
        json={"enable_push": True},
        headers=_get_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Push 通知を有効化するには")

    valid_payload = {
        "enable_push": True,
        "push_endpoint": "https://example.com/push",
        "push_p256dh": "p256dh-key",
        "push_auth": "auth-secret",
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "06:00",
    }
    response_ok = test_client.post(
        "/api/notifications/settings",
        json=valid_payload,
        headers=_get_auth_headers(token),
    )

    assert response_ok.status_code == 200
    body = response_ok.json()
    assert body["enable_push"] is True
    assert body["push_endpoint"] == valid_payload["push_endpoint"]
    assert body["quiet_hours_start"].startswith("22:00")
    assert body["quiet_hours_end"].startswith("06:00")
    assert "vapid_public_key" in body


