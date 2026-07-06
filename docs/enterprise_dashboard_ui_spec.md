# Enterprise Dashboard UI Specification

Status: E03.2 UI Specification  
Source of truth: Enterprise API Contract  
Implementation scope: Documentation only

## 1. Scope

This specification defines the Enterprise Dashboard user interface using only the existing API contract.

No frontend code, React components, dashboard implementation, business logic, or new API endpoints are introduced by this document.

Official API endpoints used:

- `GET /health`
- `GET /version`
- `GET /pipeline/history`
- `GET /pipeline/{execution_id}`
- `GET /financial/dre`
- `GET /financial/dre/{company}`
- `GET /financial/dre/{company}/{period}`
- `GET /analytics/kpis`

All API responses are expected to use the official envelope:

- `data`: endpoint payload
- `meta`: response metadata
- `errors`: contract errors

## 2. Dashboard Specification

### 2.1 Enterprise Overview Screen

Primary endpoint:

- `GET /analytics/kpis`

Supporting endpoints:

- `GET /health`
- `GET /version`
- `GET /pipeline/history`

Purpose:

Provide the executive landing screen for the Enterprise Dashboard. The screen summarizes system health, pipeline activity, persisted financial data volume, and the latest processing state.

Widgets:

- System Status widget
- API Version widget
- Pipeline Execution KPI widget
- Data Volume KPI widget
- Latest Execution widget
- Recent Pipeline History widget

Filters:

- None required for the KPI endpoint.
- Optional local UI filter for recent history display size, mapped to `GET /pipeline/history?limit={n}`.

Tables:

- Recent Pipeline Executions table
  - Source: `GET /pipeline/history`
  - Columns:
    - Execution ID
    - Pipeline name
    - Source path
    - Status
    - Success
    - Started at
    - Finished at
    - Duration seconds
    - Created at

Charts:

- Pipeline Status Donut
  - Successful executions
  - Failed executions
- Persisted Records Bar Chart
  - Accounting entries
  - DRE nodes
  - Reconciliation rows
- Average Duration KPI sparkline placeholder
  - Current API exposes aggregate average only.
  - Historical trend is not available without new endpoints, so the chart should render as a single-value KPI state.

Actions:

- Refresh dashboard
- Open latest execution detail
- Open pipeline history
- Open DRE screen

Empty states:

- No KPI data:
  - Show zero values.
  - Message: "No enterprise executions have been persisted yet."
- No pipeline history:
  - Show an empty history table.
  - Message: "No pipeline executions found."

Loading states:

- Page-level skeleton while `/analytics/kpis`, `/health`, `/version`, and `/pipeline/history` load.
- Widget-level skeletons if partial loading is supported.

Error states:

- Health endpoint failure:
  - Show "System status unavailable."
- KPI endpoint failure:
  - Show "Enterprise KPIs unavailable."
- Pipeline history failure:
  - Keep KPI widgets visible if available and show table-level error.

Navigation:

- Entry point: `/dashboard`
- Links to:
  - Pipeline History
  - Latest Execution Detail
  - Financial DRE

Permissions:

- Required role: `enterprise.viewer`
- Optional elevated role for operations visibility: `enterprise.operator`
- No write actions are available.

### 2.2 Pipeline History Screen

Primary endpoint:

- `GET /pipeline/history`

Purpose:

Display persisted pipeline executions and allow users to open execution details.

Widgets:

- Pipeline History table
- History count indicator
- Status summary strip

Filters:

- Limit
  - Type: numeric select or dropdown
  - API mapping: `limit`
  - Valid range: `1` to `200`
  - Default: `50`
- Client-side filters only:
  - Status
  - Success
  - Source path search
  - Date range over returned rows

Tables:

- Pipeline Executions table
  - Source: `GET /pipeline/history`
  - Columns:
    - Execution ID
    - Pipeline name
    - Source path
    - Status
    - Success
    - Started at
    - Finished at
    - Duration seconds
    - Created at

Charts:

- None required.
- Optional local chart based only on returned rows:
  - Success vs failure count
  - Duration by execution

Actions:

- Refresh
- Change limit
- Open execution detail
- Copy execution ID

Empty states:

- No executions:
  - Message: "No pipeline executions found."
  - Suggested action: Refresh

Loading states:

- Table skeleton with expected columns.

Error states:

- API failure:
  - Message: "Pipeline history could not be loaded."
  - Action: Retry
- Invalid limit:
  - UI should prevent invalid values before request.

Navigation:

- From Dashboard Overview to Pipeline History.
- From Pipeline History to Pipeline Execution Detail.

Permissions:

- Required role: `enterprise.viewer`

### 2.3 Pipeline Execution Detail Screen

Primary endpoint:

- `GET /pipeline/{execution_id}`

Purpose:

Display the persisted details and record counts for a single pipeline execution.

Widgets:

- Execution Header
- Execution Status widget
- Execution Metadata widget
- Persisted Artifact Counts widget
- Error List widget

Filters:

