from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from sqlalchemy import Engine

from .database import DatabaseConfig, create_engine_from_config, create_session_factory
from .models import Base
from .migrations import migrate_rel_razao_gx
from .repositories import UnitOfWork


@dataclass
class PersistedPipelineRun:
    pipeline_execution_id: str
    accounting_entries: int = 0
    dre_nodes: int = 0
    reconciliation_rows: int = 0
    metrics_rows: int = 0


class EnterprisePersistenceService:
    def __init__(self, engine: Optional[Engine] = None, config: Optional[DatabaseConfig] = None):
        self.engine = engine or create_engine_from_config(config)
        self.session_factory = create_session_factory(self.engine)

    def create_database(self) -> None:
        Base.metadata.create_all(self.engine)
        migrate_rel_razao_gx(self.engine)

    def persist_pipeline_run(
        self,
        report: Any,
        *,
        accounting_entries: Optional[Iterable[Any]] = None,
        accounting_facts: Optional[Iterable[Any]] = None,
        dre_roots: Optional[Iterable[Any]] = None,
        reconciliation_report: Any = None,
        pipeline_name: str = "ARDO Pipeline",
    ) -> PersistedPipelineRun:
        with UnitOfWork(self.session_factory) as uow:
            execution = uow.pipeline_executions.add_from_report(report, pipeline_name=pipeline_name)
            execution_id = execution.id

            accounting_count = 0
            if accounting_facts is not None:
                accounting_count = len(uow.accounting_entries.add_fact_rows(accounting_facts, execution_id))
            elif accounting_entries is not None:
                accounting_count = len(uow.accounting_entries.add_entries(accounting_entries, execution_id))

            dre_count = 0
            if dre_roots is not None:
                dre_count = len(uow.dre.add_tree(dre_roots, execution_id))

            reconciled = reconciliation_report or getattr(report, "reconciliation", None)
            reconciliation_count = 0
            if reconciled is not None:
                reconciliation_count = len(uow.reconciliation.add_report(reconciled, execution_id))

            metrics_count = self._persist_metrics(uow, report, reconciled, execution_id)

            return PersistedPipelineRun(
                pipeline_execution_id=execution_id,
                accounting_entries=accounting_count,
                dre_nodes=dre_count,
                reconciliation_rows=reconciliation_count,
                metrics_rows=metrics_count,
            )

    def _persist_metrics(self, uow: UnitOfWork, report: Any, reconciliation: Any, execution_id: str) -> int:
        count = 0
        rule_execution = getattr(report, "rule_execution", None)
        rule_metrics = getattr(rule_execution, "metrics", None)
        if rule_metrics is not None:
            uow.metrics.add_metrics(rule_metrics, "rule_execution", execution_id)
            count += 1

        if reconciliation is not None:
            execution_metrics = getattr(reconciliation, "execution", None)
            if execution_metrics is not None:
                uow.metrics.add_metrics(execution_metrics, "reconciliation", execution_id)
                count += 1

        for stage in getattr(report, "stage_results", []):
            stage_metrics = type(
                "StageMetrics",
                (),
                {
                    "start_time": None,
                    "end_time": None,
                    "duration_seconds": getattr(stage, "duration_seconds", 0.0),
                },
            )()
            uow.metrics.add_metrics(stage_metrics, f"stage:{stage.name}", execution_id)
            count += 1
        return count
