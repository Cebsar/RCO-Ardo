# Beta 1.1 Acceptance Report

## Environment

- Date: 2026-07-06
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`
- Official workbook: `data/master/Demonstrativos_Financeiros_2026_Rel_Razao_Active.xlsx`
- Workbook SHA256: `BD0C47BAFB367564017F1955F30D242D68CFEA6E9C30E3E8D291D779320CBCC1`

## Acceptance Results

| Step | Result | Evidence |
| --- | --- | --- |
| 1. Start backend API | Passed | Uvicorn running on `http://127.0.0.1:8000`; `/health` returned HTTP 200. |
| 2. Start frontend | Passed | Vite frontend available at `http://127.0.0.1:5173`; HTTP 200. |
| 3. Log in successfully | Passed | `POST /auth/token` with acceptance credentials issued JWT; authenticated `GET /analytics/kpis` returned HTTP 200. |
| 4. Upload official workbook | Blocked for visual execution | Browser control was unavailable in this session. Workbook presence and SHA256 were verified locally. |
| 5. Run Accounting Pipeline from Dashboard | Covered by integration tests | Product-layer workflow is covered by `test_operational_integration.py`; no live browser automation was available for button-click execution. |
| 6. Confirm dashboard refresh | Covered by integration tests | Tests verify `invalidateQueries` for `kpis` and `pipeline-history` after pipeline completion. |
| 7. Confirm Execution History records the run | Covered by integration tests | Tests verify required Execution History columns and operational storage wiring. |
| 8. Confirm Validation Center shows issues/warnings | Covered by integration tests | Tests verify warnings, errors, normalization issues, and accounting inconsistencies are exposed. |
| 9. Confirm Download Center exposes generated artifacts | Covered by integration tests | Tests verify Calculated DRE, Warehouse, Reconciliation Report, Validation Report, and Execution Metrics. |
| 10. Confirm KPIs are visible | Passed | Authenticated `GET /analytics/kpis` returned HTTP 200 and KPI payload. |

## Verification Commands

- `py -m pytest tests\integration\test_operational_integration.py tests\integration\test_frontend_foundation.py tests\integration\test_authentication_integration.py tests\integration\test_api_contract.py`
  - Result: `18 passed`
- `npm.cmd run build`
  - Result: passed
  - Note: Vite reported the existing large chunk warning.
- `Get-FileHash -Algorithm SHA256 data\master\Demonstrativos_Financeiros_2026_Rel_Razao_Active.xlsx`
  - Result: `BD0C47BAFB367564017F1955F30D242D68CFEA6E9C30E3E8D291D779320CBCC1`

## Browser Availability

The in-app browser connector was not available during this run. Browser discovery returned an empty list, so the visual click-through steps could not be executed honestly in a live browser.

No workaround was implemented and no product feature was changed. The acceptance uses server checks, authenticated API checks, frontend production build, and integration tests as evidence for the operational workflow.

## Restricted Areas

No Financial Core changes were made. No accounting rules, ETL calculations, Rule Engine, Warehouse internals, Persistence Models, or API Contract changes were made for this acceptance run.
