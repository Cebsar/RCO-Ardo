from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class NormalizationIssue:
    code: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str
    row_number: Optional[int] = None
    row: Optional[dict] = None


@dataclass
class NormalizationReport:
    issues: List[NormalizationIssue] = field(default_factory=list)
    normalized_count: int = 0
    invalid_count: int = 0
    skipped_empty: int = 0
    execution_time_seconds: float = 0.0

    def add(self, issue: NormalizationIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.invalid_count += 1

    @property
    def is_valid(self) -> bool:
        return self.invalid_count == 0
