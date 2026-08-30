"""Orchestrates the daily digest pipeline: fetch -> dedup -> format -> output.

Swapping the output step (e.g. to an email backend later) means changing the
OUTPUT_BACKEND assignment below -- nothing upstream of it needs to change.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from src import dedup, fetch
from src import format as fmt
from src.output.pdf import PdfOutput

logger = logging.getLogger(__name__)

STATE_PATH = dedup.DEFAULT_STATE_PATH
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_BACKEND = PdfOutput()


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    is_first_run = not STATE_PATH.exists()
    state = dedup.load_state(STATE_PATH)

    items = fetch.fetch_all()
    logger.info("Fetched %d items from all sources.", len(items))

    new_items, state = dedup.filter_new(items, state)
    state = dedup.prune_old(state, days=30)
    dedup.save_state(state, STATE_PATH)

    if is_first_run:
        logger.info(
            "First run: seeded dedup state with %d existing items. "
            "No digest generated today -- tomorrow's run will only show new items.",
            len(items),
        )
        return

    if not new_items:
        logger.info("No new items since the last run. Skipping digest generation.")
        return

    digest_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    markdown_text = fmt.render_markdown(new_items, digest_date=digest_date)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_basename = f"digest-{digest_date}"
    markdown_path = OUTPUT_DIR / f"{output_basename}.md"
    markdown_path.write_text(markdown_text, encoding="utf-8")

    OUTPUT_BACKEND.render(markdown_path, output_basename)
    logger.info("Wrote digest for %s with %d new item(s).", digest_date, len(new_items))


if __name__ == "__main__":
    main()
