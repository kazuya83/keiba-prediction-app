"""モデル評価テスト。"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

from ml.train import ModelTrainer


class TestModelEvaluation:
    """モデル評価のテスト。"""

    @pytest.fixture
    def sample_data(self):
        """サンプルデータのフィクスチャ。"""
        np.random.seed(42)
        n_samples = 200
        df = pd.DataFrame(
            {
                "feature1": np.random.randn(n_samples),
                "feature2": np.random.randn(n_samples),
                "feature3": np.random.choice(["A", "B", "C"], n_samples),
                "target_win": np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
            }
        )
        return df

    def test_model_trainer_initialization(self):
        """ModelTrainerの初期化。"""
        trainer = ModelTrainer(model_type="lightgbm", test_size=0.2, random_state=42)

        assert trainer._model_type == "lightgbm"
        assert trainer._test_size == 0.2
        assert trainer._random_state == 42

    def test_train_with_valid_data(self, sample_data):
        """有効なデータで学習が成功する。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        results = trainer.train(sample_data, use_optuna=False, n_trials=10)

        assert results["model_type"] == "lightgbm"
        assert "train_metrics" in results
        assert "test_metrics" in results
        assert results["train_metrics"]["accuracy"] > 0
        assert results["test_metrics"]["accuracy"] > 0

    def test_train_metrics_threshold(self, sample_data):
        """学習メトリクスの閾値チェック。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        results = trainer.train(sample_data, use_optuna=False, n_trials=10)

        # 精度の閾値チェック（ランダムより良い）
        assert results["test_metrics"]["accuracy"] > 0.5

        # AUCの閾値チェック
        assert results["test_metrics"]["auc"] > 0.5

    def test_train_with_quality_check_failure(self):
        """品質チェック失敗時のエラー。"""
        trainer = ModelTrainer()
        # サンプル数が少なすぎるデータ
        df = pd.DataFrame(
            {
                "feature1": range(10),
                "target_win": [0, 1] * 5,
            }
        )

        with pytest.raises(ValueError, match="Data quality check failed"):
            trainer.train(df, use_optuna=False, n_trials=10)

    def test_model_persistence(self, sample_data):
        """モデルの永続化。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        trainer.train(sample_data, use_optuna=False, n_trials=10)

        model = trainer.get_model()
        assert model is not None
        assert isinstance(model, LGBMClassifier)

    def test_pipeline_persistence(self, sample_data):
        """パイプラインの永続化。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        trainer.train(sample_data, use_optuna=False, n_trials=10)

        pipeline = trainer.get_pipeline()
        assert pipeline is not None

        schema = trainer.get_schema()
        assert schema is not None

    def test_evaluation_metrics_completeness(self, sample_data):
        """評価メトリクスの完全性。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        results = trainer.train(sample_data, use_optuna=False, n_trials=10)

        required_metrics = ["accuracy", "precision", "recall", "f1", "auc", "brier", "log_loss"]
        for metric in required_metrics:
            assert metric in results["test_metrics"]
            assert isinstance(results["test_metrics"][metric], (int, float))

    def test_train_test_split(self, sample_data):
        """学習/テスト分割の確認。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        results = trainer.train(sample_data, use_optuna=False, n_trials=10)

        assert results["train_size"] > 0
        assert results["test_size"] > 0
        assert results["train_size"] + results["test_size"] == len(sample_data)

    def test_feature_count(self, sample_data):
        """特徴量数の確認。"""
        trainer = ModelTrainer(
            model_type="lightgbm",
            test_size=0.2,
            random_state=42,
        )

        results = trainer.train(sample_data, use_optuna=False, n_trials=10)

        assert results["feature_count"] > 0

