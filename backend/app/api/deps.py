"""FastAPI 依存関係を定義するモジュール。"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_session


def get_db_session() -> Generator[Session, None, None]:
    """リクエストスコープで利用する DB セッションを提供する。"""
    yield from get_session()


__all__ = ["get_db_session"]


