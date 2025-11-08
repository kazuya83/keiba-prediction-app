# 実行計画 01: リポジトリ初期化と開発環境構築

## ゴール
- バックエンド/フロントエンド/ML共通で利用できるモノレポ（または複数リポ）構成を決定し、Cursorがローカルで開発を開始できる状態を作る。

## 手順
1. `requirements.md` と `rule/coding-guidelines.md` を参照しつつワークスペース構成を決定（例: `backend/`, `frontend/`, `ml/`, `infra/`）。
2. Git初期化、`.gitignore`（Python、Node.js、Docker、各種IDE）生成。
3. エディタとCLIで共通利用する `Makefile` または `justfile` の雛形を作成（フォーマット、テスト、起動コマンド）。
4. Python仮想環境（`uv`/`poetry`/`pipenv`のいずれか）とNodeパッケージマネージャ（`pnpm`）を設定。
5. Dockerベースの開発用 `docker-compose.yml` の雛形を作成し、主要サービス（API、DB、MLワーカー）の空コンテナを用意。

## 成果物
- ルート直下: `.gitignore`, `README.md`（開発の起動手順を最小限記載）, `Makefile`（または `justfile`）雛形。
- `backend/` と `frontend/` の最低限ディレクトリと仮の `README.md`。
- `docker-compose.yml`（Backend/Frontend/DB/MLのサービス名とポートのみ定義）。

## 依存・前提
- OS: Windows 10 + WSL2またはDocker Desktopが利用可能。
- Python 3.11+ / Node.js 20.x / Docker Engine がインストール済み。

## リスクと対策
- **リスク**: OS差異によるコマンドの不一致。  
  **対策**: すべての起動・ビルド操作をMake/justコマンドに抽象化する。
- **リスク**: 依存ツール未インストール。  
  **対策**: `README.md` に先行インストール手順を記載し、プレチェック用スクリプトを追加。*** End Patch

