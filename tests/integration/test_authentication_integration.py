from __future__ import annotations

from pathlib import Path

from tests.integration.test_enterprise_api import build_client


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_oauth2_login_unlocks_analytics_kpis(tmp_path):
    client = build_client(tmp_path)

    token_response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin"},
    )
    assert token_response.status_code == 200

    token = token_response.json()["access_token"]
    kpis_response = client.get("/analytics/kpis", headers={"Authorization": f"Bearer {token}"})

    assert kpis_response.status_code == 200
    assert kpis_response.json()["data"]["pipeline_executions"] == 1


def test_internal_api_key_authentication_remains_available(tmp_path):
    client = build_client(tmp_path)

    response = client.get("/analytics/kpis", headers={"X-API-Key": "internal-test-key"})

    assert response.status_code == 200
    assert response.json()["data"]["latest_execution_id"] == "exec-1"


def test_frontend_auth_client_uses_session_jwt_and_bearer_header():
    api_client = (FRONTEND / "src" / "lib" / "api.ts").read_text(encoding="utf-8")

    assert 'const jwtStorageKey = "enterprise.jwt"' in api_client
    assert "window.sessionStorage" in api_client
    assert "session.setItem(jwtStorageKey, accessToken)" in api_client
    assert "headers.Authorization = `Bearer ${token}`" in api_client
    assert "headers[\"X-API-Key\"] = apiKey" in api_client
    assert "response.status === 401" in api_client
    assert "window.location.hash = \"login\"" in api_client


def test_frontend_sign_in_panel_surfaces_friendly_authentication_errors():
    auth_panel = (FRONTEND / "src" / "components" / "layout" / "AuthPanel.tsx").read_text(encoding="utf-8")

    assert "enterpriseApi.login(username, password)" in auth_panel
    assert "storeToken(token.access_token, token.expires_in)" in auth_panel
    assert "Your session expired. Sign in again to continue." in auth_panel
    assert "Internal API key saved for service requests." in auth_panel
