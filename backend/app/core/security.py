"""認証関連のセキュリティユーティリティを提供するモジュール。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from passlib.context import CryptContext


DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュを比較検証する。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードのハッシュ値を生成する。"""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JWT 実装前提のアクセストークン情報を組み立てるプレースホルダー。"""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    token = secrets.token_urlsafe(32)
    payload: dict[str, Any] = {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expire,
        "sub": subject,
    }
    if additional_claims:
        payload.update(additional_claims)
    return payload


__all__ = [
    "DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "create_access_token",
    "get_password_hash",
    "verify_password",
]


