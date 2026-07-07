from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def read_frontend(relative_path: str) -> str:
    return (FRONTEND / relative_path).read_text(encoding="utf-8")


def test_operational_navigation_and_pages_are_available():
    app_shell = read_frontend("src/components/layout/AppShell.tsx")
    app = read_frontend("src/App.tsx")

    for label in ["Home", "Execution History", "Validation Center", "Download Center", "DRE", "Reconciliation", "System"]:
        assert label in app_shell

    for page in ["DashboardPage", "PipelinePage", "ValidationCenterPage", "DownloadCenterPage"]:
        assert page in app


def test_dashboard_home_runs_operational_pipeline_and_refreshes_queries():
    dashboard = read_frontend("src/pages/DashboardPage.tsx")
    runner = read_frontend("src/components/operational/PipelineRunner.tsx")

    assert "PipelineRunner" in dashboard
    assert "Run Accounting Pipeline" in runner
    for stage in ["Upload workbook", "Validation", "Processing", "Persistence", "Reconciliation", "Dashboard refresh"]:
        assert stage in runner
    assert "invalidateQueries({ queryKey: [\"kpis\"] })" in dashboard
    assert "invalidateQueries({ queryKey: [\"pipeline-history\"] })" in dashboard


def test_execution_history_contains_required_operational_columns():
    history = read_frontend("src/pages/PipelinePage.tsx")

    for column in [
        "Execution ID",
        "Date",
        "User",
        "Duration",
        "Workbook SHA256",
        "Rows processed",
        "Rows ignored",
        "Status",
    ]:
        assert column in history


def test_validation_and_download_centers_cover_required_artifacts():
    validation = read_frontend("src/pages/ValidationCenterPage.tsx")
    downloads = read_frontend("src/pages/DownloadCenterPage.tsx")

    for issue_type in ["Warnings", "Errors", "Normalization issues", "Accounting inconsistencies"]:
        assert issue_type in validation

    for artifact in ["Calculated DRE", "Warehouse", "Reconciliation Report", "Validation Report", "Execution Metrics"]:
        assert artifact in downloads


def test_operational_layer_does_not_import_restricted_core_modules():
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in (FRONTEND / "src").rglob("*") if path.is_file())

    for forbidden_term in [
        "financial_engine",
        "rule_engine",
        "WarehouseBuilder",
        "PersistenceService",
        "build_dre",
        "run_etl",
    ]:
        assert forbidden_term not in source_text


def test_operational_reports_and_component_catalog_exist():
    report = (ROOT / "docs" / "operational_integration_report.md").read_text(encoding="utf-8")
    catalog = (ROOT / "docs" / "operational_component_catalog.md").read_text(encoding="utf-8")

    assert "Operational Integration Report" in report
    assert "Operational Component Catalog" in catalog
    assert "PipelineRunner" in catalog
