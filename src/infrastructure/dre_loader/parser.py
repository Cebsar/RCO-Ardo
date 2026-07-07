from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedHierarchyItem:
    code: str
    label: str
    level: int
    row_number: int
    order: int
    row_classification: str = "DRE group"
    hidden: bool = False
    amount: Optional[Decimal] = None
    metadata: Dict[str, Any] = None


class HierarchyParser:
    HEADER_TITLES = {"n1", "n2", "n3", "level", "hierarchy", "label", "description", "name", "code", "item", "c. contabil", "c. contábil"}
    CODE_TITLES = {"code", "codigo", "id", "c. contabil", "c. contábil"}
    LEVEL_PATTERN = re.compile(r"^n?(\d+)$", re.IGNORECASE)

    def __init__(self, rows: Sequence[Dict[str, Any]]):
        self.rows = rows

    def parse(self) -> List[ParsedHierarchyItem]:
        header_index, header_row = self._find_header_row()
        self.header_row = header_row
        self.code_column = self._find_code_column(header_row) if header_row else None
        self.item_column = self._find_named_column(header_row, {"item"}) if header_row else None
        self.totalizer_column = self._find_named_column(header_row, {"totalizador"}) if header_row else None
        self.real_value_column = self._find_real_value_column(header_row) if header_row else None
        self.row_classifications: Dict[int, str] = {}
        items: List[ParsedHierarchyItem] = []
        order = 0

        for row in self.rows[header_index + 1 :]:
            row_number = int(row.get("_row_number", 0))
            initial_classification = self._classify_row(row)
            self.row_classifications[row_number] = initial_classification
            if initial_classification in {"structural empty row", "visual separator"}:
                continue
            parsed = self._parse_row(row)
            if parsed is None:
                self.row_classifications[row_number] = "invalid row"
                continue
            code, label, level = parsed
            row_classification = self._classify_hierarchy_row(row, code, label)
            self.row_classifications[row_number] = row_classification
            order += 1
            item = ParsedHierarchyItem(
                code=code,
                label=label.strip(),
                level=level,
                row_number=row_number,
                order=order,
                row_classification=row_classification,
                hidden=bool(row.get("_hidden")),
                amount=self._extract_amount(row),
                metadata=self._extract_metadata(row),
            )
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

    def _find_named_column(self, header_row: Optional[Dict[str, Any]], names: set[str]) -> Optional[int]:
        if header_row is None:
            return None
        for key, value in header_row.items():
            if not isinstance(key, str) or not key.startswith("col_"):
                continue
            if isinstance(value, str) and value.strip().lower() in names:
                return self._safe_column_index(key)
        return None

    def _find_real_value_column(self, header_row: Optional[Dict[str, Any]]) -> Optional[int]:
        if header_row is None:
            return None
        for key, value in header_row.items():
            if not isinstance(key, str) or not key.startswith("col_"):
                continue
            if isinstance(value, str) and value.strip().lower() == "real":
                return self._safe_column_index(key)
        return None

    def _parse_row(self, row: Dict[str, Any]) -> Optional[Tuple[str, str, int]]:
        if self.item_column is not None:
            label = row.get(f"col_{self.item_column}")
            if label is None or str(label).strip() == "":
                return None
            code = self._extract_code(row, str(label).strip())
            return code, str(label).strip(), self._extract_level(row)

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
        row_number = row.get("_row_number")
        if self.code_column is None:
            return label
        code_key = f"col_{self.code_column}"
        value = row.get(code_key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return f"ROW_{row_number}" if row_number else label

    def _extract_level(self, row: Dict[str, Any]) -> int:
        if self.totalizer_column is not None:
            value = row.get(f"col_{self.totalizer_column}")
            if isinstance(value, str):
                match = re.search(r"n(\d+)", value, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                if value.strip().lower() == "subtotal":
                    return 3
        return self.item_column or 1

    def _extract_amount(self, row: Dict[str, Any]) -> Optional[Decimal]:
        if self.real_value_column is None:
            return None
        value = row.get(f"col_{self.real_value_column}")
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _extract_metadata(self, row: Dict[str, Any]) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        if self.totalizer_column is not None:
            metadata["totalizer"] = row.get(f"col_{self.totalizer_column}")
        if self.real_value_column is not None:
            metadata["real_value_column"] = self.real_value_column
        return metadata

    def _classify_row(self, row: Dict[str, Any]) -> str:
        values = [
            str(value).strip()
            for key, value in row.items()
            if isinstance(key, str)
            and key.startswith("col_")
            and value is not None
            and str(value).strip()
        ]
        if not values:
            return "structural empty row"
        joined = "".join(values)
        if joined and set(joined) <= {"-", "_", "=", ".", "|", " "}:
            return "visual separator"
        return "invalid row"

    def _classify_hierarchy_row(self, row: Dict[str, Any], code: str, label: str) -> str:
        formulas = row.get("_formulas") or {}
        searchable = f"{code} {label}".lower()
        account_like = re.search(r"\d+(?:\.\d+){2,}", searchable) is not None
        if account_like:
            return "analytical account"
        if formulas or any(token in searchable for token in ("total", "subtotal", "resultado", "lucro", "margem")):
            return "synthetic account"
        return "DRE group"
