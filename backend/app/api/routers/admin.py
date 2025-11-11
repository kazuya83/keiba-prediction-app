"""管理者向け API ルータ。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.core.logging import get_admin_log_storage
from app.crud import (
    AuditLogCreateInput,
    AuditLogListParams,
    UserListParams,
    create_audit_log,
    get_user,
    list_audit_logs as crud_list_audit_logs,
    list_users as crud_list_users,
)
from app.models.user import User
from app.schemas.admin import (
    AdminErrorLogEntry,
    AdminErrorLogListResponse,
    AdminUserListResponse,
    AdminUserSummary,
    AdminUserUpdateRequest,
    AdminUserUpdateResponse,
    LogLevel,
    ModelTrainingRequest,
    ModelTrainingResponse,
    ModelTrainingStatus,
)
from app.schemas.audit_log import AuditLogListResponse, AuditLogRead
from app.services.model_trainer import ModelTrainer, ModelTrainingJobResult, ModelTrainingJobStatus

router = APIRouter(prefix="/admin", tags=["admin"])

LOG_LEVEL_MAP: dict[LogLevel, int] = {
    LogLevel.ERROR: logging.ERROR,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.CRITICAL: logging.CRITICAL,
}


def get_model_trainer() -> ModelTrainer:
    """ModelTrainer の依存性注入用ファクトリ。"""
    return ModelTrainer()


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="ユーザー一覧を取得する",
)
def list_users(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    email: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
        description="メールアドレスの部分一致で検索します。",
    ),
    is_active: bool | None = Query(default=None, description="アクティブ状態で絞り込む。"),
    is_superuser: bool | None = Query(default=None, description="管理者フラグで絞り込む。"),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
) -> AdminUserListResponse:
    params = UserListParams(
        limit=limit,
        offset=offset,
        email=email,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    result = crud_list_users(db, params)
    items = [AdminUserSummary.model_validate(user) for user in result.items]
    return AdminUserListResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserUpdateResponse,
    summary="ユーザーのステータスを更新する",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "ユーザーが存在しない場合。"},
        status.HTTP_400_BAD_REQUEST: {"description": "更新内容が不正な場合。"},
    },
)
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin),
) -> AdminUserUpdateResponse:
    target = get_user(db, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたユーザーが見つかりません。",
        )

    if not payload.model_fields_set:
        return AdminUserUpdateResponse.model_validate(target)

    changes: dict[str, object] = {}

    if payload.is_active is not None and payload.is_active != target.is_active:
        if current_admin.id == target.id and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="自身のアカウントを無効化することはできません。",
            )
        target.is_active = payload.is_active
        changes["is_active"] = payload.is_active

    if payload.is_superuser is not None and payload.is_superuser != target.is_superuser:
        if current_admin.id == target.id and not payload.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="自身の管理者権限を解除することはできません。",
            )
        target.is_superuser = payload.is_superuser
        changes["is_superuser"] = payload.is_superuser

    if not changes:
        return AdminUserUpdateResponse.model_validate(target)

    db.add(target)

    try:
        db.flush()
        create_audit_log(
            db,
            AuditLogCreateInput(
                action="user.update",
                actor_id=current_admin.id,
                resource_type="user",
                resource_id=str(target.id),
                metadata={
                    "changes": changes,
                    "reason": payload.reason,
                },
            ),
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - 例外はHTTPエラーに変換
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー更新に失敗しました。",
        ) from exc

    db.refresh(target)
    return AdminUserUpdateResponse.model_validate(target)


@router.get(
    "/errors",
    response_model=AdminErrorLogListResponse,
    summary="アプリケーションエラーログを取得する",
)
def list_error_logs(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    level: LogLevel = Query(default=LogLevel.ERROR),
    since: datetime | None = Query(
        default=None,
        description="この日時以降に発生したログのみ取得します (ISO8601)。",
    ),
    _: User = Depends(get_current_admin),
) -> AdminErrorLogListResponse:
    storage = get_admin_log_storage()
    records = storage.list_records(
        min_level=LOG_LEVEL_MAP[level],
        limit=limit,
        since=since,
    )

    items = [
        AdminErrorLogEntry(
            id=record.record_id,
            level=record.level_name,
            message=record.message,
            logger_name=record.logger_name,
            pathname=record.pathname,
            lineno=record.lineno,
            timestamp=record.created_at,
            context=record.context,
            exception=record.exception,
        )
        for record in records
    ]

    return AdminErrorLogListResponse(
        items=items,
        limit=limit,
        total=len(items),
    )


@router.post(
    "/model/train",
    response_model=ModelTrainingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="モデル再学習をキューに投入する",
)
def trigger_model_training(
    request: ModelTrainingRequest,
    trainer: ModelTrainer = Depends(get_model_trainer),
    db: Session = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin),
) -> ModelTrainingResponse:
    job: ModelTrainingJobResult = trainer.enqueue(
        model_id=request.model_id,
        parameters=request.parameters,
    )

    try:
        create_audit_log(
            db,
            AuditLogCreateInput(
                action="model.train",
                actor_id=current_admin.id,
                resource_type="model",
                resource_id=request.model_id if request.model_id else None,
                metadata={
                    "job_id": job.job_id,
                    "parameters": request.parameters or {},
                },
            ),
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - 例外はHTTPエラーに変換
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="モデル再学習ジョブの投入に失敗しました。",
        ) from exc

    return ModelTrainingResponse(
        job_id=job.job_id,
        status=ModelTrainingStatus(job.status.value),
        queued_at=job.queued_at,
    )


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="監査ログを取得する",
)
def list_audit_logs(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    actor_id: int | None = Query(default=None, description="実行者のユーザーIDで絞り込む。"),
    resource_type: str | None = Query(default=None, description="対象リソース種別で絞り込む。"),
    action: str | None = Query(default=None, description="アクション名で絞り込む。"),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
) -> AuditLogListResponse:
    params = AuditLogListParams(
        limit=limit,
        offset=offset,
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
    )
    items, total = crud_list_audit_logs(db, params)
    return AuditLogListResponse(
        items=[AuditLogRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


__all__ = ["router", "get_model_trainer"]


