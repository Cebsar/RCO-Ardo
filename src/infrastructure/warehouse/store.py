from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from src.infrastructure.warehouse.models import DimensionRow, FactRow

logger = logging.getLogger(__name__)


@dataclass
class OperationalDataStore:
    companies: Dict[str, DimensionRow] = field(default_factory=dict)
    divisions: Dict[str, DimensionRow] = field(default_factory=dict)
    costcenters: Dict[str, DimensionRow] = field(default_factory=dict)
    accounts: Dict[str, DimensionRow] = field(default_factory=dict)
    periods: Dict[str, DimensionRow] = field(default_factory=dict)
    facts: Dict[str, FactRow] = field(default_factory=dict)
    next_key: int = 1

    def _get_next_key(self) -> int:
        current = self.next_key
        self.next_key += 1
        return current

    def ensure_dimension(self, dimension: str, natural_key: str, attributes: Dict[str, object]) -> DimensionRow:
        store = getattr(self, dimension)
        row = store.get(natural_key)
        if row is not None:
            return row
        surrogate_key = self._get_next_key()
        row = DimensionRow(surrogate_key=surrogate_key, natural_key=natural_key, attributes=attributes)
        store[natural_key] = row
        logger.debug("Added %s dimension row %s -> %s", dimension, natural_key, surrogate_key)
        return row

    def add_fact(self, fact: FactRow) -> FactRow:
        existing = self.facts.get(fact.entry_id)
        if existing is not None:
            logger.debug("Fact already exists for entry_id %s, preserving reference", fact.entry_id)
            return existing
        self.facts[fact.entry_id] = fact
        logger.debug("Added fact row %s", fact.surrogate_key)
        return fact

    def get_dimension_by_key(self, dimension: str, natural_key: str) -> Optional[DimensionRow]:
        return getattr(self, dimension).get(natural_key)
