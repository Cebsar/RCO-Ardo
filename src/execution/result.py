from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class PipelineResult:
    success: bool
    output: Any = None
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    details: Optional[dict] = None
