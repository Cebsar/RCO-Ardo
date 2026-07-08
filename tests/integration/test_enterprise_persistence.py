from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from src.domain.entities import AccountingEntry, Account, DRENode
from src.domain.enums import AccountType, DRELevel, EntryType
from src.domain.value_objects import AccountCode, Money
from src.execution.configuration import ExecutionConfiguration
from src.execution.context import ExecutionContext
from src.execution.reports import PipelineReport, StageResult
from src.execution.runner import PipelineRunner
from src.infrastructure.persistence.database import DatabaseConfig
from src.infrastructure.persistence.models import (
    ExecutionMetricsORM,
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)
from src.infrastructure.persistence.service import EnterprisePersistenceService
from src.infrastructure.reconciliation.models import (
    AuditReport,
    DifferenceItem,
    DifferenceReport,
    ExecutionMetrics,
    ToleranceRule,
    ValidationMetrics,
)
from src.infrastructure.rule_engine.models import ExecutionMetrics as RuleExecutionMetrics
from src.infrastructure.rule_engine.models import ExecutionReport


def make_report() -> PipelineReport:
    config = ExecutionConfiguration(
        source_path=Path("data/master/source.xlsx"),
        rules_config_path=Path("config/business_rules.yaml"),
    )
    return PipelineReport(
        configuration=config,
        started_at=datetime(2026, 7, 6, 9, 0, 0),
        finished_at=datetime(2026, 7, 6, 9, 0, 3),
        duration_seconds=3.0,
        success=True,
        stage_results=[StageResult(name="Build Warehouse", success=True, duration_seconds=1.2)],
        rule_execution=ExecutionReport(
            metrics=RuleExecutionMetrics(
                start_time=datetime(2026, 7, 6, 9, 0, 1),
                end_time=datetime(2026, 7, 6, 9, 0, 2),
                duration_seconds=1.0,
                nodes_processed=1,
                rules_executed=1,
            )
        ),
    )


def make_entry() -> AccountingEntry:
    return AccountingEntry(
        id="entry-1",
        account=Account(code=AccountCode("4000"), name="Revenue", type=AccountType.REVENUE),
        amount=Money(Decimal("123.45")),
        date=date(2026, 6, 30),
        entry_type=EntryType.CREDIT,
        description="Integration entry",
        source_fields={
            "month": 6, "year": 2026, "company": "0001 - ARDO", "group": "ARDO",
            "division": "USINA", "dre_group": "Receita Bruta", "account_description": "Revenue",
            "account_code": "4000", "cost_center": "2 - USINA", "batch_number": "1108",
            "posting_number": "42", "title": "NF-1", "history": "Venda", "counterparty": "Cliente",
            "debit": 0, "credit": Decimal("123.45"), "value": Decimal("123.45"),
        },
    )


def make_dre() -> list[DRENode]:
    child = DRENode(
        code=AccountCode("4.01"),
        name="Gross Revenue",
        level=DRELevel.LEVEL_2,
        amount=Money(Decimal("123.45")),
    )
    root = DRENode(
        code=AccountCode("4"),
        name="Revenue",
        level=DRELevel.LEVEL_1,
        amount=Money(Decimal("123.45")),
        children=(child,),
    )
    return [root]


def make_reconciliation() -> AuditReport:
    differences = DifferenceReport()
    differences.add(
        DifferenceItem(
            node_code="4",
            node_name="Revenue",
            expected=Decimal("123.45"),
            actual=Decimal("120.00"),
            difference=Decimal("-3.45"),
            tolerance=ToleranceRule(absolute=Decimal("0.01"), relative=Decimal("0.001")),
            percentage_difference=Decimal("-0.027946"),
        )
    )
    return AuditReport(
        reconciliation=differences,
        validation=ValidationMetrics(nodes_compared=1, discrepancies_found=1, tolerance_checks=1),
        execution=ExecutionMetrics(
            start_time=datetime(2026, 7, 6, 9, 0, 2),
            end_time=datetime(2026, 7, 6, 9, 0, 3),
            duration_seconds=1.0,
        ),
        source="source.xlsx",
    )


def test_enterprise_persistence_layer_persists_required_artifacts(tmp_path):
    db_url = f"sqlite:///{(tmp_path / 'enterprise.db').as_posix()}"
    service = EnterprisePersistenceService(config=DatabaseConfig(db_url))
    service.create_database()

    persisted = service.persist_pipeline_run(
        make_report(),
        accounting_entries=[make_entry()],
        dre_roots=make_dre(),
        reconciliation_report=make_reconciliation(),
    )

    with service.session_factory() as session:
        executions = session.scalars(select(PipelineExecutionORM)).all()
        accounting = session.scalars(select(FactAccountingEntryORM)).all()
        dre = session.scalars(select(FactDREORM)).all()
        reconciliation = session.scalars(select(FactReconciliationORM)).all()
        metrics = session.scalars(select(ExecutionMetricsORM)).all()

    assert persisted.pipeline_execution_id == executions[0].id
    assert persisted.accounting_entries == 1
    assert persisted.dre_nodes == 2
    assert persisted.reconciliation_rows == 1
    assert persisted.metrics_rows == 3
    assert accounting[0].entry_id == "entry-1"
    assert accounting[0].account_code == "4000"
    assert accounting[0].group_name == "ARDO"
    assert accounting[0].dre_group == "Receita Bruta"
    assert accounting[0].source_month == 6
    assert accounting[0].source_year == 2026
    assert accounting[0].source_value == Decimal("123.45")
    assert len(dre) == 2
    assert reconciliation[0].node_code == "4"
    assert {metric.scope for metric in metrics} == {
        "rule_execution",
        "reconciliation",
        "stage:Build Warehouse",
    }


def test_pipeline_runner_enterprise_hook_persists_available_artifacts():
    class FakePersistence:
        def persist_pipeline_run(self, report, **kwargs):
            self.report = report
            self.kwargs = kwargs

            class Persisted:
                pipeline_execution_id = "run-1"
                accounting_entries = 1
                dre_nodes = 2
                reconciliation_rows = 1
                metrics_rows = 3

            return Persisted()

    report = make_report()
    context = ExecutionContext(pipeline_name="ARDO Pipeline")
    context.payload = {
        "entries": [make_entry()],
        "assigned_roots": make_dre(),
        "reconciliation": make_reconciliation(),
    }
    persistence = FakePersistence()
    runner = PipelineRunner(
        excel_adapter=None,
        header_mapper=None,
        schema_validator=None,
        warehouse_builder=None,
        dre_tree_builder=None,
        business_rule_provider=None,
        rule_engine=None,
        enterprise_persistence=persistence,
    )

    runner._attach_reports(report, context)
    runner._persist_enterprise_report(report, context)

    assert persistence.kwargs["accounting_entries"] == context.payload["entries"]
    assert persistence.kwargs["dre_roots"] == context.payload["assigned_roots"]
    assert report.metadata["enterprise_persistence"]["pipeline_execution_id"] == "run-1"
