"""SQLAlchemy の Declarative Base を定義するモジュール。"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """アプリケーション全体で共有する Declarative Base。"""


metadata = Base.metadata


def import_all_models() -> None:
    """Alembic の `autogenerate` 用にモデルを事前インポートするフック。

    モデルを追加した際は、この関数内で対象モジュールをインポートするか、
    モデル定義ファイルの import 副作用で Base に登録されるよう調整する。
    """
    # 現時点では参照モデルが存在しないため、処理はプレースホルダー。
    return None


__all__ = ["Base", "metadata", "import_all_models"]



