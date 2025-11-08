"""ユーザー関連の API ルータ。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザーを新規作成する",
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_session),
) -> UserRead:
    """管理者向けのユーザー作成エンドポイント。"""
    if user_crud.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既に登録済みのメールアドレスです。",
        )

    try:
        user = user_crud.create_user(db, user_in)
    except IntegrityError as exc:  # 冗長チェックだが整合性のため保持
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー作成に失敗しました。",
        ) from exc

    return user  # FastAPI が Pydantic モデルへ変換


@router.get(
    "/me",
    response_model=UserRead,
    summary="自身のユーザー情報を取得する",
)
def read_current_user(
    user_id: int = Query(
        ...,
        ge=1,
        description="認証未実装のため暫定的にユーザーIDを指定してください。",
    ),
    db: Session = Depends(get_db_session),
) -> UserRead:
    """自己参照用のユーザー情報取得エンドポイント。"""
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。",
        )
    return user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="自身のユーザー情報を更新する",
)
def update_current_user(
    user_in: UserUpdate,
    user_id: int = Query(
        ...,
        ge=1,
        description="認証未実装のため暫定的にユーザーIDを指定してください。",
    ),
    db: Session = Depends(get_db_session),
) -> UserRead:
    """自己参照用のユーザー情報更新エンドポイント。"""
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。",
        )

    if not user_in.model_fields_set:
        return user

    if user_in.email and user_in.email != user.email:
        existing_user = user_crud.get_user_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="既に登録済みのメールアドレスです。",
            )

    try:
        updated_user = user_crud.update_user(db, user, user_in)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー更新に失敗しました。",
        ) from exc

    return updated_user


__all__ = ["router"]


