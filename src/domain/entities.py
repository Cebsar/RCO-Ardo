from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Optional, Tuple

from .value_objects import (
    AccountCode,
    CostCenterCode,
    CompanyCode,
    DivisionCode,
    Money,
    PeriodCode,
)
from .enums import AccountType, EntryType, DRELevel


@dataclass(frozen=True)
class Company:
    code: CompanyCode
    name: str


@dataclass(frozen=True)
class Division:
    code: DivisionCode
    name: str
    company: Company


@dataclass(frozen=True)
class CostCenter:
    code: CostCenterCode
    name: str
    division: Optional[Division] = None


@dataclass(frozen=True)
class Period:
    code: PeriodCode
    start: date
    end: date


@dataclass(frozen=True)
class Account:
    code: AccountCode
    name: str
    type: AccountType


@dataclass(frozen=True)
class AccountingEntry:
    id: str
    account: Account
    amount: Money
    date: date
    entry_type: EntryType
    cost_center: Optional[CostCenter] = None
    description: Optional[str] = None
    company: Optional[Company] = None


@dataclass(frozen=True)
class DRENode:
    code: AccountCode
    name: str
    level: DRELevel
    amount: Optional[Money] = None
    percentage: Optional[Decimal] = None
    children: Tuple["DRENode", ...] = field(default_factory=tuple)
    rule: Optional[Any] = None

    def with_children(self, *children: "DRENode") -> "DRENode":
        """Return a new DRENode with additional children.

        This keeps the dataclass frozen while allowing construction of trees.
        """
        return DRENode(
            code=self.code,
            name=self.name,
            level=self.level,
            amount=self.amount,
            percentage=self.percentage,
            children=tuple(children),
            rule=self.rule,
        )

    def with_rule(self, rule: Any) -> "DRENode":
        """Return a new DRENode with the same data and an attached business rule."""
        return DRENode(
            code=self.code,
            name=self.name,
            level=self.level,
            amount=self.amount,
            percentage=self.percentage,
            children=self.children,
            rule=rule,
        )
