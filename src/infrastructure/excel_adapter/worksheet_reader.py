from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional

from openpyxl.worksheet.worksheet import Worksheet

from src.metadata_engine.models import WorksheetMetadata
from .header_reader import HeaderReader
from .row_iterator import RowIterator

logger = logging.getLogger(__name__)


class WorksheetReader:
    def __init__(self, worksheet: Worksheet, metadata: Optional[WorksheetMetadata] = None, logger: Optional[logging.Logger] = None):
        self._ws = worksheet
        self._metadata = metadata
        self._logger = logger or logger

    def get_headers(self) -> List[Optional[str]]:
        hr = HeaderReader(self._ws, self._metadata)
        return hr.read_headers()

    def iter_rows(self) -> Generator[Dict[str, Any], None, None]:
        ri = RowIterator(self._ws, self._metadata, logger=self._logger)
        yield from ri
