# バックエンドAPI用Dockerfile（マルチステージビルド）

# ステージ1: ビルドステージ
FROM python:3.11-slim as builder

WORKDIR /build

# システム依存関係のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Poetryのインストール
RUN pip install --no-cache-dir poetry==1.7.1

# 依存関係をインストール
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && (poetry install --only main --no-interaction --no-root || \
        (poetry lock && poetry install --only main --no-interaction --no-root))

# ステージ2: ランタイムステージ
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール（ランタイム用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージからPythonパッケージをコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY app/ /app/app/
COPY alembic.ini /app/alembic.ini
COPY alembic/ /app/alembic/

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# ポートの公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# アプリケーションの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

