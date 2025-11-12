"""データ更新ジョブを1回だけ実行するスクリプト。"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.core.logging import configure_logging
from app.tasks.jobs import run_data_update_job

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="データ更新ジョブを1回だけ実行する。")
    parser.add_argument(
        "--site",
        action="append",
        dest="sites",
        choices=["netkeiba", "jra", "local_keiba"],
        help="スクレイピング対象サイト（複数指定可）",
    )
    parser.add_argument(
        "--race-id",
        action="append",
        dest="race_ids",
        help="スクレイピング対象のレースID（複数指定可）",
    )
    parser.add_argument(
        "--no-trigger-training",
        action="store_true",
        help="モデル再学習をトリガーしない",
    )
    return parser.parse_args()


async def main() -> None:
    """メイン処理。"""
    configure_logging()
    args = parse_args()

    from app.schemas.scraping import ScrapingSite

    sites: list[ScrapingSite] | None = None
    if args.sites:
        sites = [ScrapingSite(site) for site in args.sites]

    try:
        logger.info("Starting data update job (run once)")
        result = await run_data_update_job(
            sites=sites,
            race_ids=args.race_ids,
            trigger_model_training=not args.no_trigger_training,
        )

        if result.status.value == "success":
            logger.info("Job completed successfully: %s", result.message)
            print(f"✓ {result.message}")
            sys.exit(0)
        elif result.status.value == "partial":
            logger.warning("Job completed with partial success: %s", result.message)
            print(f"⚠ {result.message}")
            sys.exit(1)
        else:
            logger.error("Job failed: %s", result.message)
            print(f"✗ {result.message}")
            if result.error:
                print(f"Error: {result.error}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("Interrupted by user")
        sys.exit(130)
    except Exception as exc:
        logger.exception("Unexpected error", exc_info=exc)
        print(f"Unexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

