from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.horse import Horse
from app.models.prediction import Prediction
from app.models.race import Race, RaceEntry
from app.services.prediction_runner import (
    InferenceRanking,
    ModelInferenceResult,
    PredictionFeatureContribution,
    PredictionInput,
    PredictionJobStatus,
    PredictionRunner,
    PredictionTimeoutError,
)


class ScriptedGateway:
    """テスト用の推論結果を返すゲートウェイ。"""

    def __init__(self, responses: Sequence[ModelInferenceResult]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def infer(
        self,
        race: Race,
        *,
        model_id: str | None,
        feature_set_id: str | None,
    ) -> ModelInferenceResult:
        index = min(self.calls, len(self._responses) - 1)
        self.calls += 1
        return self._responses[index]


def _create_race_with_entries(db_session: Session) -> tuple[Race, list[RaceEntry]]:
    race = Race(
        name="テストレース",
        race_date=date(2024, 11, 9),
        venue="東京",
        course_type="芝",
        distance=1800,
    )
    db_session.add(race)

    horses = [Horse(name="ホース1"), Horse(name="ホース2")]
    db_session.add_all(horses)
    db_session.flush()

    entries: list[RaceEntry] = []
    for idx, horse in enumerate(horses, start=1):
        entry = RaceEntry(
            race=race,
            horse=horse,
            horse_number=idx,
        )
        db_session.add(entry)
        entries.append(entry)

    db_session.flush()
    return race, entries


def _inference_result(entries: list[RaceEntry], *, elapsed_ms: int) -> ModelInferenceResult:
    rankings = [
        InferenceRanking(
            race_entry_id=entries[0].id,
            probability=Decimal("0.6500"),
            confidence_interval=(Decimal("0.6000"), Decimal("0.7000")),
        ),
        InferenceRanking(
            race_entry_id=entries[1].id,
            probability=Decimal("0.3500"),
            confidence_interval=(Decimal("0.3000"), Decimal("0.4000")),
        ),
    ]
    contributions = [
        PredictionFeatureContribution(
            feature_id="speed_index",
            importance=Decimal("0.55"),
            shap_value=Decimal("0.22"),
        ),
        PredictionFeatureContribution(
            feature_id="stamina_score",
            importance=Decimal("0.45"),
            shap_value=Decimal("0.18"),
        ),
    ]
    return ModelInferenceResult(
        rankings=rankings,
        feature_contributions=contributions,
        model_version="model-v1",
        elapsed_ms=elapsed_ms,
    )


def test_run_prediction_creates_prediction_and_returns_result(db_session: Session) -> None:
    race, entries = _create_race_with_entries(db_session)
    gateway = ScriptedGateway(
        responses=[_inference_result(entries, elapsed_ms=500)],
    )
    runner = PredictionRunner(
        db=db_session,
        model_gateway=gateway,
        timeout_seconds=2.0,
        max_retries=1,
    )
    request = PredictionInput(
        race_id=race.id,
        model_id="test-model",
        feature_set_id="full",
        stake_amount=Decimal("200.00"),
    )

    result = runner.run(request, user_id=1)

    assert result.status is PredictionJobStatus.COMPLETED
    assert result.metadata.model_id == "test-model"
    assert result.metadata.elapsed_ms == 500
    assert len(result.rankings) == 2
    assert result.rankings[0].horse_name == "ホース1"
    assert result.rankings[0].probability == Decimal("0.6500")
    assert result.prediction_id is not None

    stored_prediction = db_session.get(Prediction, result.prediction_id)
    assert stored_prediction is not None
    assert stored_prediction.memo is not None


def test_run_prediction_retries_after_timeout(db_session: Session) -> None:
    race, entries = _create_race_with_entries(db_session)
    gateway = ScriptedGateway(
        responses=[
            _inference_result(entries, elapsed_ms=5000),
            _inference_result(entries, elapsed_ms=300),
        ]
    )
    runner = PredictionRunner(
        db=db_session,
        model_gateway=gateway,
        timeout_seconds=1.0,
        max_retries=2,
    )
    request = PredictionInput(race_id=race.id)

    result = runner.run(request, user_id=1)

    assert gateway.calls == 2
    assert result.metadata.elapsed_ms == 300


def test_run_prediction_raises_timeout_after_exceeding_retries(db_session: Session) -> None:
    race, entries = _create_race_with_entries(db_session)
    timeout_result = _inference_result(entries, elapsed_ms=10_000)
    gateway = ScriptedGateway(responses=[timeout_result])
    runner = PredictionRunner(
        db=db_session,
        model_gateway=gateway,
        timeout_seconds=0.5,
        max_retries=1,
    )
    request = PredictionInput(race_id=race.id)

    existing_prediction_ids = list(db_session.scalars(select(Prediction.id)))

    with pytest.raises(PredictionTimeoutError):
        runner.run(request, user_id=1)

    remaining_prediction_ids = list(db_session.scalars(select(Prediction.id)))
    assert remaining_prediction_ids == existing_prediction_ids


