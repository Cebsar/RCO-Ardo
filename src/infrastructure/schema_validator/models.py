from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationIssue:
    code: str
    severity: str  # e.g., 'error', 'warning', 'info'
    message: str
    sheet: Optional[str] = None
    field: Optional[str] = None


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)
    execution_time_seconds: float = 0.0

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)
