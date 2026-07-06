from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def new_uuid() -> str:
    return str(uuid.uuid4())


class PipelineExecutionORM(Base):
    __tablename__ = "pipeline_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    execution_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    accounting_entries = relationship("FactAccountingEntryORM", cascade="all, delete-orphan")
    dre_nodes = relationship("FactDREORM", cascade="all, delete-orphan")
    reconciliation_rows = relationship("FactReconciliationORM", cascade="all, delete-orphan")
    metrics = relationship("ExecutionMetricsORM", cascade="all, delete-orphan")


class FactAccountingEntryORM(Base):
    __tablename__ = "fact_accounting_entries"
    __table_args__ = (
        UniqueConstraint("pipeline_execution_id", "entry_id", name="uq_fact_accounting_execution_entry"),
        Index("ix_fact_accounting_entry_period_account", "period_code", "account_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_execution_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_executions.id", ondelete="CASCADE"))
    entry_id: Mapped[str] = mapped_column(String(160), nullable=False)
    company_key: Mapped[int | None] = mapped_column(Integer)
    division_key: Mapped[int | None] = mapped_column(Integer)
    costcenter_key: Mapped[int | None] = mapped_column(Integer)
    account_key: Mapped[int | None] = mapped_column(Integer)
    period_key: Mapped[int | None] = mapped_column(Integer)
    period_code: Mapped[str | None] = mapped_column(String(20))
    account_code: Mapped[str] = mapped_column(String(80), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)
    accounting_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_row: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class FactDREORM(Base):
    __tablename__ = "fact_dre"
    __table_args__ = (Index("ix_fact_dre_execution_node", "pipeline_execution_id", "node_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_execution_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_executions.id", ondelete="CASCADE"))
    node_code: Mapped[str] = mapped_column(String(80), nullable=False)
    node_name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    percentage: Mapped[float | None] = mapped_column(Numeric(12, 6))
    parent_node_code: Mapped[str | None] = mapped_column(String(80))
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rule_id: Mapped[str | None] = mapped_column(String(160))
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class FactReconciliationORM(Base):
    __tablename__ = "fact_reconciliation"
    __table_args__ = (Index("ix_fact_reconciliation_execution_node", "pipeline_execution_id", "node_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_execution_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_executions.id", ondelete="CASCADE"))
    node_code: Mapped[str] = mapped_column(String(80), nullable=False)
    node_name: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    actual_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    difference_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    tolerance_absolute: Mapped[float | None] = mapped_column(Numeric(18, 2))
    tolerance_relative: Mapped[float | None] = mapped_column(Numeric(12, 6))
    percentage_difference: Mapped[float | None] = mapped_column(Numeric(12, 6))
    exists_in_expected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exists_in_actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    order_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    level_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ExecutionMetricsORM(Base):
    __tablename__ = "execution_metrics"
    __table_args__ = (Index("ix_execution_metrics_execution_scope", "pipeline_execution_id", "scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_execution_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_executions.id", ondelete="CASCADE"))
    scope: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nodes_processed: Mapped[int | None] = mapped_column(Integer)
    rules_executed: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
