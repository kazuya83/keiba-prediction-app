"""特徴量エンジニアリングパイプライン。"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from ml.data.schema import FeatureSchema

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """特徴量の前処理パイプライン。"""

    def __init__(self, schema: FeatureSchema) -> None:
        """パイプラインを初期化する。

        Args:
            schema: 特徴量スキーマ
        """
        self._schema = schema
        self._preprocessor: ColumnTransformer | None = None
        self._label_encoders: dict[str, LabelEncoder] = {}

    def fit(self, df: pd.DataFrame) -> None:
        """パイプラインを学習データに適合させる。

        Args:
            df: 学習データのDataFrame
        """
        self._schema.validate(df)

        # カテゴリ特徴量のラベルエンコーディング
        for col in self._schema.categorical_features:
            if col in df.columns:
                le = LabelEncoder()
                # NaNを一時的に文字列に変換してからエンコード
                series = df[col].fillna("__MISSING__")
                le.fit(series.astype(str))
                self._label_encoders[col] = le

        # 前処理パイプラインの構築
        transformers: list[tuple[str, Pipeline, list[str]]] = []

        # カテゴリ特徴量の処理
        if self._schema.categorical_features:
            categorical_pipeline = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
                    ("label_encoder", "passthrough"),  # ラベルエンコーディングは別途処理
                ]
            )
            transformers.append(("cat", categorical_pipeline, self._schema.categorical_features))

        # 数値特徴量の処理
        if self._schema.numerical_features:
            numerical_pipeline = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            )
            transformers.append(("num", numerical_pipeline, self._schema.numerical_features))

        if transformers:
            self._preprocessor = ColumnTransformer(transformers, remainder="drop")
            feature_df = self._prepare_features(df)
            self._preprocessor.fit(feature_df)
        else:
            logger.warning("No features to preprocess")

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """データを変換する。

        Args:
            df: 変換対象のDataFrame

        Returns:
            変換された特徴量配列
        """
        if self._preprocessor is None:
            raise ValueError("Pipeline must be fitted before transform")

        feature_df = self._prepare_features(df)
        return self._preprocessor.transform(feature_df)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """パイプラインを適合させてデータを変換する。

        Args:
            df: 学習データのDataFrame

        Returns:
            変換された特徴量配列
        """
        self.fit(df)
        return self.transform(df)

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特徴量の前準備（ラベルエンコーディングなど）を行う。

        Args:
            df: 元のDataFrame

        Returns:
            前準備済みのDataFrame
        """
        feature_df = df[self._schema.get_feature_columns()].copy()

        # カテゴリ特徴量のラベルエンコーディング
        for col in self._schema.categorical_features:
            if col in feature_df.columns and col in self._label_encoders:
                le = self._label_encoders[col]
                series = feature_df[col].fillna("__MISSING__")
                feature_df[col] = le.transform(series.astype(str))

        return feature_df

    def get_feature_names(self) -> list[str]:
        """変換後の特徴量名を取得する。

        Returns:
            特徴量名のリスト
        """
        if self._preprocessor is None:
            return []

        try:
            return list(self._preprocessor.get_feature_names_out())
        except AttributeError:
            # 古いsklearnバージョン対応
            return [f"feature_{i}" for i in range(self._preprocessor.n_features_out_)]

    def get_schema(self) -> FeatureSchema:
        """スキーマを取得する。

        Returns:
            特徴量スキーマ
        """
        return self._schema

    def to_dict(self) -> dict[str, Any]:
        """パイプラインを辞書形式に変換する（保存用）。

        注意: このメソッドはpreprocessorを保存しません。
        preprocessorは別途joblibでシリアライズする必要があります。

        Returns:
            パイプラインの辞書表現
        """
        label_encoders_dict: dict[str, list[str]] = {}
        for col, le in self._label_encoders.items():
            label_encoders_dict[col] = list(le.classes_)

        return {
            "schema": self._schema.to_dict(),
            "label_encoders": label_encoders_dict,
        }

    def get_preprocessor(self) -> ColumnTransformer | None:
        """preprocessorを取得する。

        Returns:
            preprocessor（未構築の場合はNone）
        """
        return self._preprocessor

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeaturePipeline:
        """辞書形式からパイプラインを復元する。

        Args:
            data: パイプラインの辞書表現

        Returns:
            復元されたパイプライン
        """
        schema = FeatureSchema.from_dict(data["schema"])
        pipeline = cls(schema)

        # ラベルエンコーダーの復元
        for col, classes in data.get("label_encoders", {}).items():
            le = LabelEncoder()
            le.classes_ = np.array(classes)
            pipeline._label_encoders[col] = le

        return pipeline

