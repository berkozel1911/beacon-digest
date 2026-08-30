# beacon-digest

A serverless, GitHub Actions-based daily digest of headlines from primary
sources across Linux, DevOps, Security, and AI. Runs on a schedule, dedupes
against previously seen items, and produces a PDF -- no server, no database,
no email relay (yet).

This is a **headline aggregator, not a summarizer**. Every entry reproduces
the source's own published headline and excerpt/description field verbatim
-- nothing here rewrites, paraphrases, or summarizes article content.

## How it works

```
config/sources.yml  --(read at runtime)-->  src/fetch.py
                                                  |
                                                  v
                                          src/dedup.py  <--> state/seen_items.json
                                                  |
                                                  v
                                          src/format.py  (Markdown)
                                                  |
                                                  v
                                       src/output/pdf.py  (PDF via WeasyPrint)
```

- **`config/sources.yml`** -- the only file you edit to add a category or a
  source. Nothing in `src/` hardcodes category or source names.
- **`src/fetch.py`** -- pulls each feed via `feedparser`, normalizes RSS/Atom
  entries into a common `Item` shape (category, source, title, link, excerpt,
  guid, published date). A single broken feed logs a warning and is skipped;
  it never aborts the whole run.
- **`src/dedup.py`** -- tracks which items have already been shown, in
  `state/seen_items.json` (`{guid: first_seen_date}`). Entries older than 30
  days are pruned automatically. **First run is a bootstrap**: it seeds the
  state with everything currently in the feeds but produces no digest that
  day, since several feeds (e.g. OpenAI, Hugging Face) return their entire
  back catalog and would otherwise produce a several-thousand-item digest on
  day one.
- **`src/format.py`** -- groups new items by category (in the order they
  appear in `sources.yml`) and renders Markdown. No templating engine; the
  layout is simple enough that plain string building is clearer than adding
  a dependency.
- **`src/output/`** -- pluggable output backends behind one interface
  (`OutputBackend.render(markdown_path, output_basename)`). `pdf.py` is the
  only implemented backend today; `email.py` is a stub reserving the same
  interface for a future SMTP-based phase, so swapping outputs later is a
  one-line change in `main.py`, not a rewrite.
- **`src/main.py`** -- orchestrates the whole pipeline.
- **`src/prune.py`** -- deletes `output/digest-*.{md,pdf}` files older than
  30 days, run as a separate workflow step after each digest is generated.

## Running it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Output lands in `output/digest-YYYY-MM-DD.{md,pdf}`; dedup state lands in
`state/seen_items.json`.

Note: WeasyPrint needs the system **Pango** library installed (not just the
Python package) to render PDFs. On Debian/Ubuntu:

```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0
```

## GitHub Actions

`.github/workflows/digest.yml` runs daily at 05:00 UTC (08:00 Istanbul time,
fixed offset, no DST) and can also be triggered manually via
`workflow_dispatch`. Each run:

1. Fetches all feeds, dedupes against `state/seen_items.json`.
2. Renders and writes `output/digest-<date>.md` and `.pdf`.
3. Prunes digest output files older than 30 days from the working tree.
4. Commits the updated state and output files back to the repo via
   `git-auto-commit-action`.

Note on pruning: it removes old files from the working tree, not from git
history/objects -- the blobs remain in past commits unless history is
rewritten. Fine for now; worth revisiting if repo size ever becomes a
concern.

## Design decisions (why, not just what)

- **JSON over SQLite for dedup state** -- plain text, readable git diffs,
  inspectable by hand. We only need a seen-set with a first-seen date, not
  real querying.
- **Commit digest outputs to the repo (with pruning) over Actions
  artifacts-only** -- browsable directly in the repo without going through
  the Actions UI; artifacts expire on a fixed retention window regardless.
- **WeasyPrint over Pandoc+LaTeX** -- pip-installable only (no apt-installed
  LaTeX toolchain), and HTML+CSS gives direct control over a headline-list
  layout, which is a better fit than LaTeX's prose-oriented typesetting.
- **Config-driven categories and sources** -- `sources.yml` categories carry
  an explicit `key` and `display_name` rather than deriving the label from
  the key in code, specifically so adding "devops" -> "DevOps" or "ai" ->
  "AI" doesn't require hardcoding category-specific capitalization rules.

## Not yet implemented (by design)

Email delivery is deliberately out of scope for this phase. The output-step
seam (`src/output/base.py`) is already in place so adding it later means
implementing `EmailOutput.render()` and pointing `main.py` at it -- not
restructuring the pipeline.
