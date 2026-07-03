from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterator, List

from src.domain.entities import DRENode
from src.infrastructure.rule_engine.models import BusinessRule
from .models import BusinessRuleDefinition

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class BusinessRuleProvider:
    def __init__(self, rules_config_path: Path) -> None:
        self.rules_config_path = rules_config_path
        self._rules: Dict[str, BusinessRuleDefinition] = {}
        self.load_rules()

    def load_rules(self) -> None:
        raw_text = self.rules_config_path.read_text(encoding="utf-8")
        raw_data = self._parse_raw_text(raw_text)
        self._rules = {
            rule_data["id"]: BusinessRuleDefinition(
                id=rule_data["id"],
                node_code=rule_data["node_code"],
                description=rule_data.get("description", ""),
                filters=rule_data.get("filters", {}),
                expression=rule_data.get("expression", "0"),
                derived=rule_data.get("derived", False),
                calculated=rule_data.get("calculated", False),
                children=rule_data.get("children"),
            )
            for rule_data in raw_data.get("rules", [])
        }

    def _parse_raw_text(self, raw_text: str) -> dict:
        if self.rules_config_path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to load YAML business rule configs")
            return yaml.safe_load(raw_text) or {}
        return json.loads(raw_text)

    def get_rule_by_node(self, node_code: str) -> BusinessRuleDefinition | None:
        for rule in self._rules.values():
            if rule.node_code == node_code:
                return rule
        return None

    def get_all_rules(self) -> List[BusinessRuleDefinition]:
        return list(self._rules.values())

    def get_business_rules(self) -> List[BusinessRule]:
        return [definition.to_business_rule() for definition in self.get_all_rules()]

    def assign_rules(self, dre_tree: List[DRENode]) -> List[DRENode]:
        rule_map = {rule.node_code: rule for rule in self.get_business_rules()}

        def attach(node: DRENode) -> DRENode:
            children = tuple(attach(child) for child in node.children)
            rule = rule_map.get(node.code.value)
            return DRENode(
                code=node.code,
                name=node.name,
                level=node.level,
                amount=node.amount,
                percentage=node.percentage,
                children=children,
                rule=rule,
            )

        return [attach(root) for root in dre_tree]

    def get_child_nodes(self, node_code: str) -> List[str]:
        rule = self.get_rule_by_node(node_code)
        return rule.children or []

    def __iter__(self) -> Iterator[BusinessRuleDefinition]:
        return iter(self._rules.values())
