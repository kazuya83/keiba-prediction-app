# 実行計画 10: 通知APIとバックグラウンドジョブ実装

## ゴール
- 予測完了やレース結果確定時にユーザーへ通知を送るためのAPIとジョブ処理を実装する。

## 手順
1. `backend/app/models/notification.py` と `notification_setting.py` を作成し、通知メッセージとユーザー設定のテーブルを定義。
2. Alembicマイグレーションでテーブルを作成し、ユーザーID・レースIDにインデックスを付与。
3. `backend/app/api/routers/notifications.py` に通知一覧取得、既読化、設定更新のエンドポイントを実装（`GET /api/notifications`, `PUT /api/notifications/{id}/read`, `POST /api/notifications/settings`）。
4. Web Push対応が可能な場合は `pywebpush` を導入し、VAPID鍵生成スクリプトとフロントエンドへの公開鍵提供APIを実装。
5. 予測完了・レース結果確定イベントを受け取るバックグラウンドタスクを `backend/app/services/notification_dispatcher.py` に実装し、キューシステムと連携。
6. 通知失敗時のリトライ処理と、ユーザー設定に基づくフィルタリングロジックを実装。
7. `backend/tests/api/test_notifications.py` とサービス層テストで、通知生成・既読処理・設定変更を検証。

## 成果物
- 通知関連APIとバックグラウンドジョブが正常動作する。
- VAPID鍵の生成/管理手順がドキュメント化される。
- テストスイートが通知機能をカバー。

## 依存・前提
- 計画09の予測実行および計画08の履歴処理が完了している。
- キュー/ワーカー基盤（CeleryやRedis）が `docker-compose` で利用可能。

## リスクと対策
- **リスク**: Web Push未対応ブラウザで通知不可。  
  **対策**: アプリ内通知をデフォルトとし、Pushはオプション提供。
- **リスク**: 通知重複送信。  
  **対策**: イベントIDによる重複排除とジョブの冪等性担保。

