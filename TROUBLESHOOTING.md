# トラブルシューティング

## PowerShellスクリプト実行エラー

### エラー内容
```
.\setup-git.ps1 : このシステムではスクリプトの実行が無効になっているため、ファイルを読み込むことができません。
```

### 原因
Windows PowerShellのセキュリティ機能（実行ポリシー）により、スクリプトの実行がデフォルトで無効になっています。

### 解決策

#### 方法1: 実行ポリシーを一時的に変更（推奨・最も安全）

現在のセッションのみで実行ポリシーを変更します：

```powershell
# 現在の実行ポリシーを確認
Get-ExecutionPolicy

# 実行ポリシーを一時的に変更（現在のセッションのみ）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# スクリプトを実行
.\setup-git.ps1
```

#### 方法2: スクリプトをバイパスして実行

実行ポリシーをバイパスして実行します：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-git.ps1
```

#### 方法3: 実行ポリシーを永続的に変更（注意が必要）

システム全体で実行ポリシーを変更します（管理者権限が必要）：

```powershell
# 管理者としてPowerShellを起動して実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**注意**: この方法はシステム全体に影響するため、セキュリティリスクを理解した上で実行してください。

#### 方法4: コマンドを直接実行（最も安全）

スクリプトの内容を直接コマンドラインで実行します：

```powershell
# Gitリポジトリの初期化
git init

# ブランチ名をmainに設定
git branch -M main

# ファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit: プロジェクト基盤構築完了

- FastAPIバックエンドの基盤構築
- React + TypeScriptフロントエンドの基盤構築
- データベースモデル設計
- Docker Compose設定
- データベースマイグレーション設定（Alembic）
- プロジェクト構造の作成"
```

その後、GitHubでリポジトリを作成し：

```powershell
# リモートリポジトリを追加
git remote add origin https://github.com/kazuya83/keiba-prediction-app.git

# プッシュ
git push -u origin main
```

### 実行ポリシーの説明

- **Restricted**: すべてのスクリプトが実行できない（デフォルト）
- **RemoteSigned**: ローカルのスクリプトは実行可能、リモートのスクリプトは署名が必要
- **Unrestricted**: すべてのスクリプトが実行可能（セキュリティリスクあり）

### 推奨事項

1. **方法1（一時的な変更）** または **方法4（直接実行）** を推奨します
2. 実行ポリシーを永続的に変更する場合は、セキュリティリスクを理解した上で実行してください
3. スクリプトの内容を確認してから実行することをお勧めします


