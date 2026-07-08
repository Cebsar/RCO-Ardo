from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import (
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)


class AnalyticsRepository:
    """Read-only analytics over normalized Rel_Razão G:X persisted fields."""

    def __init__(self, session: Session):
        self.session = session

    def get_kpis(self) -> dict[str, object]:
        execution_id = self._latest_success_execution_id()
        executive, charts, drilldown, pagination, warnings = self._executive_analytics(execution_id)
        return {
            "pipeline_executions": self._count(PipelineExecutionORM),
            "successful_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(True)),
            "failed_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(False)),
            "accounting_entries": (
                self._count(FactAccountingEntryORM, self._base(execution_id)) if execution_id else 0
            ),
            "dre_nodes": self._count(FactDREORM),
            "reconciliation_rows": self._count(FactReconciliationORM),
            "average_duration_seconds": float(self.session.scalar(select(func.avg(PipelineExecutionORM.duration_seconds))) or 0),
            "latest_execution_id": execution_id,
            "warnings": warnings,
            "executive": executive,
            "charts": charts,
            "drilldown": drilldown,
            "pagination": pagination,
            "filter_options": self._accounting_filter_options(execution_id),
            "source_validation": self._source_validation(execution_id),
        }

    def _count(self, model: type, predicate=None) -> int:
        stmt = select(func.count()).select_from(model)
        if predicate is not None:
            stmt = stmt.where(predicate)
        return int(self.session.scalar(stmt) or 0)

    def _latest_success_execution_id(self) -> str | None:
        return self.session.scalar(
            select(PipelineExecutionORM.id)
            .where(PipelineExecutionORM.success.is_(True))
            .order_by(PipelineExecutionORM.created_at.desc())
            .limit(1)
        )

    def _base(self, execution_id: str):
        return FactAccountingEntryORM.pipeline_execution_id == execution_id

    def _distinct(self, execution_id: str, expression) -> list[str]:
        values = self.session.scalars(
            select(expression).where(self._base(execution_id), expression.is_not(None), expression != "").distinct()
        )
        return self._friendly_sort(str(value).strip() for value in values)

    def _accounting_filter_options(self, execution_id: str | None) -> dict[str, list[str]]:
        empty = {
            "companies": [], "divisions": [], "cost_centers": [], "periods": [], "years": [],
            "accounts": [], "synthetic_accounts": [], "analytical_accounts": [], "dre_groups": [],
        }
        if not execution_id:
            return empty
        accounts = self._distinct(execution_id, FactAccountingEntryORM.account_code)
        return {
            "companies": self._distinct(execution_id, FactAccountingEntryORM.group_name),
            "divisions": self._distinct(execution_id, FactAccountingEntryORM.division_name),
            "cost_centers": self._distinct(execution_id, FactAccountingEntryORM.cost_center_name),
            "periods": self._distinct(execution_id, FactAccountingEntryORM.period_code),
            "years": self._distinct(execution_id, FactAccountingEntryORM.source_year),
            "accounts": accounts,
            "synthetic_accounts": self._friendly_sort(
                ".".join(code.split(".")[:3]) if "." in code else code[:4] for code in accounts
            ),
            "analytical_accounts": self._distinct(execution_id, FactAccountingEntryORM.account_name),
            "dre_groups": self._distinct(execution_id, FactAccountingEntryORM.dre_group),
        }

    def _executive_analytics(self, execution_id: str | None) -> tuple[dict, dict, dict, dict, list[str]]:
        if not execution_id:
            return {}, {}, {"companies": []}, {"entries_limit": 0, "entries_returned": 0}, [
                "Nenhuma execução bem-sucedida encontrada."
            ]
        dre = self._dre_from_rel_razao(execution_id)
        cash = self._cash_balance(execution_id)
        executive = {
            "receita_bruta": dre["Receita Bruta"],
            "receita_liquida": dre["Receita Líquida"],
            "ebitda": dre["EBITDA"],
            "lucro_operacional": dre["EBIT"],
            "margem_ebitda": self._ratio(dre["EBITDA"], dre["Receita Líquida"]),
            "margem_operacional": self._ratio(dre["EBIT"], dre["Receita Líquida"]),
            "caixa": cash,
            "forecast": None,
            "planejado_x_realizado": {"planejado": None, "realizado": dre["Receita Líquida"], "variacao": None},
            "latest_execution_id": execution_id,
        }
        drilldown = self._drilldown(execution_id)
        entries_returned = sum(
            len(account["entries"])
            for company in drilldown["companies"]
            for division in company["divisions"]
            for center in division["cost_centers"]
            for synthetic in center["synthetic_accounts"]
            for account in synthetic["analytical_accounts"]
        )
        charts = {
            "receita_mensal": self._monthly_metric(execution_id, "Receita Líquida"),
            "ebitda_mensal": self._monthly_metric(execution_id, "EBITDA"),
            "receita_por_empresa": self._revenue_by_dimension(execution_id, FactAccountingEntryORM.group_name),
            "receita_por_divisao": self._revenue_by_dimension(execution_id, FactAccountingEntryORM.division_name),
            "receita_por_centro_custo": self._revenue_by_dimension(execution_id, FactAccountingEntryORM.cost_center_name, 12),
            "evolucao_caixa": self._monthly_cash(execution_id),
            "waterfall_dre": [
                {"name": name, "value": value, "code": name.upper().replace(" ", "_")} for name, value in dre.items()
            ],
        }
        return executive, charts, drilldown, {"entries_limit": 250, "entries_returned": entries_returned}, [
            "Analytics calculado exclusivamente sobre os campos G:X persistidos da Rel_Razão.",
            "Forecast e Planejado não existem na Rel_Razão G:X; valores retornados como null.",
        ]

    def _group_totals(self, execution_id: str, period: str | None = None) -> dict[str, float]:
        stmt = (
            select(FactAccountingEntryORM.dre_group, func.sum(FactAccountingEntryORM.source_value))
            .where(self._base(execution_id))
            .group_by(FactAccountingEntryORM.dre_group)
        )
        if period:
            stmt = stmt.where(FactAccountingEntryORM.period_code == period)
        return {str(name or ""): self._money(value) for name, value in self.session.execute(stmt)}

    def _dre_from_rel_razao(self, execution_id: str, period: str | None = None) -> dict[str, float]:
        groups = self._group_totals(execution_id, period)
        gross = groups.get("Receita Bruta", 0.0)
        deductions = groups.get("Deduções de Vendas", 0.0)
        net = gross + deductions
        depreciation = groups.get("Depreciação", 0.0)
        financial = groups.get("Receitas Financeiras", 0.0) + groups.get("Despesas Financeiras", 0.0)
        taxes = groups.get("IRPJ/CSLL", 0.0)
        non_operating = groups.get("Equivalência Patrimonial", 0.0)
        excluded = {
            "", "None", "Patrimoniais", "Receita Bruta", "Deduções de Vendas", "Depreciação",
            "Receitas Financeiras", "Despesas Financeiras", "IRPJ/CSLL", "Equivalência Patrimonial",
        }
        operating = sum(value for name, value in groups.items() if name not in excluded)
        ebitda = net + operating
        ebit = ebitda + depreciation
        before_tax = ebit + financial + non_operating
        return {
            "Receita Bruta": round(gross, 2),
            "Deduções/Cancelamentos": round(deductions, 2),
            "Receita Líquida": round(net, 2),
            "Custos e Despesas Operacionais": round(operating, 2),
            "EBITDA": round(ebitda, 2),
            "Depreciação": round(depreciation, 2),
            "EBIT": round(ebit, 2),
            "Resultado Financeiro": round(financial, 2),
            "Lucro Antes do IRPJ e CSLL": round(before_tax, 2),
            "IRPJ e CSLL": round(taxes, 2),
            "Lucro Líquido": round(before_tax + taxes, 2),
        }

    def _monthly_metric(self, execution_id: str, metric: str) -> list[dict]:
        return [
            {"period": period, "value": self._dre_from_rel_razao(execution_id, period)[metric]}
            for period in self._distinct(execution_id, FactAccountingEntryORM.period_code)
        ]

    def _cash_balance(self, execution_id: str) -> float | None:
        value = self.session.scalar(
            select(func.sum(FactAccountingEntryORM.source_value)).where(
                self._base(execution_id), FactAccountingEntryORM.account_code.like("1.1.1%")
            )
        )
        return self._money(value) if value is not None else None

    def _monthly_cash(self, execution_id: str) -> list[dict]:
        rows = self.session.execute(
            select(FactAccountingEntryORM.period_code, func.sum(FactAccountingEntryORM.source_value))
            .where(self._base(execution_id), FactAccountingEntryORM.account_code.like("1.1.1%"))
            .group_by(FactAccountingEntryORM.period_code)
            .order_by(FactAccountingEntryORM.period_code)
        )
        running = 0.0
        result = []
        for period, amount in rows:
            running += self._money(amount)
            result.append({"period": period or "sem_periodo", "value": round(running, 2)})
        return result

    def _revenue_by_dimension(self, execution_id: str, dimension, limit: int = 10) -> list[dict]:
        rows = self.session.execute(
            select(dimension, func.sum(FactAccountingEntryORM.source_value), func.count())
            .where(
                self._base(execution_id),
                FactAccountingEntryORM.dre_group.in_(["Receita Bruta", "Deduções de Vendas"]),
            )
            .group_by(dimension)
            .order_by(func.abs(func.sum(FactAccountingEntryORM.source_value)).desc())
            .limit(limit)
        )
        return [
            {"name": str(name or "Não informado"), "value": self._money(value), "records": int(count)}
            for name, value, count in rows
        ]

    def _drilldown(self, execution_id: str) -> dict:
        rows = self.session.scalars(
            select(FactAccountingEntryORM)
            .where(self._base(execution_id))
            .order_by(
                FactAccountingEntryORM.group_name,
                FactAccountingEntryORM.division_name,
                FactAccountingEntryORM.cost_center_name,
                FactAccountingEntryORM.account_code,
                FactAccountingEntryORM.accounting_date,
            )
            .limit(250)
        )
        tree: dict[str, dict] = {}
        for row in rows:
            company = str(row.group_name or "Não informado")
            division = str(row.division_name or "Não informado")
            center = str(row.cost_center_name or "Não informado")
            synthetic_code = ".".join(row.account_code.split(".")[:3]) if "." in row.account_code else row.account_code[:4]
            company_node = tree.setdefault(company, {"name": company, "divisions": {}})
            division_node = company_node["divisions"].setdefault(division, {"name": division, "cost_centers": {}})
            center_node = division_node["cost_centers"].setdefault(center, {"name": center, "synthetic_accounts": {}})
            synthetic = center_node["synthetic_accounts"].setdefault(
                synthetic_code, {"code": synthetic_code, "name": synthetic_code, "analytical_accounts": {}}
            )
            analytical = synthetic["analytical_accounts"].setdefault(
                row.account_code, {"code": row.account_code, "name": row.account_name or row.account_code, "entries": []}
            )
            analytical["entries"].append({
                "entry_id": row.entry_id,
                "date": row.accounting_date.isoformat(),
                "description": row.history or row.description,
                "document": row.posting_number or row.batch_number,
                "debit": self._money(row.debit_amount),
                "credit": self._money(row.credit_amount),
                "amount": self._money(row.source_value),
                "entry_type": row.entry_type,
                "currency": row.currency,
            })
        return {"companies": [
            {"name": company["name"], "divisions": [
                {"name": division["name"], "cost_centers": [
                    {"name": center["name"], "synthetic_accounts": [
                        {**synthetic, "analytical_accounts": list(synthetic["analytical_accounts"].values())}
                        for synthetic in center["synthetic_accounts"].values()
                    ]} for center in division["cost_centers"].values()
                ]} for division in company["divisions"].values()
            ]} for company in tree.values()
        ]}

    def _source_validation(self, execution_id: str | None) -> dict:
        if not execution_id:
            return {"entries": 0, "total": 0.0, "by_company": [], "by_division": [], "by_cost_center": [], "by_account": []}
        def totals(dimension):
            return [
                {"name": str(name or "Não informado"), "value": self._money(value), "records": int(count)}
                for name, value, count in self.session.execute(
                    select(dimension, func.sum(FactAccountingEntryORM.source_value), func.count())
                    .where(self._base(execution_id)).group_by(dimension)
                )
            ]
        return {
            "entries": int(self.session.scalar(select(func.count()).select_from(FactAccountingEntryORM).where(self._base(execution_id))) or 0),
            "total": self._money(self.session.scalar(select(func.sum(FactAccountingEntryORM.source_value)).where(self._base(execution_id)))),
            "by_company": totals(FactAccountingEntryORM.group_name),
            "by_division": totals(FactAccountingEntryORM.division_name),
            "by_cost_center": totals(FactAccountingEntryORM.cost_center_name),
            "by_account": totals(FactAccountingEntryORM.account_code),
        }

    @staticmethod
    def _friendly_sort(values) -> list[str]:
        unique = {value for value in values if value}
        def key(value: str):
            return tuple((0, int(part)) if part.isdigit() else (1, part.casefold()) for part in value.replace("-", ".").split("."))
        return sorted(unique, key=key)

    @staticmethod
    def _money(value) -> float:
        if value is None:
            return 0.0
        return float(value if not isinstance(value, Decimal) else value)

    @staticmethod
    def _ratio(numerator: float, denominator: float) -> float | None:
        return None if denominator == 0 else round(numerator / denominator, 6)
