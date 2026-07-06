"""create enterprise persistence tables

Revision ID: 20260706_0001
Revises:
Create Date: 2026-07-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260706_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pipeline_name", sa.String(length=160), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("execution_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "execution_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pipeline_execution_id", sa.String(length=36), nullable=True),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("nodes_processed", sa.Integer(), nullable=True),
        sa.Column("rules_executed", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pipeline_execution_id"], ["pipeline_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_metrics_execution_scope", "execution_metrics", ["pipeline_execution_id", "scope"])
    op.create_table(
        "fact_accounting_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pipeline_execution_id", sa.String(length=36), nullable=True),
        sa.Column("entry_id", sa.String(length=160), nullable=False),
        sa.Column("company_key", sa.Integer(), nullable=True),
        sa.Column("division_key", sa.Integer(), nullable=True),
        sa.Column("costcenter_key", sa.Integer(), nullable=True),
        sa.Column("account_key", sa.Integer(), nullable=True),
        sa.Column("period_key", sa.Integer(), nullable=True),
        sa.Column("period_code", sa.String(length=20), nullable=True),
        sa.Column("account_code", sa.String(length=80), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("entry_type", sa.String(length=30), nullable=False),
        sa.Column("accounting_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_row", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pipeline_execution_id"], ["pipeline_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pipeline_execution_id", "entry_id", name="uq_fact_accounting_execution_entry"),
    )
    op.create_index("ix_fact_accounting_entry_period_account", "fact_accounting_entries", ["period_code", "account_code"])
    op.create_table(
        "fact_dre",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pipeline_execution_id", sa.String(length=36), nullable=True),
        sa.Column("node_code", sa.String(length=80), nullable=False),
        sa.Column("node_name", sa.String(length=255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("percentage", sa.Numeric(12, 6), nullable=True),
        sa.Column("parent_node_code", sa.String(length=80), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.String(length=160), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pipeline_execution_id"], ["pipeline_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fact_dre_execution_node", "fact_dre", ["pipeline_execution_id", "node_code"])
    op.create_table(
        "fact_reconciliation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pipeline_execution_id", sa.String(length=36), nullable=True),
        sa.Column("node_code", sa.String(length=80), nullable=False),
        sa.Column("node_name", sa.String(length=255), nullable=False),
        sa.Column("expected_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("actual_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("difference_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("tolerance_absolute", sa.Numeric(18, 2), nullable=True),
        sa.Column("tolerance_relative", sa.Numeric(12, 6), nullable=True),
        sa.Column("percentage_difference", sa.Numeric(12, 6), nullable=True),
        sa.Column("exists_in_expected", sa.Boolean(), nullable=False),
        sa.Column("exists_in_actual", sa.Boolean(), nullable=False),
        sa.Column("order_match", sa.Boolean(), nullable=False),
        sa.Column("level_match", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pipeline_execution_id"], ["pipeline_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fact_reconciliation_execution_node", "fact_reconciliation", ["pipeline_execution_id", "node_code"])


def downgrade() -> None:
    op.drop_index("ix_fact_reconciliation_execution_node", table_name="fact_reconciliation")
    op.drop_table("fact_reconciliation")
    op.drop_index("ix_fact_dre_execution_node", table_name="fact_dre")
    op.drop_table("fact_dre")
    op.drop_index("ix_fact_accounting_entry_period_account", table_name="fact_accounting_entries")
    op.drop_table("fact_accounting_entries")
    op.drop_index("ix_execution_metrics_execution_scope", table_name="execution_metrics")
    op.drop_table("execution_metrics")
    op.drop_table("pipeline_executions")
