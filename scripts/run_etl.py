"""Run the ETL pipeline: reads Rel_Razão.xlsx and loads into SQLite."""
import argparse
from pathlib import Path
from src.data_engine.etl import run_etl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', default='data/master/Rel_Razão.xlsx', help='Source Excel file')
    parser.add_argument('--table', '-t', default='rel_razao', help='Destination DB table name')
    args = parser.parse_args()

    source = Path(args.source)
    out = run_etl(source, table_name=args.table)
    print(f"Exported ARDO_DATA_PLATFORM: {out}")


if __name__ == '__main__':
    main()
