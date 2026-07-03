from __future__ import annotations

from typing import List, Optional
from openpyxl.worksheet.worksheet import Worksheet

from src.metadata_engine.models import WorksheetMetadata


class HeaderReader:
    def __init__(self, worksheet: Worksheet, metadata: Optional[WorksheetMetadata] = None):
        self._ws = worksheet
        self._metadata = metadata

    def read_headers(self) -> List[Optional[str]]:
        # Prefer metadata headers if available
        if self._metadata and self._metadata.headers:
            return self._metadata.headers
        # Otherwise, choose first non-empty row
        for row in self._ws.iter_rows(min_row=1, max_row=10, values_only=True):
            if any(cell is not None and str(cell).strip() != "" for cell in row):
                return [str(cell).strip() if cell is not None else None for cell in row]
        return []
