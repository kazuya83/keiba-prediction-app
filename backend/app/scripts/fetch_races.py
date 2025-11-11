"""スクレイピングでレースデータを取得し、DB へ取り込むユーティリティスクリプト。"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence

from app.db.session import SessionLocal
from app.schemas.scraping import ScrapedRace, ScrapingSite
from app.scraping import (
    AsyncThrottledClient,
    JRARaceScraper,
    LocalKeibaRaceScraper,
    NetkeibaRaceScraper,
    get_policy,
)
from app.services import RaceDataImporter

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY = {
    ScrapingSite.NETKEIBA: NetkeibaRaceScraper,
    ScrapingSite.JRA: JRARaceScraper,
    ScrapingSite.LOCAL_KEIBA: LocalKeibaRaceScraper,
}


async def _scrape_races(site: ScrapingSite, race_ids: Sequence[str]) -> list[ScrapedRace]:
    policy = get_policy(site.value)
    client = AsyncThrottledClient(policy)
    scraper_class = SCRAPER_REGISTRY[site]
    scraper = scraper_class(client)
    results: list[ScrapedRace] = []

    try:
        for race_id in race_ids:
            logger.info("Scraping %s race %s", site.value, race_id)
            race = await scraper.scrape(race_id)
            results.append(race)
    finally:
        await client.close()

    return results


async def _run_async(site_name: str, race_ids: Sequence[str]) -> None:
    site = ScrapingSite(site_name)
    scraped = await _scrape_races(site, race_ids)

    session = SessionLocal()
    importer = RaceDataImporter(session)
    try:
        summary = importer.import_races(scraped)
    finally:
        session.close()

    logger.info(
        "Import summary",
        extra={
            "created": summary.created,
            "updated": summary.updated,
            "skipped": summary.skipped,
            "failed": summary.failed,
            "errors": summary.errors,
        },
    )

    print(
        f"Import completed: created={summary.created}, "
        f"updated={summary.updated}, skipped={summary.skipped}, failed={summary.failed}"
    )
    if summary.errors:
        print("Errors:")
        for error in summary.errors:
            print(f"  - {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="スクレイピングでレース情報を取得する。")
    parser.add_argument(
        "--site",
        choices=[site.value for site in ScrapingSite],
        required=True,
        help="スクレイピング対象サイト",
    )
    parser.add_argument(
        "--race-id",
        action="append",
        dest="race_ids",
        required=True,
        help="取得対象のレース ID (複数指定可)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        asyncio.run(_run_async(args.site, args.race_ids))
    except KeyboardInterrupt:  # pragma: no cover - 手動中断時
        print("Interrupted by user")


if __name__ == "__main__":
    main()


