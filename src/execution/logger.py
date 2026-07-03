from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import ExecutionEvent


@dataclass
class PipelineLogger:
    name: str

    def info(self, msg: str, *args: Any) -> None:
        # placeholder: no external logging configured
        pass

    def error(self, msg: str, *args: Any) -> None:
        pass

    def debug(self, msg: str, *args: Any) -> None:
        pass

    def record_event(self, event: ExecutionEvent) -> None:
        # event recording placeholder
        pass
