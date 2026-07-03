from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class StageSpec:
    name: str
    input: Optional[str]
    output: Optional[str]
    responsibilities: List[str]
    dependencies: List[str]
    possible_exceptions: List[str]
    expected_execution_time: str  # descriptive (e.g., 'milliseconds', 'seconds')


STAGES: List[StageSpec] = [
    StageSpec(
        name="Master File",
        input="Uploaded master spreadsheet (binary)",
        output="Raw workbook handle / path",
        responsibilities=["Accept master file from user/accounting"],
        dependencies=["Storage / UI"],
        possible_exceptions=["FileNotFoundError", "PermissionError"],
        expected_execution_time="<1s",
    ),
    StageSpec(
        name="Metadata Engine",
        input="Raw workbook handle",
        output="File metadata (sheets, sizes, timestamps)",
        responsibilities=["Extract file metadata and routing info"],
        dependencies=["File I/O"],
        possible_exceptions=["InvalidFileError"],
        expected_execution_time="<1s",
    ),
    StageSpec(
        name="Excel Adapter",
        input="Workbook or path",
        output="Raw rows as dict(header->value)",
        responsibilities=["Read sheets and yield raw rows"],
        dependencies=["openpyxl (infra)"],
        possible_exceptions=["InvalidHeadersError", "IOError"],
        expected_execution_time="seconds (depending on file size)",
    ),
    StageSpec(
        name="Header Mapper",
        input="Raw header list",
        output="Normalized header list",
        responsibilities=["Normalize and map headers to domain names"],
        dependencies=["Mapping rules artifact"],
        possible_exceptions=["MappingNotFoundError"],
        expected_execution_time="<1s",
    ),
    StageSpec(
        name="Schema Validator",
        input="Normalized headers",
        output="Validation report (missing/duplicated/unexpected)",
        responsibilities=["Validate headers against MasterFileContract"],
        dependencies=["Domain contract"],
        possible_exceptions=["ValidationError"],
        expected_execution_time="<1s",
    ),
    StageSpec(
        name="Data Source Contract",
        input="Validated rows",
        output="Row DTOs conforming to contract",
        responsibilities=["Enforce data contract shapes and types"],
        dependencies=["Application DTOs"],
        possible_exceptions=["ContractViolationError"],
        expected_execution_time="milliseconds per row",
    ),
    StageSpec(
        name="Normalizer",
        input="Row DTOs",
        output="Canonicalized rows (normalized values)",
        responsibilities=["Normalize codes, dates, numeric formats"],
        dependencies=["Normalization rules"],
        possible_exceptions=["NormalizationError"],
        expected_execution_time="milliseconds per row",
    ),
    StageSpec(
        name="Warehouse Builder",
        input="Canonical rows",
        output="Warehouse snapshot (batch)",
        responsibilities=["Build canonical SQLite snapshot"],
        dependencies=["SQL/DB layer"],
        possible_exceptions=["DBWriteError"],
        expected_execution_time="seconds to minutes (batch)",
    ),
    StageSpec(
        name="Business Engine",
        input="Warehouse snapshot",
        output="Derived business artifacts (e.g., balances)",
        responsibilities=["Perform domain calculations and aggregations"],
        dependencies=["Financial Engine"],
        possible_exceptions=["CalculationError"],
        expected_execution_time="seconds to minutes",
    ),
    StageSpec(
        name="Validation Engine",
        input="Derived artifacts",
        output="Validation reports",
        responsibilities=["Run business validation rules"],
        dependencies=["Validation rules"],
        possible_exceptions=["ValidationRuleFailure"],
        expected_execution_time="seconds",
    ),
    StageSpec(
        name="Presentation Engine",
        input="Validated artifacts",
        output="Presentation-ready datasets",
        responsibilities=["Format data for reports and dashboards"],
        dependencies=["Reporting templates"],
        possible_exceptions=["RenderingError"],
        expected_execution_time="seconds",
    ),
    StageSpec(
        name="Export Engine",
        input="Presentation datasets",
        output="Files (Excel, JSON) or APIs",
        responsibilities=["Export to target formats or endpoints"],
        dependencies=["Export adapters"],
        possible_exceptions=["ExportError"],
        expected_execution_time="seconds",
    ),
    StageSpec(
        name="Dashboard",
        input="Presentation datasets",
        output="Live dashboards/visualizations",
        responsibilities=["Serve data to dashboards and UI"],
        dependencies=["Frontend/UI"],
        possible_exceptions=["VisualizationError"],
        expected_execution_time="real-time (ms to s)",
    ),
]
