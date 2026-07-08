from __future__ import annotations

from collections import defaultdict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import FactAccountingEntryORM, FactDREORM, PipelineExecutionORM


class FinancialRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_dre_nodes(
        self,
        *,
        company: str | None = None,
        period: str | None = None,
        limit: int = 500,
    ) -> list[FactDREORM]:
        latest_execution_id = self._latest_execution_id(company=None, period=None)
        if latest_execution_id is None:
            return []
        stmt = (
            select(FactDREORM)
            .where(FactDREORM.pipeline_execution_id == latest_execution_id)
            .order_by(FactDREORM.level.asc(), FactDREORM.ordinal.asc(), FactDREORM.node_code.asc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def rel_razao_amounts(
        self, nodes: list[FactDREORM], *, company: str | None = None, period: str | None = None
    ) -> dict[str, float]:
        execution_id = self._latest_execution_id(company=None, period=None)
        if execution_id is None:
            return {}
        stmt = select(FactAccountingEntryORM).where(FactAccountingEntryORM.pipeline_execution_id == execution_id)
        if company:
            stmt = stmt.where(FactAccountingEntryORM.group_name == company)
        if period:
            stmt = stmt.where(FactAccountingEntryORM.period_code == period)
        account_totals: dict[str, float] = defaultdict(float)
        for entry in self.session.scalars(stmt):
            value = float(entry.source_value or 0)
            account_totals[(entry.account_name or "").strip().casefold()] += value
        group_stmt = (
            select(FactAccountingEntryORM.dre_group, func.sum(FactAccountingEntryORM.source_value))
            .where(FactAccountingEntryORM.pipeline_execution_id == execution_id)
            .group_by(FactAccountingEntryORM.dre_group)
        )
        if company:
            group_stmt = group_stmt.where(FactAccountingEntryORM.group_name == company)
        if period:
            group_stmt = group_stmt.where(FactAccountingEntryORM.period_code == period)
        group_totals = {
            str(name or "").strip().casefold(): float(value or 0)
            for name, value in self.session.execute(group_stmt)
        }

        gross = group_totals.get("receita bruta", 0.0)
        deductions = group_totals.get("deduções de vendas", 0.0)
        net = gross + deductions
        depreciation = group_totals.get("depreciação", 0.0)
        financial = group_totals.get("receitas financeiras", 0.0) + group_totals.get("despesas financeiras", 0.0)
        taxes = group_totals.get("irpj/csll", 0.0)
        non_operating = group_totals.get("equivalência patrimonial", 0.0)
        excluded = {
            "", "none", "patrimoniais", "receita bruta", "deduções de vendas", "depreciação",
            "receitas financeiras", "despesas financeiras", "irpj/csll", "equivalência patrimonial",
        }
        operating = sum(value for name, value in group_totals.items() if name not in excluded)
        ebitda = net + operating
        ebit = ebitda + depreciation
        before_tax = ebit + financial + non_operating
        calculated = {
            "receita bruta": gross,
            "devoluções/cancelamentos": deductions,
            "impostos sobre faturamento": deductions,
            "receita líquida": net,
            "margem de contribuição (lucro bruto)": net + sum(
                value for name, value in group_totals.items() if name.startswith("custo") or name in {"cmv", "fretes"}
            ),
            "custos e despesas indiretos - sga": operating,
            "ebitda": ebitda,
            "depreciação": depreciation,
            "lucro operacional (ebit)": ebit,
            "receitas e despesas financeiras": financial,
            "lucro antes do imp.renda e cssl": before_tax,
            "irpj e csll": taxes,
            "lucro líquido": before_tax + taxes,
        }
        amounts: dict[str, float] = {}
        for node in nodes:
            name = node.node_name.strip().casefold()
            if name in calculated:
                amounts[node.node_code] = round(calculated[name], 2)
            elif name in group_totals:
                amounts[node.node_code] = round(group_totals[name], 2)
            else:
                amounts[node.node_code] = round(account_totals.get(name, 0.0), 2)
        return amounts

    def _latest_execution_id(self, *, company: str | None, period: str | None) -> str | None:
        stmt = select(PipelineExecutionORM).where(PipelineExecutionORM.success.is_(True))
        if company:
            stmt = stmt.where(PipelineExecutionORM.source_path.ilike(f"%{company}%"))
        if period:
            stmt = stmt.where(PipelineExecutionORM.source_path.ilike(f"%{period}%"))
        stmt = stmt.order_by(PipelineExecutionORM.created_at.desc()).limit(1)
        execution = self.session.scalar(stmt)
        return execution.id if execution is not None else None
