"""機械学習モデルによる予測実行を司るサービス。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.crud import prediction as prediction_crud
from app.models.prediction import Prediction
from app.models.race import Race, RaceEntry

logger = logging.getLogger(__name__)

ConfidenceInterval = tuple[Decimal, Decimal]


@dataclass(slots=True)
class PredictionInput:
    """予測実行時に必要となる入力パラメータ。"""

    race_id: int
    model_id: str | None = None
    feature_set_id: str | None = None
    stake_amount: Decimal | None = None


@dataclass(slots=True)
class InferenceRanking:
    """推論エンジンから返却される順位情報。"""

    race_entry_id: int
    probability: Decimal
    confidence_interval: ConfidenceInterval | None = None


@dataclass(slots=True)
class PredictionFeatureContribution:
    """特徴量寄与度を表すデータ構造。"""

    feature_id: str
    importance: Decimal
    shap_value: Decimal


@dataclass(slots=True)
class ModelInferenceResult:
    """推論エンジンの結果。"""

    rankings: Sequence[InferenceRanking]
    feature_contributions: Sequence[PredictionFeatureContribution]
    model_version: str | None
    elapsed_ms: int


@dataclass(slots=True)
class PredictionJobMetadata:
    """ジョブメタデータ。"""

    model_id: str | None
    model_version: str | None
    feature_set_id: str | None
    elapsed_ms: int


@dataclass(slots=True)
class PredictionRankingResult:
    """レスポンス向けの順位結果。"""

    rank: int
    race_entry_id: int
    horse_id: int | None
    horse_number: int | None
    horse_name: str | None
    probability: Decimal
    confidence_interval: ConfidenceInterval | None


class PredictionJobStatus(StrEnum):
    """ジョブの状態を表す列挙。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class PredictionJobResult:
    """予測実行後の結果データ。"""

    job_id: str
    status: PredictionJobStatus
    prediction_id: int | None
    metadata: PredictionJobMetadata
    rankings: list[PredictionRankingResult]
    explanations: list[PredictionFeatureContribution]


class PredictionRunnerError(Exception):
    """予測実行時の汎用例外。"""

    retryable: bool = False


class RaceNotFoundError(PredictionRunnerError):
    """指定レースが存在しない場合の例外。"""


class EmptyRaceEntriesError(PredictionRunnerError):
    """レースに出走馬が紐付いていない場合の例外。"""


class PredictionModelError(PredictionRunnerError):
    """推論エンジン処理で発生した例外。"""


class InvalidRaceEntryError(PredictionModelError):
    """推論結果に無効なレースエントリが含まれている場合の例外。"""


class EmptyPredictionResultError(PredictionModelError):
    """推論が空集合を返した場合の例外。"""


class PredictionTimeoutError(PredictionRunnerError):
    """推論処理がタイムアウトした場合の例外。"""

    retryable = True


class PersistenceError(PredictionRunnerError):
    """保存処理で発生した例外。"""


class PredictionModelGateway(Protocol):
    """推論エンジンへのインターフェース。"""

    def infer(
        self,
        race: Race,
        *,
        model_id: str | None,
        feature_set_id: str | None,
    ) -> ModelInferenceResult:
        """推論を実行し、結果を返す。"""


