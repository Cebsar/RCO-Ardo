from __future__ import annotations

from typing import Dict, Optional

from .models import BusinessRule


class RuleRegistry:
    def __init__(self, rules: Optional[Dict[str, BusinessRule]] = None):
        self._rules = rules or {}

    def register(self, rule: BusinessRule) -> None:
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> Optional[BusinessRule]:
        return self._rules.get(rule_id)

    def all(self) -> Dict[str, BusinessRule]:
        return dict(self._rules)
