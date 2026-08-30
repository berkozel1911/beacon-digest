"""Interface all output backends implement.

main.py calls only this interface -- swapping PdfOutput for a future
EmailOutput is a one-line change there, nothing upstream needs to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class OutputBackend(ABC):
    @abstractmethod
    def render(self, markdown_path: Path, output_basename: str) -> None:
        """Consume the rendered Markdown digest and deliver it -- write a
        PDF, send an email, etc., depending on the backend."""
        raise NotImplementedError
