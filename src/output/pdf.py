"""Markdown -> HTML -> PDF output backend, using python-markdown + WeasyPrint.

WeasyPrint was chosen over pandoc+LaTeX because it installs via pip alone
(no system LaTeX toolchain needed in CI) and renders HTML+CSS, which gives
straightforward control over a headline-list layout via a small stylesheet.
"""
from __future__ import annotations

from pathlib import Path

import markdown as md
from weasyprint import HTML

from src.output.base import OutputBackend

_CSS = """
body { font-family: sans-serif; font-size: 11pt; line-height: 1.4; }
h1 { border-bottom: 2px solid #333; padding-bottom: 4px; }
h2 { color: #b5121b; margin-top: 1.5em; border-bottom: 1px solid #ccc; }
h3 { margin-bottom: 0.2em; font-size: 12pt; }
h3 a { color: #1a4b8c; text-decoration: none; }
em { color: #555; font-size: 9.5pt; }
blockquote { margin: 0.3em 0 1em 0; padding-left: 0.8em; border-left: 3px solid #ddd; color: #333; }
"""


class PdfOutput(OutputBackend):
    def render(self, markdown_path: Path, output_basename: str) -> None:
        markdown_text = markdown_path.read_text(encoding="utf-8")
        html_body = md.markdown(markdown_text, extensions=["extra"])
        html_doc = (
            f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head>"
            f"<body>{html_body}</body></html>"
        )

        pdf_path = markdown_path.parent / f"{output_basename}.pdf"
        HTML(string=html_doc).write_pdf(pdf_path)
