from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User


def _create_user_payload(email: str = "user@example.com") -> dict[str, object]:
    return {
        "email": email,
        "password": "securepass123",
        "is_active": True,
        "is_superuser": False,
    }


def _create_admin_user(db_session: Session) -> User:
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    db_session.flush()
    return admin


def _get_auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_user_returns_created_user(
    test_client: TestClient,
    db_session: Session,
) -> None:
    payload = _create_user_payload()
    _create_admin_user(db_session)

    login_response = test_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"},
    )
    assert login_response.status_code == 200
    admin_headers = _get_auth_headers(login_response.json()["access_token"])

    response = test_client.post("/api/users", json=payload, headers=admin_headers)

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

    first = test_client.post("/api/auth/register", json={"email": payload["email"], "password": payload["password"]})
    assert first.status_code == 201

    second = test_client.post("/api/auth/register", json={"email": payload["email"], "password": payload["password"]})
    assert second.status_code == 400
    assert second.json()["detail"] == "既に登録済みのメールアドレスです。"


def test_read_current_user_returns_user_data(
    test_client: TestClient,
) -> None:
    payload = {"email": "reader@example.com", "password": "securepass123"}
    register_response = test_client.post("/api/auth/register", json=payload)
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    read_response = test_client.get(
        "/api/users/me",
        headers=_get_auth_headers(access_token),
    )

    assert read_response.status_code == 200
    data = read_response.json()
    assert data["email"] == payload["email"]


def test_update_current_user_updates_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    payload = {"email": "updater@example.com", "password": "securepass123"}
    register_response = test_client.post("/api/auth/register", json=payload)
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]
    user_id = test_client.get(
        "/api/users/me",
        headers=_get_auth_headers(access_token),
    ).json()["id"]

    update_payload = {
        "email": "updated@example.com",
        "password": "newsecurepass456",
        "is_active": False,
    }

    update_response = test_client.patch(
        "/api/users/me",
        json=update_payload,
        headers=_get_auth_headers(access_token),
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
    first_register = test_client.post(
        "/api/auth/register",
        json={"email": "first@example.com", "password": "securepass123"},
    )
    assert first_register.status_code == 201

    second_register = test_client.post(
        "/api/auth/register",
        json={"email": "second@example.com", "password": "securepass123"},
    )
    assert second_register.status_code == 201
    second_access_token = second_register.json()["access_token"]

    duplicate_update = test_client.patch(
        "/api/users/me",
        json={"email": "first@example.com"},
        headers=_get_auth_headers(second_access_token),
    )

    assert duplicate_update.status_code == 400
    assert duplicate_update.json()["detail"] == "既に登録済みのメールアドレスです。"


