from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4
from openpyxl.utils.datetime import from_excel

from src.domain.entities import AccountingEntry, Account, Company, CostCenter, Division
from src.domain.value_objects import (
    AccountCode,
    CompanyCode,
    CostCenterCode,
    DivisionCode,
    Money,
)
from src.domain.enums import EntryType, AccountType
from src.infrastructure.header_mapper.mapper import HeaderMapping
from .models import NormalizationIssue, NormalizationReport

logger = logging.getLogger(__name__)


class MappingResolver:
    """Resolve canonical fields from a raw row using HeaderMapping."""

    def __init__(self, mapping: HeaderMapping):
        self.mapping = mapping

    def resolve(self, row: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        # For each original header -> canonical, pull value
        for orig_header, canonical in self.mapping.mapping.items():
            if canonical is None:
                continue
            # if orig_header not in row, try normalized keys? assume exact match
            if orig_header in row:
                result[canonical] = row.get(orig_header)
            else:
                # try stripped string match
                for k in row.keys():
                    if k is not None and str(k).strip() == str(orig_header).strip():
                        result[canonical] = row.get(k)
                        break
                # else leave absent
        # also allow canonical_to_headers multiple headers: ensure fields present even if mapped under different original header
        for canonical, headers in self.mapping.canonical_to_headers.items():
            if canonical in result:
                continue
            for h in headers:
                if h in row:
                    result[canonical] = row.get(h)
                    break
        return result


class RowNormalizer:
    """Normalize a single row (dict) into canonical values and validate conversions."""

    DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

    def __init__(self, mapping: HeaderMapping):
        self.mapping = mapping
        self.resolver = MappingResolver(mapping)

    def _parse_date(self, value: Any) -> date:
        if value is None:
            raise ValueError("date is None")
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, (int, float)):
            try:
                return from_excel(value).date()
            except Exception:
                pass
        if isinstance(value, str):
            s = value.strip()
            # try iso
            try:
                return date.fromisoformat(s)
            except Exception:
                pass
            for fmt in self.DATE_FORMATS:
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    continue
        raise ValueError("Unparseable date")

    def _parse_decimal(self, value: Any) -> Decimal:
        if value is None:
            raise ValueError("amount is None")
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            try:
                return Decimal(str(value))
            except InvalidOperation as exc:
                raise ValueError("Invalid numeric value") from exc
        if isinstance(value, str):
            s = value.strip().replace("\u00A0", "").replace(" ", "")
            # replace comma decimal separators
            if s.count(",") > 0 and s.count(".") == 0:
                s = s.replace(",", ".")
            try:
                return Decimal(s)
            except InvalidOperation as exc:
                raise ValueError("Invalid numeric string") from exc
        raise ValueError("Unsupported numeric type")

    def _is_blank(self, value: Any) -> bool:
        return value is None or (isinstance(value, str) and value.strip() == "")

    def _text_or_none(self, value: Any) -> Optional[str]:
        if self._is_blank(value):
            return None
        return str(value).strip()

    def _text_or_empty(self, value: Any) -> str:
        text = self._text_or_none(value)
        return text or ""

    def normalize(self, row_number: Optional[int], row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[NormalizationIssue]]:
        """Return normalized canonical dict or an error issue."""
        try:
            canonical = self.resolver.resolve(row)
            # detect empty row: no significant mapped fields
            significant = [v for k, v in canonical.items() if not self._is_blank(v)]
            if not significant:
                return None, NormalizationIssue(code="EMPTY_ROW", severity="info", message="Empty row skipped", row_number=row_number, row=row)

            # required: AccountCode, AccountingDate, and amount (Debit/Credit/Balance)
            account_code = canonical.get("AccountCode")
            acc_date_raw = canonical.get("AccountingDate")
            debit_raw = canonical.get("Debit")
            credit_raw = canonical.get("Credit")
            balance_raw = canonical.get("Balance")

            if not account_code or str(account_code).strip() == "":
                raise ValueError("AccountCode missing")
            if not acc_date_raw:
                raise ValueError("AccountingDate missing")

            # parse date
            acc_date = self._parse_date(acc_date_raw)

            # parse amount: prefer signed Balance/Valor, then Debit/Credit fallbacks.
            amount = None
            entry_type = None
            if balance_raw not in (None, ""):
                amt = self._parse_decimal(balance_raw)
                amount = amt
                entry_type = EntryType.DEBIT if amt >= 0 else EntryType.CREDIT
            elif debit_raw not in (None, ""):
                amt = self._parse_decimal(debit_raw)
                amount = amt
                entry_type = EntryType.DEBIT
            elif credit_raw not in (None, ""):
                amt = self._parse_decimal(credit_raw)
                amount = amt
                entry_type = EntryType.CREDIT
            else:
                raise ValueError("No monetary amount present")

            normalized = {
                "AccountCode": str(account_code).strip(),
                "AccountDescription": self._text_or_empty(canonical.get("AccountDescription")),
                "AccountingDate": acc_date,
                "Amount": amount,
                "EntryType": entry_type,
                "Company": self._text_or_none(canonical.get("Company")),
                "Division": self._text_or_none(canonical.get("Division")),
                "CostCenter": self._text_or_none(canonical.get("CostCenter")),
                "Description": self._text_or_none(canonical.get("History")) or self._text_or_none(canonical.get("DocumentNumber")),
            }

            return normalized, None
        except Exception as exc:
            issue = NormalizationIssue(code="NORMALIZATION_ERROR", severity="error", message=str(exc), row_number=row_number, row=row)
            return None, issue


