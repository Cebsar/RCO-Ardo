from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .dataset import RegressionReport
from .models import GoldenDRE, GoldenFactAccounting, GoldenOverview, GoldenWorkbook
from .utilities import compute_dataset_hash


@dataclass
class ComparisonResult:
    name: str
    passed: bool
    differences: List[Dict[str, Any]]
    actual_hash: str
    expected_hash: str
    executed_at: datetime = datetime.utcnow()


class GoldenDatasetComparator:
    def compare_workbook(self, expected: GoldenWorkbook, actual: GoldenWorkbook) -> ComparisonResult:
        expected_payload = {
            "fingerprint": expected.fingerprint,
            "row_count": expected.row_count,
            "columns": expected.columns,
            "metadata": expected.metadata,
        }
        actual_payload = {
            "fingerprint": actual.fingerprint,
            "row_count": actual.row_count,
            "columns": actual.columns,
            "metadata": actual.metadata,
        }
        expected_hash = compute_dataset_hash(expected_payload)
        actual_hash = compute_dataset_hash(actual_payload)
        differences: List[Dict[str, Any]] = []
        if expected_hash != actual_hash:
            if expected.row_count != actual.row_count:
                differences.append({"row_count": {"expected": expected.row_count, "actual": actual.row_count}})
            if expected.columns != actual.columns:
                differences.append({"columns": {"expected": expected.columns, "actual": actual.columns}})
            if expected.fingerprint != actual.fingerprint:
                differences.append({"fingerprint": {"expected": expected.fingerprint, "actual": actual.fingerprint}})
        return ComparisonResult(
            name="workbook",
            passed=expected_hash == actual_hash,
            differences=differences,
            actual_hash=actual_hash,
            expected_hash=expected_hash,
        )

    def compare_overview(self, expected: GoldenOverview, actual: GoldenOverview) -> ComparisonResult:
        expected_hash = compute_dataset_hash(expected.entries)
        actual_hash = compute_dataset_hash(actual.entries)
        differences = []
        if expected_hash != actual_hash:
            differences.append({"entry_count": {"expected": len(expected.entries), "actual": len(actual.entries)}})
        return ComparisonResult(
            name="overview",
            passed=expected_hash == actual_hash,
            differences=differences,
            actual_hash=actual_hash,
            expected_hash=expected_hash,
        )

    def compare_fact_accounting(self, expected: GoldenFactAccounting, actual: GoldenFactAccounting) -> ComparisonResult:
        expected_hash = compute_dataset_hash(expected.records)
        actual_hash = compute_dataset_hash(actual.records)
        differences = []
        if expected_hash != actual_hash:
            differences.append({"record_count": {"expected": len(expected.records), "actual": len(actual.records)}})
        return ComparisonResult(
            name="fact_accounting",
            passed=expected_hash == actual_hash,
            differences=differences,
            actual_hash=actual_hash,
            expected_hash=expected_hash,
        )

    def compare_dre(self, expected: GoldenDRE, actual: GoldenDRE) -> ComparisonResult:
        expected_hash = compute_dataset_hash(expected.nodes)
        actual_hash = compute_dataset_hash(actual.nodes)
        differences = []
        if expected_hash != actual_hash:
            differences.append({"node_count": {"expected": len(expected.nodes), "actual": len(actual.nodes)}})
        return ComparisonResult(
            name="dre",
            passed=expected_hash == actual_hash,
            differences=differences,
            actual_hash=actual_hash,
            expected_hash=expected_hash,
        )

    def compare_dataset(self, expected: GoldenDataset, actual: GoldenDataset) -> RegressionReport:
        workbook_result = self.compare_workbook(expected.workbook, actual.workbook)
        overview_result = self.compare_overview(expected.overview, actual.overview)
        fact_result = self.compare_fact_accounting(expected.fact_accounting, actual.fact_accounting)
        dre_result = self.compare_dre(expected.dre, actual.dre)
        summary = {
            "checks": 4,
            "passed": sum(1 for result in [workbook_result, overview_result, fact_result, dre_result] if result.passed),
            "failed": sum(1 for result in [workbook_result, overview_result, fact_result, dre_result] if not result.passed),
        }
        failures = [
            {"name": result.name, "differences": result.differences, "expected_hash": result.expected_hash, "actual_hash": result.actual_hash}
            for result in [workbook_result, overview_result, fact_result, dre_result]
            if not result.passed
        ]
        return RegressionReport(
            generated_at=datetime.utcnow(),
            dataset_version=expected.manifest.version,
            dataset_hash=expected.manifest.dataset_hash,
            summary=summary,
            failures=failures,
            metadata={"comparison_time": datetime.utcnow().isoformat()},
        )