class HeuristicModelGateway(PredictionModelGateway):
    """簡易的なヒューリスティック実装。"""

    def infer(
        self,
        race: Race,
        *,
        model_id: str | None,
        feature_set_id: str | None,
    ) -> ModelInferenceResult:
        entries = list(race.entries)
        if not entries:
            raise EmptyRaceEntriesError("レースに出走馬が存在しません。")

        sorted_entries = sorted(
            entries,
            key=lambda entry: (entry.horse_number or 9999, entry.id),
        )
        weights = [Decimal(len(sorted_entries) - idx) for idx, _ in enumerate(sorted_entries)]
        total_weight = sum(weights)
        if total_weight == 0:
            raise PredictionModelError("推論用の重み計算に失敗しました。")

        rankings: list[InferenceRanking] = []
        remaining_probability = Decimal("1")
        quantize_unit = Decimal("0.0001")

        for idx, (entry, weight) in enumerate(zip(sorted_entries, weights), start=1):
            if idx == len(sorted_entries):
                probability = remaining_probability.quantize(quantize_unit, rounding=ROUND_HALF_UP)
            else:
                raw_probability = weight / total_weight
                probability = raw_probability.quantize(quantize_unit, rounding=ROUND_HALF_UP)
                remaining_probability -= probability
                if remaining_probability < Decimal("0"):
                    remaining_probability = Decimal("0")

            lower = (probability - Decimal("0.0400")).quantize(quantize_unit, rounding=ROUND_HALF_UP)
            upper = (probability + Decimal("0.0400")).quantize(quantize_unit, rounding=ROUND_HALF_UP)
            lower = max(lower, Decimal("0"))
            upper = min(upper, Decimal("1"))

            rankings.append(
                InferenceRanking(
                    race_entry_id=entry.id,
                    probability=probability,
                    confidence_interval=(lower, upper),
                )
            )

        contributions = [
            PredictionFeatureContribution(
                feature_id="speed_index",
                importance=Decimal("0.45"),
                shap_value=Decimal("0.18"),
            ),
            PredictionFeatureContribution(
                feature_id="stamina_score",
                importance=Decimal("0.32"),
                shap_value=Decimal("0.12"),
            ),
            PredictionFeatureContribution(
                feature_id="jockey_win_rate",
                importance=Decimal("0.23"),
                shap_value=Decimal("0.09"),
            ),
        ]

        elapsed_ms = min(5000, 200 + len(sorted_entries) * 90)
        resolved_model_id = model_id or "heuristic"
        model_version = f"{resolved_model_id}-v1"

        return ModelInferenceResult(
            rankings=rankings,
            feature_contributions=contributions,
            model_version=model_version,
            elapsed_ms=elapsed_ms,
        )


