"""CRUD 操作をまとめるパッケージ。"""

from app.crud.race import (
    RaceRepository,
    SqlAlchemyRaceRepository,
    create_race_entry,
    create_weather,
    get_or_create_horse,
    get_or_create_jockey,
    get_or_create_trainer,
)
from app.crud.prediction import (
    PredictionComparisonResult,
    PredictionListParams,
    PredictionListResult,
    PredictionPickInput,
    PredictionStatsData,
    create_prediction,
    get_prediction,
    get_prediction_comparison,
    get_prediction_or_raise,
    list_predictions,
)
from app.crud.user import (
    create_user,
    get_user,
    get_user_by_email,
    update_user,
)

__all__ = [
    "RaceRepository",
    "SqlAlchemyRaceRepository",
    "create_race_entry",
    "create_prediction",
    "create_user",
    "create_weather",
    "get_or_create_horse",
    "get_or_create_jockey",
    "get_or_create_trainer",
    "get_prediction",
    "get_prediction_comparison",
    "get_prediction_or_raise",
    "get_user",
    "get_user_by_email",
    "list_predictions",
    "PredictionComparisonResult",
    "PredictionListParams",
    "PredictionListResult",
    "PredictionPickInput",
    "PredictionStatsData",
    "update_user",
]


