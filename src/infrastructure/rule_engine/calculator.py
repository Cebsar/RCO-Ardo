from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.entities import DRENode
from .models import BusinessRule, RuleContext, RuleResult
from .evaluator import RuleEvaluator

logger = logging.getLogger(__name__)


class NodeCalculator:
    def __init__(self, evaluator: RuleEvaluator):
        self.evaluator = evaluator

    def calculate(
        self,
        node: DRENode,
        facts: List[Dict[str, Any]],
        rules: Dict[str, BusinessRule],
        parameters: Dict[str, Any],
        children_values: List[Decimal] | None = None,
    ) -> RuleResult:
        rule = getattr(node, "rule", None)
        if rule is None:
            result = RuleResult(node_code=node.code.value)
            result.warnings.append("No rule assigned to node")
            return result
        params = dict(parameters)
        params["children"] = children_values or []
        context = RuleContext(dre_node=node, facts=facts, parameters=params, children_values=children_values or [])
        result = self.evaluator.evaluate(rule, context)
        result.rule_id = rule.id
        result.rule_description = rule.description
        return result
