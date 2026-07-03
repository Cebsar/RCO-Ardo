from src.infrastructure.header_mapper.mapper import HeaderMapper


def test_header_mapping_basic():
    headers = ["Company", "AccountCode", "AccountingDate", "Debit", "Credit"]
    mapper = HeaderMapper()
    result = mapper.map(headers)

    assert result.mapping["Company"] == "Company"
    assert result.mapping["AccountCode"] == "AccountCode"
    assert result.duplicates == []
    assert "Company" not in result.missing_required


def test_header_mapping_aliases_and_missing():
    headers = ["empresa", "codigo", "data", "debito"]
    mapper = HeaderMapper()
    result = mapper.map(headers)

    # empresa -> Company alias
    assert result.mapping["empresa"] == "Company"
    # codigo expected to map to AccountCode
    assert result.mapping["codigo"] == "AccountCode"
    # debit alias matches Debit
    assert result.mapping["debito"] == "Debit"
    # missing required fields should include many
    assert "Credit" in result.missing_required


def test_header_mapping_duplicates():
    headers = ["AccountCode", "account_code", "AccountCode"]
    mapper = HeaderMapper()
    result = mapper.map(headers)

    # duplicates should list AccountCode
    assert "AccountCode" in result.duplicates
    # canonical_to_headers should show multiple
    assert len(result.canonical_to_headers.get("AccountCode", [])) >= 2
