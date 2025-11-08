"""
データベース初期化スクリプト
"""
from app.core.database import engine, Base
from app.models import *  # すべてのモデルをインポート


def init_db():
    """データベースの初期化（テーブル作成）"""
    Base.metadata.create_all(bind=engine)
    print("データベースの初期化が完了しました。")


if __name__ == "__main__":
    init_db()



