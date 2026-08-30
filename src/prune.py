"""Deletes committed digest output files (output/digest-*.md, .pdf) older
than N days. Run as a step after the daily digest is generated, so the
repo's working tree doesn't accumulate outputs forever.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
_FILENAME_DATE_RE = re.compile(r"digest-(\d{4}-\d{2}-\d{2})\.")


def prune(output_dir: Path = OUTPUT_DIR, days: int = 30) -> list[Path]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    removed = []
    if not output_dir.exists():
        return removed

    for path in output_dir.iterdir():
        match = _FILENAME_DATE_RE.search(path.name)
        if not match:
            continue
        file_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if file_date < cutoff:
            path.unlink()
            removed.append(path)
    return removed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    removed_paths = prune(days=args.days)
    for path in removed_paths:
        print(f"Pruned {path}")
    print(f"Pruned {len(removed_paths)} file(s) older than {args.days} days.")
