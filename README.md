# 競馬予測アプリケーション

機械学習を活用した競馬予測Webアプリケーション

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

## プロジェクト構成

```
keiba/
├── backend/          # バックエンド（FastAPI）
├── frontend/         # フロントエンド（React + TypeScript）
├── ml/              # 機械学習関連
└── docker-compose.yml
```

## クイックスタート

### Docker Composeを使用した起動（推奨）

#### Windows PowerShellでの文字化け対策

PowerShellで文字化けが発生する場合は、以下のコマンドでエンコーディングを設定してください：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

#### Docker Composeのコマンド

Docker Compose V2を使用している場合（Docker Desktopに含まれています）、`docker compose`（ハイフンなし）を使用してください。
V1を使用している場合は`docker-compose`（ハイフンあり）を使用してください。

```bash
# 1. リポジトリのクローン
git clone https://github.com/kazuya83/keiba-prediction-app
cd keiba

# 2. 環境変数ファイルの作成（必要に応じて編集）
# .envファイルは既にdocker-compose.ymlに設定済み

# 3. Docker Composeでサービスを起動
# Docker Compose V2の場合
docker compose up -d
# または Docker Compose V1の場合
docker-compose up -d

# 4. データベースマイグレーションの実行
docker compose exec backend alembic upgrade head
# または
docker-compose exec backend alembic upgrade head

# 5. サービスへのアクセス
# フロントエンド: http://localhost:3000
# バックエンドAPI: http://localhost:8000
# APIドキュメント: http://localhost:8000/docs
```

### ログの確認

```bash
# すべてのサービスのログ
docker compose logs -f
# または
docker-compose logs -f

# 特定のサービスのログ
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### サービスの停止

```bash
# サービスの停止
docker compose down
# または
docker-compose down

# データベースも含めて完全に削除
docker compose down -v
# または
docker-compose down -v
```

## セットアップ

### 前提条件

- Docker & Docker Compose（推奨）
- Node.js 18+（ローカル開発用）
- Python 3.11+（ローカル開発用）
- PostgreSQL 15+（ローカル開発用）

### ローカル開発

#### バックエンド

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# データベースマイグレーション
alembic upgrade head

# サーバーの起動
uvicorn app.main:app --reload
```

#### フロントエンド

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

## APIドキュメント

サーバー起動後、以下のURLでAPIドキュメントにアクセスできます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## データベースマイグレーション

### Docker Composeを使用している場合

```bash
# マイグレーションの実行
docker compose exec backend alembic upgrade head
# または
docker-compose exec backend alembic upgrade head

# マイグレーションファイルの作成
docker compose exec backend alembic revision --autogenerate -m "説明"

# マイグレーションのロールバック
docker compose exec backend alembic downgrade -1
```

### ローカル開発の場合

```bash
cd backend

# マイグレーションファイルの作成
alembic revision --autogenerate -m "初期マイグレーション"

# マイグレーションの実行
alembic upgrade head

# マイグレーションのロールバック
alembic downgrade -1
```

## トラブルシューティング

### Dockerがインストールされていない

- Docker Desktopをインストールしてください: https://www.docker.com/products/docker-desktop/
- インストール後、Dockerが起動していることを確認してください
- `docker --version`コマンドでバージョンを確認できます

### Windows PowerShellでの文字化け

PowerShellで文字化けが発生する場合：

```powershell
# エンコーディングをUTF-8に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

または、PowerShellのプロファイル（`$PROFILE`）に上記の設定を追加することで、毎回のセッションで自動的に適用されます。

### docker-composeコマンドが見つからない

- Docker Compose V2（Docker Desktopに含まれています）を使用している場合、`docker compose`（ハイフンなし）を使用してください
- Docker Compose V1を使用している場合、`docker-compose`（ハイフンあり）を使用してください
- `docker compose version`または`docker-compose --version`でインストール状況を確認できます

### データベース接続エラー

- PostgreSQLが起動していることを確認
- `docker-compose.yml`のデータベース接続情報を確認
- 環境変数`DATABASE_URL`が正しく設定されているか確認

### ポートが既に使用されている

- ポート8000（バックエンド）または3000（フロントエンド）が使用されている場合、`docker-compose.yml`でポート番号を変更

### 依存関係のインストールエラー

- Node.jsのバージョンが18以上であることを確認
- Pythonのバージョンが3.11以上であることを確認
- `npm install`または`pip install -r requirements.txt`を再実行

## 開発フェーズ

詳細な開発計画については、[execution_plan.md](./execution_plan.md)を参照してください。

## GitHubへのアップロード

プロジェクトをGitHubにアップロードする場合は、[GITHUB_SETUP.md](./GITHUB_SETUP.md)または[QUICK_START_GITHUB.md](./QUICK_START_GITHUB.md)を参照してください。

## 貢献

プロジェクトへの貢献を歓迎します。IssueやPull Requestをお待ちしています。

## ライセンス

MIT License

