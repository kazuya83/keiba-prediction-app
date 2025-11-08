"""DB 接続の基本的な動作を確認するテスト。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_db_session_can_execute_simple_query(db_session: Session) -> None:
    """テスト用セッションでシンプルなクエリが実行できることを検証する。"""
    result = db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


