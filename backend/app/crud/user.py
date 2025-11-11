"""ユーザー関連の CRUD 操作を提供するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


@dataclass(slots=True)
class UserListParams:
    """管理者向けのユーザー一覧取得条件。"""

    limit: int = 50
    offset: int = 0
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


@dataclass(slots=True)
class UserListResult:
    """管理者向けユーザー一覧の取得結果。"""

    items: list[User]
    total: int
    params: UserListParams


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


def list_users(db: Session, params: UserListParams) -> UserListResult:
    """管理者向けにユーザー一覧を返す。"""
    statement = select(User).order_by(User.created_at.desc(), User.id.desc())

    if params.email:
        like_pattern = f"%{params.email}%"
        statement = statement.where(User.email.ilike(like_pattern))
    if params.is_active is not None:
        statement = statement.where(User.is_active == params.is_active)
    if params.is_superuser is not None:
        statement = statement.where(User.is_superuser == params.is_superuser)

    limited_statement = statement.offset(params.offset).limit(params.limit)
    items = db.scalars(limited_statement).all()

    count_statement = select(func.count(User.id))
    if params.email:
        like_pattern = f"%{params.email}%"
        count_statement = count_statement.where(User.email.ilike(like_pattern))
    if params.is_active is not None:
        count_statement = count_statement.where(User.is_active == params.is_active)
    if params.is_superuser is not None:
        count_statement = count_statement.where(User.is_superuser == params.is_superuser)

    total = int(db.scalar(count_statement) or 0)
    return UserListResult(items=items, total=total, params=params)


__all__ = [
    "UserListParams",
    "UserListResult",
    "create_user",
    "get_user",
    "get_user_by_email",
    "list_users",
    "update_user",
]


__all__ = ["create_user", "get_user", "get_user_by_email", "update_user"]


