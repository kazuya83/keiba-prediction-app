# 実行計画 05: JWT認証とOAuthログイン導入

## ゴール
- メールアドレス/パスワードによるログインとGoogle/Twitter等のOAuthログインを実装し、JWTでセッション管理を行う。

## 手順
1. `backend/app/core/security.py` にJWT署名・検証処理を追加（`python-jose` など利用）。
2. `backend/app/schemas/auth.py` に `Token`, `LoginRequest`, `OAuthCallback` などのスキーマを定義。
3. `backend/app/api/routers/auth.py` を作成し、`POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout` を実装。
4. `backend/app/api/deps.py` に `get_current_user`, `get_current_active_user`, `get_current_admin` などの依存関数を用意。
5. OAuthログイン用に `authlib` または `requests-oauthlib` を導入し、ソーシャルログイン用エンドポイント（例: `GET /api/auth/google/login`, `GET /api/auth/google/callback`）を実装。
6. リフレッシュトークンテーブル（`auth_tokens`）を追加し、トークンローテーションと失効処理を実装。
7. `backend/tests/api/test_auth.py` にパスワード/ソーシャル両方のテストケースを記述。

## 成果物
- 認証関連エンドポイントが正常動作し、JWTが付与・検証される。
- `OAuth` クライアントID/シークレットを `.env` で管理し、ドキュメントに利用手順を記述。
- テストでログインフローがカバーされ、`pytest` が通過。

## 依存・前提
- 計画04でユーザーモデルとCRUDが整備されている。
- `.env` にJWT秘密鍵、OAuthクライアント情報が設定済み。

## リスクと対策
- **リスク**: OAuthプロバイダのリダイレクトURL不一致。  
  **対策**: `.env` にコールバックURLを定義し、回帰テストを追加。
- **リスク**: JWT秘密鍵漏洩。  
  **対策**: 秘密情報は環境変数で管理し、キー更新手順をドキュメント化。

