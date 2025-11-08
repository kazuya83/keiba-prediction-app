# Backend

FastAPI をベースにした REST API サービスです。Poetry で依存関係を管理します。

## セットアップ

```bash
poetry install --no-root
poetry run uvicorn app.main:app --reload
```

## 環境変数

`.env` または環境変数で以下を設定してください。

- `JWT_SECRET_KEY`: JWT 署名に使用するシークレットキー
- `JWT_ALGORITHM`: JWT の署名アルゴリズム（既定: `HS256`）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: アクセストークンの有効期限（分）
- `REFRESH_TOKEN_EXPIRE_MINUTES`: リフレッシュトークンの有効期限（分）
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`: Google OAuth 用のクライアント情報

`.env` を更新した後は、アプリケーションの再起動または設定キャッシュのクリアを行ってください。

## 推奨ディレクトリ構成

```
app/
  api/
    routers/
    schemas/
  core/
  services/
  repositories/
  models/
  tasks/
tests/
```

## 使用予定ツール

- FastAPI
- SQLAlchemy / Alembic
- Pydantic
- pytest
- mypy, flake8, black, isort

