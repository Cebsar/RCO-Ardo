# RC3.1 Security Foundation Report

Status: Implemented  
Scope: API security foundation only

## Implemented Controls

- JWT authentication using signed HS256 access tokens.
- OAuth2 Password Flow token issuance at `POST /auth/token`.
- API key authentication for internal services via `X-API-Key`.
- Environment-based security configuration.
- Secret management through environment variables.
- CORS configuration through environment variables.
- OpenAPI security schemes for OAuth2 Password Flow and API key auth.

## Public Endpoints

The following endpoints remain public:

- `GET /health`
- `GET /version`
- `GET /docs`
- `GET /openapi.json`

The OAuth2 token endpoint `POST /auth/token` is unauthenticated by design because it issues credentials for the password flow.

## Protected Endpoints

The following endpoints require either a Bearer JWT or `X-API-Key`:

- `GET /pipeline/history`
- `GET /pipeline/{execution_id}`
- `GET /financial/dre`
- `GET /financial/dre/{company}`
- `GET /financial/dre/{company}/{period}`
- `GET /analytics/kpis`

## Environment Configuration

Security environment variables:

- `API_SECRET_KEY`
  - JWT signing secret.
  - Must be set to a strong secret outside local development.
- `API_JWT_ALGORITHM`
  - Default: `HS256`.
- `API_ACCESS_TOKEN_EXPIRE_MINUTES`
  - Default: `60`.
- `API_AUTH_USERS`
  - Comma-separated `username:password` or `username:sha256$<digest>` entries.
- `API_INTERNAL_API_KEYS`
  - Comma-separated internal service API keys.
- `API_CORS_ALLOW_ORIGINS`
  - Comma-separated allowed origins.
  - Default: `http://localhost:3000`.
- `API_CORS_ALLOW_CREDENTIALS`
  - Default: `true`.
- `API_CORS_ALLOW_METHODS`
  - Default: `GET,POST,OPTIONS`.
- `API_CORS_ALLOW_HEADERS`
  - Default: `Authorization,Content-Type,X-API-Key,X-Request-ID`.

## OpenAPI Security

OpenAPI declares:

- `OAuth2PasswordBearer`
  - Type: `oauth2`
  - Flow: `password`
  - Token URL: `/auth/token`
- `APIKeyHeader`
  - Type: `apiKey`
  - Location: `header`
  - Name: `X-API-Key`

Protected endpoints accept either scheme.

## Validation

Integration tests cover:

- OAuth2 password token issuance.
- JWT access to protected endpoints.
- API key access for internal services.
- Authentication required for protected endpoints.
- Public access for health, version, docs, and OpenAPI.
- OpenAPI security scheme generation.
- CORS preflight behavior.

## Boundaries

No Financial Core, Rule Engine, Warehouse, ETL, Reconciliation, or business logic changes were made.
