"""監査ログに関する CRUD 操作を提供するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


@dataclass(slots=True)
class AuditLogCreateInput:
    """監査ログ作成時に利用する入力データ。"""

    action: str
    actor_id: int | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class AuditLogListParams:
    """監査ログ一覧取得時に利用するフィルタ条件。"""

    limit: int = 50
    offset: int = 0
    actor_id: int | None = None
    resource_type: str | None = None
    action: str | None = None


def create_audit_log(db: Session, payload: AuditLogCreateInput) -> AuditLog:
    """監査ログを新規作成し、永続化する。"""
    audit_log = AuditLog(
        action=payload.action,
        actor_id=payload.actor_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        metadata=payload.metadata,
    )
    if payload.created_at is not None:
        audit_log.created_at = payload.created_at

    db.add(audit_log)
    db.flush()
    db.refresh(audit_log)
    return audit_log


def list_audit_logs(db: Session, params: AuditLogListParams) -> tuple[list[AuditLog], int]:
    """監査ログを条件付きで取得する。"""
    statement = _build_filtered_statement(params)
    items = db.scalars(
        statement.offset(params.offset).limit(params.limit),
    ).all()

    total_statement = _build_filtered_statement(
        params,
        columns=select(func.count(AuditLog.id)),
    )
    total = int(db.scalar(total_statement) or 0)
    return items, total


def _build_filtered_statement(
    params: AuditLogListParams,
    *,
    columns: Select[tuple[Any]] | None = None,
) -> Select[tuple[Any]]:
    statement: Select[tuple[Any]]
    if columns is None:
        statement = select(AuditLog)
    else:
        statement = columns

    if params.actor_id is not None:
        statement = statement.where(AuditLog.actor_id == params.actor_id)
    if params.resource_type is not None:
        statement = statement.where(AuditLog.resource_type == params.resource_type)
    if params.action is not None:
        statement = statement.where(AuditLog.action == params.action)

    statement = statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    return statement


__all__ = [
    "AuditLogCreateInput",
    "AuditLogListParams",
    "create_audit_log",
    "list_audit_logs",
]


