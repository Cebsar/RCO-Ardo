from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .configuration import ExecutionConfiguration
from src.infrastructure.golden_dataset.dataset import RegressionReport as GoldenRegressionReport
from src.infrastructure.reconciliation.models import AuditReport
from src.infrastructure.rule_engine.models import ExecutionReport


@dataclass
class StageResult:
    name: str
    success: bool
    duration_seconds: float = 0.0
    output: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    configuration: ExecutionConfiguration
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    success: bool
    stage_results: List[StageResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    reconciliation: Optional[AuditReport] = None
    rule_execution: Optional[ExecutionReport] = None
    golden_regression: Optional[GoldenRegressionReport] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def failed_stages(self) -> int:
        return sum(1 for stage in self.stage_results if not stage.success)

    @property
    def passed_stages(self) -> int:
        return sum(1 for stage in self.stage_results if stage.success)


@dataclass
class ExecutionSummary:
    total_stages: int
    passed_stages: int
    failed_stages: int
    success: bool
    duration_seconds: float
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_report(cls, report: PipelineReport) -> "ExecutionSummary":
        return cls(
            total_stages=len(report.stage_results),
            passed_stages=report.passed_stages,
            failed_stages=report.failed_stages,
            success=report.success,
            duration_seconds=report.duration_seconds,
            errors=report.errors,
        )
