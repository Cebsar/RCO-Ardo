from __future__ import annotations

from src.infrastructure.persistence.database import DatabaseConfig, create_engine_from_config
from src.infrastructure.persistence.migrations import migrate_rel_razao_gx


if __name__ == "__main__":
    migrate_rel_razao_gx(create_engine_from_config(DatabaseConfig.from_env()))
    print("Rel_Razão G:X migration applied.")
