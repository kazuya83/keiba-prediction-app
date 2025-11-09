from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.routers import predictions as predictions_router
from app.models.horse import Horse
from app.models.prediction import Prediction
from app.models.race import Race, RaceEntry
from app.models.user import User
from app.services.prediction_runner import (
    InferenceRanking,
    ModelInferenceResult,
    PredictionFeatureContribution,
    PredictionInput,
    PredictionJobResult,
    PredictionJobStatus,
    PredictionRunner,
    PredictionRunnerError,
    PredictionTimeoutError,
)


def _create_race_with_entries(db_session: Session) -> tuple[Race, list[RaceEntry]]:
    race = Race(
        name="インテグレーションレース",
        race_date=date(2024, 11, 9),
        venue="京都",
        course_type="芝",
        distance=2000,
    )
    db_session.add(race)

    horses = [Horse(name="インテグホース1"), Horse(name="インテグホース2"), Horse(name="インテグホース3")]
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


def _model_inference_result(entries: list[RaceEntry]) -> ModelInferenceResult:
    rankings = [
        InferenceRanking(
            race_entry_id=entries[0].id,
            probability=Decimal("0.5000"),
            confidence_interval=(Decimal("0.4500"), Decimal("0.5500")),
        ),
        InferenceRanking(
            race_entry_id=entries[1].id,
            probability=Decimal("0.3000"),
            confidence_interval=(Decimal("0.2500"), Decimal("0.3500")),
        ),
        InferenceRanking(
            race_entry_id=entries[2].id,
            probability=Decimal("0.2000"),
            confidence_interval=(Decimal("0.1500"), Decimal("0.2500")),
        ),
    ]
    contributions = [
        PredictionFeatureContribution(
            feature_id="speed_index",
            importance=Decimal("0.4"),
            shap_value=Decimal("0.16"),
        ),
        PredictionFeatureContribution(
            feature_id="pace_bias",
            importance=Decimal("0.35"),
            shap_value=Decimal("0.14"),
        ),
        PredictionFeatureContribution(
            feature_id="trainer_win_rate",
            importance=Decimal("0.25"),
            shap_value=Decimal("0.10"),
        ),
    ]
    return ModelInferenceResult(
        rankings=rankings,
        feature_contributions=contributions,
        model_version="integration-model-v1",
        elapsed_ms=450,
    )


def test_execute_prediction_returns_job_response(
    test_client: TestClient,
    db_session: Session,
) -> None:
    race, entries = _create_race_with_entries(db_session)
    user = User(email="runner@example.com", hashed_password="dummy", is_active=True)
    db_session.add(user)
    db_session.flush()
    initial_prediction_ids = list(
        db_session.scalars(select(Prediction.id).where(Prediction.user_id == user.id))
    )

    inference_result = _model_inference_result(entries)

    class StaticGateway:
        def infer(self, *args, **kwargs) -> ModelInferenceResult:
            return inference_result

    def _override_runner() -> PredictionRunner:
        return PredictionRunner(
            db=db_session,
            model_gateway=StaticGateway(),
            timeout_seconds=2.0,
            max_retries=1,
        )

    def _override_user() -> User:
        return user

    test_client.app.dependency_overrides[predictions_router.get_prediction_runner] = _override_runner
    test_client.app.dependency_overrides[get_current_active_user] = _override_user

    try:
        response = test_client.post(
            "/api/predictions",
            json={
                "raceId": race.id,
                "modelId": "integration-model",
                "featureSetId": "full",
                "stakeAmount": "150.00",
            },
        )
    finally:
        test_client.app.dependency_overrides.pop(predictions_router.get_prediction_runner, None)
        test_client.app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == PredictionJobStatus.COMPLETED.value
    assert body["predictionId"] is not None
    assert body["metadata"]["modelId"] == "integration-model"
    assert len(body["rankings"]) == 3
    assert body["rankings"][0]["horseName"] == "インテグホース1"
    assert body["rankings"][0]["confidenceInterval"]["lower"] == "0.4500"

    saved_predictions = db_session.scalars(select(Prediction).where(Prediction.user_id == user.id)).all()
    assert len(saved_predictions) == len(initial_prediction_ids) + 1


def test_execute_prediction_returns_504_on_timeout(
    test_client: TestClient,
    db_session: Session,
) -> None:
    race, _ = _create_race_with_entries(db_session)
    user = User(email="timeout@example.com", hashed_password="dummy", is_active=True)
    db_session.add(user)
    db_session.flush()

    class TimeoutRunner(PredictionRunner):
        def run(self, request: PredictionInput, *, user_id: int) -> PredictionJobResult:  # type: ignore[override]
            raise PredictionTimeoutError("timed out")

    def _override_runner() -> PredictionRunner:
        return TimeoutRunner(db=db_session)

    def _override_user() -> User:
        return user

    test_client.app.dependency_overrides[predictions_router.get_prediction_runner] = _override_runner
    test_client.app.dependency_overrides[get_current_active_user] = _override_user

    try:
        response = test_client.post(
            "/api/predictions",
            json={"raceId": race.id},
        )
    finally:
        test_client.app.dependency_overrides.pop(predictions_router.get_prediction_runner, None)
        test_client.app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 504
    assert response.json()["detail"] == "推論処理がタイムアウトしました。"


def test_execute_prediction_returns_503_on_failure(
    test_client: TestClient,
    db_session: Session,
) -> None:
    race, _ = _create_race_with_entries(db_session)
    user = User(email="failure@example.com", hashed_password="dummy", is_active=True)
    db_session.add(user)
    db_session.flush()

    class FailingRunner(PredictionRunner):
        def run(self, request: PredictionInput, *, user_id: int) -> PredictionJobResult:  # type: ignore[override]
            raise PredictionRunnerError("failed")

    def _override_runner() -> PredictionRunner:
        return FailingRunner(db=db_session)

    def _override_user() -> User:
        return user

    test_client.app.dependency_overrides[predictions_router.get_prediction_runner] = _override_runner
    test_client.app.dependency_overrides[get_current_active_user] = _override_user

    try:
        response = test_client.post(
            "/api/predictions",
            json={"raceId": race.id},
        )
    finally:
        test_client.app.dependency_overrides.pop(predictions_router.get_prediction_runner, None)
        test_client.app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "予測実行に失敗しました。"


