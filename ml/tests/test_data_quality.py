"""データ品質テスト。"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np

from ml.quality.checks import FeatureQualityChecker, QualityReport
from ml.data.schema import FeatureSchema


class TestFeatureQualityChecker:
    """FeatureQualityCheckerのテスト。"""

    def test_check_min_samples(self):
        """最小サンプル数のチェック。"""
        checker = FeatureQualityChecker(min_samples=100)
        df = pd.DataFrame({"feature1": range(50), "target_win": [0, 1] * 25})

        report = checker.check(df)

        assert not report.passed
        assert any("Sample size" in error for error in report.errors)

    def test_check_missing_ratio(self):
        """欠損率のチェック。"""
        checker = FeatureQualityChecker(max_missing_ratio=0.5)
        df = pd.DataFrame(
            {
                "feature1": [1, 2, None, None, None, None, None, None, None, None],
                "target_win": [0, 1] * 5,
            }
        )

        report = checker.check(df)

        assert not report.passed
        assert any("missing ratio" in error.lower() for error in report.errors)

    def test_check_passes_with_valid_data(self):
        """有効なデータでチェックがパスする。"""
        checker = FeatureQualityChecker(min_samples=10, max_missing_ratio=0.5)
        df = pd.DataFrame(
            {
                "feature1": range(100),
                "feature2": [0.5] * 100,
                "target_win": [0, 1] * 50,
            }
        )

        report = checker.check(df)

        assert report.passed
        assert len(report.errors) == 0

    def test_check_with_schema(self):
        """スキーマを使用したチェック。"""
        checker = FeatureQualityChecker()
        schema = FeatureSchema(
            categorical_features=["cat_feature"],
            numerical_features=["num_feature"],
            target_features=["target_win"],
            identifier_features=[],
        )
        df = pd.DataFrame(
            {
                "cat_feature": ["A", "B", "C"] * 50,
                "num_feature": range(150),
                "target_win": [0, 1] * 75,
            }
        )

        report = checker.check(df, schema=schema)

        assert report.passed

    def test_check_with_missing_schema_column(self):
        """スキーマに存在しないカラムがある場合のチェック。"""
        checker = FeatureQualityChecker()
        schema = FeatureSchema(
            categorical_features=["cat_feature"],
            numerical_features=["num_feature"],
            target_features=["target_win"],
            identifier_features=[],
        )
        df = pd.DataFrame(
            {
                "cat_feature": ["A", "B", "C"] * 50,
                "num_feature": range(150),
                "target_win": [0, 1] * 75,
            }
        )

        # スキーマに存在しないカラムを追加
        df["extra_feature"] = range(150)

        # スキーマ検証でエラーになる
        with pytest.raises(ValueError):
            schema.validate(df)

    def test_check_class_imbalance_warning(self):
        """クラス不均衡の警告。"""
        checker = FeatureQualityChecker()
        # クラス不均衡なデータ
        df = pd.DataFrame(
            {
                "feature1": range(100),
                "target_win": [0] * 95 + [1] * 5,  # 95:5の不均衡
            }
        )

        report = checker.check(df)

        assert report.passed  # エラーではない
        assert any("class imbalance" in warning.lower() for warning in report.warnings)

    def test_check_zero_variance_warning(self):
        """分散ゼロの警告。"""
        checker = FeatureQualityChecker()
        df = pd.DataFrame(
            {
                "feature1": [1.0] * 100,  # 分散ゼロ
                "target_win": [0, 1] * 50,
            }
        )

        report = checker.check(df)

        assert report.passed
        assert any("zero variance" in warning.lower() for warning in report.warnings)

    def test_generate_report(self):
        """レポート生成。"""
        checker = FeatureQualityChecker()
        df = pd.DataFrame(
            {
                "feature1": range(100),
                "target_win": [0, 1] * 50,
            }
        )

        report = checker.check(df)
        report_text = checker.generate_report(report)

        assert "Feature Quality Report" in report_text
        assert "PASSED" in report_text or "FAILED" in report_text
        assert "Total samples" in report_text


class TestQualityReport:
    """QualityReportのテスト。"""

    def test_to_dict(self):
        """辞書形式への変換。"""
        report = QualityReport(
            passed=True,
            warnings=["warning1"],
            errors=[],
            statistics={"total_samples": 100},
        )

        result = report.to_dict()

        assert result["passed"] is True
        assert result["warnings"] == ["warning1"]
        assert result["errors"] == []
        assert result["statistics"]["total_samples"] == 100

