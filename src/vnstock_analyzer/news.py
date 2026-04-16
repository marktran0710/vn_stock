from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen
import re
import unicodedata
import xml.etree.ElementTree as ET


VNEXPRESS_STOCK_FEEDS = [
    "https://vnexpress.net/rss/kinh-doanh/chung-khoan.rss",
    "https://vnexpress.net/rss/kinh-doanh.rss",
]

STOCK_KEYWORDS = {
    "chung khoan",
    "co phieu",
    "vn-index",
    "vnindex",
    "hose",
    "hnx",
    "upcom",
    "niem yet",
    "thi truong",
    "gia co",
}


@dataclass
class NewsItem:
    title: str
    link: str
    published_at: str | None
    source: str


def _normalize_text(value: str) -> str:
    lowered = value.lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_only).strip()


def _is_stock_related(title: str, description: str) -> bool:
    content = _normalize_text(f"{title} {description}")
    return any(keyword in content for keyword in STOCK_KEYWORDS)


def _parse_pub_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return value
    if dt is None:
        return value
    return dt.strftime("%Y-%m-%d %H:%M")


def _read_feed(feed_url: str) -> list[NewsItem]:
    req = Request(feed_url, headers={"User-Agent": "VNStockAnalyzer/1.0"})
    with urlopen(req, timeout=15) as response:  # nosec B310
        payload = response.read()

    root = ET.fromstring(payload)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[NewsItem] = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = unescape((item.findtext("description") or "").strip())
        pub_date = _parse_pub_date(item.findtext("pubDate"))

        if not title or not link:
            continue
        if not _is_stock_related(title, description):
            continue

        items.append(
            NewsItem(
                title=title,
                link=link,
                published_at=pub_date,
                source="VNExpress",
            )
        )
    return items


def fetch_vnexpress_stock_news(limit: int = 10, feeds: Iterable[str] | None = None) -> list[NewsItem]:
    selected_feeds = list(feeds) if feeds else VNEXPRESS_STOCK_FEEDS

    collected: list[NewsItem] = []
    seen_links: set[str] = set()

    for feed_url in selected_feeds:
        try:
            feed_items = _read_feed(feed_url)
        except (URLError, TimeoutError, ET.ParseError, ValueError):
            continue

        for item in feed_items:
            if item.link in seen_links:
                continue
            seen_links.add(item.link)
            collected.append(item)

    collected.sort(key=lambda row: row.published_at or "", reverse=True)
    return collected[:limit]
