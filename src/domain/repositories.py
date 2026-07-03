from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .entities import Company, AccountingEntry, DRENode
from .value_objects import CompanyCode, PeriodCode


class CompanyRepository(ABC):
    @abstractmethod
    def get_by_code(self, code: CompanyCode) -> Optional[Company]:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> Iterable[Company]:
        raise NotImplementedError

    @abstractmethod
    def save(self, company: Company) -> None:
        raise NotImplementedError


class AccountingRepository(ABC):
    @abstractmethod
    def list_entries(self, period: Optional[PeriodCode] = None) -> Iterable[AccountingEntry]:
        raise NotImplementedError

    @abstractmethod
    def save_entry(self, entry: AccountingEntry) -> None:
        raise NotImplementedError


class DRERepository(ABC):
    @abstractmethod
    def get_dre_for_period(self, period: PeriodCode) -> Optional[DRENode]:
        raise NotImplementedError

    @abstractmethod
    def save_dre(self, period: PeriodCode, dre_root: DRENode) -> None:
        raise NotImplementedError
