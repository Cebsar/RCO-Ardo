# ardo-financial-analytics (RCO-Ardo)

Quickstart:

1. Create virtualenv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Place `Rel_Razão.xlsx` in `data/master/`.
3. Run ETL:

```bash
python scripts/run_etl.py --source data/master/Rel_Razão.xlsx
```

4. Start API:

```bash
python -m src.api.app
```

Outputs:
- `data/warehouse/warehouse.db` (SQLite)
- `data/output/ARDO_DATA_PLATFORM.xlsx`
- `audit_logs` table in SQLite for basic auditing

Notes:
- Configuration: see `config/settings.py` and `config/logging.yaml`.
- Adjust `DATABASE_URL` via environment variables or `.env`.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Project Information

- **Owner:** ARDO Construções Ltda.
- **Copyright:** Copyright (c) 2026 ARDO Construções Ltda.
- **Project:** ARDO Financial Analytics
- **Author:** César Barreto
- **Architecture:** OpenAI + ChatGPT (Technical Architecture)
- **Repository:** Private