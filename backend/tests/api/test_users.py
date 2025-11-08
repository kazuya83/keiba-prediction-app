from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def _create_user_payload(email: str = "user@example.com") -> dict[str, object]:
    return {
        "email": email,
        "password": "securepass123",
        "is_active": True,
        "is_superuser": False,
    }


def test_create_user_returns_created_user(
    test_client: TestClient,
    db_session: Session,
) -> None:
    payload = _create_user_payload()

    response = test_client.post("/api/users", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["is_active"] is True
    assert body["is_superuser"] is False
    assert "hashed_password" not in body

    user = db_session.get(User, body["id"])
    assert user is not None
    assert verify_password(payload["password"], user.hashed_password)


def test_create_user_with_duplicate_email_returns_400(
    test_client: TestClient,
) -> None:
    payload = _create_user_payload()

    first = test_client.post("/api/users", json=payload)
    assert first.status_code == 201

    second = test_client.post("/api/users", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "既に登録済みのメールアドレスです。"


def test_read_current_user_returns_user_data(
    test_client: TestClient,
) -> None:
    payload = _create_user_payload()
    response = test_client.post("/api/users", json=payload)
    user_id = response.json()["id"]

    read_response = test_client.get("/api/users/me", params={"user_id": user_id})

    assert read_response.status_code == 200
    data = read_response.json()
    assert data["id"] == user_id
    assert data["email"] == payload["email"]


def test_update_current_user_updates_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    payload = _create_user_payload()
    response = test_client.post("/api/users", json=payload)
    user_id = response.json()["id"]

    update_payload = {
        "email": "updated@example.com",
        "password": "newsecurepass456",
        "is_active": False,
    }

    update_response = test_client.patch(
        "/api/users/me",
        params={"user_id": user_id},
        json=update_payload,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["email"] == update_payload["email"]
    assert updated["is_active"] is False

    user = db_session.get(User, user_id)
    assert user is not None
    assert verify_password(update_payload["password"], user.hashed_password)


def test_update_current_user_with_duplicate_email_returns_400(
    test_client: TestClient,
) -> None:
    first_response = test_client.post(
        "/api/users",
        json=_create_user_payload(email="first@example.com"),
    )
    second_response = test_client.post(
        "/api/users",
        json=_create_user_payload(email="second@example.com"),
    )
    second_id = second_response.json()["id"]

    duplicate_update = test_client.patch(
        "/api/users/me",
        params={"user_id": second_id},
        json={"email": "first@example.com"},
    )

    assert duplicate_update.status_code == 400
    assert duplicate_update.json()["detail"] == "既に登録済みのメールアドレスです。"


