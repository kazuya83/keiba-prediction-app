"""特徴量スキーマ定義。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class FeatureSchema:
    """特徴量のスキーマ定義。"""

    categorical_features: list[str]
    numerical_features: list[str]
    target_features: list[str]
    identifier_features: list[str]

    def get_feature_columns(self) -> list[str]:
        """すべての特徴量カラム名を取得する。

        Returns:
            特徴量カラム名のリスト
        """
        return self.categorical_features + self.numerical_features

    def validate(self, df: pd.DataFrame) -> None:
        """DataFrameがスキーマに適合しているか検証する。

        Args:
            df: 検証対象のDataFrame

        Raises:
            ValueError: スキーマに適合しない場合
        """
        required_columns = (
            self.categorical_features
            + self.numerical_features
            + self.target_features
            + self.identifier_features
        )

        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> FeatureSchema:
        """DataFrameからスキーマを推論する。

        Args:
            df: スキーマ推論対象のDataFrame

        Returns:
            推論されたスキーマ
        """
        categorical_features: list[str] = []
        numerical_features: list[str] = []
        target_features: list[str] = []
        identifier_features: list[str] = []

        for col in df.columns:
            if col.startswith("target_"):
                target_features.append(col)
            elif col.endswith("_id") or col in ["race_id", "race_entry_id", "horse_id"]:
                identifier_features.append(col)
            elif df[col].dtype in ["object", "string", "category"]:
                categorical_features.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                numerical_features.append(col)

        return cls(
            categorical_features=categorical_features,
            numerical_features=numerical_features,
            target_features=target_features,
            identifier_features=identifier_features,
        )

    def to_dict(self) -> dict[str, Any]:
        """スキーマを辞書形式に変換する。

        Returns:
            スキーマの辞書表現
        """
        return {
            "categorical_features": self.categorical_features,
            "numerical_features": self.numerical_features,
            "target_features": self.target_features,
            "identifier_features": self.identifier_features,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureSchema:
        """辞書形式からスキーマを復元する。

        Args:
            data: スキーマの辞書表現

        Returns:
            復元されたスキーマ
        """
        return cls(
            categorical_features=data.get("categorical_features", []),
            numerical_features=data.get("numerical_features", []),
            target_features=data.get("target_features", []),
            identifier_features=data.get("identifier_features", []),
        )

