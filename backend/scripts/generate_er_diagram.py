"""データベースER図を生成するスクリプト。

注意: このスクリプトを実行するには、以下のパッケージが必要です:
- eralchemy2 (pip install eralchemy2)
- graphviz (システムにインストールが必要)

または、sqlalchemy_schemadisplayを使用する場合:
- sqlalchemy_schemadisplay (pip install sqlalchemy-schemadisplay)
- graphviz (システムにインストールが必要)
"""

from pathlib import Path

try:
    from eralchemy2 import render_er
except ImportError:
    try:
        from sqlalchemy_schemadisplay import create_schema_graph
    except ImportError:
        print(
            "ER図生成に必要なパッケージがインストールされていません。\n"
            "以下のいずれかをインストールしてください:\n"
            "  pip install eralchemy2\n"
            "  または\n"
            "  pip install sqlalchemy-schemadisplay\n"
            "また、graphvizもシステムにインストールが必要です。"
        )
        raise

from app.core.config import get_settings
from app.db.base import Base
from app.models import (  # noqa: F401
    AuditLog,
    AuthToken,
    Horse,
    Jockey,
    Notification,
    NotificationSetting,
    Prediction,
    PredictionHistory,
    Race,
    RaceEntry,
    Trainer,
    User,
    Weather,
)


def generate_er_diagram(output_path: Path) -> None:
    """データベースER図を生成する。"""
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URLが設定されていません")

    # すべてのモデルをインポートしてBaseに登録
    # モデルは既にインポートされている

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # eralchemy2を使用する場合
        render_er(Base, str(output_path))
        print(f"ER図を生成しました: {output_path}")
    except NameError:
        # sqlalchemy_schemadisplayを使用する場合
        graph = create_schema_graph(
            metadata=Base.metadata,
            show_datatypes=False,
            show_indexes=False,
            rankdir="TB",  # Top to Bottom
            concentrate=False,
        )
        graph.write_png(str(output_path))
        print(f"ER図を生成しました: {output_path}")


if __name__ == "__main__":
    # プロジェクトルートからの相対パス
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "docs" / "db" / "er_diagram.png"
    generate_er_diagram(output_path)

