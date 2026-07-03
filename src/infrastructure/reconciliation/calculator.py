from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, List, Optional

from src.domain.entities import DRENode
from .models import DifferenceItem, ToleranceRule

logger = logging.getLogger(__name__)


class DifferenceCalculator:
    def compare_node(self, expected: Optional[DRENode], actual: Optional[DRENode], tolerance: ToleranceRule, order_match: bool = True, level_match: bool = True) -> DifferenceItem:
        expected_val = expected.amount.amount if expected and expected.amount is not None else None
        actual_val = actual.amount.amount if actual and actual.amount is not None else None
        difference = None
        pct_diff = None

        if expected_val is not None and actual_val is not None:
            difference = actual_val - expected_val
            pct_diff = (difference / expected_val * Decimal("100")) if expected_val != Decimal("0") else None

        return DifferenceItem(
            node_code=expected.code.value if expected else actual.code.value if actual else "",
            node_name=expected.name if expected else actual.name if actual else "",
            expected=expected_val,
            actual=actual_val,
            difference=difference,
            tolerance=tolerance,
            percentage_difference=pct_diff,
            exists_in_expected=expected is not None,
            exists_in_actual=actual is not None,
            order_match=order_match,
            level_match=level_match,
        )

    def compare_hierarchy(self, expected_nodes: List[DRENode], actual_nodes: List[DRENode], tolerance: ToleranceRule) -> List[DifferenceItem]:
        expected_map = {node.code.value: node for node in expected_nodes}
        actual_map = {node.code.value: node for node in actual_nodes}
        differences: List[DifferenceItem] = []

        keys = list(dict.fromkeys([*expected_map.keys(), *actual_map.keys()]))
        for key in keys:
            expected = expected_map.get(key)
            actual = actual_map.get(key)
            differences.append(self.compare_node(expected, actual, tolerance))
        return differences
