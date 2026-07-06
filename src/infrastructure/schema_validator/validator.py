from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, Iterable, List

from src.domain.master_file_contract import (
    MASTER_FILE_SCHEMA,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
)
from src.infrastructure.header_mapper.mapper import HeaderMapping
from .models import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validate canonical header mappings and workbook-level schema.

    Input: dict of sheet_name -> HeaderMapping (from HeaderMapper)
    Produces: ValidationReport with ValidationIssue entries.
    """

    def __init__(self, required_sheets: Iterable[str] | None = None):
        self.required_sheets = list(required_sheets) if required_sheets else []

    def validate_sheet(self, sheet_name: str, mapping: HeaderMapping) -> ValidationReport:
        start = perf_counter()
        issues: List[ValidationIssue] = []
        # Check duplicates reported by HeaderMapping
        for dup in mapping.duplicates:
            issues.append(ValidationIssue(code="DUPLICATE_MAPPING", severity="error", message=f"Duplicate mapping for canonical field: {dup}", sheet=sheet_name, field=dup))
        mapped_fields = set(mapping.canonical_to_headers)

        # Check missing required fields from the frozen domain contract only.
        for missing in REQUIRED_COLUMNS:
            if missing in mapped_fields:
                continue
            issues.append(ValidationIssue(code="MISSING_FIELD", severity="error", message=f"Missing required canonical field: {missing}", sheet=sheet_name, field=missing))

        # Optional fields are contract-aware but may be absent without warning.
        optional_present = sorted(field for field in OPTIONAL_COLUMNS if field in mapped_fields)
        optional_missing = sorted(field for field in OPTIONAL_COLUMNS if field not in mapped_fields)

        # Unmatched source headers are intentionally ignored by the accounting schema.
        ignored_headers = [header for header in mapping.unmatched_headers if str(header).strip()]
        for header in ignored_headers:
            issues.append(ValidationIssue(code="IGNORED_COLUMN", severity="info", message=f"Ignored source column: {header}", sheet=sheet_name))

        # Basic data-type expectations: ensure at least one numeric field present among Debit/Credit/Balance if financial columns expected
        numeric_fields = [f for f in ["Debit", "Credit", "Balance"] if f in MASTER_FILE_SCHEMA]
        numeric_present = any(f in mapping.canonical_to_headers for f in numeric_fields)
        if not numeric_present:
            issues.append(ValidationIssue(code="NUMERIC_FIELDS_MISSING", severity="warning", message="No numeric columns (Debit/Credit/Balance) mapped", sheet=sheet_name))

        report = ValidationReport(issues=issues)
        report.metadata = {
            "required_columns": list(REQUIRED_COLUMNS),
            "optional_columns": list(OPTIONAL_COLUMNS),
            "optional_present": optional_present,
            "optional_missing": optional_missing,
            "ignored_columns": ignored_headers,
        }
        report.execution_time_seconds = perf_counter() - start
        logger.info("Validated sheet %s in %.6f seconds: %d issues", sheet_name, report.execution_time_seconds, len(issues))
        return report

    def validate_workbook(self, mappings: Dict[str, HeaderMapping]) -> ValidationReport:
        start = perf_counter()
        issues: List[ValidationIssue] = []
        # Check required sheets
        sheet_names = list(mappings.keys())
        for req in self.required_sheets:
            if req not in sheet_names:
                issues.append(ValidationIssue(code="MISSING_SHEET", severity="error", message=f"Required sheet missing: {req}"))
        # Validate each sheet
        for sheet, mapping in mappings.items():
            sheet_report = self.validate_sheet(sheet, mapping)
            issues.extend(sheet_report.issues)
        report = ValidationReport(issues=issues)
        report.execution_time_seconds = perf_counter() - start
        logger.info("Validated workbook in %.6f seconds: %d issues", report.execution_time_seconds, len(issues))
        return report
