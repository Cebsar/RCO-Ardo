from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ColumnMetadata:
    header: Optional[str]
    index: int
    is_hidden: bool = False
    merged_range: Optional[str] = None


@dataclass
class NamedRangeMetadata:
    name: str
    sheet: Optional[str]
    range: str


@dataclass
class WorksheetMetadata:
    name: str
    title: str
    max_row: int
    max_column: int
    used_range: Optional[Tuple[int, int, int, int]] = None  # (min_row, min_col, max_row, max_col)
    headers: List[Optional[str]] = field(default_factory=list)
    columns: List[ColumnMetadata] = field(default_factory=list)
    merged_cells: List[str] = field(default_factory=list)
    hidden_rows: List[int] = field(default_factory=list)
    hidden_columns: List[int] = field(default_factory=list)


@dataclass
class WorkbookMetadata:
    path: Optional[str]
    engine_version: Optional[str]
    sheet_names: List[str]
    worksheets: List[WorksheetMetadata] = field(default_factory=list)
    named_ranges: List[NamedRangeMetadata] = field(default_factory=list)
    execution_time_seconds: float = 0.0
