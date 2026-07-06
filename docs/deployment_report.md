# RC3.2 Deployment Report

Status: Implemented  
Scope: Production deployment foundation only

## Deployment Artifacts

Created:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `startup.sh`
- `startup.ps1`
- `Makefile`
- `docs/deployment_readme.md`
- `docs/deployment_report.md`
- `docs/deployment_infrastructure.mmd`
- `tests/integration/test_deployment_foundation.py`

## Containerization

The Docker image:

- Uses Python 3.14 slim runtime.
- Installs dependencies from `requirements.txt`.
- Copies only API, source, Alembic, and migration assets needed at runtime.
- Runs as a non-root `appuser`.
- Exposes port `8000`.
- Defines a `/health` Docker healthcheck.
- Starts through `startup.sh`.

## Startup Behavior

Startup is standardized for Linux and Windows:

- Linux: `startup.sh`
- Windows: `startup.ps1`

Both scripts run:

1. `python -m alembic upgrade head`
2. `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`

This ensures migrations run automatically before the FastAPI process starts.

## Persistence Volume

Docker Compose mounts:

```text
enterprise_database:/app/database
```

Default container database URL:

```text
sqlite:////app/database/enterprise.db
```

## Environment Support

Deployment configuration is provided through `.env.example`.

Key environment groups:

- Runtime:
  - `ENV`
  - `PORT`
- Persistence:
  - `ENTERPRISE_DATABASE_URL`
- Security:
  - `API_SECRET_KEY`
  - `API_JWT_ALGORITHM`
  - `API_ACCESS_TOKEN_EXPIRE_MINUTES`
  - `API_AUTH_USERS`
  - `API_INTERNAL_API_KEYS`
- CORS:
  - `API_CORS_ALLOW_ORIGINS`
  - `API_CORS_ALLOW_CREDENTIALS`
  - `API_CORS_ALLOW_METHODS`
  - `API_CORS_ALLOW_HEADERS`

## Health and Swagger

Healthcheck:

```text
GET /health
```

Swagger:

```text
GET /docs
```

OpenAPI:

```text
GET /openapi.json
```

## Validation

Deployment tests validate:

- Required deployment files exist.
- Dockerfile starts FastAPI through the startup script.
- Dockerfile includes healthcheck and non-root execution.
- Docker Compose mounts the enterprise database volume.
- Compose healthcheck targets `/health`.
- Startup scripts run Alembic migrations before Uvicorn.
- `.env.example` includes required deployment variables.
- Deployment documentation and infrastructure diagram exist.

## Boundaries

No Financial Core, business rules, ETL, Warehouse, Reconciliation, or API business behavior was modified.
