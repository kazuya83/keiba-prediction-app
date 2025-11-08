"""FastAPI 依存関係を定義するモジュール。"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_token
from app.crud import user as user_crud
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT Authorization",
)


def get_db_session() -> Generator[Session, None, None]:
    """リクエストスコープで利用する DB セッションを提供する。"""
    yield from get_session()


def _credentials_exception(detail: str = "認証情報が無効です。") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: Session = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """アクセストークンから現在のユーザーを取得する。"""
    if not token:
        raise _credentials_exception()

    try:
        payload = decode_token(token, token_type="access")
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as exc:
        raise _credentials_exception() from exc

    try:
        user_id = int(token_data.sub)
    except ValueError as exc:
        raise _credentials_exception() from exc

    user = user_crud.get_user(db, user_id)
    if user is None:
        raise _credentials_exception()
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """アクティブ状態のユーザーのみ許可する。"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アカウントが無効化されています。",
        )
    return current_user


def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """管理者権限を持つユーザーを検証する。"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です。",
        )
    return current_user


__all__ = [
    "get_current_active_user",
    "get_current_admin",
    "get_current_user",
    "get_db_session",
    "oauth2_scheme",
]

