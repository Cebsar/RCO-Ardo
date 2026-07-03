from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ExecutionConfiguration:
    source_path: Path
    rules_config_path: Path
    dre_sheet_name: str = "Overview RCO"
    golden_dataset_output_dir: Optional[Path] = None
    enable_golden_dataset: bool = False
    logging_name: str = "ArdoPipeline"

    @property
    def golden_enabled(self) -> bool:
        return self.enable_golden_dataset and self.golden_dataset_output_dir is not None
