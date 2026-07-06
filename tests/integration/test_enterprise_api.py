from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.dependencies import get_db_session
from api.main import create_app
from src.infrastructure.persistence.models import (
    Base,
    ExecutionMetricsORM,
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)


def build_client(tmp_path) -> TestClient:
    engine = create_engine(f"sqlite:///{(tmp_path / 'api.db').as_posix()}", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)

    with session_factory() as session:
        execution = PipelineExecutionORM(
            id="exec-1",
            pipeline_name="ARDO Pipeline",
            source_path="data/master/company-a-202606.xlsx",
            status="succeeded",
            success=True,
            started_at=datetime(2026, 7, 6, 9, 0, 0),
            finished_at=datetime(2026, 7, 6, 9, 0, 2),
            duration_seconds=2.0,
            errors=[],
            execution_metadata={"source": "integration"},
            created_at=datetime(2026, 7, 6, 9, 0, 3),
        )
        session.add(execution)
        session.add(
            FactAccountingEntryORM(
                pipeline_execution_id="exec-1",
                entry_id="entry-1",
                period_code="202606",
                account_code="4000",
                account_name="Revenue",
                amount=Decimal("100.00"),
                currency="BRL",
                entry_type="credit",
                accounting_date=datetime(2026, 6, 30).date(),
                source_row={},
            )
        )
        session.add(
            FactDREORM(
                pipeline_execution_id="exec-1",
                node_code="4",
                node_name="Revenue",
                level=1,
                amount=Decimal("100.00"),
                currency="BRL",
                ordinal=0,
                payload={"node_code": "4"},
            )
        )
        session.add(
            FactReconciliationORM(
                pipeline_execution_id="exec-1",
                node_code="4",
                node_name="Revenue",
                expected_amount=Decimal("100.00"),
                actual_amount=Decimal("100.00"),
                difference_amount=Decimal("0.00"),
                exists_in_expected=True,
                exists_in_actual=True,
                order_match=True,
                level_match=True,
                payload={},
            )
        )
        session.add(
            ExecutionMetricsORM(
                pipeline_execution_id="exec-1",
                scope="rule_execution",
                duration_seconds=1.0,
                nodes_processed=1,
                rules_executed=1,
                payload={},
            )
        )
        session.commit()

    app = create_app()

    def override_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    return TestClient(app)


def test_api_startup_and_system_endpoints(tmp_path):
    client = build_client(tmp_path)

    health = client.get("/health")
    version = client.get("/version")
    openapi = client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "ok"}
    assert version.status_code == 200
    assert version.json()["version"] == "0.2.0"
    assert openapi.status_code == 200
    assert "/pipeline/history" in openapi.json()["paths"]


def test_api_exposes_pipeline_financial_and_analytics_endpoints(tmp_path):
    client = build_client(tmp_path)

    history = client.get("/pipeline/history")
    execution = client.get("/pipeline/exec-1")
    dre = client.get("/financial/dre/company-a/202606")
    kpis = client.get("/analytics/kpis")

    assert history.status_code == 200
    assert history.json()["executions"][0]["id"] == "exec-1"
    assert execution.status_code == 200
    assert execution.json()["execution"]["accounting_entries"] == 1
    assert dre.status_code == 200
    assert dre.json()["filters"] == {"company": "company-a", "period": "202606"}
    assert dre.json()["nodes"][0]["node_code"] == "4"
    assert kpis.status_code == 200
    assert kpis.json()["pipeline_executions"] == 1
    assert kpis.json()["latest_execution_id"] == "exec-1"
