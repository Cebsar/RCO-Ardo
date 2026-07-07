from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi import UploadFile

from api.metadata import API_VERSION
from api.repositories.pipeline import PipelineRepository
from api.schemas.common import response_meta
from api.schemas.pipeline import (
    PipelineExecutionAPIResponse,
    PipelineExecutionDetail,
    PipelineExecutionResponse,
    PipelineExecutionSummary,
    PipelineHistoryAPIResponse,
    PipelineHistoryResponse,
)
from src.execution.configuration import ExecutionConfiguration
from src.execution.runner import PipelineRunner
from src.infrastructure.business_rules.provider import BusinessRuleProvider
from src.infrastructure.dre_loader.builder import DRETreeBuilder
from src.infrastructure.excel.excel_adapter import ExcelAdapter
from src.infrastructure.header_mapper.mapper import HeaderMapper
from src.infrastructure.persistence.database import DatabaseConfig
from src.infrastructure.persistence.service import EnterprisePersistenceService
from src.infrastructure.reconciliation.engine import ReconciliationEngine
from src.infrastructure.rule_engine.engine import RuleEngine
from src.infrastructure.schema_validator.validator import SchemaValidator
from src.infrastructure.warehouse.builder import WarehouseBuilder


class PipelineService:
    def __init__(self, repository: PipelineRepository):
        self.repository = repository

    def history(self, limit: int = 50) -> PipelineHistoryAPIResponse:
        executions = [self._summary(row) for row in self.repository.list_history(limit=limit)]
        return PipelineHistoryAPIResponse(
            data=PipelineHistoryResponse(executions=executions),
            meta=response_meta(API_VERSION),
        )

    def get_execution(self, execution_id: str) -> PipelineExecutionAPIResponse:
        execution = self.repository.get(execution_id)
        if execution is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline execution not found")
        detail = PipelineExecutionDetail(
            **self._summary(execution).model_dump(),
            errors=execution.errors,
            metadata=execution.execution_metadata,
            accounting_entries=self.repository.count_accounting_entries(execution.id),
            dre_nodes=self.repository.count_dre_nodes(execution.id),
            reconciliation_rows=self.repository.count_reconciliation_rows(execution.id),
            metrics_rows=self.repository.count_metrics(execution.id),
        )
        return PipelineExecutionAPIResponse(
            data=PipelineExecutionResponse(execution=detail),
            meta=response_meta(API_VERSION),
        )

    def run_uploaded_workbook(self, workbook: UploadFile) -> PipelineExecutionAPIResponse:
        suffix = Path(workbook.filename or "").suffix.lower()
        if suffix not in {".xlsx", ".xlsm", ".xls"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workbook must be an Excel file")

        upload_dir = Path("data") / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(workbook.filename or "workbook.xlsx").name
        source_path = upload_dir / f"{uuid4().hex}_{safe_name}"
        with source_path.open("wb") as handle:
            shutil.copyfileobj(workbook.file, handle)

        persistence = EnterprisePersistenceService(config=DatabaseConfig.from_env())
        persistence.create_database()
        runner = PipelineRunner(
            excel_adapter=ExcelAdapter(path=str(source_path)),
            header_mapper=HeaderMapper(),
            schema_validator=SchemaValidator(),
            warehouse_builder=WarehouseBuilder(),
            dre_tree_builder=DRETreeBuilder(),
            business_rule_provider=BusinessRuleProvider(Path("config") / "business_rules.yaml"),
            rule_engine=RuleEngine(),
            reconciliation_engine=ReconciliationEngine(),
            enterprise_persistence=persistence,
        )
        report = runner.run(
            ExecutionConfiguration(
                source_path=source_path,
                rules_config_path=Path("config") / "business_rules.yaml",
                accounting_sheet_name="Rel_Razão",
                dre_sheet_name="Overview RCO",
            )
        )
        persisted = report.metadata.get("enterprise_persistence", {})
        execution_id = persisted.get("pipeline_execution_id")
        if not execution_id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Pipeline did not persist execution")
        return self.get_execution(execution_id)

    def _summary(self, row) -> PipelineExecutionSummary:
        return PipelineExecutionSummary(
            id=row.id,
            pipeline_name=row.pipeline_name,
            source_path=row.source_path,
            status=row.status,
            success=row.success,
            started_at=row.started_at,
            finished_at=row.finished_at,
            duration_seconds=row.duration_seconds,
            created_at=row.created_at,
        )