class EntryFactory:
    """Create domain AccountingEntry from normalized canonical dict."""

    def __init__(self, default_account_type: AccountType = AccountType.EXPENSE):
        self.default_account_type = default_account_type

    def create(self, normalized: Dict[str, Any]) -> AccountingEntry:
        # id generation
        entry_id = uuid4().hex
        account_code = AccountCode(normalized["AccountCode"])
        account_name = normalized.get("AccountDescription") or ""
        account = Account(code=account_code, name=account_name, type=self.default_account_type)
        amount = Money(normalized["Amount"]) if not isinstance(normalized["Amount"], Money) else normalized["Amount"]
        acc_date = normalized["AccountingDate"]
        entry_type = normalized["EntryType"]
        company = None
        if normalized.get("Company"):
            company_text = str(normalized["Company"]).strip()
            company_code, company_name = self._split_code_name(company_text)
            company = Company(code=CompanyCode(company_code), name=company_name or company_code)

        division = None
        if normalized.get("Division"):
            division_text = str(normalized["Division"]).strip()
            division_code, division_name = self._split_code_name(division_text)
            division_company = company or Company(code=CompanyCode("UNKNOWN"), name="UNKNOWN")
            division = Division(code=DivisionCode(division_code), name=division_name or division_code, company=division_company)

        cost_center = None
        if normalized.get("CostCenter"):
            try:
                cost_center_text = str(normalized.get("CostCenter")).strip()
                cost_center_code, cost_center_name = self._split_code_name(cost_center_text)
                cost_center = CostCenter(
                    code=CostCenterCode(cost_center_code),
                    name=cost_center_name or cost_center_code,
                    division=division,
                )
            except Exception:
                cost_center = None
        description = normalized.get("Description")

        return AccountingEntry(
            id=entry_id,
            account=account,
            amount=amount,
            date=acc_date,
            entry_type=entry_type,
            cost_center=cost_center,
            description=description,
            company=company,
        )

    def _split_code_name(self, value: str) -> tuple[str, str]:
        text = value.strip()
        if " - " not in text:
            return text, text
        code, name = text.split(" - ", 1)
        return code.strip() or text, name.strip() or text


class AccountingNormalizer:
    """Top-level normalizer to process rows into AccountingEntry instances."""

    def __init__(self, mapping: HeaderMapping, default_account_type: AccountType = AccountType.EXPENSE):
        self.mapping = mapping
        self.row_normalizer = RowNormalizer(mapping)
        self.factory = EntryFactory(default_account_type=default_account_type)

    def normalize(self, rows: Iterable[Any], sheet_name: Optional[str] = None) -> Tuple[List[AccountingEntry], NormalizationReport]:
        """rows: iterable of either (row_number, row_dict) tuples or row_dicts that may include a row key like 'row_number' or '__row__'."""
        start = perf_counter()
        entries: List[AccountingEntry] = []
        report = NormalizationReport()

        for item in rows:
            # determine row_number and row dict
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], dict):
                row_number, row = item
            elif isinstance(item, dict):
                row = item
                row_number = None
                for key in ("__row__", "row_number", "_row", "_row_index"):
                    if key in row:
                        try:
                            row_number = int(row.get(key))
                        except Exception:
                            row_number = None
                        break
            else:
                # unsupported row format
                row_number = None
                row = {}

            normalized, issue = self.row_normalizer.normalize(row_number, row)
            if issue:
                if issue.code == "EMPTY_ROW":
                    report.skipped_empty += 1
                    report.add(issue)
                    continue
                report.add(issue)
                logger.warning("Row %s invalid: %s", row_number, issue.message)
                continue
            # create entry
            try:
                entry = self.factory.create(normalized)
                entries.append(entry)
                report.normalized_count += 1
            except Exception as exc:
                issue = NormalizationIssue(code="ENTRY_FACTORY_ERROR", severity="error", message=str(exc), row_number=row_number, row=row)
                report.add(issue)
                logger.exception("Failed to create AccountingEntry for row %s", row_number)

        report.execution_time_seconds = perf_counter() - start
        logger.info("Normalization completed in %.6f seconds: %d entries, %d invalid, %d skipped", report.execution_time_seconds, report.normalized_count, report.invalid_count, report.skipped_empty)
        return entries, report
