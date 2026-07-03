from datetime import date
from decimal import Decimal

from src.domain.entities import AccountingEntry, Account, CostCenter, Company, Division
from src.domain.enums import AccountType, EntryType
from src.domain.value_objects import AccountCode, CostCenterCode
from src.infrastructure.warehouse.builder import WarehouseBuilder
from src.infrastructure.warehouse.store import OperationalDataStore


def make_entry(entry_id: str, account_code: str, account_name: str, amount: Decimal, entry_type: EntryType, accounting_date: date, costcenter: CostCenter | None = None) -> AccountingEntry:
    account = Account(code=AccountCode(account_code), name=account_name, type=AccountType.EXPENSE)
    return AccountingEntry(id=entry_id, account=account, amount=amount, date=accounting_date, entry_type=entry_type, cost_center=costcenter, description="Test")


def test_warehouse_builder_creates_dimensions_and_fact():
    store = OperationalDataStore()
    builder = WarehouseBuilder(store)

    company = Company(code=AccountCode("1000"), name="ACME")
    division = Division(code=CostCenterCode("D1"), name="Div1", company=company)
    costcenter = CostCenter(code=CostCenterCode("CC1"), name="Cost Center 1", division=division)
    entry = make_entry("e1", "1000", "ACME", Decimal("100.00"), EntryType.DEBIT, date(2024, 1, 31), costcenter)

    report = builder.build([entry])
    assert report.fact_rows == 1
    assert report.company_rows == 1
    assert report.division_rows == 1
    assert report.costcenter_rows == 1
    assert report.account_rows == 1
    assert report.period_rows == 1


def test_incremental_load_preserves_surrogate_keys():
    store = OperationalDataStore()
    builder = WarehouseBuilder(store)

    entry1 = make_entry("e1", "1000", "ACME", Decimal("100.00"), EntryType.DEBIT, date(2024, 1, 31))
    entry2 = make_entry("e2", "1000", "ACME", Decimal("50.00"), EntryType.CREDIT, date(2024, 1, 31))

    first_report = builder.build([entry1])
    first_company_key = store.companies["1000"].surrogate_key
    second_report = builder.build([entry2])

    assert store.companies["1000"].surrogate_key == first_company_key
    assert first_report.new_rows == 1
    assert second_report.new_rows == 1
    assert second_report.updated_rows == 0
    assert store.fact_rows == 2


def test_fact_preserves_original_entry_reference():
    store = OperationalDataStore()
    builder = WarehouseBuilder(store)
    entry = make_entry("e10", "2000", "Sales", Decimal("200.00"), EntryType.CREDIT, date(2024, 3, 15))
    builder.build([entry])
    fact = store.facts[entry.id]
    assert fact.entry_id == entry.id
    assert fact.source_row["entry_id"] == entry.id
    assert fact.source_entry is entry
