"""地方競馬全国協会(NAR) のレース情報スクレイパー実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from selectolax.parser import HTMLParser, Node

from app.scraping.base import BaseRaceScraper
from app.scraping.utils import (
    normalize_text,
    parse_course,
    parse_date,
    parse_grade_from_name,
    parse_start_time,
)
from app.schemas.scraping import ScrapingSite


def _text(node: Node | None) -> str:
    return normalize_text(node.text()) if node else ""


def _attr(node: Node | None, key: str) -> str | None:
    if node is None:
        return None
    return node.attributes.get(key)


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


class LocalKeibaRaceScraper(BaseRaceScraper):
    """地方競馬サイトの出走表を解析するスクレイパー。"""

    site = ScrapingSite.LOCAL_KEIBA

    def build_url(self, race_id: str) -> str:
        return f"/Race/RaceDetail/{race_id}"

    def _extract_payload(
        self,
        *,
        tree: HTMLParser,
        race_id: str,
        raw_html: str,
    ) -> dict[str, Any]:
        header = tree.css_first(".nar-race-header")
        if header is None:
            raise ValueError("race header not found")

        title = _text(header.css_first(".nar-race-header__title"))
        race_date = parse_date(_text(header.css_first(".nar-race-header__date")))
        venue_text = _text(header.css_first(".nar-race-header__venue"))
        venue = venue_text.split()[0] if venue_text else ""
        course_type, distance = parse_course(_text(header.css_first(".nar-race-header__course")))
        track_condition = _text(header.css_first(".nar-race-header__track"))
        weather = _text(header.css_first(".nar-race-header__weather"))
        start_time = parse_start_time(race_date, _text(header.css_first(".nar-race-header__start")))

        updated_at_raw = _attr(header, "data-last-modified")
        source_last_modified = (
            datetime.fromisoformat(updated_at_raw) if updated_at_raw else None
        )

        entries: list[dict[str, Any]] = []
        for row in tree.css("table.nar-race-table tbody tr"):
            horse_cell = row.css_first(".nar-race-table__horse")
            horse_name = _text(horse_cell)
            if not horse_name:
                continue

            entry: dict[str, Any] = {
                "horse": {
                    "name": horse_name,
                    "sex": _attr(horse_cell, "data-sex"),
                    "age": _to_int(_attr(horse_cell, "data-age")),
                },
                "jockey_name": _text(row.css_first(".nar-race-table__jockey")),
                "trainer_name": _text(row.css_first(".nar-race-table__trainer")),
                "horse_number": _to_int(_text(row.css_first(".nar-race-table__number"))),
                "post_position": _to_int(_text(row.css_first(".nar-race-table__post"))),
                "final_position": _to_int(_text(row.css_first(".nar-race-table__result"))),
                "odds": _text(row.css_first(".nar-race-table__odds")),
                "carried_weight": _text(row.css_first(".nar-race-table__weight")),
                "comment": _text(row.css_first(".nar-race-table__comment")),
            }
            entries.append(entry)

        payload: dict[str, Any] = {
            "name": title,
            "venue": venue,
            "course_type": course_type,
            "distance": distance,
            "grade": parse_grade_from_name(title),
            "race_date": race_date,
            "start_time": start_time,
            "weather": weather or None,
            "track_condition": track_condition or None,
            "source_last_modified": source_last_modified,
            "entries": entries,
            "raw": {"source_url": self.build_url(race_id)},
        }
        return payload


__all__ = ["LocalKeibaRaceScraper"]


