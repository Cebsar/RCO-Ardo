from src.infrastructure.header_mapper.mapper import HeaderMapping
from src.infrastructure.schema_validator.validator import SchemaValidator


def make_header_mapping(mapped=None, duplicates=None, missing=None, unmatched=None):
    mapped = mapped or {}
    duplicates = duplicates or []
    missing = missing or []
    unmatched = unmatched or []
    return HeaderMapping(mapping=mapped, canonical_to_headers={k: [v] for v,k in ((v,v) for v in mapped.values() if v)}, duplicates=duplicates, missing_required=missing, unmatched_headers=unmatched, execution_time_seconds=0.0)


def test_validate_sheet_ok():
    mapped = {"Company": "Company", "AccountCode": "AccountCode", "Debit": "Debit"}
    hm = make_header_mapping(mapped=mapped)
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)
    assert report.is_valid or any(i.severity != "error" for i in report.issues)


def test_validate_sheet_missing_required():
    mapped = {"Company": "Company"}
    hm = make_header_mapping(mapped=mapped, missing=["AccountCode"]) 
    sv = SchemaValidator()
    report = sv.validate_sheet("Sheet1", hm)
    assert any(i.code == "MISSING_FIELD" for i in report.issues)


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
