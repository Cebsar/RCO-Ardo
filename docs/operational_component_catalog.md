# Operational Component Catalog

## Navigation

- Home
- Execution History
- Validation Center
- Download Center
- DRE
- Reconciliation
- System

## Product Components

- `PipelineRunner`: workbook upload, stage progress, SHA256 capture, validation handling, operational history storage, and dashboard refresh callback.
- `ToastViewport`: global operational notifications for success, error, and informational states.
- `Progress`: stable progress indicator used by the accounting pipeline flow.

## Pages

- `DashboardPage`: executive KPI cards, processing status, last execution, last reconciliation, last import, charts, and pipeline execution.
- `PipelinePage`: execution history table and detail panel.
- `ValidationCenterPage`: warnings, errors, normalization issues, and accounting inconsistencies.
- `DownloadCenterPage`: DRE, warehouse summary, reconciliation report, validation report, and execution metrics downloads.

## Existing Components Reused

- `AuthPanel`
- `AppShell`
- `PageState`
- `DataTable`
- `StatusCharts`
- `Button`
- `Badge`
- `Card`
- `Input`
- `Skeleton`
