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
    "create_user",
    "create_weather",
    "get_or_create_horse",
    "get_or_create_jockey",
    "get_or_create_trainer",
    "get_user",
    "get_user_by_email",
    "update_user",
]


