from __future__ import annotations

from sqlalchemy import Engine, inspect, text


GX_COLUMNS = {
    "source_company": "VARCHAR(255)",
    "group_name": "VARCHAR(255)",
    "division_name": "VARCHAR(255)",
    "dre_group": "VARCHAR(255)",
    "cost_center_name": "VARCHAR(255)",
    "source_month": "INTEGER",
    "source_year": "INTEGER",
    "batch_number": "VARCHAR(160)",
    "posting_number": "VARCHAR(160)",
    "document_title": "VARCHAR(255)",
    "history": "TEXT",
    "counterparty": "VARCHAR(255)",
    "debit_amount": "NUMERIC(18, 2)",
    "credit_amount": "NUMERIC(18, 2)",
    "source_value": "NUMERIC(18, 2)",
}


def migrate_rel_razao_gx(engine: Engine) -> None:
    """Idempotent additive migration for normalized Rel_Razão G:X fields."""
    inspector = inspect(engine)
    if "fact_accounting_entries" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("fact_accounting_entries")}
    with engine.begin() as connection:
        for name, ddl_type in GX_COLUMNS.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE fact_accounting_entries ADD COLUMN {name} {ddl_type}"))
