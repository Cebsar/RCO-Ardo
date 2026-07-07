from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional

from src.domain.entities import DRENode
from .calculator import NodeCalculator
from .evaluator import RuleEvaluator
from .models import BusinessRule, CalculatedDRE, ExecutionMetrics, ExecutionReport, RuleResult
from .registry import RuleRegistry

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, registry: Optional[RuleRegistry] = None):
        self.registry = registry or RuleRegistry()
        self.evaluator = RuleEvaluator()
        self.calculator = NodeCalculator(self.evaluator)

    def execute(self, dre_tree: Iterable[DRENode], facts: List[Dict[str, Any]], rules: List[BusinessRule], parameters: Optional[Dict[str, Any]] = None) -> CalculatedDRE:
        start = perf_counter()
        metrics = ExecutionMetrics(start_time=datetime.now(timezone.utc))
        report = ExecutionReport(metrics=metrics)
        parameters = parameters or {}

        for rule in rules:
            self.registry.register(rule)

        results: List[RuleResult] = []
        result_map: Dict[str, RuleResult] = {}
        self._evaluate_nodes_recursive(list(dre_tree), facts, parameters, report, metrics, results, result_map)
        report.results = results
        metrics.end_time = datetime.now(timezone.utc)
        metrics.duration_seconds = perf_counter() - start
        calculated = CalculatedDRE(roots=list(dre_tree), report=report)
        logger.info("Rule engine executed in %.6f seconds for %d nodes", metrics.duration_seconds, metrics.nodes_processed)
        return calculated

    def _evaluate_nodes_recursive(
        self,
        nodes: List[DRENode],
        facts: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        report: ExecutionReport,
        metrics: ExecutionMetrics,
        results: List[RuleResult],
        result_map: Dict[str, RuleResult],
    ) -> None:
        for node in nodes:
            if node.children:
                self._evaluate_nodes_recursive(list(node.children), facts, parameters, report, metrics, results, result_map)
            result = self._evaluate_node(node, facts, parameters, result_map)
            results.append(result)
            result_map[node.code.value] = result
            metrics.rules_executed += 1
            metrics.nodes_processed += 1
            if result.errors:
                report.errors.extend(result.errors)
            if result.warnings:
                report.warnings.extend(result.warnings)

    def _evaluate_node(self, node: DRENode, facts: List[Dict[str, Any]], parameters: Dict[str, Any], result_map: Dict[str, RuleResult]) -> RuleResult:
        rule = getattr(node, "rule", None)
        if rule is None:
            value = node.amount.amount if node.amount is not None else None
            return RuleResult(node_code=node.code.value, value=value, warnings=["No rule assigned"])

        children_values = [
            result_map[child.code.value].value
            for child in node.children
            if child.code.value in result_map and result_map[child.code.value].value is not None
        ]
        return self.calculator.calculate(node, facts, {rule.id: rule}, parameters, children_values)
