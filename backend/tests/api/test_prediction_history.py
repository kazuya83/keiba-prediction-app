from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import prediction as prediction_crud
from app.models.prediction import PredictionResult
from app.models.race import Race, RaceEntry
from app.models.user import User
from app.models.horse import Horse


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_user(test_client: TestClient, email: str = "predictor@example.com") -> str:
    response = test_client.post(
        "/api/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _get_user_by_email(db_session: Session, email: str) -> User:
    user = db_session.query(User).filter(User.email == email).one()
    return user


def _create_race_with_entries(db_session: Session) -> tuple[Race, list[RaceEntry]]:
    race = Race(
        name="テストレース",
        race_date=date(2024, 11, 9),
        venue="東京",
        course_type="芝",
        distance=1800,
    )
    db_session.add(race)

    horses = [
        Horse(name="テストホース1"),
        Horse(name="テストホース2"),
        Horse(name="テストホース3"),
    ]
    db_session.add_all(horses)
    db_session.flush()

    entries = []
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


def test_list_predictions_returns_items_and_stats(
    test_client: TestClient,
    db_session: Session,
) -> None:
    email = "history@example.com"
    token = _register_user(test_client, email=email)
    user = _get_user_by_email(db_session, email)
    race, entries = _create_race_with_entries(db_session)

    prediction_crud.create_prediction(
        db_session,
        user_id=user.id,
        race_id=race.id,
        prediction_at=datetime(2024, 11, 1, tzinfo=timezone.utc),
        result=PredictionResult.HIT,
        payout=Decimal("150.00"),
        stake_amount=Decimal("100.00"),
        picks=[
            prediction_crud.PredictionPickInput(
                rank=1,
                race_entry_id=entries[0].id,
                probability=Decimal("0.45"),
            ),
            prediction_crud.PredictionPickInput(
                rank=2,
                race_entry_id=entries[1].id,
                probability=Decimal("0.35"),
            ),
        ],
    )
    prediction_crud.create_prediction(
        db_session,
        user_id=user.id,
        race_id=race.id,
        prediction_at=datetime(2024, 11, 2, tzinfo=timezone.utc),
        result=PredictionResult.MISS,
        payout=Decimal("0"),
        stake_amount=Decimal("100.00"),
        picks=[
            prediction_crud.PredictionPickInput(
                rank=1,
                race_entry_id=entries[2].id,
                probability=Decimal("0.50"),
            ),
        ],
    )

    response = test_client.get(
        "/api/predictions",
        headers=_auth_headers(token),
        params={"limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    stats = body["stats"]
    assert stats["hit_count"] == 1
    assert Decimal(str(stats["hit_rate"])) == Decimal("0.5000")
    assert Decimal(str(stats["total_stake"])) == Decimal("200.00")
    assert Decimal(str(stats["total_payout"])) == Decimal("150.00")
    assert Decimal(str(stats["return_rate"])) == Decimal("0.7500")

    first_item = body["items"][0]
    assert first_item["result"] == PredictionResult.MISS.value
    assert len(first_item["picks"]) == 1
    assert first_item["picks"][0]["horse_name"] == "テストホース3"


def test_read_prediction_detail_requires_authentication(
    test_client: TestClient,
) -> None:
    response = test_client.get("/api/predictions/1")
    assert response.status_code == 401


def test_read_prediction_detail_returns_prediction(
    test_client: TestClient,
    db_session: Session,
) -> None:
    email = "detail@example.com"
    token = _register_user(test_client, email=email)
    user = _get_user_by_email(db_session, email)
    race, entries = _create_race_with_entries(db_session)

    prediction = prediction_crud.create_prediction(
        db_session,
        user_id=user.id,
        race_id=race.id,
        prediction_at=datetime(2024, 11, 3, tzinfo=timezone.utc),
        result=PredictionResult.HIT,
        payout=Decimal("210.00"),
        stake_amount=Decimal("100.00"),
        memo="confidence high",
        picks=[
            prediction_crud.PredictionPickInput(
                rank=1,
                race_entry_id=entries[0].id,
                probability=Decimal("0.55"),
            ),
        ],
    )

    response = test_client.get(
        f"/api/predictions/{prediction.id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == prediction.id
    assert body["memo"] == "confidence high"
    assert body["payout"] == "210.00"
    assert len(body["picks"]) == 1
    assert body["picks"][0]["horse_name"] == "テストホース1"


def test_compare_predictions_returns_history(
    test_client: TestClient,
    db_session: Session,
) -> None:
    email = "compare@example.com"
    token = _register_user(test_client, email=email)
    user = _get_user_by_email(db_session, email)
    race, entries = _create_race_with_entries(db_session)

    earlier = prediction_crud.create_prediction(
        db_session,
        user_id=user.id,
        race_id=race.id,
        prediction_at=datetime(2024, 10, 25, tzinfo=timezone.utc),
        result=PredictionResult.MISS,
        payout=Decimal("0"),
        stake_amount=Decimal("100.00"),
        picks=[
            prediction_crud.PredictionPickInput(
                rank=1,
                race_entry_id=entries[1].id,
                probability=Decimal("0.40"),
            ),
        ],
    )
    latest = prediction_crud.create_prediction(
        db_session,
        user_id=user.id,
        race_id=race.id,
        prediction_at=datetime(2024, 10, 30, tzinfo=timezone.utc),
        result=PredictionResult.HIT,
        payout=Decimal("120.00"),
        stake_amount=Decimal("100.00"),
        picks=[
            prediction_crud.PredictionPickInput(
                rank=1,
                race_entry_id=entries[0].id,
                probability=Decimal("0.42"),
            ),
        ],
    )

    response = test_client.get(
        f"/api/predictions/{latest.id}/compare",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["current"]["id"] == latest.id
    assert len(body["history"]) == 1
    assert body["history"][0]["id"] == earlier.id
    assert body["history"][0]["result"] == PredictionResult.MISS.value


