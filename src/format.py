"""Render new feed items into a Markdown digest, grouped by category.

This module only groups and lays out what fetch.py already extracted --
headlines, excerpts, and links are reproduced as published, never
summarized or paraphrased.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone

from src.fetch import Item


def _group_by_category(items: list[Item]) -> tuple[OrderedDict, dict]:
    grouped: OrderedDict = OrderedDict()
    display_names: dict = {}
    for item in items:
        grouped.setdefault(item.category_key, []).append(item)
        display_names[item.category_key] = item.category_display
    return grouped, display_names


def render_markdown(items: list[Item], digest_date: str | None = None) -> str:
    digest_date = digest_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grouped, display_names = _group_by_category(items)

    lines = [f"# Beacon Digest -- {digest_date}", ""]

    for category_key, category_items in grouped.items():
        lines.append(f"## {display_names[category_key]}")
        lines.append("")
        for item in category_items:
            lines.append(f"### [{item.title}]({item.link})")
            lines.append(f"*Source: {item.source}*")
            lines.append("")
            if item.excerpt:
                lines.append(f"> {item.excerpt}")
                lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
