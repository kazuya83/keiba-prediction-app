"""ユーザー関連の CRUD 操作を提供するモジュール。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User | None:
    """ID からユーザーを取得する。"""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """メールアドレスからユーザーを取得する。"""
    statement = select(User).where(User.email == email)
    return db.scalars(statement).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """ユーザーを新規作成する。"""
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """ユーザー情報を更新する。"""
    data = user_in.model_dump(exclude_unset=True)

    if "password" in data:
        password = data.pop("password")
        if password is not None:
            user.hashed_password = get_password_hash(password)

    for field, value in data.items():
        if value is None:
            continue
        setattr(user, field, value)

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


__all__ = ["create_user", "get_user", "get_user_by_email", "update_user"]


