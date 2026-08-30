"""Placeholder output backend for a future 'send digest by email' phase.

Not implemented yet -- SMTP/relay configuration is deliberately deferred.
This file exists only so the output-selection seam in main.py already has
the shape it will need later, without a rewrite.
"""
from __future__ import annotations

from pathlib import Path

from src.output.base import OutputBackend


class EmailOutput(OutputBackend):
    def render(self, markdown_path: Path, output_basename: str) -> None:
        raise NotImplementedError("Email output is not implemented yet.")
