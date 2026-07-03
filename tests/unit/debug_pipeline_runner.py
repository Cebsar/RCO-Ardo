from __future__ import annotations

from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from src.execution.runner import PipelineRunner
from src.execution.configuration import ExecutionConfiguration
from src.domain.enums import AccountType, DRELevel, EntryType
from src.domain.value_objects import AccountCode, CostCenterCode, Money
from src.domain.entities import AccountingEntry, Account, CostCenter, DRENode
from src.infrastructure.rule_engine.models import BusinessRule
from src.infrastructure.warehouse.models import WarehouseReport
from src.infrastructure.reconciliation.models import AuditReport, DifferenceReport, ValidationMetrics, ExecutionMetrics
from src.infrastructure.dre_loader.models import DRETree
import src.infrastructure.header_mapper.mapper as hm
import src.infrastructure.schema_validator.validator as sv
import src.infrastructure.rule_engine.engine as re


class DummyExcelAdapter:
    def __init__(self, rows, headers):
        self._rows = rows
        self._headers = headers

    def read(self, source: str):
        return self._rows

    def get_headers(self):
        return self._headers


class DummyNormalizer:
    def __init__(self, entries):
        self.entries = entries

    def normalize(self, rows):
        return self.entries, type(
            "R",
            (),
            {
                "issues": [],
                "normalized_count": 1,
                "invalid_count": 0,
                "skipped_empty": 0,
                "execution_time_seconds": 0.0,
            },
        )()


class DummyWarehouseBuilder:
    def build(self, entries):
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

    def assign_rules(self, dre_tree):
        return [
            DRENode(
                code=node.code,
                name=node.name,
                level=node.level,
                amount=node.amount,
                percentage=node.percentage,
                children=node.children,
                rule=self.rule,
            )
            for node in dre_tree
        ]

    def get_business_rules(self):
        return [self.rule]


class DummyReconciliationEngine:
    def reconcile(self, expected_tree, actual_tree, tolerance=None, source_name=None):
        return AuditReport(
            reconciliation=DifferenceReport(),
            validation=ValidationMetrics(nodes_compared=0, discrepancies_found=0, tolerance_checks=0, start_time=datetime.utcnow(), end_time=datetime.utcnow()),
            execution=ExecutionMetrics(start_time=datetime.utcnow(), end_time=datetime.utcnow(), duration_seconds=0.0),
            source=source_name,
        )


def main():
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
    runner = PipelineRunner(
        excel_adapter=adapter,
        header_mapper=hm.HeaderMapper(),
        schema_validator=sv.SchemaValidator(),
        warehouse_builder=DummyWarehouseBuilder(),
        dre_tree_builder=DummyDRETreeBuilder(),
        business_rule_provider=DummyBusinessRuleProvider(),
        rule_engine=re.RuleEngine(),
        reconciliation_engine=DummyReconciliationEngine(),
        normalizer_factory=lambda mapping: DummyNormalizer([
            AccountingEntry(
                id="entry1",
                account=Account(code=AccountCode("4000"), name="Sales", type=AccountType.EXPENSE),
                amount=Money(Decimal("100")),
                date=date(2026, 1, 1),
                entry_type=EntryType.DEBIT,
                cost_center=CostCenter(code=CostCenterCode("CC1"), name="Cost Center 1"),
                description="Sale",
            )
        ]),
    )
    config = ExecutionConfiguration(source_path=Path("data/master/Rel_Razão.xlsx"), rules_config_path=Path("config/business_rules.yaml"))
    report = runner.run(config)
    print("success", report.success)
    for stage in report.stage_results:
        print(stage.name, stage.success, stage.errors)
    print(report.metadata)


if __name__ == "__main__":
    main()
