"""SQLAlchemy セッションとエンジンの初期化処理を提供する。"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _create_engine() -> Engine:
    """設定値から SQLAlchemy エンジンを生成する。"""
    settings = get_settings()
    database_url = settings.database_url or "sqlite:///./app.db"

    connect_args: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
        future=True,
    )


engine: Engine = _create_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """新しい DB セッションを生成して呼び出し元へ提供するジェネレータ。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["Engine", "SessionLocal", "engine", "get_session"]



