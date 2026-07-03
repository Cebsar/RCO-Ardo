from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .context import ExecutionContext
from .result import PipelineResult


class PipelineStep(ABC):
    """Abstract pipeline step.

    Concrete steps should implement `execute(context)` and return a PipelineResult.
    """

    name: str

    @abstractmethod
    def execute(self, context: ExecutionContext) -> PipelineResult:
        raise NotImplementedError
