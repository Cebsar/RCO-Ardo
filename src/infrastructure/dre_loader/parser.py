from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedHierarchyItem:
    code: str
    label: str
    level: int
    row_number: int
    order: int


class HierarchyParser:
    HEADER_TITLES = {"n1", "n2", "n3", "level", "hierarchy", "label", "description", "name", "code"}
    CODE_TITLES = {"code", "codigo", "id"}
    LEVEL_PATTERN = re.compile(r"^n?(\d+)$", re.IGNORECASE)

    def __init__(self, rows: Sequence[Dict[str, Any]]):
        self.rows = rows

    def parse(self) -> List[ParsedHierarchyItem]:
        header_index, header_row = self._find_header_row()
        self.header_row = header_row
        self.code_column = self._find_code_column(header_row) if header_row else None
        items: List[ParsedHierarchyItem] = []
        order = 0

        for row in self.rows[header_index + 1 :]:
            row_number = int(row.get("_row_number", 0))
            parsed = self._parse_row(row)
            if parsed is None:
                continue
            code, label, level = parsed
            order += 1
            item = ParsedHierarchyItem(code=code, label=label.strip(), level=level, row_number=row_number, order=order)
            logger.debug("Parsed hierarchy item: %s", item)
            items.append(item)

        return items

    def _find_header_row(self) -> tuple[int, Optional[Dict[str, Any]]]:
        for index, row in enumerate(self.rows):
            values = [str(value).strip().lower() for value in row.values() if isinstance(value, str) and value.strip()]
            if any(value in self.HEADER_TITLES for value in values):
                logger.debug("Found header row at index %d", index)
                return index, row
        return 0, None

    def _find_code_column(self, header_row: Optional[Dict[str, Any]]) -> Optional[int]:
        if header_row is None:
            return None
        for key, value in header_row.items():
            if not isinstance(key, str) or not key.startswith("col_"):
                continue
            if isinstance(value, str) and value.strip().lower() in self.CODE_TITLES:
                try:
                    return int(key.split("_")[1])
                except ValueError:
                    continue
        return None

    def _parse_row(self, row: Dict[str, Any]) -> Optional[Tuple[str, str, int]]:
        candidate_label = None
        candidate_level = None
        for key, value in row.items():
            if not isinstance(key, str) or not key.startswith("col_"):
                continue
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            col_index = self._safe_column_index(key)
            if col_index is None:
                continue
            if self.code_column is not None and col_index == self.code_column:
                continue
            if candidate_label is None:
                candidate_label = text
                candidate_level = col_index
                break
        if candidate_label is None or candidate_level is None:
            return None
        code = self._extract_code(row, candidate_label)
        return code, candidate_label, candidate_level

    def _safe_column_index(self, key: str) -> Optional[int]:
        try:
            return int(key.split("_")[1])
        except (ValueError, IndexError):
            return None

    def _extract_code(self, row: Dict[str, Any], label: str) -> str:
        if self.code_column is None:
            return label
        code_key = f"col_{self.code_column}"
        value = row.get(code_key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return label
