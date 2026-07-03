from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ExecutionContext:
    pipeline_name: str
    stage: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Any = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def set_stage(self, stage_name: str) -> None:
        self.stage = stage_name
