from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Any

from .step import PipelineStep
from .context import ExecutionContext
from .result import PipelineResult
from .logger import PipelineLogger


@dataclass
class ExecutionPipeline:
    name: str
    steps: List[PipelineStep] = field(default_factory=list)
    logger: PipelineLogger | None = None

    def add_step(self, step: PipelineStep) -> None:
        self.steps.append(step)

    def run(self, context: ExecutionContext) -> PipelineResult:
        """Execute steps in order and return a PipelineResult.

        No business logic implemented; this method is a structural placeholder.
        """
        if self.logger:
            self.logger.info(f"Starting pipeline: {self.name}")
        # Structural flow only; real execution logic is not implemented.
        return PipelineResult(success=True, output=None, errors=[], execution_time=0.0)
