# ARDO Enterprise Dashboard Frontend

Production-ready React dashboard for the ARDO Enterprise API.

## Stack

- React
- TypeScript
- Vite
- TailwindCSS
- ShadCN UI conventions
- React Query
- TanStack Table
- Recharts

## API Contract

The dashboard consumes only the existing REST API:

- `GET /health`
- `GET /version`
- `GET /pipeline/history`
- `GET /pipeline/{execution_id}`
- `GET /financial/dre`
- `GET /financial/dre/{company}`
- `GET /financial/dre/{company}/{period}`
- `GET /analytics/kpis`
- `POST /auth/token`

No SQLite access, Financial Core access, or business rule execution exists in the frontend.

## Environment

Optional local override:

```env
VITE_API_BASE_URL=http://localhost:8000
```

If omitted, Vite proxies `/api` to `http://localhost:8000`.

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Authentication

The dashboard supports:

- OAuth2 password flow through `POST /auth/token`
- Internal service API key through `X-API-Key`

Credentials are stored in browser local storage for the dashboard session.