- None.

Route parameters:

- `execution_id`
  - Type: string
  - Source: selected execution row or deep link

Tables:

- Error table
  - Source: `data.execution.errors`
  - Columns:
    - Index
    - Error payload
- Metadata table
  - Source: `data.execution.metadata`
  - Columns:
    - Key
    - Value

Charts:

- Artifact Counts Bar Chart
  - Accounting entries
  - DRE nodes
  - Reconciliation rows
  - Metrics rows

Actions:

- Refresh execution
- Back to Pipeline History
- Copy execution ID
- Open DRE screen

Empty states:

- Execution exists but no errors:
  - Message: "No errors recorded for this execution."
- Execution exists but no metadata:
  - Message: "No metadata recorded."

Loading states:

- Detail header skeleton.
- Counts skeleton.
- Tables skeleton.

Error states:

- `404`:
  - Message: "Pipeline execution not found."
  - Action: Back to Pipeline History
- API failure:
  - Message: "Pipeline execution could not be loaded."
  - Action: Retry

Navigation:

- From Pipeline History row.
- From Dashboard Latest Execution widget.

Permissions:

- Required role: `enterprise.viewer`

### 2.4 Financial DRE Screen

Primary endpoints:

- `GET /financial/dre`
- `GET /financial/dre/{company}`
- `GET /financial/dre/{company}/{period}`

Purpose:

Display the latest persisted DRE output exposed by the Financial Core through the persistence layer.

Widgets:

- DRE Filter Bar
- DRE Tree Table
- DRE Amount Summary
- DRE Node Detail drawer

Filters:

- Company
  - Type: text input or select if values are available locally.
  - API mapping:
    - Empty: `GET /financial/dre`
    - Present: `GET /financial/dre/{company}`
- Period
  - Type: text input or select.
  - API mapping:
    - Requires company.
    - Present with company: `GET /financial/dre/{company}/{period}`
- No additional server-side filters are available in the current API contract.

Tables:

- DRE Tree table
  - Source: `data.nodes`
  - Columns:
    - Node code
    - Node name
    - Level
    - Amount
    - Currency
    - Percentage
    - Parent node code
    - Ordinal
    - Rule ID

Charts:

- DRE Amount Bar Chart
  - X-axis: node name or node code
  - Y-axis: amount
  - Grouping: level
- DRE Composition Chart
  - Uses only returned nodes.
  - Should avoid implying calculated business semantics beyond persisted amounts.

Actions:

- Apply filters
- Clear filters
- Refresh DRE
- Expand or collapse tree rows locally
- Open node detail drawer
- Copy node code

Empty states:

- No DRE nodes:
  - Message: "No DRE data found for the selected filters."
- Company selected with no period:
  - Message remains data-oriented, not validation-oriented, because the API supports company-only lookup.

Loading states:

- Filter bar disabled while request is active.
- Tree table skeleton.
- Chart placeholder skeleton.

Error states:

- API failure:
  - Message: "DRE data could not be loaded."
  - Action: Retry
- Invalid local filter:
  - Message: "Review company and period filters."

Navigation:

- From Dashboard Overview.
- From Pipeline Execution Detail.
- Optional deep links:
  - `/financial/dre`
  - `/financial/dre/{company}`
  - `/financial/dre/{company}/{period}`

Permissions:

- Required role: `enterprise.viewer`
- Optional restricted role: `financial.viewer`

### 2.5 System Status Screen

Primary endpoints:

- `GET /health`
- `GET /version`

Purpose:

Display operational API status and contract version information.

Widgets:

- Health Status widget
- Database Status widget
- API Version widget
- Contract Metadata widget

Filters:

- None.

Tables:

- None required.

Charts:

- None required.

Actions:

- Refresh status
- Copy API version

Empty states:

- Not applicable for successful responses.

Loading states:

- Small status card skeleton.

Error states:

- Health unavailable:
  - Message: "Health endpoint unavailable."
- Version unavailable:
  - Message: "Version endpoint unavailable."

Navigation:

- Available from global navigation footer or system menu.

Permissions:

- Required role: `enterprise.viewer`
- May be public internally if enterprise authentication later allows unauthenticated health checks.

## 3. Navigation Map

Primary navigation:

- Dashboard
  - Route: `/dashboard`
  - API dependencies:
    - `GET /analytics/kpis`
    - `GET /health`
    - `GET /version`
    - `GET /pipeline/history`
- Pipeline
  - Route: `/pipeline`
  - API dependencies:
    - `GET /pipeline/history`
- Pipeline Detail
  - Route: `/pipeline/{execution_id}`
  - API dependencies:
    - `GET /pipeline/{execution_id}`
- Financial DRE
  - Route: `/financial/dre`
  - API dependencies:
    - `GET /financial/dre`
    - `GET /financial/dre/{company}`
    - `GET /financial/dre/{company}/{period}`
- System
  - Route: `/system`
  - API dependencies:
    - `GET /health`
    - `GET /version`

Navigation hierarchy:

