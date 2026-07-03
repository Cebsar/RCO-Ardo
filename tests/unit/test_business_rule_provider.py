from pathlib import Path
from decimal import Decimal

from src.domain.entities import DRENode
from src.domain.enums import DRELevel
from src.domain.value_objects import AccountCode
from src.infrastructure.business_rules.provider import BusinessRuleProvider
from src.infrastructure.business_rules.report import BusinessRuleReport
from src.infrastructure.rule_engine.engine import RuleEngine


def test_business_rule_provider_loads_yaml_and_assigns_rules(tmp_path: Path):
    config_path = tmp_path / "business_rules.yaml"
    config_path.write_text(
        """rules:
  - id: "REVENUE"
    node_code: "REVENUE"
    description: "Revenue from sales"
    filters:
      account_code_prefix: "4"
    expression: "sum([Decimal(f['amount']) for f in facts])"
    calculated: true

  - id: "EXPENSES"
    node_code: "EXPENSES"
    description: "Operating expenses"
    filters:
      account_code_prefix: "6"
    expression: "sum([Decimal(f['amount']) for f in facts])"
    calculated: true
""",
        encoding="utf-8",
    )

    provider = BusinessRuleProvider(config_path)
    assert provider.get_rule_by_node("REVENUE") is not None
    assert provider.get_rule_by_node("EXPENSES") is not None
    assert len(provider.get_business_rules()) == 2


def test_business_rule_provider_assigns_rules_to_dre_nodes(tmp_path: Path):
    config_path = tmp_path / "business_rules.yaml"
    config_path.write_text(
        """rules:
  - id: "REVENUE"
    node_code: "REVENUE"
    expression: "sum([Decimal(f['amount']) for f in facts])"
    calculated: true

  - id: "COGS"
    node_code: "COGS"
    expression: "sum([Decimal(f['amount']) for f in facts])"
    calculated: true

  - id: "GROSS_MARGIN"
    node_code: "GROSS_MARGIN"
    expression: "children[0] - children[1]"
    calculated: true
    children:
      - "REVENUE"
      - "COGS"
""",
        encoding="utf-8",
    )

    provider = BusinessRuleProvider(config_path)
    revenue = DRENode(code=AccountCode("REVENUE"), name="Revenue", level=DRELevel.LEVEL_1, amount=None, children=())
    cogs = DRENode(code=AccountCode("COGS"), name="COGS", level=DRELevel.LEVEL_1, amount=None, children=())
    gross_margin = DRENode(code=AccountCode("GROSS_MARGIN"), name="Gross Margin", level=DRELevel.LEVEL_1, amount=None, children=(revenue, cogs))

    assigned = provider.assign_rules([gross_margin])
    assert assigned[0].rule is not None
    assert assigned[0].children[0].rule is not None
    assert assigned[0].children[1].rule is not None


def test_business_rule_report_from_execution_report(tmp_path: Path):
    config_path = tmp_path / "business_rules.yaml"
    config_path.write_text(
        """rules:
  - id: "REVENUE"
    node_code: "REVENUE"
    expression: "sum([Decimal(f['amount']) for f in facts])"
    calculated: true
""",
        encoding="utf-8",
    )

    provider = BusinessRuleProvider(config_path)
    revenue = DRENode(code=AccountCode("REVENUE"), name="Revenue", level=DRELevel.LEVEL_1, amount=None, children=())
    assigned = provider.assign_rules([revenue])
    engine = RuleEngine()
    facts = [{"account_code": "4000", "amount": "100.00"}]

    calculated = engine.execute(assigned, facts, provider.get_business_rules())
    report = BusinessRuleReport.from_execution_report(calculated.report, {"REVENUE": "Revenue"})

    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.node_code == "REVENUE"
    assert entry.node_description == "Revenue"
    assert entry.computed_value == Decimal("100.00")
    assert entry.matched_fact_count == 1
    assert not entry.errors
