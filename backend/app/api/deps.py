"""FastAPI 依存関係の雛形を定義するモジュール。"""

from collections.abc import AsyncGenerator


async def get_db_session() -> AsyncGenerator[None, None]:
    """データベースセッションを取得する依存関数のプレースホルダー。"""
    raise NotImplementedError("Database session dependency is not implemented yet.")


__all__ = ["get_db_session"]