```text
Dashboard
  Pipeline History
    Pipeline Execution Detail
  Financial DRE
  System Status
```

Cross-navigation:

- Dashboard Latest Execution -> Pipeline Execution Detail
- Dashboard Recent History -> Pipeline History
- Pipeline History row -> Pipeline Execution Detail
- Pipeline Execution Detail -> Financial DRE
- Any screen -> System Status

## 4. Component Catalog

### 4.1 Layout Components

App Shell:

- Global navigation
- Main content area
- Status area for health/version indicators

Page Header:

- Title
- Subtitle
- Optional primary action
- Optional refresh action

Filter Bar:

- Used on Pipeline History and Financial DRE.
- Contains only filters supported by the current API contract or local filters over returned data.

### 4.2 Data Components

KPI Card:

- Label
- Value
- Optional secondary value
- Loading skeleton
- Error state

Status Badge:

- Values:
  - `ok`
  - `succeeded`
  - `failed`
  - `unavailable`
- Used for health, database, execution status, and success fields.

Pipeline History Table:

- Uses `PipelineExecutionSummary`.
- Supports row navigation.

Pipeline Execution Detail Panel:

- Uses `PipelineExecutionDetail`.
- Shows status, duration, source path, metadata, errors, and artifact counts.

DRE Tree Table:

- Uses `DRERow`.
- Supports indentation by `level`.
- Supports local expand/collapse.

Metadata Key Value Table:

- Displays arbitrary metadata dictionaries from the API contract.

Error List:

- Displays API envelope errors or execution-specific errors.

### 4.3 Chart Components

Status Donut Chart:

- Inputs:
  - Successful executions
  - Failed executions
- Source: `KPIResponse`

Artifact Count Bar Chart:

- Inputs:
  - Accounting entries
  - DRE nodes
  - Reconciliation rows
  - Metrics rows
- Source: `PipelineExecutionDetail`

DRE Amount Bar Chart:

- Inputs:
  - Node code
  - Node name
  - Amount
  - Level
- Source: `DRERow`

### 4.4 Feedback Components

Loading Skeleton:

- Page skeleton
- Widget skeleton
- Table skeleton

Empty State:

- Title
- Message
- Optional retry or refresh action

Error Banner:

- Uses API envelope `errors`.
- Includes retry action when request is repeatable.

Request Metadata Indicator:

- Displays `meta.api_version`.
- Optionally displays `meta.generated_at`.

## 5. Screen Flow

### 5.1 Initial Load

1. User opens Dashboard.
2. UI requests:
   - `GET /health`
   - `GET /version`
   - `GET /analytics/kpis`
   - `GET /pipeline/history`
3. UI renders global status, KPIs, charts, and recent executions.
4. If any request fails, only the affected widget enters error state.

### 5.2 Pipeline Investigation

1. User opens Pipeline History.
2. UI requests `GET /pipeline/history`.
3. User selects an execution row.
4. UI navigates to Pipeline Execution Detail.
5. UI requests `GET /pipeline/{execution_id}`.
6. UI displays execution metadata, errors, and persisted artifact counts.

### 5.3 DRE Review

1. User opens Financial DRE.
2. UI requests `GET /financial/dre`.
3. User optionally applies company filter.
4. UI requests `GET /financial/dre/{company}`.
5. User optionally applies period filter.
6. UI requests `GET /financial/dre/{company}/{period}`.
7. UI renders DRE table and charts using returned persisted nodes only.

### 5.4 System Verification

1. User opens System Status.
2. UI requests:
   - `GET /health`
   - `GET /version`
3. UI displays service status, database status, API title, version, and response metadata.

## 6. Permissions Model

Current API contract does not define authentication or authorization endpoints. UI permissions are therefore specified as frontend and future-auth readiness roles only.

Roles:

- `enterprise.viewer`
  - Can view all dashboard screens.
- `enterprise.operator`
  - Can view operational pipeline metadata.
  - No write actions exist in the current contract.
- `financial.viewer`
  - Can view Financial DRE screens.

Permission behavior:

- Hide navigation items when the user lacks the required role.
- Show a permission empty state for deep-linked screens without access.
- Do not call restricted endpoints when the user lacks permission.

## 7. Contract Boundaries

The UI must not:

- Create new API calls outside the official contract.
- Recalculate business rules.
- Reconcile financial data client-side.
- Infer missing financial values.
- Mutate persisted Enterprise data.
- Upload source files.
- Trigger pipeline execution.

The UI may:

- Format dates, numbers, and currency values.
- Sort and filter already returned rows locally.
- Render charts directly from returned response fields.
- Show empty, loading, and error states based on the API envelope.

## 8. Acceptance Criteria

- Every official endpoint maps to at least one screen or widget.
- No unsupported endpoint is required by the UI.
- Every screen defines filters, tables, charts, actions, empty states, loading states, error states, navigation, and permissions.
- Components rely on Pydantic API response schemas from the contract.
- No frontend implementation is included.
