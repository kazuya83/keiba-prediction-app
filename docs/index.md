# Keiba Prediction App ドキュメント

競馬予測アプリケーションのドキュメントへようこそ。

## 概要

本アプリケーションは、機械学習を活用した競馬予測システムです。

## ドキュメント構成

### API

- [OpenAPI仕様](./api/openapi.json): APIエンドポイントの仕様

### データベース

- [ER図](./db/er_diagram.png): データベースのER図

### 機械学習

- [パイプライン](./ml/README.md): 機械学習パイプラインの使用方法と再学習手順

### 運用

- [Runbook](./runbook.md): 運用に関する手順書

### UI

- [デザインガイドライン](./ui/style-guide.md): フロントエンドのデザインガイドライン

### 通知

- [Web Push](./notifications/webpush.md): Web Push通知の設定方法

### 画面仕様

各画面の仕様は [画面仕様](./screens/) セクションを参照してください。

## クイックスタート

### 開発環境のセットアップ

```bash
# 依存関係のインストール
make setup

# データベースのマイグレーション
cd backend
poetry run alembic upgrade head

# アプリケーションの起動
docker compose up -d
```

### ドキュメントの生成

```bash
# OpenAPI仕様のエクスポート
cd backend
poetry run python scripts/export_openapi.py

# ER図の生成（オプション）
poetry run python scripts/generate_er_diagram.py

# MkDocsでドキュメントサイトをビルド
mkdocs build

# ローカルでプレビュー
mkdocs serve
```

## コントリビューション

ドキュメントの改善にご協力いただける場合は、Pull Requestをお送りください。

## ライセンス

[ライセンス情報]

