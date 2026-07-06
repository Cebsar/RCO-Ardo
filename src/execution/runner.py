from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Dict, Iterable, List, Optional

from src.application.contracts.datasource import IDataSource
from src.domain.entities import DRENode
from src.domain.value_objects import Money
from src.infrastructure.business_rules.provider import BusinessRuleProvider
from src.infrastructure.dre_loader.builder import DRETreeBuilder
from src.infrastructure.golden_dataset.comparators import GoldenDatasetComparator
from src.infrastructure.golden_dataset.dataset import GoldenDataset, GoldenDRE, GoldenFactAccounting, GoldenOverview, GoldenWorkbook
from src.infrastructure.golden_dataset.utilities import compute_dataset_hash, format_dataset_version
from src.infrastructure.reconciliation.engine import ReconciliationEngine
from src.infrastructure.rule_engine.engine import RuleEngine
from src.infrastructure.warehouse.builder import WarehouseBuilder
from src.infrastructure.header_mapper.mapper import HeaderMapper, HeaderMapping
from src.infrastructure.normalizer.normalizer import AccountingNormalizer
from src.infrastructure.schema_validator.validator import SchemaValidator
from .configuration import ExecutionConfiguration
from .context import ExecutionContext
from .pipeline import ExecutionPipeline, PipelineStep
from .reports import PipelineReport, StageResult
from .result import PipelineResult

logger = logging.getLogger(__name__)


class FunctionalPipelineStep(PipelineStep):
    def __init__(self, name: str, func: Callable[[ExecutionContext], PipelineResult]):
        self.name = name
        self._func = func

    def execute(self, context: ExecutionContext) -> PipelineResult:
        return self._func(context)


