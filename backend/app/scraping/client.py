"""HTTP 通信を行う非同期スクレイピングクライアント。"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_fixed

from app.scraping.exceptions import FetchError, RateLimitError
from app.scraping.policy import SiteAccessPolicy

logger = logging.getLogger(__name__)


class AsyncThrottledClient:
    """レート制御とリトライ機能を備えた httpx.AsyncClient ラッパー。"""

    def __init__(self, policy: SiteAccessPolicy) -> None:
        self._policy = policy
        self._client = httpx.AsyncClient(
            base_url=policy.base_url,
            headers={"User-Agent": policy.user_agent},
            timeout=policy.timeout_seconds,
        )
        self._concurrency = asyncio.Semaphore(policy.max_concurrency)
        self._rate_lock = asyncio.Lock()
        self._last_request_timestamp = 0.0

    async def close(self) -> None:
        """内部 httpx クライアントをクローズする。"""
        await self._client.aclose()

    @asynccontextmanager
    async def _acquire_slot(self) -> AsyncIterator[None]:
        await self._concurrency.acquire()
        try:
            await self._respect_rate_limit()
            yield
        finally:
            self._concurrency.release()

    async def _respect_rate_limit(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_timestamp
            wait_time = self._policy.request_interval_seconds - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request_timestamp = time.monotonic()

    async def get_text(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """指定 URL から HTML を取得する。"""
        retrying = AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self._policy.retry_max_attempts),
            wait=wait_fixed(self._policy.retry_wait_seconds),
        )

        async for attempt in retrying:
            with attempt:
                async with self._acquire_slot():
                    try:
                        response = await self._client.get(
                            url,
                            headers=headers,
                            params=params,
                        )
                    except httpx.TimeoutException as exc:
                        logger.warning(
                            "Scraping request timed out",
                            extra={"url": url, "site": self._policy.site_name},
                        )
                        raise FetchError(url=url, message="timeout") from exc
                    except httpx.HTTPError as exc:
                        logger.warning(
                            "HTTP error during scraping",
                            extra={"url": url, "site": self._policy.site_name},
                        )
                        raise FetchError(url=url, message=str(exc)) from exc

                    if response.status_code == 429:
                        logger.warning(
                            "Received 429 from %s",
                            self._policy.site_name,
                            extra={"url": url},
                        )
                        raise RateLimitError("Too many requests")

                    if response.status_code >= 400:
                        raise FetchError(
                            url=url,
                            status_code=response.status_code,
                            message=response.text[:200],
                        )

                    logger.debug(
                        "Fetched url successfully",
                        extra={
                            "url": url,
                            "site": self._policy.site_name,
                            "attempt": attempt.retry_state.attempt_number,
                        },
                    )
                    return response.text

        raise RetryError("Failed to fetch URL")  # pragma: no cover - tenacity が例外を返す想定


__all__ = ["AsyncThrottledClient"]


