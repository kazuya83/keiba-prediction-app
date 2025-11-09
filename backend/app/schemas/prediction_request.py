"""予測実行リクエストおよびレスポンスのスキーマ。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.services.prediction_runner import (
    PredictionFeatureContribution,
    PredictionJobMetadata,
    PredictionJobResult,
    PredictionJobStatus,
    PredictionRankingResult,
)


class PredictionRequest(BaseModel):
    """予測実行 API のリクエストボディ。"""

    race_id: int = Field(..., alias="raceId", ge=1, description="予測対象のレース ID")
    model_id: str | None = Field(
        default=None,
        alias="modelId",
        description="使用するモデルの識別子（未指定時はデフォルトモデル）",
        max_length=128,
    )
    feature_set_id: str | None = Field(
        default=None,
        alias="featureSetId",
        description="特徴量セットの識別子（未指定時は標準設定）",
        max_length=128,
    )
    stake_amount: Decimal = Field(
        default=Decimal("100.00"),
        alias="stakeAmount",
        ge=0,
        description="想定投資額。未指定時は100円相当。",
    )

    model_config = ConfigDict(populate_by_name=True)


class PredictionConfidenceInterval(BaseModel):
    """確率の信頼区間を表すスキーマ。"""

    lower: Decimal = Field(..., ge=0, le=1, description="下限値")
    upper: Decimal = Field(..., ge=0, le=1, description="上限値")

    model_config = ConfigDict(populate_by_name=True)


class PredictionRankingItem(BaseModel):
    """レスポンス内の順位情報。"""

    rank: int = Field(..., ge=1, description="順位（1始まり）")
    race_entry_id: int = Field(..., alias="raceEntryId", ge=1, description="レースエントリID")
    horse_id: int | None = Field(default=None, alias="horseId", ge=1, description="馬ID")
    horse_number: int | None = Field(
        default=None,
        alias="horseNumber",
        ge=1,
        description="馬番。設定されていない場合はnull。",
    )
    horse_name: str | None = Field(default=None, alias="horseName", description="馬名")
    probability: Decimal = Field(..., ge=0, le=1, description="推定勝率")
    confidence_interval: PredictionConfidenceInterval | None = Field(
        default=None,
        alias="confidenceInterval",
        description="推定勝率の信頼区間",
    )

    model_config = ConfigDict(populate_by_name=True)


class PredictionExplanationItem(BaseModel):
    """特徴量寄与度情報。"""

    feature_id: str = Field(..., alias="featureId", description="特徴量の識別子")
    importance: Decimal = Field(..., ge=0, description="重要度（正規化済み）")
    shap_value: Decimal = Field(..., alias="shapValue", description="SHAP値などの寄与度")

    model_config = ConfigDict(populate_by_name=True)


class PredictionMetadata(BaseModel):
    """レスポンスの付随情報。"""

    model_id: str | None = Field(default=None, alias="modelId", description="使用モデルID")
    model_version: str | None = Field(default=None, alias="modelVersion", description="モデルバージョン")
    feature_set_id: str | None = Field(
        default=None,
        alias="featureSetId",
        description="特徴量セットの識別子",
    )
    elapsed_ms: int = Field(..., alias="elapsedMs", ge=0, description="推論に要した時間（ミリ秒）")

    model_config = ConfigDict(populate_by_name=True)


class PredictionJobResponse(BaseModel):
    """予測実行 API のレスポンス。"""

    job_id: str = Field(..., alias="jobId", description="ジョブID")
    status: PredictionJobStatus = Field(..., description="ジョブ実行状態")
    prediction_id: int | None = Field(
        default=None,
        alias="predictionId",
        ge=1,
        description="保存された予測ID。失敗時はnull。",
    )
    metadata: PredictionMetadata
    rankings: list[PredictionRankingItem] = Field(default_factory=list, description="順位リスト")
    explanations: list[PredictionExplanationItem] = Field(
        default_factory=list,
        description="特徴量寄与度のリスト",
    )

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_result(cls, result: PredictionJobResult) -> "PredictionJobResponse":
        """サービス層の結果オブジェクトからレスポンスを構築する。"""
        return cls.model_validate(
            {
                "jobId": result.job_id,
                "status": result.status,
                "predictionId": result.prediction_id,
                "metadata": _metadata_dict(result.metadata),
                "rankings": [_ranking_dict(ranking) for ranking in result.rankings],
                "explanations": [_explanation_dict(explanation) for explanation in result.explanations],
            }
        )


def _metadata_dict(metadata: PredictionJobMetadata) -> dict[str, object]:
    return {
        "modelId": metadata.model_id,
        "modelVersion": metadata.model_version,
        "featureSetId": metadata.feature_set_id,
        "elapsedMs": metadata.elapsed_ms,
    }


def _ranking_dict(ranking: PredictionRankingResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "rank": ranking.rank,
        "raceEntryId": ranking.race_entry_id,
        "horseId": ranking.horse_id,
        "horseNumber": ranking.horse_number,
        "horseName": ranking.horse_name,
        "probability": ranking.probability,
    }
    if ranking.confidence_interval is not None:
        payload["confidenceInterval"] = {
            "lower": ranking.confidence_interval[0],
            "upper": ranking.confidence_interval[1],
        }
    else:
        payload["confidenceInterval"] = None
    return payload


def _explanation_dict(explanation: PredictionFeatureContribution) -> dict[str, object]:
    return {
        "featureId": explanation.feature_id,
        "importance": explanation.importance,
        "shapValue": explanation.shap_value,
    }


__all__ = [
    "PredictionExplanationItem",
    "PredictionJobResponse",
    "PredictionMetadata",
    "PredictionRequest",
    "PredictionRankingItem",
]


