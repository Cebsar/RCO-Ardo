# ARDO Enterprise Deployment README

This guide describes production startup for the ARDO Enterprise FastAPI platform.

## Prerequisites

- Docker and Docker Compose for container deployment.
- Python 3.14 for local deployment.
- A production `.env` file created from `.env.example`.

## Environment Setup

1. Copy the example file:

```bash
cp .env.example .env
```

2. Replace all placeholder secrets:

- `API_SECRET_KEY`
- `API_AUTH_USERS`
- `API_INTERNAL_API_KEYS`

3. Review persistence configuration:

```env
ENTERPRISE_DATABASE_URL=sqlite:///database/enterprise.db
```

Inside Docker Compose, the default database path resolves to:

```env
sqlite:////app/database/enterprise.db
```

The `/app/database` directory is mounted to the `enterprise_database` volume.

## Docker Startup

Build and start:

```bash
docker compose up --build -d
```

Inspect logs:

```bash
docker compose logs -f enterprise-api
```

Stop:

```bash
docker compose down
```

Stop and remove the enterprise database volume:

```bash
docker compose down -v
```

## Linux Startup Without Docker

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
./startup.sh
```

The script runs:

```bash
python -m alembic upgrade head
python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
```

## Windows Startup Without Docker

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run:

```powershell
.\startup.ps1
```

The script runs migrations before starting FastAPI.

## Healthcheck

Health endpoint:

```text
GET /health
```

Docker healthcheck:

```text
curl --fail http://127.0.0.1:8000/health
```

## Swagger

Swagger is available after startup:

```text
http://localhost:8000/docs
```

OpenAPI JSON:

```text
http://localhost:8000/openapi.json
```

## Makefile Commands

```bash
make install
make migrate
make test-integration
make docker-build
make docker-up
make docker-logs
make docker-down
```

## Production Notes

- Do not commit `.env`.
- Use strong secrets for JWT signing and internal API keys.
- Keep the enterprise database volume backed up.
- Run `python -m alembic upgrade head` before serving the API. The provided startup scripts already do this.
- `/health`, `/version`, `/docs`, and `/openapi.json` remain public.
- Enterprise data endpoints require JWT or `X-API-Key`.
