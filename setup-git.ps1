# GitHubへのアップロード用セットアップスクリプト (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "GitHubアップロード用セットアップ" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Gitリポジトリの初期化
Write-Host "1. Gitリポジトリを初期化しています..." -ForegroundColor Yellow
git init

# ブランチ名をmainに設定
Write-Host "2. ブランチ名をmainに設定しています..." -ForegroundColor Yellow
git branch -M main

# ファイルを追加
Write-Host "3. ファイルを追加しています..." -ForegroundColor Yellow
git add .

# 初回コミット
Write-Host "4. 初回コミットを作成しています..." -ForegroundColor Yellow
git commit -m "Initial commit: プロジェクト基盤構築完了

- FastAPIバックエンドの基盤構築
- React + TypeScriptフロントエンドの基盤構築
- データベースモデル設計
- Docker Compose設定
- データベースマイグレーション設定（Alembic）
- プロジェクト構造の作成"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "セットアップ完了！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Cyan
Write-Host "1. GitHubでリポジトリを作成: https://github.com/new" -ForegroundColor White
Write-Host "2. 以下のコマンドを実行:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/your-username/your-repository-name.git" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "詳細は QUICK_START_GITHUB.md を参照してください。" -ForegroundColor Yellow