class PredictionRunner:
    """予測実行と結果保存を担当するサービスクラス。"""

    def __init__(
        self,
        *,
        db: Session,
        model_gateway: PredictionModelGateway | None = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 1,
    ) -> None:
        self._db = db
        self._model_gateway = model_gateway or HeuristicModelGateway()
        self._timeout_ms = max(int(timeout_seconds * 1000), 0)
        self._max_retries = max(int(max_retries), 0)

    def run(self, request: PredictionInput, *, user_id: int) -> PredictionJobResult:
        """予測を実行し、結果を永続化した上でレスポンスデータを返す。"""
        race = self._load_race(request.race_id)
        job_id = self._generate_job_id()
        max_attempts = self._max_retries + 1

        for attempt in range(1, max_attempts + 1):
            try:
                inference = self._invoke_inference(race, request)
                prediction = self._persist_prediction(
                    job_id=job_id,
                    user_id=user_id,
                    race=race,
                    request=request,
                    inference=inference,
                )
                self._db.commit()
            except PredictionRunnerError as exc:
                self._db.rollback()
                self._db.expire_all()
                logger.warning(
                    "Prediction attempt failed",
                    extra={
                        "race_id": request.race_id,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "retryable": exc.retryable,
                        "error": exc.__class__.__name__,
                    },
                )
                if exc.retryable and attempt < max_attempts:
                    continue
                raise
            except Exception as exc:  # pragma: no cover - 予期しない例外はログ出力後再送出
                self._db.rollback()
                self._db.expire_all()
                logger.exception(
                    "Unexpected error while running prediction",
                    extra={"race_id": request.race_id},
                )
                raise PredictionRunnerError("予測実行中に予期しないエラーが発生しました。") from exc
            else:
                return self._build_job_result(
                    job_id=job_id,
                    prediction=prediction,
                    inference=inference,
                    race=race,
                    request=request,
                )

        raise PredictionRunnerError("予測実行に失敗しました。再試行回数を超過しています。")

    def _load_race(self, race_id: int) -> Race:
        statement = (
            select(Race)
            .options(
                selectinload(Race.entries).selectinload(RaceEntry.horse),
            )
            .where(Race.id == race_id)
        )
        race = self._db.scalars(statement).first()
        if race is None:
            raise RaceNotFoundError("指定されたレースが見つかりません。")
        if not race.entries:
            raise EmptyRaceEntriesError("レースに出走馬が登録されていません。")
        return race

    def _invoke_inference(self, race: Race, request: PredictionInput) -> ModelInferenceResult:
        try:
            inference = self._model_gateway.infer(
                race,
                model_id=request.model_id,
                feature_set_id=request.feature_set_id,
            )
        except PredictionRunnerError:
            raise
        except Exception as exc:
            raise PredictionModelError("推論処理に失敗しました。") from exc

        if not inference.rankings:
            raise EmptyPredictionResultError("推論結果が空です。")
        if self._timeout_ms and inference.elapsed_ms > self._timeout_ms:
            raise PredictionTimeoutError("推論処理が制限時間を超過しました。")

        return inference

    def _persist_prediction(
        self,
        *,
        job_id: str,
        user_id: int,
        race: Race,
        request: PredictionInput,
        inference: ModelInferenceResult,
    ) -> Prediction:
        entry_map = {entry.id: entry for entry in race.entries}
        picks: list[prediction_crud.PredictionPickInput] = []

        for rank_index, ranking in enumerate(inference.rankings, start=1):
            entry = entry_map.get(ranking.race_entry_id)
            if entry is None:
                raise InvalidRaceEntryError("推論結果に存在しないレースエントリが含まれています。")
            picks.append(
                prediction_crud.PredictionPickInput(
                    rank=rank_index,
                    race_entry_id=entry.id,
                    probability=ranking.probability,
                )
            )

        memo_payload = self._build_memo_payload(
            job_id=job_id,
            request=request,
            inference=inference,
        )
        stake_amount = request.stake_amount or Decimal("100.00")

        try:
            prediction = prediction_crud.create_prediction(
                self._db,
                user_id=user_id,
                race_id=race.id,
                picks=picks,
                stake_amount=stake_amount,
                model_version=inference.model_version,
                memo=json.dumps(memo_payload, ensure_ascii=False),
            )
        except Exception as exc:  # pragma: no cover - 例外は呼び出し元で処理
            raise PersistenceError("予測結果の保存に失敗しました。") from exc

        return prediction

    def _build_job_result(
        self,
        *,
        job_id: str,
        prediction: Prediction,
        inference: ModelInferenceResult,
        race: Race,
        request: PredictionInput,
    ) -> PredictionJobResult:
        entry_map = {entry.id: entry for entry in race.entries}
        rankings: list[PredictionRankingResult] = []

        for rank_index, ranking in enumerate(inference.rankings, start=1):
            entry = entry_map.get(ranking.race_entry_id)
            if entry is None:
                raise InvalidRaceEntryError("保存済みの予測とエントリの整合性に失敗しました。")
            rankings.append(
                PredictionRankingResult(
                    rank=rank_index,
                    race_entry_id=entry.id,
                    horse_id=entry.horse.id if entry.horse else None,
                    horse_number=entry.horse_number,
                    horse_name=entry.horse.name if entry.horse else None,
                    probability=ranking.probability,
                    confidence_interval=ranking.confidence_interval,
                )
            )

        metadata = PredictionJobMetadata(
            model_id=request.model_id,
            model_version=inference.model_version,
            feature_set_id=request.feature_set_id,
            elapsed_ms=inference.elapsed_ms,
        )

        return PredictionJobResult(
            job_id=job_id,
            status=PredictionJobStatus.COMPLETED,
            prediction_id=prediction.id,
            metadata=metadata,
            rankings=rankings,
            explanations=list(inference.feature_contributions),
        )

    def _build_memo_payload(
        self,
        *,
        job_id: str,
        request: PredictionInput,
        inference: ModelInferenceResult,
    ) -> dict[str, object]:
        return {
            "job_id": job_id,
            "model_id": request.model_id,
            "feature_set_id": request.feature_set_id,
            "elapsed_ms": inference.elapsed_ms,
            "explanations": [
                {
                    "feature_id": contribution.feature_id,
                    "importance": str(contribution.importance),
                    "shap_value": str(contribution.shap_value),
                }
                for contribution in inference.feature_contributions
            ],
        }

    @staticmethod
    def _generate_job_id() -> str:
        return uuid4().hex


__all__ = [
    "EmptyPredictionResultError",
    "EmptyRaceEntriesError",
    "HeuristicModelGateway",
    "InferenceRanking",
    "InvalidRaceEntryError",
    "ModelInferenceResult",
    "PredictionFeatureContribution",
    "PredictionInput",
    "PredictionJobMetadata",
    "PredictionJobResult",
    "PredictionJobStatus",
    "PredictionModelError",
    "PredictionModelGateway",
    "PredictionRunner",
    "PredictionRunnerError",
    "PredictionTimeoutError",
    "PredictionRankingResult",
    "RaceNotFoundError",
]


