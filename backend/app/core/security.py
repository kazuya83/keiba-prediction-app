"""認証関連のセキュリティユーティリティを提供するモジュール。"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


class InvalidTokenError(Exception):
    """トークンが検証に失敗した場合に送出される例外。"""


def _normalized_password(password: str) -> str:
    """bcrypt の入力長制限を回避するため、事前にハッシュ化する。"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュを比較検証する。"""
    normalized = _normalized_password(plain_password)
    if pwd_context.verify(normalized, hashed_password):
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """パスワードのハッシュ値を生成する。"""
    normalized = _normalized_password(password)
    return pwd_context.hash(normalized)


def create_access_token(
    subject: str | int,
    *,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """JWT のアクセストークンを生成する。"""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": uuid.uuid4().hex,
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, *, token_type: str | None = None) -> dict[str, Any]:
    """JWT を復号し、期待する種別であることを検証する。"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:  # トークン署名/期限エラー
        raise InvalidTokenError("無効なトークンです。") from exc

    if token_type and payload.get("type") != token_type:
        raise InvalidTokenError("トークン種別が一致しません。")

    return payload


def create_refresh_token() -> str:
    """リフレッシュトークンのプレーンテキストを生成する。"""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """トークンを SHA-256 でハッシュ化する。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_oauth_state(
    provider: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """OAuth 用の state パラメータを署名付きで生成する。"""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.oauth_state_ttl_minutes)
    )
    payload = {
        "sub": provider,
        "type": "oauth_state",
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "nbf": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_oauth_state(state: str) -> dict[str, Any]:
    """OAuth state を検証してペイロードを返す。"""
    return decode_token(state, token_type="oauth_state")


__all__ = [
    "DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "InvalidTokenError",
    "create_access_token",
    "create_oauth_state",
    "create_refresh_token",
    "decode_oauth_state",
    "decode_token",
    "get_password_hash",
    "hash_token",
    "verify_password",
]
