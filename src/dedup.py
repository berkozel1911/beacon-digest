"""Persisted dedup state: which feed items have already been shown.

State is a flat JSON map of {guid: first_seen_date (YYYY-MM-DD, UTC)}. Plain
JSON was chosen over SQLite deliberately: it's plain text, so git diffs are
readable and the file is inspectable by hand. Old entries are pruned so the
file doesn't grow forever -- feed items age out of relevance long before
30 days pass.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.fetch import Item

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "seen_items.json"

DATE_FMT = "%Y-%m-%d"


def _today() -> str:
    return datetime.now(timezone.utc).strftime(DATE_FMT)


def load_state(state_path: Path = DEFAULT_STATE_PATH) -> dict[str, str]:
    if not state_path.exists():
        return {}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict[str, str], state_path: Path = DEFAULT_STATE_PATH) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def filter_new(items: list[Item], state: dict[str, str]) -> tuple[list[Item], dict[str, str]]:
    """Split items into (new_items, updated_state). Every item's guid gets
    recorded in the returned state, whether it was already known or not."""
    new_items: list[Item] = []
    updated_state = dict(state)
    today = _today()

    for item in items:
        if item.guid not in updated_state:
            new_items.append(item)
            updated_state[item.guid] = today

    return new_items, updated_state


def prune_old(state: dict[str, str], days: int = 30) -> dict[str, str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    pruned = {}
    for guid, first_seen in state.items():
        try:
            seen_date = datetime.strptime(first_seen, DATE_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if seen_date >= cutoff:
            pruned[guid] = first_seen
    return pruned
