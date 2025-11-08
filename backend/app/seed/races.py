"""レース関連テーブルへダミーデータを投入するスクリプト。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud.race import (
    SqlAlchemyRaceRepository,
    create_race_entry,
    create_weather,
    get_or_create_horse,
    get_or_create_jockey,
    get_or_create_trainer,
)
from app.db.session import SessionLocal
from app.models.race import Race


def seed_race_data(session: Session) -> None:
    """テスト用のレースデータを投入する。既に存在する場合は何もしない。"""
    existing_count = session.scalar(select(func.count()).select_from(Race))
    if existing_count and existing_count > 0:
        return

    repository = SqlAlchemyRaceRepository(session)

    # 1件目: 東京芝マイルのレース
    tokyo_weather = create_weather(
        session,
        condition="晴",
        track_condition="良",
        temperature_c=18.5,
        humidity=55.0,
        wind_speed_ms=3.2,
    )
    tokyo_mile = Race(
        name="東京優駿プレップ",
        race_date=date(2024, 5, 12),
        venue="東京",
        course_type="芝",
        distance=1600,
        grade="G2",
        weather=tokyo_weather,
        start_time=datetime(2024, 5, 12, 15, 40),
    )

    horse_sunrise = get_or_create_horse(session, name="サンライズブレイヴ", sex="牡", color="鹿毛")
    horse_moon = get_or_create_horse(session, name="ムーンライトベル", sex="牝", color="青鹿毛")
    horse_wind = get_or_create_horse(session, name="ウィンドコメット", sex="牡", color="黒鹿毛")

    jockey_tanaka = get_or_create_jockey(session, name="田中 健", license_area="JRA", debut_year=2005)
    jockey_suzuki = get_or_create_jockey(session, name="鈴木 一郎", license_area="JRA", debut_year=2010)
    jockey_sato = get_or_create_jockey(session, name="佐藤 智", license_area="JRA", debut_year=2012)

    trainer_kobayashi = get_or_create_trainer(session, name="小林 誠", stable_location="美浦", license_area="JRA")
    trainer_inoue = get_or_create_trainer(session, name="井上 大輔", stable_location="栗東", license_area="JRA")

    create_race_entry(
        race=tokyo_mile,
        horse=horse_sunrise,
        jockey=jockey_tanaka,
        trainer=trainer_kobayashi,
        horse_number=1,
        post_position=1,
        final_position=1,
        odds=2.4,
        carried_weight=57.0,
    )
    create_race_entry(
        race=tokyo_mile,
        horse=horse_moon,
        jockey=jockey_suzuki,
        trainer=trainer_inoue,
        horse_number=2,
        post_position=2,
        final_position=3,
        odds=5.1,
        carried_weight=55.0,
    )
    create_race_entry(
        race=tokyo_mile,
        horse=horse_wind,
        jockey=jockey_sato,
        trainer=trainer_kobayashi,
        horse_number=3,
        post_position=4,
        final_position=2,
        odds=3.8,
        carried_weight=57.0,
    )

    repository.save(tokyo_mile)

    # 2件目: 京都ダート1800mのレース
    kyoto_weather = create_weather(
        session,
        condition="曇",
        track_condition="稍重",
        temperature_c=16.0,
        humidity=65.0,
        wind_speed_ms=2.1,
    )
    kyoto_dirt = Race(
        name="京都クラシックトライアル",
        race_date=date(2024, 11, 3),
        venue="京都",
        course_type="ダート",
        distance=1800,
        grade="G3",
        weather=kyoto_weather,
        start_time=datetime(2024, 11, 3, 14, 20),
    )

    horse_blaze = get_or_create_horse(session, name="ブレイズチャレンジ", sex="牡", color="栗毛")
    horse_aurora = get_or_create_horse(session, name="オーロラスター", sex="牝", color="芦毛")

    jockey_kato = get_or_create_jockey(session, name="加藤 潤", license_area="JRA", debut_year=2008)
    jockey_murata = get_or_create_jockey(session, name="村田 彩", license_area="JRA", debut_year=2015)

    trainer_fujita = get_or_create_trainer(session, name="藤田 亮", stable_location="栗東", license_area="JRA")

    create_race_entry(
        race=kyoto_dirt,
        horse=horse_blaze,
        jockey=jockey_kato,
        trainer=trainer_fujita,
        horse_number=8,
        post_position=7,
        final_position=1,
        odds=4.8,
        carried_weight=57.0,
    )
    create_race_entry(
        race=kyoto_dirt,
        horse=horse_aurora,
        jockey=jockey_murata,
        trainer=trainer_fujita,
        horse_number=9,
        post_position=9,
        final_position=4,
        odds=7.2,
        carried_weight=55.0,
    )

    repository.save(kyoto_dirt)


def main() -> None:
    """スタンドアロン実行用のエントリーポイント。"""
    with SessionLocal() as session:
        seed_race_data(session)


if __name__ == "__main__":
    main()


