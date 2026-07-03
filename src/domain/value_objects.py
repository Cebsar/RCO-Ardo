from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "amount", Decimal(self.amount))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Invalid monetary amount") from exc
        if not isinstance(self.currency, str) or not self.currency:
            raise ValueError("currency must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - simple formatting
        return f"{self.currency} {self.amount}"


@dataclass(frozen=True)
class AccountCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("AccountCode must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True)
class CostCenterCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("CostCenterCode must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True)
class CompanyCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("CompanyCode must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True)
class DivisionCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("DivisionCode must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True)
class PeriodCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("PeriodCode must be a non-empty string")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
