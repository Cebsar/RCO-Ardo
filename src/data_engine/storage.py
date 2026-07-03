import logging
from sqlalchemy import create_engine, text
import pandas as pd
from pathlib import Path
from config.settings import DATABASE_URL, BASE_DIR

logger = logging.getLogger(__name__)


def get_engine(db_url: str = None):
    db_url = db_url or DATABASE_URL
    engine = create_engine(db_url, future=True)
    return engine


def save_df_to_table(df: pd.DataFrame, table_name: str, engine=None, if_exists: str = 'append'):
    engine = engine or get_engine()
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
    logger.info("Saved %d rows to table %s", len(df), table_name)


def read_table(table_name: str, engine=None, limit: int | None = None):
    engine = engine or get_engine()
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {int(limit)}"
    df = pd.read_sql_query(text(query), con=engine)
    return df


def export_table_to_excel(table_name: str, output_path: str | None = None, engine=None):
    engine = engine or get_engine()
    output_path = output_path or Path(BASE_DIR) / 'data' / 'output' / 'ARDO_DATA_PLATFORM.xlsx'
    df = read_table(table_name, engine=engine)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    logger.info("Exported table %s to %s", table_name, output_path)
    return output_path


def insert_audit(action: str, table_name: str, row_count: int, metadata: dict | None = None, engine=None):
    engine = engine or get_engine()
    metadata = metadata or {}
    audit = pd.DataFrame([{
        'action': action,
        'table_name': table_name,
        'row_count': int(row_count),
        'metadata': str(metadata)
    }])
    audit.to_sql('audit_logs', con=engine, if_exists='append', index=False)
    logger.info("Inserted audit record for %s: %s rows", table_name, row_count)
