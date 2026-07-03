from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional


@dataclass
class AccountingEntryDTO:
    id: str
    account_code: str
    amount: Any
    date: str
    entry_type: str
    cost_center: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AccountingEntriesDTO:
    entries: Iterable[AccountingEntryDTO]
    period: Optional[str] = None
