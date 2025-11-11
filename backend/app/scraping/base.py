"""スクレイパーの抽象基底クラスと共通ユーティリティ。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from selectolax.parser import HTMLParser

from app.scraping.client import AsyncThrottledClient
from app.scraping.exceptions import ParseError
from app.schemas.scraping import ScrapedRace, ScrapingSite

logger = logging.getLogger(__name__)


class BaseRaceScraper(ABC):
    """レース情報スクレイパー共通の抽象クラス。"""

    site: ScrapingSite

    def __init__(self, client: AsyncThrottledClient) -> None:
        self._client = client

    async def scrape(self, race_id: str) -> ScrapedRace:
        """レース ID を指定してスクレイピングを実施する。"""
        html = await self.fetch_html(race_id)
        return self.parse_html(race_id=race_id, html=html)

    async def fetch_html(self, race_id: str) -> str:
        """対象レースページの HTML を取得する。"""
        url = self.build_url(race_id)
        logger.debug(
            "Fetching race page",
            extra={"site": self.site.value, "race_id": race_id, "url": url},
        )
        return await self._client.get_text(url)

    def parse_html(self, *, race_id: str, html: str) -> ScrapedRace:
        """取得済み HTML を解析し、正規化済みレースデータへ変換する。"""
        try:
            tree = HTMLParser(html)
        except Exception as exc:  # pragma: no cover - selectolax の内部例外を捕捉
            raise ParseError("HTML のパースに失敗しました。") from exc

        if tree.body is None:
            raise ParseError("body 要素が存在しません。")

        payload = self._extract_payload(tree=tree, race_id=race_id, raw_html=html)
        payload.setdefault("race_id", race_id)
        payload.setdefault("source", self.site.value)
        payload.setdefault("raw", None)
        payload.setdefault("entries", [])

        try:
            race = ScrapedRace.model_validate(payload)
        except Exception as exc:
            raise ParseError("正規化済みデータへの変換に失敗しました。") from exc

        logger.debug(
            "Parsed race page",
            extra={
                "site": self.site.value,
                "race_id": race.race_id,
                "entry_count": len(race.entries),
            },
        )
        return race

    @abstractmethod
    def build_url(self, race_id: str) -> str:
        """レース ID からアクセスすべき URL を構築する。"""

    @abstractmethod
    def _extract_payload(
        self,
        *,
        tree: HTMLParser,
        race_id: str,
        raw_html: str,
    ) -> dict[str, object]:
        """DOM ツリーから正規化前の辞書データを抽出する。"""


__all__ = ["BaseRaceScraper"]


