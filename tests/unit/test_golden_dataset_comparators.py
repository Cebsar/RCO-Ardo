from datetime import datetime
from pathlib import Path

from src.infrastructure.golden_dataset.comparators import GoldenDatasetComparator
from src.infrastructure.golden_dataset.dataset import GoldenDataset
from src.infrastructure.golden_dataset.models import GoldenDRE, GoldenFactAccounting, GoldenOverview, GoldenWorkbook


def make_dataset() -> GoldenDataset:
    workbook = GoldenWorkbook(path=Path("workbook.xlsx"), fingerprint="abc", row_count=2, columns=["A", "B"])
    overview = GoldenOverview(source="overview.json", generated_at=datetime(2026, 7, 2), entries=[{"code": "R1"}])
    fact_accounting = GoldenFactAccounting(source="facts.json", generated_at=datetime(2026, 7, 2), records=[{"account_code": "4000", "amount": 100}])
    dre = GoldenDRE(source="dre.json", generated_at=datetime(2026, 7, 2), nodes=[{"code": "GROSS_MARGIN", "amount": 50}])
    manifest = {
        "version": "1.0.0",
        "created_at": datetime(2026, 7, 2).isoformat(),
        "dataset_hash": "hash123",
        "source_paths": {},
        "artifacts": {},
        "metadata": {},
    }
    return GoldenDataset(
        workbook=workbook,
        overview=overview,
        fact_accounting=fact_accounting,
        dre=dre,
        manifest=type("M", (), manifest),
    )


def test_compare_dataset_passes_for_equal_datasets():
    expected = make_dataset()
    actual = make_dataset()
    comparator = GoldenDatasetComparator()
    report = comparator.compare_dataset(expected, actual)

    assert report.summary["passed"] == 4
    assert report.summary["failed"] == 0
    assert not report.failures


def test_compare_dataset_detects_difference():
    expected = make_dataset()
    actual = make_dataset()
    actual.workbook = GoldenWorkbook(path=Path("workbook.xlsx"), fingerprint="abc", row_count=3, columns=["A", "B"])
    comparator = GoldenDatasetComparator()
    report = comparator.compare_dataset(expected, actual)

    assert report.summary["passed"] == 3
    assert report.summary["failed"] == 1
    assert report.failures[0]["name"] == "workbook"
