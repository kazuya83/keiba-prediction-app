# 実行計画 04: 認証モデルとユーザーCRUD実装

## ゴール
- ユーザー関連のDBモデルとCRUD APIを実装し、JWT認証の下準備を整える。

## 手順
1. `backend/app/models/user.py` に `User` モデルを定義（`id`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`, `updated_at`）。
2. Alembicマイグレーションを生成し、`users` テーブルを作成。`alembic upgrade head` を実施。
3. `backend/app/schemas/user.py` に `UserCreate`, `UserUpdate`, `UserRead` Pydanticモデルを作成。
4. `backend/app/core/security.py` にパスワードハッシュ（`passlib`）とトークン関連ユーティリティを追加。
5. `backend/app/crud/user.py` にユーザー取得・作成・更新の関数を実装。
6. `backend/app/api/routers/users.py` に `/api/users` 系エンドポイント（管理者用ユーザー作成、自己参照取得/更新）を実装し、ルータ登録。
7. `backend/tests/api/test_users.py` でユーザーCRUDとバリデーションの単体テストを作成。

## 成果物
- `User` モデルと対応するCRUD/スキーマ。
- `/api/users` の基本エンドポイント（認証未実装のため一時的にオープンでも可）。
- ユーザー作成・取得テストが `pytest` で成功。

## 依存・前提
- 計画03でDB接続とAlembicが整備済み。
- `passlib[bcrypt]` など必要ライブラリを `pyproject.toml` に追加済み。

## リスクと対策
- **リスク**: パスワード平文保存。  
  **対策**: `hashed_password` のみ保存するユニットテストを追加。
- **リスク**: メールアドレス重複。  
  **対策**: DBレベルでユニーク制約を設定し、例外処理を統一。*** End Patch

