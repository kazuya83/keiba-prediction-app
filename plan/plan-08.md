# 実行計画 08: 予測履歴・統計API実装

## ゴール
- ユーザーごとの予測履歴、的中率や回収率などの統計を扱うAPIを実装する。

## 手順
1. `backend/app/models/prediction.py`, `prediction_history.py` を作成し、予測結果と履歴保存用テーブルを定義。
2. Alembicマイグレーションでテーブルを追加し、`prediction_at`, `result`, `odds`, `payout` など必要な列とインデックスを設定。
3. `backend/app/schemas/prediction.py` にリクエスト/レスポンススキーマを追加。
4. `backend/app/crud/prediction.py` に履歴保存、統計集計（的中率/回収率）の処理を実装。
5. `backend/app/api/routers/predictions.py` に `GET /api/predictions`, `GET /api/predictions/{id}`, `GET /api/predictions/{id}/compare` を追加し、JWT認証でユーザーを識別。
6. 集計処理をSQLまたはSQLAlchemyで実装し、パフォーマンスが問題ないか確認。必要に応じてビュー/マテリアライズドビューを検討。
7. `backend/tests/api/test_prediction_history.py` を実装し、履歴保存・統計取得のテストを作成。

## 成果物
- 予測履歴テーブルとCRUD、APIエンドポイント。
- 使用頻度の高い統計処理が`pytest`で検証済み。
- OpenAPIにサマリー説明と例示レスポンスが追加。

## 依存・前提
- 計画05のJWT認証が完了し、ユーザー識別が可能。
- レース参照データ（計画07）が存在し、予測データと関連付けできる。

## リスクと対策
- **リスク**: 統計集計のパフォーマンス低下。  
  **対策**: SQL最適化やキャッシュ導入、集計テーブルの検討。
- **リスク**: 履歴データ肥大によるストレージ圧迫。  
  **対策**: 古いデータのアーカイブや、期間指定取得の実装。

