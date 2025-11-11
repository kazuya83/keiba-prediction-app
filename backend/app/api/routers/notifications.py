"""通知関連 API を提供するルータ。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.core.config import get_settings
from app.crud import notification as notification_crud
from app.models.notification import NotificationCategory
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationRead,
    NotificationReadRequest,
    NotificationSettingRead,
    NotificationSettingUpdate,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="通知一覧を取得する",
    description="ログインユーザーに紐づく通知をページネーション付きで返します。",
)
def list_notifications(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    category: NotificationCategory | None = Query(
        default=None,
        description="通知カテゴリでフィルタリングする。",
    ),
    is_read: bool | None = Query(
        default=None,
        description="既読・未読でフィルタリングする。未指定の場合は全件。",
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationListResponse:
    params = notification_crud.NotificationListParams(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        category=category,
        is_read=is_read,
    )
    result = notification_crud.list_notifications(db, params)
    return NotificationListResponse(
        items=[NotificationRead.model_validate(item) for item in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
        unread_count=result.unread_count,
    )


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="通知を既読化する",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "通知が見つからない場合に返されます。"},
    },
)
def mark_notification_read(
    notification_id: int,
    payload: NotificationReadRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationRead:
    try:
        notification = notification_crud.mark_notification_read(
            db,
            notification_id,
            user_id=current_user.id,
            read=payload.read,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知が見つかりません。",
        ) from exc
    return NotificationRead.model_validate(notification)


@router.post(
    "/settings",
    response_model=NotificationSettingRead,
    summary="通知設定を更新する",
    description="通知カテゴリやブラウザ Push の設定を更新します。未指定の項目は現状の設定を維持します。",
)
def update_notification_settings(
    payload: NotificationSettingUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> NotificationSettingRead:
    changes = payload.model_dump(exclude_unset=True, exclude_none=False)

    setting = notification_crud.get_or_create_setting(db, user_id=current_user.id)

    if changes.get("enable_push") is True:
        endpoint = changes.get("push_endpoint") or setting.push_endpoint
        p256dh = changes.get("push_p256dh") or setting.push_p256dh
        auth = changes.get("push_auth") or setting.push_auth
        if not endpoint or not p256dh or not auth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Push 通知を有効化するには購読情報(push_endpoint, push_p256dh, push_auth)が必要です。",
            )

    updated = notification_crud.update_setting(
        db,
        user_id=current_user.id,
        **changes,
    )
    response = NotificationSettingRead.model_validate(updated)
    settings_config = get_settings()
    response.vapid_public_key = settings_config.notification_vapid_public_key
    return response


__all__ = ["router"]


