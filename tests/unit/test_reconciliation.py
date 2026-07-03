from decimal import Decimal

from src.domain.entities import DRENode
from src.domain.enums import DRELevel
from src.domain.value_objects import AccountCode, Money
from src.infrastructure.reconciliation.engine import ReconciliationEngine
from src.infrastructure.reconciliation.models import ToleranceRule


def make_node(code: str, name: str, amount: Decimal, level: DRELevel) -> DRENode:
    return DRENode(code=AccountCode(code), name=name, level=level, amount=Money(amount), children=())


def test_reconciliation_detects_value_differences():
    expected = make_node("N1", "Revenue", Decimal("100"), DRELevel.LEVEL_1)
    actual = make_node("N1", "Revenue", Decimal("110"), DRELevel.LEVEL_1)

    engine = ReconciliationEngine(tolerance=ToleranceRule(absolute=Decimal("0"), relative=Decimal("0")))
    audit = engine.reconcile([expected], [actual])

    assert audit.reconciliation.mismatches == 1
    item = audit.reconciliation.differences[0]
    assert item.difference == Decimal("10")
    assert not item.tolerance.evaluate(item.expected, item.actual)


def test_reconciliation_supports_tolerance():
    expected = make_node("N2", "Expenses", Decimal("200"), DRELevel.LEVEL_1)
    actual = make_node("N2", "Expenses", Decimal("205"), DRELevel.LEVEL_1)
    tol = ToleranceRule(absolute=Decimal("10"), relative=Decimal("0"))

    engine = ReconciliationEngine(tolerance=tol)
    audit = engine.reconcile([expected], [actual])

    assert audit.reconciliation.out_of_tolerance == 0
    assert audit.reconciliation.mismatches == 1


def test_reconciliation_reports_missing_nodes():
    expected = make_node("N3", "Cost", Decimal("50"), DRELevel.LEVEL_1)
    engine = ReconciliationEngine()
    audit = engine.reconcile([expected], [])

    assert audit.reconciliation.missing_in_actual == 1
    assert audit.reconciliation.mismatches == 1
