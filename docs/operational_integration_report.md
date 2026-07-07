# Operational Integration Report

## Scope

Beta 1.1 turns the dashboard into an operational financial analytics workspace for daily ARDO Controllership use.

The implementation only extends the product layer. It does not change Financial Core, accounting rules, ETL calculations, Rule Engine, Warehouse internals, Persistence Models, or the existing API Contract.

## Delivered Workflow

- Dashboard Home now includes executive KPI cards, last pipeline execution, processing status, last reconciliation result, and last import date.
- The Home page includes the `Run Accounting Pipeline` flow with workbook upload, validation, processing, persistence, reconciliation, and dashboard refresh stages.
- Execution History shows execution ID, date, user, duration, workbook SHA256, rows processed, rows ignored, and status.
- Validation Center consolidates warnings, errors, normalization issues, and accounting inconsistencies.
- Download Center generates downloadable operational artifacts for calculated DRE, warehouse summary, reconciliation report, validation report, and execution metrics.
- Successful operational runs invalidate dashboard queries so KPI and history data refresh automatically.
- Loading indicators, progress bar, toast notifications, friendly errors, and empty states are present across the workflow.

## Modified Files

- `frontend/src/App.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/ToastViewport.tsx`
- `frontend/src/components/operational/PipelineRunner.tsx`
- `frontend/src/components/ui/progress.tsx`
- `frontend/src/lib/operational.ts`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/PipelinePage.tsx`
- `frontend/src/pages/ValidationCenterPage.tsx`
- `frontend/src/pages/DownloadCenterPage.tsx`
- `tests/integration/test_operational_integration.py`
- `docs/operational_integration_report.md`
- `docs/operational_component_catalog.md`

## Verification

Integration coverage validates that the operational product layer exposes updated navigation, dashboard execution, history, validation, downloads, progress, toasts, and documentation without modifying restricted layers.
