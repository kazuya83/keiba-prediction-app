# GitHubへのクイックアップロード手順

## 最も簡単な方法

### 方法A: スクリプトを使用

#### Windows (PowerShell)

**実行ポリシーエラーが発生する場合:**
```powershell
# 方法1: 実行ポリシーを一時的に変更（推奨）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup-git.ps1

# 方法2: バイパスして実行
powershell -ExecutionPolicy Bypass -File .\setup-git.ps1

# 方法3: コマンドを直接実行（最も安全、下記参照）
```

**エラーが発生しない場合:**
```powershell
.\setup-git.ps1
```

**トラブルシューティング:** 詳細は [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) を参照してください。

#### Linux/Mac
```bash
chmod +x setup-git.sh
./setup-git.sh
```

### 方法B: 手動でコマンドを実行

### 1. GitHubでリポジトリを作成
1. https://github.com にログイン
2. 右上の「+」→「New repository」
3. リポジトリ名を入力（例: `keiba-prediction-app`）
4. **「Initialize this repository with a README」はチェックしない**
5. 「Create repository」をクリック

### 2. コマンドを実行

```bash
# Gitリポジトリの初期化
git init

# すべてのファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit: プロジェクト基盤構築完了"

# ブランチ名をmainに設定
git branch -M main

# リモートリポジトリを追加（your-usernameとyour-repository-nameを置き換える）
git remote add origin https://github.com/your-username/your-repository-name.git

# プッシュ
git push -u origin main
```

### 3. 認証
プッシュ時に認証を求められた場合：
- **Personal Access Token (PAT)** を使用
  - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - 「Generate new token」をクリック
  - `repo`権限を選択
  - トークンを生成し、パスワードの代わりに入力

## 詳細な手順

詳細な手順やトラブルシューティングについては、[GITHUB_SETUP.md](./GITHUB_SETUP.md)を参照してください。

## 注意事項

⚠️ **アップロード前に確認**
- `.env`ファイルが含まれていないか（機密情報）
- APIキーやパスワードがコードに含まれていないか
- 大きなファイル（モデルファイルなど）が含まれていないか

✅ **`.gitignore`で除外されるもの**
- `.env`ファイル
- `venv/`, `node_modules/`
- ログファイル、キャッシュファイル
- 機械学習モデルファイル（`.pkl`, `.joblib`など）

