#!/bin/bash

# GitHubへのアップロード用セットアップスクリプト

echo "=========================================="
echo "GitHubアップロード用セットアップ"
echo "=========================================="
echo ""

# Gitリポジトリの初期化
echo "1. Gitリポジトリを初期化しています..."
git init

# ブランチ名をmainに設定
echo "2. ブランチ名をmainに設定しています..."
git branch -M main

# ファイルを追加
echo "3. ファイルを追加しています..."
git add .

# 初回コミット
echo "4. 初回コミットを作成しています..."
git commit -m "Initial commit: プロジェクト基盤構築完了

- FastAPIバックエンドの基盤構築
- React + TypeScriptフロントエンドの基盤構築
- データベースモデル設計
- Docker Compose設定
- データベースマイグレーション設定（Alembic）
- プロジェクト構造の作成"

echo ""
echo "=========================================="
echo "セットアップ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. GitHubでリポジトリを作成: https://github.com/new"
echo "2. 以下のコマンドを実行:"
echo "   git remote add origin https://github.com/your-username/your-repository-name.git"
echo "   git push -u origin main"
echo ""
echo "詳細は QUICK_START_GITHUB.md を参照してください。"


