# 機械学習パイプライン

競馬予測モデルのデータ前処理・学習・推論に関するドキュメントです。

## 目次

- [構成](#構成)
- [使用方法](#使用方法)
- [再学習手順](#再学習手順)
- [評価指標](#評価指標)
- [特徴量の品質チェック](#特徴量の品質チェック)
- [トラブルシューティング](#トラブルシューティング)

## 構成

```
ml/
  data/           # データ取得と特徴量定義
    repository.py  # データベースからのデータ取得
    schema.py      # 特徴量スキーマ定義
  features/        # 特徴量エンジニアリング
    pipelines.py   # 前処理パイプライン
  quality/         # 品質チェック
    checks.py      # 特徴量の品質チェック
  train.py         # モデル学習スクリプト
  inference/       # 推論サーバー
    server.py      # 推論APIサーバー
    model_loader.py # モデル読み込み
  artifacts/       # 学習成果物（モデル、メタデータなど）
```

## 使用方法

### モデルの学習

#### 基本的な学習（デフォルトパラメータ）

```bash
cd backend
poetry run python -m ml.train
```

#### Optunaを使用したハイパーパラメータチューニング

```bash
poetry run python -m ml.train --use-optuna --n-trials 100
```

#### 日付範囲を指定した学習

```bash
poetry run python -m ml.train --start-date 2024-01-01 --end-date 2024-12-31
```

#### モデルタイプを指定

```bash
# LightGBMを使用（デフォルト）
poetry run python -m ml.train --model-type lightgbm

# XGBoostを使用
poetry run python -m ml.train --model-type xgboost
```

#### 出力ディレクトリを指定

```bash
poetry run python -m ml.train --output-dir ml/artifacts
```

### 学習成果物

学習が完了すると、指定した出力ディレクトリ（デフォルト: `ml/artifacts/`）に以下のファイルが保存されます：

- `model_YYYYMMDD_HHMMSS.pkl`: 学習済みモデル（joblib形式）
- `pipeline_YYYYMMDD_HHMMSS.json`: 特徴量パイプラインの設定
- `preprocessor_YYYYMMDD_HHMMSS.pkl`: 前処理パイプライン（joblib形式）
- `metadata_YYYYMMDD_HHMMSS.json`: 学習メタデータ（評価指標、ハイパーパラメータなど）

### 推論サーバーの起動

```bash
cd ml
poetry run python -m ml.inference.server
```

推論サーバーはデフォルトで `http://localhost:8001` で起動します。

## 再学習手順

### 1. データの準備

データベースに最新のレースデータが取り込まれていることを確認します。

```bash
# データ更新ジョブを手動実行
cd backend
poetry run python -m app.tasks.run_once
```

### 2. 学習の実行

#### 定期再学習（スケジューラ経由）

スケジューラが自動的にデータ更新後にモデル再学習をトリガーします（`TRIGGER_MODEL_TRAINING=true` の場合）。

#### 手動再学習

```bash
cd backend
poetry run python -m ml.train \
  --use-optuna \
  --n-trials 100 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output-dir ml/artifacts
```

### 3. モデルの評価

学習完了後、`metadata_*.json` ファイルを確認して評価指標を確認します。

```bash
cat ml/artifacts/metadata_*.json | jq '.test_metrics'
```

### 4. モデルのデプロイ

#### 推論サーバーへの反映

1. 新しいモデルファイルを推論サーバーがアクセスできる場所に配置
2. 推論サーバーを再起動（モデルローダーが自動的に最新モデルを読み込む）

#### バックエンドAPIの設定

環境変数 `USE_ML_INFERENCE=true` を設定し、推論サーバーのURLを `ML_INFERENCE_BASE_URL` に設定します。

### 5. モデルのロールバック

問題が発生した場合は、以前のモデルファイルに戻すことができます。

```bash
# 以前のモデルファイルを確認
ls -lt ml/artifacts/model_*.pkl

# 推論サーバーの設定を変更して以前のモデルを指定
```

## 評価指標

学習時に以下の評価指標が計算されます：

- **accuracy**: 正解率
- **precision**: 適合率
- **recall**: 再現率
- **f1**: F1スコア
- **auc**: ROC-AUC
- **brier**: Brierスコア
- **log_loss**: 対数損失
- **top1_accuracy**: 的中率（トップ1予測の的中率）

これらの指標は学習データとテストデータの両方で計算され、`metadata_*.json` に保存されます。

## 特徴量の品質チェック

学習前に自動的に特徴量の品質チェックが実行されます：

- **サンプル数の検証**: 十分な学習データがあることを確認
- **欠損値の検証**: 欠損値の割合を確認
- **クラス不均衡の検証**: ターゲット変数の分布を確認
- **分散の検証**: 特徴量の分散を確認

品質チェックに失敗した場合は、エラーメッセージが表示され、学習は中断されます。警告のみの場合は学習は続行されますが、結果を確認することを推奨します。

## トラブルシューティング

### 学習データが見つからない

**症状**: `No training data found` エラー

**対処法**:
1. データベースにレースデータが存在することを確認
2. 日付範囲を調整して再実行
3. データ更新ジョブを実行してデータを取得

### 品質チェックに失敗する

**症状**: `Data quality check failed` エラー

**対処法**:
1. エラーメッセージを確認して問題の特徴量を特定
2. データの前処理を見直す
3. 必要に応じてデータを再取得

### メモリ不足エラー

**症状**: 学習中にメモリエラーが発生

**対処法**:
1. 日付範囲を狭めて学習データ量を減らす
2. バッチサイズを調整（実装に応じて）
3. より軽量なモデル（例: LightGBM）を使用

### 推論サーバーがモデルを読み込めない

**症状**: 推論サーバーが起動しない、またはエラーが発生

**対処法**:
1. モデルファイルのパスを確認
2. モデルファイルの権限を確認
3. 推論サーバーのログを確認

## 依存関係

以下のパッケージが必要です（`backend/pyproject.toml` に定義済み）：

- pandas
- numpy
- scikit-learn
- lightgbm
- xgboost
- optuna
- joblib

## 参考資料

- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Optuna Documentation](https://optuna.readthedocs.io/)

