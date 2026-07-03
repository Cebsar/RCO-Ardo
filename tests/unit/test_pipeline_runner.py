from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.domain.entities import AccountingEntry, Account, CostCenter, DRENode
from src.domain.enums import AccountType, DRELevel, EntryType
from src.domain.value_objects import AccountCode, CostCenterCode, Money
from src.execution.configuration import ExecutionConfiguration
from src.execution.runner import PipelineRunner
from src.infrastructure.rule_engine.models import BusinessRule
from src.infrastructure.rule_engine.models import ExecutionReport, RuleResult
from src.infrastructure.reconciliation.models import AuditReport, DifferenceReport, ExecutionMetrics, ValidationMetrics, ToleranceRule
from src.infrastructure.dre_loader.models import DRETree
from src.infrastructure.warehouse.models import WarehouseReport


class DummyExcelAdapter:
    def __init__(self, rows: List[Dict[str, Any]], headers: List[str]):
        self._rows = rows
        self._headers = headers

    def read(self, source: str) -> List[Dict[str, Any]]:
        return self._rows

    def get_headers(self) -> List[str]:
        return self._headers


class DummyNormalizer:
    def __init__(self, entries: List[AccountingEntry]):
        self.entries = entries

    def normalize(self, rows: List[Dict[str, Any]]) -> tuple[List[AccountingEntry], Any]:
        return self.entries, DummyNormalizationReport()


@dataclass
class DummyNormalizationReport:
    issues: List[Any] = None
    normalized_count: int = 0
    invalid_count: int = 0
    skipped_empty: int = 0
    execution_time_seconds: float = 0.0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class DummyWarehouseBuilder:
    def build(self, entries: List[AccountingEntry]) -> WarehouseReport:
        report = WarehouseReport()
        report.fact_rows = len(entries)
        report.new_rows = len(entries)
        report.company_rows = 1
        report.account_rows = 1
        report.period_rows = 1
        report.execution_time_seconds = 0.001
        return report


class DummyDRETreeBuilder:
    def build_from_path(self, path: Path, sheet_name: str = "Overview RCO"):
        root = DRENode(code=AccountCode("REVENUE"), name="Revenue", level=DRELevel.LEVEL_1, amount=None, children=())
        return DRETree(roots=(root,)), None


class DummyBusinessRuleProvider:
    def __init__(self):
        self.rule = BusinessRule(
            id="REVENUE",
            node_code="REVENUE",
            expression="sum([Decimal(f['amount']) for f in facts])",
            description="Sum revenue facts",
            filters={"account_code_prefix": "4"},
            calculated=True,
        )

    def assign_rules(self, dre_tree: List[DRENode]) -> List[DRENode]:
        return [DRENode(code=node.code, name=node.name, level=node.level, amount=node.amount, percentage=node.percentage, children=node.children, rule=self.rule) for node in dre_tree]

    def get_business_rules(self) -> List[BusinessRule]:
        return [self.rule]


class DummyReconciliationEngine:
    def reconcile(self, expected_tree: Any, actual_tree: Any, tolerance: Optional[ToleranceRule] = None, source_name: Optional[str] = None) -> AuditReport:
        return AuditReport(
            reconciliation=DifferenceReport(),
            validation=ValidationMetrics(nodes_compared=0, discrepancies_found=0, tolerance_checks=0, start_time=datetime.utcnow(), end_time=datetime.utcnow()),
            execution=ExecutionMetrics(start_time=datetime.utcnow(), end_time=datetime.utcnow(), duration_seconds=0.0),
            source=source_name,
        )


def make_entry() -> AccountingEntry:
    account = Account(code=AccountCode("4000"), name="Sales", type=AccountType.EXPENSE)
    return AccountingEntry(
        id="entry1",
        account=account,
        amount=Money(Decimal("100")),
        date=date(2026, 1, 1),
        entry_type=EntryType.DEBIT,
        cost_center=CostCenter(code=CostCenterCode("CC1"), name="Cost Center 1"),
        description="Sale",
    )


def test_pipeline_runner_executes_all_stages_successfully():
    rows = [
        {
            "Company": "X",
            "Division": "Y",
            "CostCenter": "Z",
            "AccountCode": "4000",
            "AccountDescription": "Sale",
            "AccountingDate": date(2026, 1, 1),
            "DocumentNumber": "DOC1",
            "History": "Sale",
            "Debit": "100",
            "Credit": None,
            "Balance": None,
        }
    ]
    headers = [
        "Company",
        "Division",
        "CostCenter",
        "AccountCode",
        "AccountDescription",
        "AccountingDate",
        "DocumentNumber",
        "History",
        "Debit",
        "Credit",
        "Balance",
    ]
    adapter = DummyExcelAdapter(rows=rows, headers=headers)
    header_mapper = __import__("src.infrastructure.header_mapper.mapper", fromlist=["HeaderMapper"]).HeaderMapper()
    schema_validator = __import__("src.infrastructure.schema_validator.validator", fromlist=["SchemaValidator"]).SchemaValidator()
    warehouse_builder = DummyWarehouseBuilder()
    dre_tree_builder = DummyDRETreeBuilder()
    business_rule_provider = DummyBusinessRuleProvider()
    rule_engine = __import__("src.infrastructure.rule_engine.engine", fromlist=["RuleEngine"]).RuleEngine()
    reconciliation_engine = DummyReconciliationEngine()

    runner = PipelineRunner(
        excel_adapter=adapter,
        header_mapper=header_mapper,
        schema_validator=schema_validator,
        warehouse_builder=warehouse_builder,
        dre_tree_builder=dre_tree_builder,
        business_rule_provider=business_rule_provider,
        rule_engine=rule_engine,
        reconciliation_engine=reconciliation_engine,
        normalizer_factory=lambda mapping: DummyNormalizer([make_entry()]),
    )

    config = ExecutionConfiguration(source_path=Path("data/master/Rel_Razão.xlsx"), rules_config_path=Path("config/business_rules.yaml"))
    report = runner.run(config)

    assert report.success
    assert report.failed_stages == 0
    assert report.passed_stages == len(report.stage_results)
    assert any(stage.name == "Run Business Rules" for stage in report.stage_results)
    assert report.reconciliation is not None
    assert report.reconciliation.source == str(config.source_path.name)
