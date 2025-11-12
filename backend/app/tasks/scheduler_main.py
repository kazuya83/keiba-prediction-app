"""スケジューラを起動するメインスクリプト。"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from app.core.logging import configure_logging
from app.tasks.scheduler import SchedulerConfig, setup_scheduler

logger = logging.getLogger(__name__)

_scheduler = None


def signal_handler(signum: int, frame: object) -> None:
    """シグナルハンドラ。"""
    logger.info("Received signal %d, shutting down scheduler", signum)
    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
    sys.exit(0)


async def main() -> None:
    """メイン処理。"""
    global _scheduler

    configure_logging()
    logger.info("Starting scheduler")

    # シグナルハンドラを登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # スケジューラを設定
    config = SchedulerConfig.from_env()
    _scheduler = setup_scheduler(config)

    try:
        # スケジューラを起動
        _scheduler.start()
        logger.info("Scheduler started")

        # 無限ループで待機
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as exc:
        logger.exception("Unexpected error", exc_info=exc)
        raise
    finally:
        if _scheduler is not None:
            _scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())

