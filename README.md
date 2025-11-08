# Keiba Prediction App Monorepo

競馬予測アプリケーションのモノレポです。バックエンド（Python/FastAPI想定）、フロントエンド（React/TypeScript）、機械学習パイプライン、インフラ構成を同一リポジトリで管理します。

## リポジトリ構成

- `backend/`: FastAPI ベースの REST API。Poetry で依存管理。
- `frontend/`: React + TypeScript アプリ。pnpm で依存管理。
- `ml/`: 機械学習モデル学習・推論コード。
- `infra/`: インフラ構成定義（IaC、Terraform 等の想定）。
- `plan/`: 実行計画ドキュメント。
- `rule/`: コーディング規約等のドキュメント。

## 前提ツール

- Python 3.11 以上
- [Poetry](https://python-poetry.org/) 1.8 以上
- Node.js 20.x
- [pnpm](https://pnpm.io/) 9 以上
- Docker & Docker Compose

## セットアップ手順

1. Poetry と pnpm をインストール  
   - `pipx install poetry`  
   - `corepack enable && corepack prepare pnpm@latest --activate`
2. 依存関係の初期化
   - `poetry install --no-root`（`backend/` ディレクトリで実行）
   - `pnpm install`（`frontend/` ディレクトリで実行）
3. 開発用 Docker コンテナの起動  
   - `docker-compose up -d`

## Make コマンド

主要な開発コマンドは `Makefile` にまとめています。

- `make setup`: Python/Node 依存関係をインストール
- `make format`: 各言語のフォーマッタを実行
- `make lint`: 静的解析を実行
- `make test`: テストスイートを実行
- `make up`: Docker Compose を起動
- `make down`: Docker Compose を停止

## 追加メモ

- 詳細なコーディング規約は `rule/coding-guidelines.md` を参照してください。
- 要件・仕様は `requirements.md` に記載しています。

