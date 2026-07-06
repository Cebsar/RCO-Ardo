from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_required_deployment_files_exist():
    for relative_path in [
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "startup.sh",
        "startup.ps1",
        "Makefile",
        "docs/deployment_readme.md",
        "docs/deployment_report.md",
        "docs/deployment_infrastructure.mmd",
    ]:
        assert (ROOT / relative_path).exists(), relative_path


def test_dockerfile_containerizes_fastapi_with_healthcheck_and_non_root_user():
    dockerfile = read_text("Dockerfile")

    assert "FROM python:3.14-slim" in dockerfile
    assert "python -m pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/health" in dockerfile
    assert 'CMD ["./startup.sh"]' in dockerfile


def test_docker_compose_mounts_enterprise_database_volume_and_healthcheck():
    compose = yaml.safe_load(read_text("docker-compose.yml"))
    service = compose["services"]["enterprise-api"]

    assert "enterprise_database:/app/database" in service["volumes"]
    assert service["environment"]["ENTERPRISE_DATABASE_URL"].endswith("/app/database/enterprise.db}")
    assert "/health" in " ".join(service["healthcheck"]["test"])
    assert compose["volumes"]["enterprise_database"]["name"] == "ardo_enterprise_database"


def test_startup_scripts_run_migrations_before_fastapi():
    linux_script = read_text("startup.sh")
    windows_script = read_text("startup.ps1")

    assert linux_script.index("python -m alembic upgrade head") < linux_script.index("python -m uvicorn api.main:app")
    assert windows_script.index("python -m alembic upgrade head") < windows_script.index("python -m uvicorn api.main:app")


def test_env_example_declares_runtime_persistence_security_and_cors_settings():
    env_example = read_text(".env.example")

    for key in [
        "PORT=",
        "ENTERPRISE_DATABASE_URL=",
        "API_SECRET_KEY=",
        "API_AUTH_USERS=",
        "API_INTERNAL_API_KEYS=",
        "API_CORS_ALLOW_ORIGINS=",
    ]:
        assert key in env_example


def test_deployment_docs_include_startup_swagger_and_infrastructure_diagram():
    deployment_readme = read_text("docs/deployment_readme.md")
    deployment_report = read_text("docs/deployment_report.md")
    diagram = read_text("docs/deployment_infrastructure.mmd")

    assert "docker compose up --build -d" in deployment_readme
    assert "http://localhost:8000/docs" in deployment_readme
    assert "Automatic" not in deployment_report or "migrations" in deployment_report.lower()
    assert "FastAPI Container" in diagram
    assert "enterprise_database" in diagram
