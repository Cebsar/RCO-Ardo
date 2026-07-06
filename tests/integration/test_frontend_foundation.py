from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_frontend_stack_files_exist():
    for relative_path in [
        "package.json",
        "vite.config.ts",
        "tailwind.config.ts",
        "postcss.config.js",
        "components.json",
        "src/main.tsx",
        "src/App.tsx",
    ]:
        assert (FRONTEND / relative_path).exists(), relative_path


def test_enterprise_dashboard_pages_exist():
    for page in [
        "DashboardPage.tsx",
        "DrePage.tsx",
        "PipelinePage.tsx",
        "ReconciliationPage.tsx",
        "SystemPage.tsx",
    ]:
        assert (FRONTEND / "src" / "pages" / page).exists(), page


def test_frontend_consumes_only_existing_rest_api_paths():
    api_client = (FRONTEND / "src" / "lib" / "api.ts").read_text(encoding="utf-8")

    for path in [
        "/health",
        "/version",
        "/analytics/kpis",
        "/pipeline/history",
        "/pipeline/",
        "/financial/dre",
        "/auth/token",
    ]:
        assert path in api_client

    forbidden_terms = [
        "sqlite",
        "create_engine",
        "rule_engine",
        "WarehouseBuilder",
        "ReconciliationEngine",
    ]
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in (FRONTEND / "src").rglob("*") if path.is_file())
    for term in forbidden_terms:
        assert term not in source_text
