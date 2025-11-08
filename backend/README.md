# Backend

FastAPI をベースにした REST API サービスです。Poetry で依存関係を管理します。

## セットアップ

```bash
poetry install --no-root
poetry run uvicorn app.main:app --reload
```

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

