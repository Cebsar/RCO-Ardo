"""Master file data contract for Rel_Razão.

Defines expected header names, column specifications, and lightweight validation helpers.
Columns are identified by header names only.
No I/O or ETL is implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional


# Header names (must match source file exact headers)
HEADER_COMPANY = "Company"
HEADER_DIVISION = "Division"
HEADER_COST_CENTER = "CostCenter"
HEADER_ACCOUNT_CODE = "AccountCode"
HEADER_ACCOUNT_DESCRIPTION = "AccountDescription"
HEADER_ACCOUNTING_DATE = "AccountingDate"
HEADER_DOCUMENT_NUMBER = "DocumentNumber"
HEADER_HISTORY = "History"
HEADER_DEBIT = "Debit"
HEADER_CREDIT = "Credit"
HEADER_BALANCE = "Balance"


@dataclass(frozen=True)
class ColumnSpec:
    header: str
    required: bool
    dtype: str  # descriptive type name: 'str', 'date', 'decimal', etc.
    allow_null: bool
    description: Optional[str] = None


# Schema definition: map header -> ColumnSpec
MASTER_FILE_SCHEMA: Dict[str, ColumnSpec] = {
    HEADER_COMPANY: ColumnSpec(
        header=HEADER_COMPANY,
        required=True,
        dtype="str",
        allow_null=False,
        description="Company identifier or name",
    ),
    HEADER_DIVISION: ColumnSpec(
        header=HEADER_DIVISION,
        required=False,
        dtype="str",
        allow_null=True,
        description="Division within the company",
    ),
    HEADER_COST_CENTER: ColumnSpec(
        header=HEADER_COST_CENTER,
        required=False,
        dtype="str",
        allow_null=True,
        description="Cost center code or name",
    ),
    HEADER_ACCOUNT_CODE: ColumnSpec(
        header=HEADER_ACCOUNT_CODE,
        required=True,
        dtype="str",
        allow_null=False,
        description="Chart of accounts code",
    ),
    HEADER_ACCOUNT_DESCRIPTION: ColumnSpec(
        header=HEADER_ACCOUNT_DESCRIPTION,
        required=False,
        dtype="str",
        allow_null=True,
        description="Account description",
    ),
    HEADER_ACCOUNTING_DATE: ColumnSpec(
        header=HEADER_ACCOUNTING_DATE,
        required=True,
        dtype="date",
        allow_null=False,
        description="Date of the accounting entry (ISO format preferred)",
    ),
    HEADER_DOCUMENT_NUMBER: ColumnSpec(
        header=HEADER_DOCUMENT_NUMBER,
        required=False,
        dtype="str",
        allow_null=True,
        description="Document or invoice number",
    ),
    HEADER_HISTORY: ColumnSpec(
        header=HEADER_HISTORY,
        required=False,
        dtype="str",
        allow_null=True,
        description="Transaction history or narrative",
    ),
    HEADER_DEBIT: ColumnSpec(
        header=HEADER_DEBIT,
        required=False,
        dtype="decimal",
        allow_null=True,
        description="Debit amount",
    ),
    HEADER_CREDIT: ColumnSpec(
        header=HEADER_CREDIT,
        required=False,
        dtype="decimal",
        allow_null=True,
        description="Credit amount",
    ),
    HEADER_BALANCE: ColumnSpec(
        header=HEADER_BALANCE,
        required=False,
        dtype="decimal",
        allow_null=True,
        description="Running balance (optional)",
    ),
}


# Convenience lists
REQUIRED_COLUMNS: List[str] = [
    h for h, spec in MASTER_FILE_SCHEMA.items() if spec.required
]
OPTIONAL_COLUMNS: List[str] = [
    h for h, spec in MASTER_FILE_SCHEMA.items() if not spec.required
]


@dataclass(frozen=True)
class MasterFileValidationResult:
    missing_columns: List[str]
    duplicated_columns: List[str]
    unexpected_columns: List[str]

    @property
    def ignored_columns(self) -> List[str]:
        """Columns outside MASTER_FILE_SCHEMA that ingestion may ignore."""
        return self.unexpected_columns


# Lightweight helpers (pure, no I/O) to check headers
def find_missing_columns(headers: Iterable[str]) -> List[str]:
    present = {h.strip() for h in headers}
    return [c for c in REQUIRED_COLUMNS if c not in present]


def find_duplicated_columns(headers: Iterable[str]) -> List[str]:
    seen = set()
    duplicates: List[str] = []
    for h in headers:
        key = h.strip()
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def find_unexpected_columns(headers: Iterable[str]) -> List[str]:
    known = set(MASTER_FILE_SCHEMA.keys())
    return [h for h in (x.strip() for x in headers) if h and h not in known]


def validate_headers(headers: Iterable[str]) -> MasterFileValidationResult:
    """Validate a collection of header names against the contract.

    Returns lists of missing, duplicated, and unexpected columns.
    """
    missing = find_missing_columns(headers)
    duplicated = find_duplicated_columns(headers)
    unexpected = find_unexpected_columns(headers)
    return MasterFileValidationResult(
        missing_columns=missing,
        duplicated_columns=duplicated,
        unexpected_columns=unexpected,
    )


# Data type expectations (descriptive; parsing not implemented here)
DATA_TYPE_MAP: Dict[str, str] = {h: spec.dtype for h, spec in MASTER_FILE_SCHEMA.items()}


# Null handling rules
NULL_HANDLING: Dict[str, bool] = {h: spec.allow_null for h, spec in MASTER_FILE_SCHEMA.items()}


# Duplicated columns policy (domain decision):
# - Duplicated required columns: invalid
# - Duplicated optional columns: invalid (must be disambiguated before ingest)
# Implementation of policy checks belong to parsers/infrastructure.
DUPLICATE_POLICY: str = (
    "Duplicates are considered invalid for all columns; source must be normalized before ingestion."
)


# Missing columns policy:
# - If any required column is missing, ingestion must fail and report missing columns.
MISSING_COLUMNS_POLICY: str = (
    "Missing required columns must be reported and corrected before ETL runs."
)
