from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.execution.configuration import ExecutionConfiguration

from .service import EnterprisePersistenceService, PersistedPipelineRun


@dataclass
class EnterprisePipelineRunner:
    runner: Any
    persistence: EnterprisePersistenceService

    def run(self, config: ExecutionConfiguration) -> Any:
        report = self.runner.run(config)
        payload = report.metadata.get("workflow_payload", {})
        persisted = self.persistence.persist_pipeline_run(
            report,
            accounting_entries=payload.get("entries"),
            dre_roots=payload.get("assigned_roots") or payload.get("dre_tree"),
            reconciliation_report=report.reconciliation,
        )
        report.metadata["enterprise_persistence"] = {
            "pipeline_execution_id": persisted.pipeline_execution_id,
            "accounting_entries": persisted.accounting_entries,
            "dre_nodes": persisted.dre_nodes,
            "reconciliation_rows": persisted.reconciliation_rows,
            "metrics_rows": persisted.metrics_rows,
        }
        return report


__all__ = ["EnterprisePipelineRunner", "PersistedPipelineRun"]
