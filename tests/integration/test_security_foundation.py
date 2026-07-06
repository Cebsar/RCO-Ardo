from __future__ import annotations

from tests.integration.test_enterprise_api import auth_headers, build_client


def test_oauth2_password_flow_issues_jwt_and_unlocks_protected_endpoint(tmp_path):
    client = build_client(tmp_path)

    headers = auth_headers(client)
    response = client.get("/pipeline/history", headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["executions"][0]["id"] == "exec-1"


def test_public_endpoints_and_docs_do_not_require_authentication(tmp_path):
    client = build_client(tmp_path)

    assert client.get("/health").status_code == 200
    assert client.get("/version").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_openapi_declares_jwt_oauth2_and_api_key_security(tmp_path):
    client = build_client(tmp_path)
    schema = client.get("/openapi.json").json()

    security_schemes = schema["components"]["securitySchemes"]
    assert security_schemes["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"] == "/auth/token"
    assert security_schemes["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    assert schema["paths"]["/analytics/kpis"]["get"]["security"] == [
        {"OAuth2PasswordBearer": []},
        {"APIKeyHeader": []},
    ]


def test_cors_preflight_uses_environment_configuration(tmp_path):
    client = build_client(tmp_path)

    response = client.options(
        "/analytics/kpis",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
