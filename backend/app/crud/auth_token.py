"""認証トークンに関する永続化処理を提供するモジュール。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_token import AuthToken


def create_refresh_token(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> AuthToken:
    """リフレッシュトークンを新規発行する。"""
    auth_token = AuthToken(
        user_id=user_id,
        token_hash=token_hash,
        token_type="refresh",
        expires_at=expires_at,
    )
    db.add(auth_token)
    db.commit()
    db.refresh(auth_token)
    return auth_token


def get_by_token_hash(db: Session, token_hash: str) -> AuthToken | None:
    """トークンハッシュでレコードを取得する。"""
    statement = select(AuthToken).where(AuthToken.token_hash == token_hash)
    return db.scalars(statement).first()


def get_active_refresh_token(db: Session, token_hash: str) -> AuthToken | None:
    """アクティブなリフレッシュトークンを取得する。"""
    token = get_by_token_hash(db, token_hash)
    if token is None:
        return None
    now = datetime.now(timezone.utc)
    if token.revoked or token.expires_at < now:
        return None
    if token.token_type != "refresh":
        return None
    return token


def revoke_token(db: Session, token: AuthToken) -> AuthToken:
    """トークンを失効させる。"""
    token.revoked = True
    token.revoked_at = datetime.now(timezone.utc)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    """対象ユーザーの既存リフレッシュトークンを全て失効させる。"""
    statement = select(AuthToken).where(
        AuthToken.user_id == user_id,
        AuthToken.token_type == "refresh",
        AuthToken.revoked.is_(False),
    )
    now = datetime.now(timezone.utc)
    tokens = db.scalars(statement).all()
    if not tokens:
        return
    for token in tokens:
        token.revoked = True
        token.revoked_at = now
    db.add_all(tokens)
    db.commit()


__all__ = [
    "create_refresh_token",
    "get_active_refresh_token",
    "get_by_token_hash",
    "revoke_all_refresh_tokens",
    "revoke_token",
]


