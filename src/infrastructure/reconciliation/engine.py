from __future__ import annotations

import logging
from datetime import datetime
from time import perf_counter
from typing import Dict, Iterable, List, Optional

from src.domain.entities import DRENode
from .calculator import DifferenceCalculator
from .models import (
    AuditReport,
    DifferenceReport,
    ExecutionMetrics,
    ToleranceRule,
    ValidationMetrics,
)

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    def __init__(self, tolerance: Optional[ToleranceRule] = None):
        self.tolerance = tolerance or ToleranceRule()
        self.calculator = DifferenceCalculator()

    def reconcile(
        self,
        expected_tree: Iterable[DRENode],
        actual_tree: Iterable[DRENode],
        tolerance: Optional[ToleranceRule] = None,
        source_name: Optional[str] = None,
    ) -> AuditReport:
        start = perf_counter()
        tolerance = tolerance or self.tolerance
        expected_nodes = list(expected_tree)
        actual_nodes = list(actual_tree)

        differences = self.calculator.compare_hierarchy(expected_nodes, actual_nodes, tolerance)
        report = DifferenceReport()
        for item in differences:
            report.add(item)
        validation = ValidationMetrics(
            nodes_compared=len(differences),
            discrepancies_found=report.mismatches,
            tolerance_checks=len(differences),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        execution = ExecutionMetrics(start_time=datetime.utcnow(), end_time=datetime.utcnow(), duration_seconds=perf_counter() - start)

        audit = AuditReport(reconciliation=report, validation=validation, execution=execution, source=source_name)
        logger.info("Reconciliation completed in %.6f seconds: %d nodes compared", execution.duration_seconds, len(differences))
        return audit
