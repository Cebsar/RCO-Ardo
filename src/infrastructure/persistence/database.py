from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


DEFAULT_SQLITE_PATH = Path("database/enterprise.db")


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    echo: bool = False

    @classmethod
    def from_env(cls, env_var: str = "ENTERPRISE_DATABASE_URL") -> "DatabaseConfig":
        database_url = os.getenv(env_var)
        if not database_url:
            database_url = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
        return cls(url=database_url, echo=os.getenv("SQLALCHEMY_ECHO", "").lower() == "true")


def create_engine_from_config(config: Optional[DatabaseConfig] = None) -> Engine:
    resolved = config or DatabaseConfig.from_env()
    if resolved.url.startswith("sqlite:///"):
        sqlite_path = Path(resolved.url.removeprefix("sqlite:///"))
        if sqlite_path.parent != Path("."):
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if resolved.url.startswith("sqlite") else {}
    return create_engine(resolved.url, echo=resolved.echo, future=True, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)
