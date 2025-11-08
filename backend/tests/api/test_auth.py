from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_oauth_state, hash_token
from app.models.auth_token import AuthToken
from app.models.user import User


def test_register_creates_user_and_tokens(
    test_client: TestClient,
    db_session: Session,
) -> None:
    response = test_client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "securepass123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body

    user = db_session.scalars(
        select(User).where(User.email == "newuser@example.com"),
    ).first()
    assert user is not None

    refresh_token_hash = hash_token(body["refresh_token"])
    token_record = db_session.scalars(
        select(AuthToken).where(AuthToken.token_hash == refresh_token_hash),
    ).first()
    assert token_record is not None
    assert token_record.revoked is False


def test_login_returns_new_tokens_and_revokes_previous_refresh(
    test_client: TestClient,
    db_session: Session,
) -> None:
    register_response = test_client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    initial_refresh_token = register_response.json()["refresh_token"]

    login_response = test_client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )

    assert login_response.status_code == 200
    new_tokens = login_response.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    initial_record = db_session.scalars(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(initial_refresh_token),
        ),
    ).first()
    assert initial_record is not None
    assert initial_record.revoked is True

    new_record = db_session.scalars(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(new_tokens["refresh_token"]),
        ),
    ).first()
    assert new_record is not None
    assert new_record.revoked is False


def test_refresh_rotates_refresh_token(
    test_client: TestClient,
    db_session: Session,
) -> None:
    register_response = test_client.post(
        "/api/auth/register",
        json={"email": "refresh@example.com", "password": "securepass123"},
    )
    refresh_token = register_response.json()["refresh_token"]

    refresh_response = test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["refresh_token"] != refresh_token

    original_record = db_session.scalars(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(refresh_token),
        ),
    ).first()
    assert original_record is not None
    assert original_record.revoked is True

    new_record = db_session.scalars(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(refreshed["refresh_token"]),
        ),
    ).first()
    assert new_record is not None
    assert new_record.revoked is False


def test_logout_revokes_refresh_token(
    test_client: TestClient,
    db_session: Session,
) -> None:
    register_response = test_client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "securepass123"},
    )
    body = register_response.json()

    logout_response = test_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        json={"refresh_token": body["refresh_token"]},
    )

    assert logout_response.status_code == 204

    token_record = db_session.scalars(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(body["refresh_token"]),
        ),
    ).first()
    assert token_record is not None
    assert token_record.revoked is True


class _StubOAuthClient:
    def __init__(self, *, state: str | None = None) -> None:
        self.state = state

    def create_authorization_url(self, url: str, **kwargs: Any) -> tuple[str, str]:
        return ("https://example.com/oauth/google", kwargs.get("state", self.state))

    def fetch_token(self, token_url: str, code: str) -> dict[str, str]:
        return {"access_token": "oauth-access-token"}

    def get(self, url: str) -> "_StubOAuthResponse":
        return _StubOAuthResponse()


class _StubOAuthResponse:
    def json(self) -> dict[str, str]:
        return {"email": "oauth-user@example.com"}


def test_google_login_returns_authorization_url(
    monkeypatch: Any,
    test_client: TestClient,
) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.com/callback")
    get_settings.cache_clear()

    def _factory(state: str | None = None) -> _StubOAuthClient:
        return _StubOAuthClient(state=state)

    monkeypatch.setattr("app.api.routers.auth._get_google_oauth_client", _factory)

    response = test_client.get("/api/auth/google/login")
    assert response.status_code == 200
    data = response.json()
    assert data["authorization_url"] == "https://example.com/oauth/google"
    assert data["state"]


def test_google_callback_creates_user(
    monkeypatch: Any,
    test_client: TestClient,
    db_session: Session,
) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.com/callback")
    get_settings.cache_clear()

    def _factory(state: str | None = None) -> _StubOAuthClient:
        return _StubOAuthClient(state=state)

    monkeypatch.setattr("app.api.routers.auth._get_google_oauth_client", _factory)

    state = create_oauth_state("google")
    response = test_client.get(
        "/api/auth/google/callback",
        params={"code": "dummy-code", "state": state},
    )

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    user = db_session.scalars(
        select(User).where(User.email == "oauth-user@example.com"),
    ).first()
    assert user is not None


