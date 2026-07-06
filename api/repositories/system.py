from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class SystemRepository:
    def __init__(self, session: Session):
        self.session = session

    def ping(self) -> bool:
        self.session.execute(text("select 1"))
        return True
