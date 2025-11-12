# ML

競馬予測モデルのデータ前処理・学習・推論コードを配置する領域です。

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
  artifacts/       # 学習成果物（モデル、メタデータなど）
```

## 使用方法

### モデルの学習

```bash
# 基本的な学習（デフォルトパラメータ）
python -m ml.train

# Optunaを使用したハイパーパラメータチューニング
python -m ml.train --use-optuna --n-trials 100

# 日付範囲を指定
python -m ml.train --start-date 2024-01-01 --end-date 2024-12-31

# モデルタイプを指定（lightgbm または xgboost）
python -m ml.train --model-type xgboost

# 出力ディレクトリを指定
python -m ml.train --output-dir ml/artifacts
```

### 学習成果物

学習が完了すると、`ml/artifacts/` ディレクトリに以下のファイルが保存されます：

- `model_YYYYMMDD_HHMMSS.pkl`: 学習済みモデル（joblib形式）
- `pipeline_YYYYMMDD_HHMMSS.json`: 特徴量パイプラインの設定
- `metadata_YYYYMMDD_HHMMSS.json`: 学習メタデータ（評価指標、ハイパーパラメータなど）

### 評価指標

学習時に以下の評価指標が計算されます：

- **accuracy**: 正解率
- **precision**: 適合率
- **recall**: 再現率
- **f1**: F1スコア
- **auc**: ROC-AUC
- **brier**: Brierスコア
- **log_loss**: 対数損失
- **top1_accuracy**: 的中率（トップ1予測の的中率）

### 特徴量の品質チェック

学習前に自動的に特徴量の品質チェックが実行されます：

- サンプル数の検証
- 欠損値の検証
- クラス不均衡の検証
- 分散の検証

品質チェックに失敗した場合は、エラーメッセージが表示され、学習は中断されます。

## 依存関係

以下のパッケージが必要です（`backend/pyproject.toml` に定義済み）：

- pandas
- numpy
- scikit-learn
- lightgbm
- xgboost
- optuna
- joblib

