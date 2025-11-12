# 運用Runbook

本ドキュメントは、競馬予測アプリケーションの運用に関する手順をまとめたものです。

## 目次

- [ジョブ管理](#ジョブ管理)
- [通知設定](#通知設定)
- [ログ確認](#ログ確認)
- [データベース管理](#データベース管理)
- [トラブルシューティング](#トラブルシューティング)

## ジョブ管理

### データ更新ジョブの実行

#### スケジューラの起動

データ更新ジョブは、スケジューラによって自動実行されます。スケジューラを起動するには：

```bash
cd backend
poetry run python -m app.tasks.scheduler_main
```

または、Makefileを使用：

```bash
make run-scheduler
```

#### 手動実行

データ更新ジョブを手動で実行する場合：

```bash
cd backend
poetry run python -m app.tasks.run_once
```

または、Makefileを使用：

```bash
make run-once
```

#### ジョブの設定

ジョブの設定は環境変数で制御されます：

- `DATA_UPDATE_CRON`: データ更新ジョブのcron表現（デフォルト: `0 3 * * *` = 毎日3時）
- `DATA_UPDATE_TIMEZONE`: タイムゾーン（デフォルト: `Asia/Tokyo`）
- `TRIGGER_MODEL_TRAINING`: データ更新後にモデル再学習をトリガーするか（デフォルト: `true`）
- `NOTIFY_ON_SUCCESS`: ジョブ成功時も通知を送信するか（デフォルト: `false`）
- `NOTIFY_ON_PARTIAL`: ジョブ部分成功時も通知を送信するか（デフォルト: `true`）
- `NOTIFY_ON_FAILURE`: ジョブ失敗時も通知を送信するか（デフォルト: `true`）

### ジョブの再実行

#### 失敗したジョブの再実行

1. ログを確認して失敗原因を特定
2. 問題を修正
3. 手動でジョブを再実行

```bash
cd backend
poetry run python -m app.tasks.run_once
```

#### 特定のレースデータのみ更新

```python
from app.tasks.jobs import run_data_update_job
from app.schemas.scraping import ScrapingSite

# 特定のレースIDを指定して実行
result = await run_data_update_job(
    sites=[ScrapingSite.NETKEIBA],
    race_ids=["20240101_01"],
    trigger_model_training=False,
)
```

### モデル再学習の実行

モデル再学習は、データ更新ジョブの完了後に自動的にトリガーされます（`TRIGGER_MODEL_TRAINING=true` の場合）。

手動で実行する場合：

```bash
cd backend
poetry run python -m ml.train \
  --use-optuna \
  --n-trials 100 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31
```

詳細は [機械学習パイプラインのドキュメント](./ml/README.md) を参照してください。

## 通知設定

### Web Push通知の設定

#### VAPID鍵の生成

```bash
cd backend
poetry run python scripts/generate_vapid_keys.py
```

生成された公開鍵と秘密鍵を環境変数に設定：

```bash
NOTIFICATION_VAPID_PUBLIC_KEY=<公開鍵>
NOTIFICATION_VAPID_PRIVATE_KEY=<秘密鍵>
NOTIFICATION_VAPID_SUBJECT=mailto:admin@example.com
```

#### 通知設定の確認

管理者ユーザーは、フロントエンドの設定画面から通知設定を確認・変更できます。

### 通知の送信確認

#### 管理者への通知

ジョブの実行結果は、管理者ユーザー（`is_superuser=true`）に自動的に通知されます。

通知の送信状況は、データベースの `notifications` テーブルで確認できます：

```sql
SELECT * FROM notifications 
WHERE category = 'system' 
ORDER BY created_at DESC 
LIMIT 10;
```

#### 通知の再送信

通知の再送信が必要な場合：

```python
from app.services.notification_dispatcher import NotificationDispatcher
from app.models.notification import NotificationCategory
from app.services.notification_dispatcher import NotificationEvent

# 通知ディスパッチャを初期化
dispatcher = NotificationDispatcher(db, ...)

# 通知イベントを作成
event = NotificationEvent(
    user_id=admin_user_id,
    category=NotificationCategory.SYSTEM,
    title="通知タイトル",
    message="通知メッセージ",
    metadata={},
)

# 通知を送信
dispatcher.dispatch_event(event)
```

## ログ確認

### アプリケーションログ

#### ログレベルの確認

アプリケーションのログレベルは、環境変数 `LOG_LEVEL` で制御されます（デフォルト: `INFO`）。

#### ログの確認方法

##### 1. 標準出力/標準エラー出力

アプリケーションを直接起動している場合、ログは標準出力に出力されます。

##### 2. 管理者向けログストレージ

エラーログは、アプリケーション内の `AdminLogStorage` に保存されます。管理者APIエンドポイントから確認できます：

```bash
# 管理者APIでログを取得（認証が必要）
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/admin/logs
```

##### 3. Dockerコンテナのログ

Docker Composeを使用している場合：

```bash
# バックエンドのログを確認
docker compose logs backend

# リアルタイムでログを確認
docker compose logs -f backend

# 特定の時間範囲のログを確認
docker compose logs --since 1h backend
```

##### 4. ログファイル

ログファイルが設定されている場合、指定されたパスから確認できます。

### ログレベルの説明

- `DEBUG`: デバッグ情報（開発時のみ）
- `INFO`: 一般的な情報（ジョブ開始・完了など）
- `WARNING`: 警告（部分的な失敗など）
- `ERROR`: エラー（処理の失敗）
- `CRITICAL`: 重大なエラー（システム全体に影響）

### ログのフィルタリング

#### エラーログのみ確認

```bash
docker compose logs backend | grep ERROR
```

#### 特定のジョブのログを確認

```bash
docker compose logs backend | grep "data_update"
```

#### 時間範囲でフィルタリング

```bash
docker compose logs --since 2024-01-01T00:00:00 --until 2024-01-02T00:00:00 backend
```

## データベース管理

### データベース接続の確認

```bash
# データベースに接続
docker compose exec db psql -U postgres -d keiba

# または、直接接続
psql $DATABASE_URL
```

### マイグレーションの実行

```bash
cd backend
poetry run alembic upgrade head
```

### マイグレーションの作成

```bash
cd backend
poetry run alembic revision --autogenerate -m "マイグレーション名"
```

### データベースのバックアップ

```bash
# バックアップを作成
docker compose exec db pg_dump -U postgres keiba > backup_$(date +%Y%m%d_%H%M%S).sql

# バックアップから復元
docker compose exec -T db psql -U postgres keiba < backup_20240101_120000.sql
```

### データベースの状態確認

```sql
-- テーブル一覧
\dt

-- 特定のテーブルのレコード数
SELECT COUNT(*) FROM races;
SELECT COUNT(*) FROM predictions;

-- 最近のレースデータ
SELECT * FROM races ORDER BY race_date DESC LIMIT 10;

-- 最近の予測データ
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;
```

## トラブルシューティング

### ジョブが実行されない

#### 確認事項

1. スケジューラが起動しているか確認
2. cron表現が正しいか確認
3. タイムゾーン設定が正しいか確認
4. ログを確認してエラーがないか確認

#### 対処法

```bash
# スケジューラのログを確認
docker compose logs scheduler

# 手動でジョブを実行して動作確認
make run-once
```

### データ更新が失敗する

#### 確認事項

1. スクレイピング対象サイトがアクセス可能か確認
2. ネットワーク接続を確認
3. レート制限に引っかかっていないか確認
4. データベース接続を確認

#### 対処法

1. ログを確認してエラーメッセージを特定
2. スクレイピングポリシーを確認（`app/scraping/policy.py`）
3. 必要に応じてリトライ間隔を調整
4. 特定のレースIDのみ再実行

### 通知が送信されない

#### 確認事項

1. VAPID鍵が正しく設定されているか確認
2. 管理者ユーザーが存在するか確認
3. 通知設定が有効になっているか確認
4. Web Pushのエンドポイントが有効か確認

#### 対処法

1. VAPID鍵を再生成
2. 管理者ユーザーの通知設定を確認
3. ブラウザの通知許可を確認
4. 通知の送信ログを確認

### モデル推論が失敗する

#### 確認事項

1. 推論サーバーが起動しているか確認
2. モデルファイルが存在するか確認
3. モデルファイルのパスが正しいか確認
4. 推論サーバーのログを確認

#### 対処法

1. 推論サーバーを再起動
2. モデルファイルのパスを確認
3. モデルファイルの権限を確認
4. 推論サーバーのログを確認

### パフォーマンスの問題

#### 確認事項

1. データベースのクエリパフォーマンスを確認
2. キャッシュの設定を確認
3. リソース使用量を確認（CPU、メモリ、ディスク）

#### 対処法

1. スロークエリログを確認
2. インデックスを追加
3. キャッシュのTTLを調整
4. リソースをスケールアップ

## 緊急時の対応

### システム全体の停止

```bash
# すべてのサービスを停止
docker compose down

# データベースを保持したまま停止
docker compose stop
```

### データベースのロールバック

```bash
# 特定のマイグレーションまでロールバック
cd backend
poetry run alembic downgrade <revision>

# すべてのマイグレーションをロールバック
poetry run alembic downgrade base
```

### 緊急時の連絡先

- テックリード: [連絡先情報]
- インフラ担当: [連絡先情報]
- オンコール: [連絡先情報]

## 定期メンテナンス

### 毎日

- ジョブの実行状況を確認
- エラーログを確認
- 通知の送信状況を確認

### 毎週

- データベースのバックアップを確認
- ディスク使用量を確認
- パフォーマンスメトリクスを確認

### 毎月

- ログのアーカイブ
- データベースの最適化（VACUUM、ANALYZE）
- セキュリティアップデートの確認

