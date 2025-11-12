"""HTTP経由で推論サーバと通信するゲートウェイ実装。"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from pydantic import BaseModel

from app.services.prediction_runner import (
    InferenceRanking,
    ModelInferenceResult,
    PredictionFeatureContribution,
    PredictionModelError,
    PredictionModelGateway,
    PredictionTimeoutError,
)
from app.models.race import Race

logger = logging.getLogger(__name__)


class InferenceRequest(BaseModel):
    """推論リクエストのスキーマ。"""

    race_id: int
    model_version: str | None = None


class RankingResult(BaseModel):
    """順位結果のスキーマ。"""

    race_entry_id: int
    probability: float
    rank: int


class InferenceResponse(BaseModel):
    """推論レスポンスのスキーマ。"""

    race_id: int
    model_version: str
    rankings: list[RankingResult]
    elapsed_ms: int


class HTTPModelGateway(PredictionModelGateway):
    """HTTP経由で推論サーバと通信するゲートウェイ。"""

    def __init__(
        self,
        *,
        base_url: str = "http://ml-inference:8001",
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """HTTPゲートウェイを初期化する。

        Args:
            base_url: 推論サーバのベースURL
            timeout_seconds: タイムアウト秒数
            max_retries: 最大リトライ回数
        """
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """HTTPクライアントを取得する（必要に応じて作成）。

        Returns:
            HTTPクライアント
        """
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout_seconds),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

    def _close_client(self) -> None:
        """HTTPクライアントを閉じる。"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def infer(
        self,
        race: Race,
        *,
        model_id: str | None = None,
        feature_set_id: str | None = None,
    ) -> ModelInferenceResult:
        """推論を実行する。

        Args:
            race: レース情報
            model_id: モデルID（未使用）
            feature_set_id: 特徴量セットID（未使用）

        Returns:
            推論結果

        Raises:
            PredictionModelError: 推論に失敗した場合
            PredictionTimeoutError: タイムアウトした場合
        """
        client = self._get_client()
        request_data = InferenceRequest(race_id=race.id)

        last_exception: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    f"Calling inference server for race {race.id}",
                    extra={"race_id": race.id, "attempt": attempt},
                )

                response = client.post(
                    "/infer",
                    json=request_data.model_dump(),
                )

                if response.status_code == 404:
                    raise PredictionModelError(
                        f"Race {race.id} not found in inference server"
                    )
                if response.status_code == 503:
                    raise PredictionModelError(
                        f"Inference server is not available: {response.text}"
                    )
                if response.status_code == 500:
                    raise PredictionModelError(
                        f"Inference server error: {response.text}"
                    )
                response.raise_for_status()

                inference_response = InferenceResponse.model_validate(response.json())

                # ModelInferenceResultに変換
                rankings = [
                    InferenceRanking(
                        race_entry_id=ranking.race_entry_id,
                        probability=Decimal(str(ranking.probability)),
                        confidence_interval=None,  # 推論サーバからは取得できないためNone
                    )
                    for ranking in inference_response.rankings
                ]

                # 特徴量寄与度は推論サーバから取得できないため、空のリストを返す
                # 将来的には推論サーバから取得できるようにする
                feature_contributions: list[PredictionFeatureContribution] = []

                return ModelInferenceResult(
                    rankings=rankings,
                    feature_contributions=feature_contributions,
                    model_version=inference_response.model_version,
                    elapsed_ms=inference_response.elapsed_ms,
                )

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(
                    f"Inference request timeout (attempt {attempt}/{self._max_retries})",
                    extra={"race_id": race.id, "attempt": attempt},
                )
                if attempt < self._max_retries:
                    continue
                raise PredictionTimeoutError(
                    f"Inference request timeout after {self._timeout_seconds}s"
                ) from e

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(
                    f"Inference request failed with status {e.response.status_code}",
                    extra={
                        "race_id": race.id,
                        "attempt": attempt,
                        "status_code": e.response.status_code,
                    },
                )
                if attempt < self._max_retries and e.response.status_code >= 500:
                    continue
                raise PredictionModelError(
                    f"Inference request failed: {e.response.text}"
                ) from e

            except Exception as e:
                last_exception = e
                logger.exception(
                    f"Unexpected error during inference request",
                    extra={"race_id": race.id, "attempt": attempt},
                )
                if attempt < self._max_retries:
                    continue
                raise PredictionModelError(f"Inference request failed: {e}") from e

        raise PredictionModelError(
            f"Inference request failed after {self._max_retries} attempts"
        ) from last_exception

    def __del__(self) -> None:
        """デストラクタでHTTPクライアントを閉じる。"""
        self._close_client()


__all__ = ["HTTPModelGateway"]

