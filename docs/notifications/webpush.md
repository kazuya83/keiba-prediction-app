# Web Push / VAPID 設定手順

通知 API でブラウザ Push を利用するためには VAPID 鍵の生成と設定が必要です。以下の手順で鍵を生成し、環境変数に登録してください。

## 1. 依存パッケージのインストール

バックエンドの依存に `pywebpush` を追加しています。まだインストールしていない場合は次のコマンドを実行します。

```bash
cd backend
poetry install
```

## 2. 鍵の生成

`backend/scripts/generate_vapid_keys.py` を利用して鍵を生成します。

```bash
cd backend
poetry run python scripts/generate_vapid_keys.py
```

実行すると以下の情報が出力されます。

- `VAPID_PUBLIC_KEY`
- `VAPID_PRIVATE_KEY`
- `VAPID_CLAIMS_SUBJECT`（ブラウザに通知する連絡先。`mailto:` 形式を推奨）

## 3. 環境変数への設定

生成した値を `.env` または実行環境の環境変数に設定します。

```
NOTIFICATION_VAPID_PUBLIC_KEY=生成した公開鍵
NOTIFICATION_VAPID_PRIVATE_KEY=生成した秘密鍵
NOTIFICATION_VAPID_SUBJECT=mailto:notify@example.com
```

FastAPI アプリケーションはこれらの環境変数を読み込み、`PyWebPushSender` へ渡します。Push を利用しない場合は設定不要ですが、API から `enable_push=true` を受け付けるときには鍵が必要です。

## 4. フロントエンドへの公開鍵提供

公開鍵はクライアントが購読登録を行う際に必要になるため、`GET /api/notifications/settings` などのエンドポイントを追加して公開鍵を返すか、既存の設定 API レスポンスに `vapidPublicKey` を含める運用を推奨します。本計画ではバックエンド内部に公開鍵を保持しているため、必要に応じてレスポンスへ追加してください。

## 5. Push 購読の登録

フロントエンドは以下の情報をバックエンドに送信する必要があります。

- `push_endpoint`
- `push_p256dh`
- `push_auth`

`POST /api/notifications/settings` に上記3つの値を渡し、`enable_push=true` を設定すると Push 配信が有効化されます。

## 6. 運用上の注意

- 鍵の管理は Secrets Manager 等を利用し、リポジトリには含めないでください。
- 鍵を再生成した場合は、既存の購読は無効になるためユーザーに再登録を促す必要があります。
- Push 配信が失敗した場合はバックエンドでリトライしますが、ブラウザが購読を解除している場合はエラーが継続するため、`last_error` フィールドを参考にクリーンアップしてください。