@dataclass
class PipelineRunner:
    excel_adapter: IDataSource
    header_mapper: HeaderMapper
    schema_validator: SchemaValidator
    warehouse_builder: WarehouseBuilder
    dre_tree_builder: DRETreeBuilder
    business_rule_provider: BusinessRuleProvider
    rule_engine: RuleEngine
    reconciliation_engine: Optional[ReconciliationEngine] = None
    golden_dataset_comparator: Optional[GoldenDatasetComparator] = None
    logger: Optional[logging.Logger] = None
    normalizer_factory: Callable[[HeaderMapping], AccountingNormalizer] = AccountingNormalizer
    enterprise_persistence: Optional[Any] = None

    def run(self, config: ExecutionConfiguration) -> PipelineReport:
        context = ExecutionContext(pipeline_name="ARDO Pipeline")
        context.metadata["config"] = config

        pipeline = ExecutionPipeline(name="ARDO ETL Pipeline", logger=None)
        pipeline.add_step(FunctionalPipelineStep("Load Workbook", self._load_workbook))
        pipeline.add_step(FunctionalPipelineStep("Map Headers", self._map_headers))
        pipeline.add_step(FunctionalPipelineStep("Validate Schema", self._validate_schema))
        pipeline.add_step(FunctionalPipelineStep("Normalize Entries", self._normalize_entries))
        pipeline.add_step(FunctionalPipelineStep("Build Warehouse", self._build_warehouse))
        pipeline.add_step(FunctionalPipelineStep("Build DRE", self._build_dre_tree))
        pipeline.add_step(FunctionalPipelineStep("Run Business Rules", self._run_business_rules))
        pipeline.add_step(FunctionalPipelineStep("Run Reconciliation", self._run_reconciliation))
        pipeline.add_step(FunctionalPipelineStep("Golden Dataset", self._build_golden_dataset))

        stage_results: List[StageResult] = []
        start = perf_counter()
        errors: List[str] = []

        for step in pipeline.steps:
            context.set_stage(step.name)
            stage_start = perf_counter()
            try:
                result = step.execute(context)
            except Exception as exc:  # pragma: no cover
                duration = perf_counter() - stage_start
                error_message = str(exc)
                errors.append(error_message)
                stage_results.append(
                    StageResult(
                        name=step.name,
                        success=False,
                        duration_seconds=duration,
                        output=None,
                        errors=[error_message],
                        details={"exception": error_message},
                    )
                )
                if self.logger:
                    self.logger.error("Pipeline step failed %s: %s", step.name, error_message)
                break

            duration = perf_counter() - stage_start
            stage_info = StageResult(
                name=step.name,
                success=result.success,
                duration_seconds=duration,
                output=result.output,
                errors=result.errors,
                warnings=getattr(result, "warnings", []),
                details=result.details or {},
            )
            stage_results.append(stage_info)

            if not result.success:
                errors.extend(result.errors)
                if self.logger:
                    self.logger.error("Pipeline step reported failure %s: %s", step.name, result.errors)
                break

            context.payload = result.output

        finished = perf_counter()
        total_duration = finished - start
        success = len(errors) == 0
        report = PipelineReport(
            configuration=config,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            duration_seconds=total_duration,
            success=success,
            stage_results=stage_results,
            errors=errors,
        )

        self._attach_reports(report, context)
        self._persist_enterprise_report(report, context)
        return report

    def _attach_reports(self, report: PipelineReport, context: ExecutionContext) -> None:
        payload = context.payload or {}
        if isinstance(payload, dict):
            report.rule_execution = payload.get("rule_execution")
            report.reconciliation = payload.get("reconciliation")
            report.golden_regression = payload.get("golden_regression")
            report.metadata["workflow_payload"] = {k: v for k, v in payload.items() if k not in {"entries", "rows", "mapping", "assigned_roots"}}

    def _persist_enterprise_report(self, report: PipelineReport, context: ExecutionContext) -> None:
        if self.enterprise_persistence is None:
            return
        payload = context.payload or {}
        if not isinstance(payload, dict):
            return
        dre_tree = payload.get("dre_tree")
        dre_roots = payload.get("assigned_roots")
        if dre_roots is None and dre_tree is not None:
            dre_roots = getattr(dre_tree, "roots", None)
        accounting_facts = None
        warehouse_store = getattr(self.warehouse_builder, "store", None)
        if warehouse_store is not None:
            accounting_facts = getattr(warehouse_store, "facts", {}).values()
        persisted = self.enterprise_persistence.persist_pipeline_run(
            report,
            accounting_entries=payload.get("entries"),
            accounting_facts=accounting_facts,
            dre_roots=dre_roots,
            reconciliation_report=report.reconciliation,
        )
        report.metadata["enterprise_persistence"] = {
            "pipeline_execution_id": persisted.pipeline_execution_id,
            "accounting_entries": persisted.accounting_entries,
            "dre_nodes": persisted.dre_nodes,
            "reconciliation_rows": persisted.reconciliation_rows,
            "metrics_rows": persisted.metrics_rows,
        }

    def _load_workbook(self, context: ExecutionContext) -> PipelineResult:
        config: ExecutionConfiguration = context.metadata["config"]
        rows = self.excel_adapter.read(str(config.source_path))
        headers = self.excel_adapter.get_headers()
        return PipelineResult(success=True, output={"rows": rows, "headers": headers})

    def _map_headers(self, context: ExecutionContext) -> PipelineResult:
        current = context.payload or {}
        headers = current.get("headers", [])
        mapping = self.header_mapper.map(headers)
        return PipelineResult(success=True, output={"rows": current.get("rows", []), "headers": headers, "mapping": mapping})

    def _validate_schema(self, context: ExecutionContext) -> PipelineResult:
        config: ExecutionConfiguration = context.metadata["config"]
        current = context.payload or {}
        mapping = current.get("mapping")
        if mapping is None:
            return PipelineResult(success=False, errors=["Header mapping not available"], output=current)
        validation = self.schema_validator.validate_sheet(config.source_path.name, mapping)
        if not validation.is_valid:
            errors = [issue.message for issue in validation.issues if issue.severity == "error"]
            return PipelineResult(success=False, errors=errors, output={**current, "validation_report": validation})
        return PipelineResult(success=True, output={**current, "validation_report": validation})

    def _normalize_entries(self, context: ExecutionContext) -> PipelineResult:
        current = context.payload or {}
        rows = current.get("rows", [])
        mapping = current.get("mapping")
        if mapping is None:
            return PipelineResult(success=False, errors=["Header mapping missing"], output=current)
        normalizer = self.normalizer_factory(mapping)
        entries, normalization_report = normalizer.normalize(rows)
        if normalization_report.invalid_count > 0 and normalization_report.normalized_count == 0:
            errors = [issue.message for issue in normalization_report.issues if issue.severity == "error"]
            return PipelineResult(success=False, errors=errors or ["Normalization failed"], output={**current, "normalization_report": normalization_report})
        output = {
            **current,
            "entries": entries,
            "normalization_report": normalization_report,
        }
        return PipelineResult(success=True, output=output)

    def _build_warehouse(self, context: ExecutionContext) -> PipelineResult:
        current = context.payload or {}
        entries = current.get("entries", [])
        report = self.warehouse_builder.build(entries)
        return PipelineResult(success=True, output={**current, "warehouse_report": report})

    def _build_dre_tree(self, context: ExecutionContext) -> PipelineResult:
        config: ExecutionConfiguration = context.metadata["config"]
        dre_tree, hierarchy_report = self.dre_tree_builder.build_from_path(config.source_path, config.dre_sheet_name)
        return PipelineResult(success=True, output={**context.payload, "dre_tree": dre_tree, "hierarchy_report": hierarchy_report})

    def _run_business_rules(self, context: ExecutionContext) -> PipelineResult:
        current = context.payload or {}
        dre_tree = current.get("dre_tree")
        entries = current.get("entries", [])
        if dre_tree is None:
            return PipelineResult(success=False, errors=["DRE tree unavailable"], output=current)
        assigned_roots = self.business_rule_provider.assign_rules(list(dre_tree.roots))
        facts = self._build_rule_facts(entries)
        calculated = self.rule_engine.execute(assigned_roots, facts, self.business_rule_provider.get_business_rules())
        return PipelineResult(success=True, output={**current, "assigned_roots": assigned_roots, "rule_execution": calculated})

    def _run_reconciliation(self, context: ExecutionContext) -> PipelineResult:
        if self.reconciliation_engine is None:
            return PipelineResult(success=True, output=context.payload)
        current = context.payload or {}
        dre_tree = current.get("dre_tree")
        assigned_roots = current.get("assigned_roots")
        rule_execution = current.get("rule_execution")
        if dre_tree is None or assigned_roots is None or rule_execution is None:
            return PipelineResult(success=False, errors=["Reconciliation dependencies missing"], output=current)
        expected_roots = list(dre_tree.roots)
        actual_roots = self._materialize_actual_dre(assigned_roots, rule_execution)
        audit = self.reconciliation_engine.reconcile(expected_roots, actual_roots, source_name=str(context.metadata["config"].source_path.name))
        return PipelineResult(success=True, output={**current, "reconciliation": audit})

    def _build_golden_dataset(self, context: ExecutionContext) -> PipelineResult:
        config: ExecutionConfiguration = context.metadata["config"]
        current = context.payload or {}
        if not config.golden_enabled:
            return PipelineResult(success=True, output=current)
        entries = current.get("entries", [])
        headers = current.get("headers", [])
        rows = current.get("rows", [])
        assigned_roots = current.get("assigned_roots", [])
        rule_execution = current.get("rule_execution")

        workbook = GoldenWorkbook(
            path=config.source_path,
            fingerprint=self._compute_workbook_fingerprint(config.source_path, len(rows), headers),
            row_count=len(rows),
            columns=[str(h) for h in headers],
        )
        overview = GoldenOverview(
            source=str(config.source_path),
            generated_at=datetime.utcnow(),
            entries=self._flatten_dre_records(assigned_roots),
        )
        fact_accounting = GoldenFactAccounting(
            source=str(config.source_path),
            generated_at=datetime.utcnow(),
            records=self._flatten_fact_records(entries),
        )
        dre = GoldenDRE(
            source=str(config.source_path),
            generated_at=datetime.utcnow(),
            nodes=self._flatten_dre_records(assigned_roots, include_amount=True),
        )
        dataset = GoldenDataset.build(
            workbook=workbook,
            overview=overview,
            fact_accounting=fact_accounting,
            dre=dre,
            version=format_dataset_version(1, 0, 0),
            source_paths={
                "workbook": str(config.source_path),
                "overview": str(config.source_path),
                "fact_accounting": str(config.source_path),
                "dre": str(config.source_path),
            },
        )
        dataset.save(config.golden_dataset_output_dir)
        output = {**current, "golden_dataset": dataset}
        if self.golden_dataset_comparator and rule_execution is not None:
            # future hook for comparing against expected dataset
            output["golden_regression"] = None
        return PipelineResult(success=True, output=output)

    def _build_rule_facts(self, entries: List[Any]) -> List[Dict[str, Any]]:
        facts: List[Dict[str, Any]] = []
        for entry in entries:
            facts.append(
                {
                    "account_code": entry.account.code.value,
                    "amount": entry.amount.amount if hasattr(entry.amount, "amount") else entry.amount,
                    "date": entry.date,
                    "entry_id": entry.id,
                }
            )
        return facts

    def _materialize_actual_dre(self, roots: Iterable[DRENode], execution_report: Any) -> List[DRENode]:
        report_results = getattr(execution_report, "results", None)
        if report_results is None:
            report_results = getattr(getattr(execution_report, "report", None), "results", [])
        by_code = {result.node_code: result for result in report_results}

        def materialize(node: DRENode) -> DRENode:
            result = by_code.get(node.code.value)
            amount = node.amount
            if result and result.value is not None:
                try:
                    amount = Money(result.value)
                except Exception:
                    amount = node.amount
            return DRENode(
                code=node.code,
                name=node.name,
                level=node.level,
                amount=amount,
                percentage=node.percentage,
                children=tuple(materialize(child) for child in node.children),
                rule=node.rule,
            )

        return [materialize(root) for root in roots]

    def _flatten_dre_records(self, roots: Iterable[DRENode], include_amount: bool = False) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []

        def walk(node: DRENode) -> None:
            record: Dict[str, Any] = {
                "code": node.code.value,
                "name": node.name,
                "level": int(node.level),
                "children_count": len(node.children),
            }
            if include_amount and node.amount is not None:
                record["amount"] = str(node.amount.amount)
            if getattr(node, "rule", None) is not None:
                record["rule_id"] = getattr(node.rule, "id", None)
            records.append(record)
            for child in node.children:
                walk(child)

        for root in roots:
            walk(root)
        return records

    def _flatten_fact_records(self, entries: List[Any]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for entry in entries:
            records.append(
                {
                    "entry_id": entry.id,
                    "account_code": entry.account.code.value,
                    "amount": str(entry.amount.amount),
                    "date": entry.date.isoformat(),
                    "description": entry.description,
                }
            )
        return records

    def _compute_workbook_fingerprint(self, path: Path, row_count: int, headers: List[Any]) -> str:
        stats = path.stat()
        fingerprint_payload = {
            "path": str(path),
            "row_count": row_count,
            "headers": [str(h) for h in headers],
            "size": stats.st_size,
            "mtime": stats.st_mtime_ns,
        }
        return compute_dataset_hash(fingerprint_payload)
