from __future__ import annotations

import logging

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_admin_log_storage
from app.core.security import get_password_hash
from app.models.audit_log import AuditLog
from app.models.user import User


def _create_admin(db_session: Session) -> User:
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    db_session.flush()
    return admin


def _create_user(db_session: Session, email: str = "member@example.com") -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash("UserPass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _get_auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_non_admin_access_is_forbidden(test_client: TestClient) -> None:
    register_response = test_client.post(
        "/api/auth/register",
        json={"email": "user1@example.com", "password": "UserPass123!"},
    )
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    response = test_client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者権限が必要です。"


def test_admin_updates_user_and_creates_audit_log(
    test_client: TestClient,
    db_session: Session,
) -> None:
    admin = _create_admin(db_session)
    user = _create_user(db_session, email="target@example.com")

    admin_headers = _get_auth_headers(test_client, admin.email, "AdminPass123!")

    response = test_client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False, "reason": "manual_test"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_active"] is False

    db_session.expire_all()
    audit_log = db_session.scalars(
        select(AuditLog).order_by(AuditLog.id.desc()),
    ).first()
    assert audit_log is not None
    assert audit_log.action == "user.update"
    assert audit_log.actor_id == admin.id
    assert audit_log.resource_id == str(user.id)
    assert audit_log.metadata is not None
    assert audit_log.metadata["changes"]["is_active"] is False
    assert audit_log.metadata["reason"] == "manual_test"


def test_model_training_triggers_job_and_logs_audit(
    test_client: TestClient,
    db_session: Session,
) -> None:
    admin = _create_admin(db_session)
    admin_headers = _get_auth_headers(test_client, admin.email, "AdminPass123!")

    response = test_client.post(
        "/api/admin/model/train",
        json={"model_id": "baseline-model", "parameters": {"window": 30}},
        headers=admin_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["job_id"]

    db_session.expire_all()
    audit_log = db_session.scalars(
        select(AuditLog)
        .where(AuditLog.action == "model.train")
        .order_by(AuditLog.id.desc()),
    ).first()
    assert audit_log is not None
    assert audit_log.metadata is not None
    assert audit_log.metadata["job_id"] == data["job_id"]
    assert audit_log.metadata["parameters"] == {"window": 30}


def test_error_logs_endpoint_returns_recent_entries(
    test_client: TestClient,
    db_session: Session,
) -> None:
    admin = _create_admin(db_session)
    admin_headers = _get_auth_headers(test_client, admin.email, "AdminPass123!")

    storage = get_admin_log_storage()
    storage.reset()

    logger = logging.getLogger("test.admin")
    logger.error("admin endpoint error test", extra={"code": "AD001"})

    response = test_client.get("/api/admin/errors", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    first_log = data["items"][0]
    assert first_log["message"] == "admin endpoint error test"
    assert first_log["context"]["code"] == "AD001"


