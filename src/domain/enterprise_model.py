"""Enterprise financial domain model.

Defines entities, value objects, enumerations, and aggregate roots for the
financial domain. No persistence or infrastructure code is included.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict


# Enumerations
class EntryType(str):
    DEBIT = "debit"
    CREDIT = "credit"


class AccountType(str):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class DRELevel(int):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class PostingType(str):
    AUTOMATIC = "automatic"
    MANUAL = "manual"


# Value Objects
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "amount", Decimal(self.amount))
        except (InvalidOperation, TypeError):
            raise ValueError("Invalid monetary amount")


@dataclass(frozen=True)
class Currency:
    code: str


@dataclass(frozen=True)
class AccountCode:
    value: str


@dataclass(frozen=True)
class CompanyCode:
    value: str


@dataclass(frozen=True)
class DivisionCode:
    value: str


@dataclass(frozen=True)
class CostCenterCode:
    value: str


@dataclass(frozen=True)
class DocumentNumber:
    value: str


@dataclass(frozen=True)
class JournalNumber:
    value: str


# Entities and Aggregate Roots
@dataclass
class Company:
    code: CompanyCode
    name: str
    divisions: List["Division"] = field(default_factory=list)
    cost_centers: List["CostCenter"] = field(default_factory=list)


@dataclass
class Division:
    code: DivisionCode
    name: str
    company: Company
    cost_centers: List["CostCenter"] = field(default_factory=list)


@dataclass
class CostCenter:
    code: CostCenterCode
    name: str
    division: Optional[Division] = None


@dataclass
class Account:
    code: AccountCode
    name: str
    type: AccountType
    parent: Optional["Account"] = None
    children: List["Account"] = field(default_factory=list)


@dataclass
class AccountingPeriod:
    code: str
    start: date
    end: date


@dataclass
class AccountingEntry:
    id: str
    account: Account
    amount: Money
    date: date
    entry_type: EntryType
    cost_center: Optional[CostCenter] = None
    document_number: Optional[DocumentNumber] = None
    journal_number: Optional[JournalNumber] = None
    posting_type: Optional[PostingType] = None
    description: Optional[str] = None


@dataclass
class Journal:
    number: JournalNumber
    period: AccountingPeriod
    entries: List[AccountingEntry] = field(default_factory=list)


@dataclass
class Ledger:
    company: Company
    accounts: List[Account] = field(default_factory=list)
    journals: List[Journal] = field(default_factory=list)

    # Aggregate root behavior not implemented (no methods)


@dataclass
class DRENode:
    code: AccountCode
    name: str
    level: DRELevel
    amount: Optional[Money] = None
    children: Tuple["DRENode", ...] = field(default_factory=tuple)


@dataclass
class FinancialStatement:
    company: Company
    period: AccountingPeriod
    dre_root: Optional[DRENode] = None
    generated_on: Optional[date] = None


# Relationships (expressed via type hints above):
# - Company -> Division (1:N)
# - Company -> CostCenter (1:N)
# - Division -> CostCenter (1:N)
# - Ledger aggregates Accounts and Journals for a Company
# - Journal contains multiple AccountingEntry
# - Account can have hierarchical parent/children
# - FinancialStatement references a DRENode tree
