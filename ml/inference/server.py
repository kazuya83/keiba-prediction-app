"""ML推論サーバのFastAPIアプリケーション。"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.session import SessionLocal
from ml.data.repository import DataRepository
from ml.inference.model_loader import ModelLoader

logger = logging.getLogger(__name__)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="ML Inference Service",
    description="競馬予測モデルの推論サービス",
    version="0.1.0",
)

# モデルローダーの初期化
MODEL_LOADER = ModelLoader(artifacts_dir=Path("ml/artifacts"))


class InferenceRequest(BaseModel):
    """推論リクエストのスキーマ。"""

    race_id: int = Field(..., description="レースID")
    model_version: str | None = Field(None, description="モデルバージョン（指定しない場合は最新）")


class RankingResult(BaseModel):
    """順位結果のスキーマ。"""

    race_entry_id: int = Field(..., description="レースエントリID")
    probability: float = Field(..., description="勝利確率")
    rank: int = Field(..., description="予測順位")


class InferenceResponse(BaseModel):
    """推論レスポンスのスキーマ。"""

    race_id: int = Field(..., description="レースID")
    model_version: str = Field(..., description="使用したモデルバージョン")
    rankings: list[RankingResult] = Field(..., description="予測順位結果")
    elapsed_ms: int = Field(..., description="処理時間（ミリ秒）")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンスのスキーマ。"""

    status: str = Field(..., description="ステータス")
    model_loaded: bool = Field(..., description="モデルがロードされているか")
    model_version: str | None = Field(None, description="モデルバージョン")


class VersionResponse(BaseModel):
    """バージョン情報レスポンスのスキーマ。"""

    model_version: str | None = Field(None, description="モデルバージョン")
    metadata: dict[str, Any] | None = Field(None, description="モデルメタデータ")


@app.on_event("startup")
async def startup_event() -> None:
    """アプリケーション起動時の処理。"""
    logger.info("Starting ML Inference Service")
    try:
        MODEL_LOADER.load_latest_model()
        logger.info(f"Model loaded successfully. Version: {MODEL_LOADER.get_model_version()}")
    except FileNotFoundError as e:
        logger.warning(f"Model not found: {e}. Service will start without model.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)


@app.get("/health", response_model=HealthResponse, summary="ヘルスチェック")
def health_check() -> HealthResponse:
    """ヘルスチェックエンドポイント。

    Returns:
        ヘルスチェック結果
    """
    return HealthResponse(
        status="healthy",
        model_loaded=MODEL_LOADER.is_loaded(),
        model_version=MODEL_LOADER.get_model_version(),
    )


@app.get("/version", response_model=VersionResponse, summary="モデルバージョン情報取得")
def get_version() -> VersionResponse:
    """モデルバージョン情報を取得する。

    Returns:
        モデルバージョン情報

    Raises:
        HTTPException: モデルがロードされていない場合
    """
    if not MODEL_LOADER.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )

    return VersionResponse(
        model_version=MODEL_LOADER.get_model_version(),
        metadata=MODEL_LOADER.get_metadata(),
    )


@app.post("/infer", response_model=InferenceResponse, summary="推論実行")
def infer(request: InferenceRequest) -> InferenceResponse:
    """推論を実行する。

    Args:
        request: 推論リクエスト

    Returns:
        推論結果

    Raises:
        HTTPException: モデルがロードされていない場合、レースが見つからない場合、推論に失敗した場合
    """
    if not MODEL_LOADER.is_loaded():
        # リクエストで指定されたバージョンがある場合はロードを試みる
        if request.model_version:
            try:
                MODEL_LOADER.load_model_by_version(request.model_version)
            except FileNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model version {request.model_version} not found: {e}",
                ) from e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load model: {e}",
                ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is not loaded",
            )

    start_time = time.time()

    try:
        # データベースからレースデータを取得
        settings = get_settings()
        if not settings.database_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database URL is not configured",
            )

        session = SessionLocal()
        try:
            repository = DataRepository(session)
            df = repository.fetch_race_for_prediction(request.race_id)

            if len(df) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Race {request.race_id} not found or has no entries",
                )

            # 特徴量を変換
            features = MODEL_LOADER.transform_features(df)

            # 推論を実行
            probabilities = MODEL_LOADER.predict(features)

            # 結果を構築
            rankings: list[RankingResult] = []
            race_entry_ids = df["race_entry_id"].values
            probability_rank_pairs = list(zip(race_entry_ids, probabilities))
            probability_rank_pairs.sort(key=lambda x: x[1], reverse=True)

            for rank, (race_entry_id, probability) in enumerate(probability_rank_pairs, start=1):
                rankings.append(
                    RankingResult(
                        race_entry_id=int(race_entry_id),
                        probability=float(probability),
                        rank=rank,
                    )
                )

            elapsed_ms = int((time.time() - start_time) * 1000)

            return InferenceResponse(
                race_id=request.race_id,
                model_version=MODEL_LOADER.get_model_version() or "unknown",
                rankings=rankings,
                elapsed_ms=elapsed_ms,
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to infer race {request.race_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to infer: {e}",
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

