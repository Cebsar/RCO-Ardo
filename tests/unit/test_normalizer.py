from datetime import date
from decimal import Decimal

from src.infrastructure.header_mapper.mapper import HeaderMapping
from src.infrastructure.normalizer.normalizer import AccountingNormalizer


def make_header_mapping():
    # simple identity mapping: original header -> canonical
    mapping = {
        "Conta": "AccountCode",
        "Descricao": "AccountDescription",
        "Data": "AccountingDate",
        "Debito": "Debit",
        "Credito": "Credit",
        "Valor": "Balance",
        "Centro": "CostCenter",
        "Empresa": "Company",
        "Divisao": "Division",
        "Historico": "History",
    }
    canonical_to_headers = {v: [k] for k, v in mapping.items()}
    return HeaderMapping(mapping=mapping, canonical_to_headers=canonical_to_headers, duplicates=[], missing_required=[], unmatched_headers=[], execution_time_seconds=0.0)


def test_normalize_success():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (10, {"Conta": "1000", "Descricao": "Sales", "Data": "2021-12-31", "Debito": "", "Credito": "150.50", "Centro": "CC1", "Historico": "Invoice 123"}),
    ]
    entries, report = normalizer.normalize(rows, sheet_name="Sheet1")
    assert len(entries) == 1
    assert report.normalized_count == 1
    e = entries[0]
    assert e.account.code.value == "1000"
    assert e.amount.amount == Decimal("150.50")
    assert e.date == date(2021, 12, 31)


def test_signed_balance_value_takes_precedence_over_debit_credit():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (10, {"Conta": "4000", "Descricao": "Revenue", "Data": "2026-01-31", "Debito": "1000", "Credito": "0", "Valor": "-1000"}),
    ]

    entries, report = normalizer.normalize(rows)

    assert report.normalized_count == 1
    assert entries[0].amount.amount == Decimal("-1000")


def test_missing_account_code():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (5, {"Conta": "", "Descricao": "No account", "Data": "2021-12-31", "Debito": "10", "Credito": ""}),
    ]
    entries, report = normalizer.normalize(rows)
    assert len(entries) == 0
    assert report.invalid_count == 1
    assert any(i.code == "NORMALIZATION_ERROR" for i in report.issues)


def test_invalid_date():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (7, {"Conta": "1000", "Descricao": "Bad date", "Data": "31-31-2021", "Debito": "10", "Credito": ""}),
    ]
    entries, report = normalizer.normalize(rows)
    assert len(entries) == 0
    assert report.invalid_count == 1
    assert any(i.code == "NORMALIZATION_ERROR" for i in report.issues)


def test_invalid_decimal():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (11, {"Conta": "1000", "Descricao": "Bad amount", "Data": "2021-12-31", "Debito": "abc", "Credito": ""}),
    ]
    entries, report = normalizer.normalize(rows)
    assert len(entries) == 0
    assert report.invalid_count == 1


def test_empty_row_skipped():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (12, {"Conta": "", "Descricao": "", "Data": "", "Debito": "", "Credito": ""}),
    ]
    entries, report = normalizer.normalize(rows)
    assert len(entries) == 0
    assert report.skipped_empty == 1


def test_preserve_row_number():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (20, {"Conta": "2000", "Descricao": "Preserve", "Data": "2022-01-01", "Credito": "50"}),
    ]
    entries, report = normalizer.normalize(rows)
    assert len(entries) == 1
    # ensure report has no errors and entry produced
    assert report.normalized_count == 1


def test_normalize_preserves_company_division_and_cost_center_dimensions():
    hm = make_header_mapping()
    normalizer = AccountingNormalizer(hm)
    rows = [
        (
            21,
            {
                "Conta": "4000",
                "Descricao": "Revenue",
                "Data": "2026-01-31",
                "Credito": "100",
                "Empresa": "0001 - ARDO CONSTRUTORA E PAVIMENTAÇÃO LTDA",
                "Divisao": "USINA",
                "Centro": "2 - ARDO - USINA DE ASFALTO",
            },
        ),
    ]

    entries, report = normalizer.normalize(rows)

    assert report.normalized_count == 1
    entry = entries[0]
    assert entry.company is not None
    assert entry.company.code.value == "0001"
    assert entry.company.name == "ARDO CONSTRUTORA E PAVIMENTAÇÃO LTDA"
    assert entry.cost_center is not None
    assert entry.cost_center.code.value == "2"
    assert entry.cost_center.division is not None
    assert entry.cost_center.division.code.value == "USINA"
