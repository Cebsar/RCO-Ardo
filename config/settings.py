import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ENV = os.getenv('ENV', 'development')
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR}/data/warehouse/warehouse.db")
