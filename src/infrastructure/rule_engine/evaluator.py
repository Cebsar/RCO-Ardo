from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from .models import BusinessRule, RuleContext, RuleResult

logger = logging.getLogger(__name__)


class RuleEvaluator:
    def evaluate(self, rule: BusinessRule, context: RuleContext) -> RuleResult:
        result = RuleResult(node_code=context.dre_node.code.value)
        try:
            matched_facts = self._filter_facts(context.facts, rule.filters)
            result.matched_fact_count = len(matched_facts)
            if rule.derived or rule.calculated:
                value = self._evaluate_expression(rule.expression, matched_facts, context.parameters)
                result.value = value
            return result
        except Exception as exc:
            logger.exception("Rule evaluation failed for rule %s", rule.id)
            result.errors.append(str(exc))
            return result

    def _filter_facts(self, facts: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not filters:
            return facts
        filtered: List[Dict[str, Any]] = []
        for fact in facts:
            if all(self._matches_filter(fact, key, value) for key, value in filters.items()):
                filtered.append(fact)
        return filtered

    def _matches_filter(self, fact: Dict[str, Any], key: str, value: Any) -> bool:
        if key.endswith("_prefix"):
            field = key[: -len("_prefix")]
            return isinstance(fact.get(field), str) and fact[field].startswith(value)
        return fact.get(key) == value

    def _evaluate_expression(self, expression: str, facts: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Decimal:
        safe_globals = {"__builtins__": {}}
        safe_locals = {
            "facts": facts,
            "sum": sum,
            "len": len,
            "Decimal": Decimal,
            "params": parameters,
            "children": parameters.get("children", []),
        }
        try:
            raw_value = eval(expression, safe_globals, safe_locals)
            if isinstance(raw_value, Decimal):
                return raw_value
            if isinstance(raw_value, (int, float, str)):
                return Decimal(str(raw_value))
            raise ValueError("Expression did not produce numeric result")
        except InvalidOperation as exc:
            raise ValueError("Invalid numeric expression result") from exc
