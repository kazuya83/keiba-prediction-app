# 実行計画 03: DB接続とORMセットアップ

## ゴール
- SQLAlchemyベースのDB接続層を整備し、Alembicでマイグレーションが生成・実行できる状態を構築する。

## 手順
1. `backend/app/db/session.py` を作成し、`SQLAlchemy` セッション生成（`create_engine`, `sessionmaker`）と非同期対応方針を決定。
2. `backend/app/db/base.py` を用意し、ベースメタデータとモデル登録の仕組みを実装。
3. `backend/app/core/config.py` にDB接続文字列の環境変数（`DATABASE_URL`）を追加。
4. `alembic init` を実行し、`backend/alembic/` ディレクトリを生成。`alembic.ini` と `env.py` をFastAPI構成に合わせて更新。
5. 最初の空マイグレーションを作成し、`alembic upgrade head` が成功することを確認。
6. `backend/tests` にテスト用DB（SQLiteメモリなど）を使用する設定を追加し、セッションフィクスチャを実装。

## 成果物
- `backend/app/db/session.py`, `backend/app/db/base.py`。
- Alembic設定済みの`backend/alembic/` ディレクトリと初期マイグレーション。
- DB接続テスト（`pytest`）での接続確認テスト。

## 依存・前提
- 計画02のFastAPI基盤が存在し、`.env` から設定を読み込めること。
- PostgreSQLまたはSQLiteのDockerサービスが動作していること（計画01で定義）。

## リスクと対策
- **リスク**: 非同期と同期DB処理の混在。  
  **対策**: 早期に同期/非同期方針を固定し、ヘルパー関数で統一。
- **リスク**: Alembicでのモデル検出漏れ。  
  **対策**: `backend/app/db/base.py` にモデルをインポート・登録するか、`autogenerate` のターゲットメタデータを明確化。*** End Patch

