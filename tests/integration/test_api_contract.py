from __future__ import annotations

from tests.integration.test_enterprise_api import auth_headers, build_client


EXPECTED_GET_ENDPOINTS = {
    "/health",
    "/version",
    "/pipeline/history",
    "/pipeline/{execution_id}",
    "/financial/dre",
    "/financial/dre/{company}",
    "/financial/dre/{company}/{period}",
    "/analytics/kpis",
}


def test_api_contract_exposes_only_official_get_endpoints(tmp_path):
    client = build_client(tmp_path)
    schema = client.get("/openapi.json").json()

    get_endpoints = {
        path
        for path, operations in schema["paths"].items()
        if "get" in operations and not path.startswith("/docs")
    }

    assert get_endpoints == EXPECTED_GET_ENDPOINTS


def test_api_contract_uses_standard_response_envelope(tmp_path):
    client = build_client(tmp_path)
    headers = auth_headers(client)

    endpoints = [
        ("/health", None),
        ("/version", None),
        ("/pipeline/history", headers),
        ("/pipeline/exec-1", headers),
        ("/financial/dre", headers),
        ("/financial/dre/company-a", headers),
        ("/financial/dre/company-a/202606", headers),
        ("/analytics/kpis", headers),
    ]

    for endpoint, request_headers in endpoints:
        response = client.get(endpoint, headers=request_headers)
        payload = response.json()
        assert response.status_code == 200
        assert set(payload) == {"data", "meta", "errors"}
        assert payload["meta"]["api_version"] == "0.2.0"
        assert isinstance(payload["errors"], list)


def test_api_contract_protects_enterprise_endpoints(tmp_path):
    client = build_client(tmp_path)

    protected_endpoints = [
        "/pipeline/history",
        "/pipeline/exec-1",
        "/financial/dre",
        "/financial/dre/company-a",
        "/financial/dre/company-a/202606",
        "/analytics/kpis",
    ]

    for endpoint in protected_endpoints:
        assert client.get(endpoint).status_code == 401


def test_api_contract_accepts_internal_api_key(tmp_path):
    client = build_client(tmp_path)

    response = client.get("/analytics/kpis", headers={"X-API-Key": "internal-test-key"})

    assert response.status_code == 200
    assert response.json()["data"]["pipeline_executions"] == 1


def test_openapi_contract_has_examples_for_response_components(tmp_path):
    client = build_client(tmp_path)
    schema = client.get("/openapi.json").json()
    components = schema["components"]["schemas"]

    for component_name in [
        "HealthResponse",
        "VersionResponse",
        "PipelineExecutionSummary",
        "PipelineHistoryResponse",
        "PipelineExecutionResponse",
        "DRERow",
        "DRETreeResponse",
        "KPIResponse",
    ]:
        assert "examples" in components[component_name]
