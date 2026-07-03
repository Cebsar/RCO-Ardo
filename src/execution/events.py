from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class ExecutionEvent:
    name: str
    timestamp: datetime = datetime.utcnow()
    payload: Optional[Any] = None
    details: Optional[dict] = None
