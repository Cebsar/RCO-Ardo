import logging
from pathlib import Path
import pandas as pd
from .storage import save_df_to_table, insert_audit, export_table_to_excel

logger = logging.getLogger(__name__)


def run_etl(source_excel: str | Path, table_name: str = 'rel_razao'):
    source_excel = Path(source_excel)
    logger.info("Starting ETL for %s -> table %s", source_excel, table_name)

    if not source_excel.exists():
        logger.error("Source file not found: %s", source_excel)
        raise FileNotFoundError(f"{source_excel} not found")

    # Read Excel (first sheet by default)
    df = pd.read_excel(source_excel)

    # Basic cleaning: drop completely empty rows
    df = df.dropna(how='all')

    # Write to DB
    save_df_to_table(df, table_name)

    # Audit
    insert_audit(action='etl_load', table_name=table_name, row_count=len(df), metadata={'source': str(source_excel)})

    # Export consolidated platform spreadsheet
    out_path = export_table_to_excel(table_name)
    logger.info("ETL finished, exported to %s", out_path)
    return out_path
