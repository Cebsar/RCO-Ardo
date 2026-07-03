from __future__ import annotations

from datetime import datetime
from pathlib import Path
from decimal import Decimal

from src.infrastructure.golden_dataset.dataset import GoldenDataset, DatasetManifest, RegressionReport
from src.infrastructure.golden_dataset.models import GoldenDRE, GoldenFactAccounting, GoldenOverview, GoldenWorkbook
from src.infrastructure.golden_dataset.utilities import compute_dataset_hash, format_dataset_version


def test_format_dataset_version():
    assert format_dataset_version(1, 0, 0) == "1.0.0"


def test_compute_dataset_hash_is_stable():
    payload = {"a": 1, "b": 2}
    assert compute_dataset_hash(payload) == compute_dataset_hash(payload)


def test_golden_dataset_build_and_manifest():
    workbook = GoldenWorkbook(
        path=Path("data/golden/workbook.xlsx"),
        fingerprint="abc123",
        row_count=10,
        columns=["A", "B"],
    )
    overview = GoldenOverview(
        source="template/overview.json",
        generated_at=datetime(2026, 7, 2, 0, 0, 0),
        entries=[{"code": "R1", "amount": 100}],
    )
    fact_accounting = GoldenFactAccounting(
        source="template/facts.json",
        generated_at=datetime(2026, 7, 2, 0, 0, 0),
        records=[{"account_code": "4000", "amount": 100}],
    )
    dre = GoldenDRE(
        source="template/dre.json",
        generated_at=datetime(2026, 7, 2, 0, 0, 0),
        nodes=[{"code": "GROSS_MARGIN", "value": 50}],
    )
    dataset = GoldenDataset.build(
        workbook=workbook,
        overview=overview,
        fact_accounting=fact_accounting,
        dre=dre,
        version="1.0.0",
        source_paths={
            "workbook": "data/golden/workbook.xlsx",
            "overview": "template/overview.json",
            "fact_accounting": "template/facts.json",
            "dre": "template/dre.json",
        },
    )

    assert dataset.manifest.version == "1.0.0"
    assert dataset.manifest.dataset_hash
    assert dataset.manifest.artifacts["workbook"] == "data/golden/workbook.xlsx"
    assert dataset.overview.entries[0]["code"] == "R1"


def test_regression_report_basics():
    report = RegressionReport(
        generated_at=datetime(2026, 7, 2, 0, 0, 0),
        dataset_version="1.0.0",
        dataset_hash="hash123",
        summary={"total_checks": 10, "passed": 10},
    )

    assert report.dataset_version == "1.0.0"
    assert report.summary["passed"] == 10
