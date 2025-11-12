"""特徴量の品質チェックを実装するモジュール。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ml.data.schema import FeatureSchema

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """品質チェックの結果を表すレポート。"""

    passed: bool
    warnings: list[str]
    errors: list[str]
    statistics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """レポートを辞書形式に変換する。

        Returns:
            レポートの辞書表現
        """
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "statistics": self.statistics,
        }


class FeatureQualityChecker:
    """特徴量の品質をチェックするクラス。"""

    def __init__(
        self,
        *,
        min_samples: int = 100,
        max_missing_ratio: float = 0.5,
        min_unique_ratio: float = 0.01,
    ) -> None:
        """品質チェッカーを初期化する。

        Args:
            min_samples: 最小サンプル数
            max_missing_ratio: 最大欠損率
            min_unique_ratio: 最小ユニーク値比率
        """
        self._min_samples = min_samples
        self._max_missing_ratio = max_missing_ratio
        self._min_unique_ratio = min_unique_ratio

    def check(self, df: pd.DataFrame, schema: FeatureSchema | None = None) -> QualityReport:
        """データの品質をチェックする。

        Args:
            df: チェック対象のDataFrame
            schema: 特徴量スキーマ（Noneの場合は推論）

        Returns:
            品質レポート
        """
        warnings: list[str] = []
        errors: list[str] = []
        statistics: dict[str, Any] = {}

        # 基本統計
        statistics["total_samples"] = len(df)
        statistics["total_features"] = len(df.columns)

        # サンプル数チェック
        if len(df) < self._min_samples:
            errors.append(f"Sample size ({len(df)}) is less than minimum ({self._min_samples})")

        # スキーマの検証
        if schema:
            try:
                schema.validate(df)
            except ValueError as e:
                errors.append(f"Schema validation failed: {e}")

        # 各特徴量のチェック
        feature_stats: dict[str, dict[str, Any]] = {}
        for col in df.columns:
            col_stats = self._check_feature(df[col], col)
            feature_stats[col] = col_stats

            # 欠損値チェック
            missing_ratio = col_stats["missing_ratio"]
            if missing_ratio > self._max_missing_ratio:
                errors.append(
                    f"Column '{col}' has high missing ratio ({missing_ratio:.2%}) "
                    f"> {self._max_missing_ratio:.2%}"
                )
            elif missing_ratio > self._max_missing_ratio * 0.5:
                warnings.append(
                    f"Column '{col}' has moderate missing ratio ({missing_ratio:.2%})"
                )

            # ユニーク値チェック（カテゴリ特徴量）
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                unique_ratio = col_stats["unique_ratio"]
                if unique_ratio < self._min_unique_ratio:
                    warnings.append(
                        f"Column '{col}' has low unique ratio ({unique_ratio:.2%}) "
                        f"< {self._min_unique_ratio:.2%}"
                    )

            # 分散チェック（数値特徴量）
            if pd.api.types.is_numeric_dtype(df[col]):
                std = col_stats.get("std")
                if std is not None and std == 0:
                    warnings.append(f"Column '{col}' has zero variance")

        statistics["feature_statistics"] = feature_stats

        # ターゲットのチェック
        target_cols = [col for col in df.columns if col.startswith("target_")]
        if target_cols:
            for target_col in target_cols:
                target_stats = self._check_target(df[target_col], target_col)
                statistics[f"target_{target_col}"] = target_stats

                # クラス不均衡チェック
                if "class_distribution" in target_stats:
                    dist = target_stats["class_distribution"]
                    if len(dist) > 0:
                        min_class_ratio = min(dist.values()) / sum(dist.values())
                        if min_class_ratio < 0.1:
                            warnings.append(
                                f"Target '{target_col}' has class imbalance "
                                f"(min class ratio: {min_class_ratio:.2%})"
                            )

        passed = len(errors) == 0

        return QualityReport(
            passed=passed,
            warnings=warnings,
            errors=errors,
            statistics=statistics,
        )

    def _check_feature(self, series: pd.Series, name: str) -> dict[str, Any]:
        """個別の特徴量をチェックする。

        Args:
            series: チェック対象のシリーズ
            name: 特徴量名

        Returns:
            特徴量の統計情報
        """
        stats: dict[str, Any] = {
            "name": name,
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_ratio": float(series.isna().sum() / len(series)),
            "unique_count": int(series.nunique()),
            "unique_ratio": float(series.nunique() / len(series)),
        }

        if pd.api.types.is_numeric_dtype(series):
            stats["mean"] = float(series.mean()) if not series.isna().all() else None
            stats["std"] = float(series.std()) if not series.isna().all() else None
            stats["min"] = float(series.min()) if not series.isna().all() else None
            stats["max"] = float(series.max()) if not series.isna().all() else None
            stats["median"] = float(series.median()) if not series.isna().all() else None

        return stats

    def _check_target(self, series: pd.Series, name: str) -> dict[str, Any]:
        """ターゲット変数をチェックする。

        Args:
            series: チェック対象のシリーズ
            name: ターゲット名

        Returns:
            ターゲットの統計情報
        """
        stats: dict[str, Any] = {
            "name": name,
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_ratio": float(series.isna().sum() / len(series)),
        }

        if pd.api.types.is_numeric_dtype(series):
            # クラス分布（分類問題の場合）
            if series.nunique() <= 10:
                class_counts = series.value_counts().to_dict()
                stats["class_distribution"] = {str(k): int(v) for k, v in class_counts.items()}
            else:
                stats["mean"] = float(series.mean()) if not series.isna().all() else None
                stats["std"] = float(series.std()) if not series.isna().all() else None

        return stats

    def generate_report(self, report: QualityReport, output_path: str | None = None) -> str:
        """品質レポートを生成する。

        Args:
            report: 品質レポート
            output_path: 出力パス（Noneの場合は文字列として返す）

        Returns:
            レポートの文字列表現
        """
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("Feature Quality Report")
        lines.append("=" * 80)
        lines.append("")

        lines.append(f"Status: {'PASSED' if report.passed else 'FAILED'}")
        lines.append("")

        if report.errors:
            lines.append("Errors:")
            for error in report.errors:
                lines.append(f"  - {error}")
            lines.append("")

        if report.warnings:
            lines.append("Warnings:")
            for warning in report.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        lines.append("Statistics:")
        lines.append(f"  Total samples: {report.statistics.get('total_samples', 'N/A')}")
        lines.append(f"  Total features: {report.statistics.get('total_features', 'N/A')}")
        lines.append("")

        report_text = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)

        return report_text

