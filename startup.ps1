$ErrorActionPreference = "Stop"

if (-not $env:PORT) {
    $env:PORT = "8000"
}

Write-Host "Running enterprise database migrations..."
python -m alembic upgrade head

Write-Host "Starting ARDO Enterprise API on port $env:PORT..."
python -m uvicorn api.main:app --host 0.0.0.0 --port $env:PORT
