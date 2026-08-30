"""Fetch and normalize entries from the RSS/Atom feeds defined in config/sources.yml.

This module only reads config/sources.yml and network feeds -- it has no
knowledge of dedup state, output format, or which categories exist. Adding a
category or source is purely a config change; nothing here needs to change.
"""
from __future__ import annotations

import calendar
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import feedparser
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "sources.yml"

EXCERPT_MAX_CHARS = 300

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class Item:
    category_key: str
    category_display: str
    source: str
    title: str
    link: str
    excerpt: str
    guid: str
    published: Optional[str]  # ISO 8601 UTC timestamp, or None if the feed omitted one


def load_categories(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["categories"]


def _clean_excerpt(raw: str) -> str:
    """Strip HTML tags from the feed's raw description/summary field.

    This is NOT summarization -- it only removes markup and caps length so
    the excerpt is readable in a headline list. The wording is untouched.
    """
    text = html.unescape(_TAG_RE.sub(" ", raw or ""))
    text = _WS_RE.sub(" ", text).strip()
    if len(text) > EXCERPT_MAX_CHARS:
        text = text[:EXCERPT_MAX_CHARS].rstrip() + "..."
    return text


def _parsed_time_to_iso(struct_time) -> Optional[str]:
    if struct_time is None:
        return None
    return datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc).isoformat()


def fetch_source(category_key: str, category_display: str, name: str, feed_url: str) -> list[Item]:
    """Fetch a single feed. Returns [] (and logs a warning) on any failure --
    one broken source must never take down the whole digest run."""
    try:
        parsed = feedparser.parse(feed_url)
    except Exception:
        logger.warning("Failed to fetch feed for %s (%s)", name, feed_url, exc_info=True)
        return []

    if parsed.bozo and not parsed.entries:
        logger.warning(
            "Feed for %s (%s) failed to parse: %s", name, feed_url, parsed.get("bozo_exception")
        )
        return []

    items: list[Item] = []
    for entry in parsed.entries:
        guid = entry.get("id") or entry.get("link")
        link = entry.get("link", "")
        title = entry.get("title", "").strip()
        raw_excerpt = entry.get("summary") or entry.get("description") or ""
        published = _parsed_time_to_iso(
            entry.get("published_parsed") or entry.get("updated_parsed")
        )

        if not guid or not link or not title:
            logger.warning("Skipping malformed entry from %s: missing title/link/id", name)
            continue

        items.append(
            Item(
                category_key=category_key,
                category_display=category_display,
                source=name,
                title=title,
                link=link,
                excerpt=_clean_excerpt(raw_excerpt),
                guid=guid,
                published=published,
            )
        )
    return items


def fetch_all(config_path: Path = DEFAULT_CONFIG_PATH) -> list[Item]:
    categories = load_categories(config_path)
    all_items: list[Item] = []
    for category in categories:
        for source in category["sources"]:
            all_items.extend(
                fetch_source(
                    category["key"], category["display_name"], source["name"], source["feed_url"]
                )
            )
    return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetched = fetch_all()
    print(f"Fetched {len(fetched)} items total.\n")
    for item in fetched[:20]:
        print(f"[{item.category_display}] {item.source}: {item.title}")
