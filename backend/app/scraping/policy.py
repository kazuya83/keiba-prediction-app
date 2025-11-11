"""スクレイピング時のサイト別アクセス方針を定義するモジュール。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class SiteAccessPolicy:
    """スクレイピング時に遵守すべきアクセス方針。"""

    site_name: str
    base_url: str
    robots_url: str | None
    user_agent: str
    request_interval_seconds: float
    max_concurrency: int
    timeout_seconds: float
    retry_max_attempts: int
    retry_wait_seconds: float


DEFAULT_USER_AGENT: Final[str] = os.getenv(
    "SCRAPING_USER_AGENT",
    "KeibaDataCollector/0.1 (+https://example.com/contact; respect-robots.txt)",
)


def _env_float(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


SCRAPING_POLICIES: Final[dict[str, SiteAccessPolicy]] = {
    "netkeiba": SiteAccessPolicy(
        site_name="netkeiba",
        base_url="https://race.netkeiba.com",
        robots_url="https://race.netkeiba.com/robots.txt",
        user_agent=DEFAULT_USER_AGENT,
        request_interval_seconds=_env_float("SCRAPING_NETKEIBA_INTERVAL", 2.0),
        max_concurrency=_env_int("SCRAPING_NETKEIBA_CONCURRENCY", 2),
        timeout_seconds=_env_float("SCRAPING_NETKEIBA_TIMEOUT", 15.0),
        retry_max_attempts=_env_int("SCRAPING_NETKEIBA_RETRY_MAX", 3),
        retry_wait_seconds=_env_float("SCRAPING_NETKEIBA_RETRY_WAIT", 2.0),
    ),
    "jra": SiteAccessPolicy(
        site_name="jra",
        base_url="https://www.jra.go.jp",
        robots_url="https://www.jra.go.jp/robots.txt",
        user_agent=DEFAULT_USER_AGENT,
        request_interval_seconds=_env_float("SCRAPING_JRA_INTERVAL", 3.0),
        max_concurrency=_env_int("SCRAPING_JRA_CONCURRENCY", 1),
        timeout_seconds=_env_float("SCRAPING_JRA_TIMEOUT", 20.0),
        retry_max_attempts=_env_int("SCRAPING_JRA_RETRY_MAX", 3),
        retry_wait_seconds=_env_float("SCRAPING_JRA_RETRY_WAIT", 3.0),
    ),
    "local_keiba": SiteAccessPolicy(
        site_name="local_keiba",
        base_url="https://www.keiba.go.jp",
        robots_url="https://www.keiba.go.jp/robots.txt",
        user_agent=DEFAULT_USER_AGENT,
        request_interval_seconds=_env_float("SCRAPING_LOCAL_INTERVAL", 3.0),
        max_concurrency=_env_int("SCRAPING_LOCAL_CONCURRENCY", 1),
        timeout_seconds=_env_float("SCRAPING_LOCAL_TIMEOUT", 20.0),
        retry_max_attempts=_env_int("SCRAPING_LOCAL_RETRY_MAX", 3),
        retry_wait_seconds=_env_float("SCRAPING_LOCAL_RETRY_WAIT", 3.0),
    ),
}


def get_policy(site_name: str) -> SiteAccessPolicy:
    """サイト名からアクセスポリシーを取得する。"""
    try:
        return SCRAPING_POLICIES[site_name]
    except KeyError as exc:  # pragma: no cover - 呼び出し側で防ぐ想定
        raise KeyError(f"Unknown site policy: {site_name}") from exc


__all__ = ["SCRAPING_POLICIES", "SiteAccessPolicy", "get_policy"]


