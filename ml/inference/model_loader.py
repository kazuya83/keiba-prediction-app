"""モデル成果物のロードと管理を行うモジュール。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ml.data.schema import FeatureSchema
from ml.features.pipelines import FeaturePipeline

logger = logging.getLogger(__name__)


class ModelLoader:
    """モデル成果物をロードし、管理するクラス。"""

    def __init__(self, artifacts_dir: Path | str = "ml/artifacts") -> None:
        """モデルローダーを初期化する。

        Args:
            artifacts_dir: モデル成果物のディレクトリパス
        """
        self._artifacts_dir = Path(artifacts_dir)
        self._model: Any = None
        self._pipeline: FeaturePipeline | None = None
        self._metadata: dict[str, Any] | None = None
        self._model_version: str | None = None
        self._model_path: Path | None = None
        self._pipeline_path: Path | None = None
        self._metadata_path: Path | None = None

    def load_latest_model(self) -> None:
        """最新のモデル成果物をロードする。

        Raises:
            FileNotFoundError: モデルファイルが見つからない場合
            ValueError: モデルのロードに失敗した場合
        """
        model_files = sorted(self._artifacts_dir.glob("model_*.pkl"), reverse=True)
        if not model_files:
            raise FileNotFoundError(f"No model files found in {self._artifacts_dir}")

        model_path = model_files[0]
        timestamp = model_path.stem.replace("model_", "")
        pipeline_path = self._artifacts_dir / f"pipeline_{timestamp}.json"
        metadata_path = self._artifacts_dir / f"metadata_{timestamp}.json"

        if not pipeline_path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        logger.info(f"Loading model from {model_path}")
        self._model = joblib.load(model_path)
        logger.info(f"Model loaded successfully")

        logger.info(f"Loading pipeline from {pipeline_path}")
        with open(pipeline_path, "r", encoding="utf-8") as f:
            pipeline_data = json.load(f)
        self._pipeline = FeaturePipeline.from_dict(pipeline_data)
        logger.info(f"Pipeline metadata loaded successfully")

        # preprocessorをロード
        preprocessor_path = self._artifacts_dir / f"preprocessor_{timestamp}.pkl"
        if preprocessor_path.exists():
            logger.info(f"Loading preprocessor from {preprocessor_path}")
            preprocessor = joblib.load(preprocessor_path)
            # preprocessorをパイプラインに設定
            self._pipeline._preprocessor = preprocessor
            logger.info(f"Preprocessor loaded successfully")
        else:
            logger.warning(f"Preprocessor file not found: {preprocessor_path}")

        logger.info(f"Loading metadata from {metadata_path}")
        with open(metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)
        logger.info(f"Metadata loaded successfully")

        self._model_version = self._metadata.get("model_version", timestamp)
        self._model_path = model_path
        self._pipeline_path = pipeline_path
        self._metadata_path = metadata_path

    def load_model_by_version(self, version: str) -> None:
        """指定されたバージョンのモデルをロードする。

        Args:
            version: モデルバージョン（タイムスタンプ）

        Raises:
            FileNotFoundError: モデルファイルが見つからない場合
        """
        model_path = self._artifacts_dir / f"model_{version}.pkl"
        pipeline_path = self._artifacts_dir / f"pipeline_{version}.json"
        metadata_path = self._artifacts_dir / f"metadata_{version}.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not pipeline_path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        logger.info(f"Loading model from {model_path}")
        self._model = joblib.load(model_path)

        logger.info(f"Loading pipeline from {pipeline_path}")
        with open(pipeline_path, "r", encoding="utf-8") as f:
            pipeline_data = json.load(f)
        self._pipeline = FeaturePipeline.from_dict(pipeline_data)
        logger.info(f"Pipeline metadata loaded successfully")

        # preprocessorをロード
        preprocessor_path = self._artifacts_dir / f"preprocessor_{version}.pkl"
        if preprocessor_path.exists():
            logger.info(f"Loading preprocessor from {preprocessor_path}")
            preprocessor = joblib.load(preprocessor_path)
            # preprocessorをパイプラインに設定
            self._pipeline._preprocessor = preprocessor
            logger.info(f"Preprocessor loaded successfully")
        else:
            logger.warning(f"Preprocessor file not found: {preprocessor_path}")

        logger.info(f"Loading metadata from {metadata_path}")
        with open(metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        self._model_version = version
        self._model_path = model_path
        self._pipeline_path = pipeline_path
        self._metadata_path = metadata_path

    def predict(self, features: np.ndarray) -> np.ndarray:
        """特徴量に対して予測を実行する。

        Args:
            features: 特徴量配列

        Returns:
            予測確率の配列

        Raises:
            ValueError: モデルがロードされていない場合
        """
        if self._model is None:
            raise ValueError("Model is not loaded. Call load_latest_model() first.")

        predictions = self._model.predict_proba(features)[:, 1]
        return predictions

    def transform_features(self, df: Any) -> np.ndarray:
        """特徴量を前処理パイプラインで変換する。

        Args:
            df: 特徴量DataFrame

        Returns:
            変換された特徴量配列

        Raises:
            ValueError: パイプラインがロードされていない場合
        """
        if self._pipeline is None:
            raise ValueError("Pipeline is not loaded. Call load_latest_model() first.")

        return self._pipeline.transform(df)

    def get_model_version(self) -> str | None:
        """モデルバージョンを取得する。

        Returns:
            モデルバージョン
        """
        return self._model_version

    def get_metadata(self) -> dict[str, Any] | None:
        """モデルメタデータを取得する。

        Returns:
            モデルメタデータ
        """
        return self._metadata

    def is_loaded(self) -> bool:
        """モデルがロードされているかどうかを確認する。

        Returns:
            モデルがロードされている場合True
        """
        return self._model is not None and self._pipeline is not None

