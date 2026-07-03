from datetime import date
from decimal import Decimal

from src.domain.entities import DRENode
from src.domain.enums import DRELevel, EntryType
from src.domain.value_objects import AccountCode
from src.infrastructure.rule_engine.engine import RuleEngine
from src.infrastructure.rule_engine.models import BusinessRule


def test_rule_engine_evaluates_node_expression():
    rule = BusinessRule(id="r1", expression="sum([Decimal(f['amount']) for f in facts])", description="Sum amounts", filters={"account_code": "1000"}, calculated=True)
    node = DRENode(code=AccountCode("N1"), name="Revenue", level=DRELevel.LEVEL_1, amount=None, children=(), rule=rule)

    facts = [{"account_code": "1000", "amount": "150.00"}, {"account_code": "2000", "amount": "50.00"}]
    engine = RuleEngine()
    calculated = engine.execute([node], facts, [rule])

    assert len(calculated.report.results) == 1
    result = calculated.report.results[0]
    assert result.value == Decimal("150.00")
    assert result.matched_fact_count == 1


def test_rule_engine_reports_missing_rule():
    node = DRENode(code=AccountCode("N2"), name="Expenses", level=DRELevel.LEVEL_1, amount=None, children=())
    engine = RuleEngine()
    calculated = engine.execute([node], [], [])

    assert len(calculated.report.results) == 1
    result = calculated.report.results[0]
    assert "No rule assigned" in result.warnings


def test_rule_engine_handles_invalid_expression():
    rule = BusinessRule(id="r2", expression="sum(facts) / 0", calculated=True)
    node = DRENode(code=AccountCode("N3"), name="Bad Rule", level=DRELevel.LEVEL_1, amount=None, children=(), rule=rule)
    engine = RuleEngine()
    calculated = engine.execute([node], [{"amount": "100"}], [rule])

    result = calculated.report.results[0]
    assert result.errors
