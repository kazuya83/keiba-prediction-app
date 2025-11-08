# GitHubへのアップロード手順

このプロジェクトをGitHubにアップロードする手順を説明します。

## 前提条件

- Gitがインストールされていること
- GitHubアカウントを持っていること

## 手順

### 1. Gitリポジトリの初期化

```bash
# プロジェクトルートで実行
git init
```

### 2. ファイルのステージング

```bash
# すべてのファイルをステージング
git add .

# または、個別に追加する場合
git add README.md
git add .gitignore
git add backend/
git add frontend/
git add docker-compose.yml
git add execution_plan.md
git add requirements.md
```

### 3. 初回コミット

```bash
git commit -m "Initial commit: プロジェクト基盤構築完了

- FastAPIバックエンドの基盤構築
- React + TypeScriptフロントエンドの基盤構築
- データベースモデル設計
- Docker Compose設定
- データベースマイグレーション設定（Alembic）
- プロジェクト構造の作成"
```

### 4. GitHubリポジトリの作成

1. GitHubにログイン
2. 右上の「+」をクリック → 「New repository」を選択
3. リポジトリ名を入力（例: `keiba-prediction-app`）
4. 説明を入力（オプション）
5. プライベートまたはパブリックを選択
6. **「Initialize this repository with a README」はチェックしない**（既にREADMEがあるため）
7. 「Create repository」をクリック

### 5. リモートリポジトリの追加

```bash
# GitHubで作成したリポジトリのURLを指定
# 例: https://github.com/your-username/keiba-prediction-app.git
git remote add origin https://github.com/your-username/your-repository-name.git

# リモートリポジトリの確認
git remote -v
```

### 6. ブランチ名の設定（オプション）

```bash
# メインブランチ名を設定（GitHubのデフォルトに合わせる）
git branch -M main
```

### 7. プッシュ

```bash
# 初回プッシュ
git push -u origin main
```

### 8. 認証

GitHubへのプッシュ時に認証が求められる場合：

- **Personal Access Token (PAT) を使用する場合**:
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. 「Generate new token」をクリック
  3. 必要な権限を選択（repo）
  4. トークンを生成し、コピー
  5. パスワードの代わりにトークンを入力

- **SSHを使用する場合**:
  ```bash
  # SSHキーの生成（まだ持っていない場合）
  ssh-keygen -t ed25519 -C "your_email@example.com"
  
  # SSHキーをGitHubに登録
  # GitHub → Settings → SSH and GPG keys → New SSH key
  
  # リモートURLをSSHに変更
  git remote set-url origin git@github.com:your-username/your-repository-name.git
  ```

## 今後のコミット手順

```bash
# 変更を確認
git status

# 変更をステージング
git add .

# コミット
git commit -m "コミットメッセージ"

# プッシュ
git push
```

## 注意事項

### アップロード前に確認すべきこと

1. **機密情報が含まれていないか確認**
   - `.env`ファイルは`.gitignore`に含まれているか確認
   - APIキーやパスワードがコードに含まれていないか確認
   - `SECRET_KEY`などの機密情報は環境変数で管理

2. **大きなファイルが含まれていないか確認**
   - 機械学習モデル（`.pkl`, `.h5`, `.joblib`）は`.gitignore`に含まれているか確認
   - `node_modules`や`__pycache__`が含まれていないか確認

3. **不要なファイルが含まれていないか確認**
   - エディタの設定ファイル（`.vscode/`, `.idea/`）は必要に応じて除外

### .gitignoreで除外されているファイル

- `.env`ファイル（環境変数）
- `venv/`, `env/`（Python仮想環境）
- `node_modules/`（Node.js依存関係）
- `__pycache__/`, `*.pyc`（Pythonキャッシュ）
- `*.log`（ログファイル）
- `*.db`, `*.sqlite`（データベースファイル）
- `ml/models/*.pkl`, `ml/models/*.joblib`（機械学習モデル）
- `.DS_Store`, `Thumbs.db`（OS固有ファイル）

## トラブルシューティング

### プッシュが拒否される場合

```bash
# リモートの変更を取得
git pull origin main --rebase

# 再度プッシュ
git push -u origin main
```

### 大きなファイルを誤ってコミットしてしまった場合

```bash
# Git履歴から削除（注意: 履歴が書き換わります）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch ファイルパス" \
  --prune-empty --tag-name-filter cat -- --all

# 強制プッシュ（チームメンバーと相談してから実行）
git push origin --force --all
```

### コミットを取り消す場合

```bash
# 最後のコミットを取り消す（変更は残る）
git reset --soft HEAD~1

# 最後のコミットを完全に取り消す（変更も削除）
git reset --hard HEAD~1
```

## 参考リンク

- [Git公式ドキュメント](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com/)
- [GitHub CLI](https://cli.github.com/)（コマンドラインからGitHubを操作）


