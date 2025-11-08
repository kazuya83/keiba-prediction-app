# 実行計画 02: バックエンド基盤スキャフォールド

## ゴール
- FastAPIベースのバックエンド骨格とテスト/リンタ設定を整備し、以降のAPI機能を拡張できる状態を作る。

## 手順
1. `backend/pyproject.toml` を作成し、`fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic`, `python-dotenv`, `pytest`, `httpx`, `black`, `isort`, `flake8`, `mypy` を依存追加。
2. `backend/app/__init__.py`, `backend/app/main.py` を作成し、`FastAPI` インスタンス、`/health` エンドポイント、例外ハンドラの雛形を追加。
3. `backend/app/core/config.py` に環境変数管理クラスを定義し、`.env.example` を生成。
4. `backend/app/api/routers/__init__.py` と `backend/app/api/deps.py` を用意し、ルータ登録のベースコードを準備。
5. `backend/tests/conftest.py` にテストクライアントフィクスチャを作成し、`pytest` が通ることを確認。
6. `backend/pyproject.toml` に `tool.black`, `tool.isort`, `tool.flake8`, `tool.mypy` の設定を追加し、ルート `Makefile` に `fmt`, `lint`, `test` コマンドを連携。

## 成果物
- `backend/app/main.py` に最小構成のFastAPIアプリ。
- `.env.example` と `.env` の読み込み処理。
- `backend/tests/` で健康チェックを検証するサンプルテスト。

## 依存・前提
- 計画01で仮想環境とMakeファイルが整備済み。
- Python 3.11 仮想環境がアクティブになっていること。

## リスクと対策
- **リスク**: Lint/Format設定の不整合。  
  **対策**: `pre-commit` 導入を検討し、設定ファイルをバージョン管理。
- **リスク**: `.env` の取り扱いミス。  
  **対策**: `.env` は `.gitignore` に含め、`example` ファイルの更新を徹底。*** End Patch

