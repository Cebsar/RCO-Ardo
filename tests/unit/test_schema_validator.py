from src.infrastructure.header_mapper.mapper import HeaderMapping
from src.infrastructure.schema_validator.validator import SchemaValidator


def make_header_mapping(mapped=None, duplicates=None, missing=None, unmatched=None):
    mapped = mapped or {}
    duplicates = duplicates or []
    missing = missing or []
    unmatched = unmatched or []
    return HeaderMapping(mapping=mapped, canonical_to_headers={k: [v] for v,k in ((v,v) for v in mapped.values() if v)}, duplicates=duplicates, missing_required=missing, unmatched_headers=unmatched, execution_time_seconds=0.0)


def test_validate_sheet_ok():
    mapped = {"Company": "Company", "AccountCode": "AccountCode", "AccountingDate": "AccountingDate", "Debit": "Debit"}
    hm = make_header_mapping(mapped=mapped)
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)
    assert report.is_valid


def test_validate_sheet_missing_required():
    mapped = {"Company": "Company"}
    hm = make_header_mapping(mapped=mapped)
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)
    assert any(i.code == "MISSING_FIELD" for i in report.issues)
    assert {i.field for i in report.issues if i.code == "MISSING_FIELD"} == {"AccountCode", "AccountingDate"}


def test_validate_sheet_allows_missing_optional_fields():
    mapped = {"Company": "Company", "AccountCode": "AccountCode", "AccountingDate": "AccountingDate", "Debit": "Debit"}
    hm = make_header_mapping(mapped=mapped)
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)

    assert report.is_valid
    assert "Balance" in report.metadata["optional_missing"]
    assert "DocumentNumber" in report.metadata["optional_missing"]
    assert "History" in report.metadata["optional_missing"]


def test_validate_sheet_distinguishes_ignored_columns():
    mapped = {"Company": "Company", "AccountCode": "AccountCode", "AccountingDate": "AccountingDate", "Credit": "Credit"}
    hm = make_header_mapping(mapped=mapped, unmatched=["YTD", "IgnoreColumn25"])
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)

    assert report.is_valid
    assert report.metadata["ignored_columns"] == ["YTD", "IgnoreColumn25"]
    assert [i.code for i in report.issues if i.severity == "info"] == ["IGNORED_COLUMN", "IGNORED_COLUMN"]


def test_validate_workbook_missing_sheet():
    mappings = {"Another": make_header_mapping(mapped={"Company":"Company"})}
    sv = SchemaValidator(required_sheets=["Sheet1"]) 
    report = sv.validate_workbook(mappings)
    assert any(i.code == "MISSING_SHEET" for i in report.issues)


def test_validate_duplicates():
    mapped = {"Company": "Company", "AccountCode": "AccountCode"}
    hm = make_header_mapping(mapped=mapped, duplicates=["AccountCode"]) 
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)
    assert any(i.code == "DUPLICATE_MAPPING" for i in report.issues)
