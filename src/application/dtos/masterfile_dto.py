from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any, List, Optional


@dataclass
class MasterFileValidationResultDTO:
    missing_columns: List[str]
    duplicated_columns: List[str]
    unexpected_columns: List[str]


@dataclass
class MasterFileRowDTO:
    # row represented as mapping header -> raw value
    values: Mapping[str, Any]
    row_number: Optional[int] = None
