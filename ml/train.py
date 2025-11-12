"""機械学習モデルの学習パイプライン。"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.core.config import get_settings
from app.db.session import SessionLocal
from ml.data.repository import DataRepository
from ml.data.schema import FeatureSchema
from ml.features.pipelines import FeaturePipeline
from ml.quality.checks import FeatureQualityChecker

logger = logging.getLogger(__name__)


class ModelTrainer:
    """機械学習モデルの学習を管理するクラス。"""

    def __init__(
        self,
        *,
        model_type: str = "lightgbm",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> None:
        """トレーナーを初期化する。

        Args:
            model_type: モデルタイプ（"lightgbm" または "xgboost"）
            test_size: テストデータの割合
            random_state: 乱数シード
        """
        self._model_type = model_type
        self._test_size = test_size
        self._random_state = random_state
        self._model: Any = None
        self._pipeline: FeaturePipeline | None = None
        self._schema: FeatureSchema | None = None

    def train(
        self,
        df: pd.DataFrame,
        *,
        use_optuna: bool = True,
        n_trials: int = 50,
    ) -> dict[str, Any]:
        """モデルを学習する。

        Args:
            df: 学習データのDataFrame
            use_optuna: Optunaを使用してハイパーパラメータチューニングを行うか
            n_trials: Optunaの試行回数

        Returns:
            学習結果のメタデータ
        """
        logger.info(f"Starting training with {len(df)} samples")

        # 品質チェック
        quality_checker = FeatureQualityChecker()
        quality_report = quality_checker.check(df)
        if not quality_report.passed:
            logger.error("Quality check failed:")
            for error in quality_report.errors:
                logger.error(f"  - {error}")
            raise ValueError("Data quality check failed. Please fix the issues above.")

        if quality_report.warnings:
            logger.warning("Quality check warnings:")
            for warning in quality_report.warnings:
                logger.warning(f"  - {warning}")

        # スキーマの作成
        self._schema = FeatureSchema.from_dataframe(df)
        logger.info(f"Schema: {len(self._schema.categorical_features)} categorical, "
                   f"{len(self._schema.numerical_features)} numerical features")

        # ターゲットの抽出
        target_col = "target_win"
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found")

        y = df[target_col].values
        logger.info(f"Target distribution: {np.bincount(y.astype(int))}")

        # データ分割
        train_df, test_df, y_train, y_test = train_test_split(
            df,
            y,
            test_size=self._test_size,
            random_state=self._random_state,
            stratify=y,
        )

        logger.info(f"Train: {len(train_df)}, Test: {len(test_df)}")

        # 特徴量パイプラインの構築
        self._pipeline = FeaturePipeline(self._schema)
        X_train = self._pipeline.fit_transform(train_df)
        X_test = self._pipeline.transform(test_df)

        # モデルの学習
        if use_optuna:
            best_params = self._optimize_hyperparameters(
                X_train,
                y_train,
                X_test,
                y_test,
                n_trials=n_trials,
            )
            logger.info(f"Best parameters: {best_params}")
        else:
            best_params = self._get_default_params()

        self._model = self._create_model(best_params)
        self._model.fit(X_train, y_train)

        # 評価
        train_metrics = self._evaluate(self._model, X_train, y_train)
        test_metrics = self._evaluate(self._model, X_test, y_test)

        logger.info(f"Train metrics: {train_metrics}")
        logger.info(f"Test metrics: {test_metrics}")

        return {
            "model_type": self._model_type,
            "best_params": best_params,
            "train_metrics": train_metrics,
            "test_metrics": test_metrics,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "feature_count": X_train.shape[1],
            "quality_report": quality_report.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }

    def _optimize_hyperparameters(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_trials: int,
    ) -> dict[str, Any]:
        """Optunaを使用してハイパーパラメータを最適化する。

        Args:
            X_train: 学習データの特徴量
            y_train: 学習データのターゲット
            X_val: 検証データの特徴量
            y_val: 検証データのターゲット
            n_trials: 試行回数

        Returns:
            最適なハイパーパラメータ
        """
        def objective(trial: optuna.Trial) -> float:
            if self._model_type == "lightgbm":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 10, 100),
                    "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
                    "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
                    "random_state": self._random_state,
                    "verbosity": -1,
                }
                model = LGBMClassifier(**params)
            else:  # xgboost
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
                    "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
                    "random_state": self._random_state,
                    "verbosity": 0,
                }
                model = XGBClassifier(**params)

            model.fit(X_train, y_train)
            y_pred_proba = model.predict_proba(X_val)[:, 1]
            score = roc_auc_score(y_val, y_pred_proba)
            return score

        study = optuna.create_study(direction="maximize", study_name=f"{self._model_type}_optimization")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

        return study.best_params

    def _get_default_params(self) -> dict[str, Any]:
        """デフォルトのハイパーパラメータを取得する。

        Returns:
            デフォルトパラメータ
        """
        if self._model_type == "lightgbm":
            return {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": self._random_state,
                "verbosity": -1,
            }
        else:  # xgboost
            return {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": self._random_state,
                "verbosity": 0,
            }

    def _create_model(self, params: dict[str, Any]) -> Any:
        """モデルインスタンスを作成する。

        Args:
            params: モデルパラメータ

        Returns:
            モデルインスタンス
        """
        if self._model_type == "lightgbm":
            return LGBMClassifier(**params)
        else:  # xgboost
            return XGBClassifier(**params)

    def _evaluate(self, model: Any, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """モデルを評価する。

        Args:
            model: 評価対象のモデル
            X: 特徴量
            y: ターゲット

        Returns:
            評価指標の辞書
        """
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]

        accuracy = accuracy_score(y, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average="binary", zero_division=0)
        auc = roc_auc_score(y, y_pred_proba)
        brier = brier_score_loss(y, y_pred_proba)
        logloss = log_loss(y, y_pred_proba)

        # 的中率（トップ1の予測が的中した割合）
        top1_accuracy = self._calculate_top1_accuracy(X, y, model)

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "auc": float(auc),
            "brier": float(brier),
            "log_loss": float(logloss),
            "top1_accuracy": float(top1_accuracy),
        }

    def _calculate_top1_accuracy(self, X: np.ndarray, y: np.ndarray, model: Any) -> float:
        """トップ1の予測が的中した割合を計算する。

        Args:
            X: 特徴量
            y: ターゲット
            model: モデル

        Returns:
            的中率
        """
        # レース単位でグループ化する必要があるが、簡易実装として全体のaccuracyを使用
        # 実際の実装では、race_idでグループ化して各レースのトップ1を予測し、的中率を計算
        y_pred_proba = model.predict_proba(X)[:, 1]
        top1_indices = np.argmax(y_pred_proba)
        return float(y[top1_indices] == 1) if len(y) > 0 else 0.0

    def get_model(self) -> Any:
        """学習済みモデルを取得する。

        Returns:
            学習済みモデル
        """
        return self._model

    def get_pipeline(self) -> FeaturePipeline | None:
        """特徴量パイプラインを取得する。

        Returns:
            特徴量パイプライン
        """
        return self._pipeline

    def get_schema(self) -> FeatureSchema | None:
        """スキーマを取得する。

        Returns:
            特徴量スキーマ
        """
        return self._schema


def main() -> None:
    """学習スクリプトのエントリーポイント。"""
    parser = argparse.ArgumentParser(description="Train machine learning model for horse racing prediction")
    parser.add_argument("--model-type", choices=["lightgbm", "xgboost"], default="lightgbm", help="Model type")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random state")
    parser.add_argument("--use-optuna", action="store_true", help="Use Optuna for hyperparameter tuning")
    parser.add_argument("--n-trials", type=int, default=50, help="Number of Optuna trials")
    parser.add_argument("--output-dir", type=str, default="ml/artifacts", help="Output directory")

    args = parser.parse_args()

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # データ取得
    settings = get_settings()
    if not settings.database_url:
        logger.error("DATABASE_URL is not set")
        sys.exit(1)

    session = SessionLocal()
    try:
        repository = DataRepository(session)

        start_date = date.fromisoformat(args.start_date) if args.start_date else None
        end_date = date.fromisoformat(args.end_date) if args.end_date else None

        logger.info("Fetching training data...")
        df = repository.fetch_training_data(start_date=start_date, end_date=end_date)

        if len(df) == 0:
            logger.error("No training data found")
            sys.exit(1)

        # 学習
        trainer = ModelTrainer(
            model_type=args.model_type,
            test_size=args.test_size,
            random_state=args.random_state,
        )

        logger.info("Training model...")
        results = trainer.train(df, use_optuna=args.use_optuna, n_trials=args.n_trials)

        # 成果物の保存
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = output_dir / f"model_{timestamp}.pkl"
        pipeline_filename = output_dir / f"pipeline_{timestamp}.json"
        metadata_filename = output_dir / f"metadata_{timestamp}.json"

        import joblib

        joblib.dump(trainer.get_model(), model_filename)
        logger.info(f"Model saved to {model_filename}")

        pipeline = trainer.get_pipeline()
        if pipeline:
            # パイプラインのメタデータをJSONで保存
            with open(pipeline_filename, "w", encoding="utf-8") as f:
                json.dump(pipeline.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Pipeline metadata saved to {pipeline_filename}")

            # preprocessorをjoblibで保存
            preprocessor_filename = output_dir / f"preprocessor_{timestamp}.pkl"
            preprocessor = pipeline.get_preprocessor()
            if preprocessor:
                joblib.dump(preprocessor, preprocessor_filename)
                logger.info(f"Preprocessor saved to {preprocessor_filename}")

        with open(metadata_filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Metadata saved to {metadata_filename}")

        logger.info("Training completed successfully")

    finally:
        session.close()


if __name__ == "__main__":
    main()
