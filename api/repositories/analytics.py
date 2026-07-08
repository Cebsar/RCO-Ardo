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
    def __init__(self, session: Session):
        self.session = session

    def get_kpis(self) -> dict[str, object]:
        latest_stmt = select(PipelineExecutionORM.id).order_by(PipelineExecutionORM.created_at.desc()).limit(1)
        latest_success = self._latest_success_execution_id()
        executive, charts, drilldown, pagination, warnings = self._executive_analytics(latest_success)
        return {
            "pipeline_executions": self._count(PipelineExecutionORM),
            "successful_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(True)),
            "failed_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(False)),
            "accounting_entries": self._count(FactAccountingEntryORM),
            "dre_nodes": self._count(FactDREORM),
            "reconciliation_rows": self._count(FactReconciliationORM),
            "average_duration_seconds": float(
                self.session.scalar(select(func.avg(PipelineExecutionORM.duration_seconds))) or 0.0
            ),
            "latest_execution_id": self.session.scalar(latest_stmt),
            "warnings": warnings,
            "executive": executive,
            "charts": charts,
            "drilldown": drilldown,
            "pagination": pagination,
        }

    def _count(self, model: type, predicate=None) -> int:
        stmt = select(func.count()).select_from(model)
        if predicate is not None:
            stmt = stmt.where(predicate)
        return int(self.session.scalar(stmt) or 0)

    def _latest_success_execution_id(self) -> str | None:
        stmt = (
            select(PipelineExecutionORM.id)
            .where(PipelineExecutionORM.success.is_(True))
            .order_by(PipelineExecutionORM.created_at.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def _executive_analytics(self, execution_id: str | None) -> tuple[dict, dict, dict, dict, list[str]]:
        warnings: list[str] = []
        if execution_id is None:
            warnings.append("Nenhuma execução bem-sucedida encontrada para analytics executivo.")
            return {}, {}, {}, {"entries_limit": 0, "entries_returned": 0}, warnings

        dre_rows = list(
            self.session.scalars(
                select(FactDREORM)
                .where(FactDREORM.pipeline_execution_id == execution_id)
                .order_by(FactDREORM.level.asc(), FactDREORM.ordinal.asc(), FactDREORM.node_code.asc())
            )
        )
        dre_by_name = {row.node_name.strip().casefold(): self._money(row.amount) for row in dre_rows}
        receita_bruta = self._first_value(dre_by_name, "Receita Bruta")
        receita_liquida = self._first_value(dre_by_name, "Receita Líquida")
        ebitda = self._first_value(dre_by_name, "EBITDA")
        lucro_operacional = self._first_value(dre_by_name, "Lucro Operacional (EBIT)", "Lucro Operacional")
        caixa = self._cash_balance(execution_id)

        if caixa is None:
            warnings.append("Caixa não encontrado em contas 1.1.1* dos lançamentos persistidos.")
        warnings.append("Forecast não encontrado nas tabelas autorizadas; valor retornado como null.")
        warnings.append("Planejado x Realizado não encontrado nas tabelas autorizadas; valores retornados como null.")

        executive = {
            "receita_bruta": receita_bruta,
            "receita_liquida": receita_liquida,
            "ebitda": ebitda,
            "lucro_operacional": lucro_operacional,
            "margem_ebitda": self._ratio(ebitda, receita_liquida),
            "margem_operacional": self._ratio(lucro_operacional, receita_liquida),
            "caixa": caixa,
            "forecast": None,
            "planejado_x_realizado": {"planejado": None, "realizado": receita_liquida, "variacao": None},
            "latest_execution_id": execution_id,
        }

        charts = {
            "receita_mensal": self._monthly_revenue(execution_id),
            "ebitda_mensal": self._monthly_ebitda(execution_id, ebitda),
            "receita_por_empresa": self._revenue_by_dimension(execution_id, "company"),
            "receita_por_divisao": self._revenue_by_dimension(execution_id, "division"),
            "receita_por_centro_custo": self._revenue_by_dimension(execution_id, "cost_center", limit=12),
            "evolucao_caixa": self._monthly_cash(execution_id),
            "waterfall_dre": [
                {"name": row.node_name, "value": self._money(row.amount), "code": row.node_code}
                for row in dre_rows
                if row.level == 1
            ],
        }
        drilldown = self._drilldown(execution_id)
        pagination = {
            "entries_limit": 250,
            "entries_returned": sum(
                len(analytical["entries"])
                for company in drilldown["companies"]
                for division in company["divisions"]
                for cost_center in division["cost_centers"]
                for synthetic in cost_center["synthetic_accounts"]
                for analytical in synthetic["analytical_accounts"]
            ),
        }
        return executive, charts, drilldown, pagination, warnings

    def _cash_balance(self, execution_id: str) -> float | None:
        value = self.session.scalar(
            select(func.sum(FactAccountingEntryORM.amount)).where(
                FactAccountingEntryORM.pipeline_execution_id == execution_id,
                FactAccountingEntryORM.account_code.like("1.1.1%"),
            )
        )
        return self._money(value) if value is not None else None

    def _monthly_revenue(self, execution_id: str) -> list[dict]:
        rows = self.session.execute(
            select(FactAccountingEntryORM.period_code, func.sum(FactAccountingEntryORM.amount))
            .where(
                FactAccountingEntryORM.pipeline_execution_id == execution_id,
                FactAccountingEntryORM.account_code.like("3.%"),
            )
            .group_by(FactAccountingEntryORM.period_code)
            .order_by(FactAccountingEntryORM.period_code.asc())
        )
        return [{"period": period or "sem_periodo", "value": self._money(amount)} for period, amount in rows]

    def _monthly_ebitda(self, execution_id: str, total_ebitda: float) -> list[dict]:
        revenue = self._monthly_revenue(execution_id)
        total_revenue = sum(item["value"] for item in revenue)
        if not revenue:
            return []
        if total_revenue == 0:
            return [{"period": item["period"], "value": 0.0} for item in revenue]
        return [{"period": item["period"], "value": round(total_ebitda * (item["value"] / total_revenue), 2)} for item in revenue]

    def _monthly_cash(self, execution_id: str) -> list[dict]:
        rows = self.session.execute(
            select(FactAccountingEntryORM.period_code, func.sum(FactAccountingEntryORM.amount))
            .where(
                FactAccountingEntryORM.pipeline_execution_id == execution_id,
                FactAccountingEntryORM.account_code.like("1.1.1%"),
            )
            .group_by(FactAccountingEntryORM.period_code)
            .order_by(FactAccountingEntryORM.period_code.asc())
        )
        running = 0.0
        series = []
        for period, amount in rows:
            running += self._money(amount)
            series.append({"period": period or "sem_periodo", "value": round(running, 2)})
        return series

    def _revenue_by_dimension(self, execution_id: str, key: str, limit: int = 10) -> list[dict]:
        extractor = func.json_extract(FactAccountingEntryORM.source_row, f"$.{key}")
        rows = self.session.execute(
            select(extractor, func.sum(FactAccountingEntryORM.amount), func.count())
            .where(
                FactAccountingEntryORM.pipeline_execution_id == execution_id,
                FactAccountingEntryORM.account_code.like("3.%"),
            )
            .group_by(extractor)
            .order_by(func.abs(func.sum(FactAccountingEntryORM.amount)).desc())
            .limit(limit)
        )
        return [
            {"name": str(name) if name not in (None, "") else "Não informado", "value": self._money(amount), "records": int(count)}
            for name, amount, count in rows
        ]

    def _drilldown(self, execution_id: str) -> dict:
        rows = self.session.scalars(
            select(FactAccountingEntryORM)
            .where(FactAccountingEntryORM.pipeline_execution_id == execution_id)
            .order_by(
                FactAccountingEntryORM.company_key.asc(),
                FactAccountingEntryORM.division_key.asc(),
                FactAccountingEntryORM.costcenter_key.asc(),
                FactAccountingEntryORM.account_code.asc(),
                FactAccountingEntryORM.accounting_date.asc(),
            )
            .limit(250)
        )
        tree: dict[str, dict] = {}
        for row in rows:
            source = row.source_row or {}
            company = str(source.get("company") or row.company_key or "Não informado")
            division = str(source.get("division") or row.division_key or "Não informado")
            cost_center = str(source.get("cost_center") or row.costcenter_key or "Não informado")
            synthetic_code = ".".join(row.account_code.split(".")[:3]) if "." in row.account_code else row.account_code[:4]
            company_node = tree.setdefault(company, {"name": company, "divisions": {}})
            division_node = company_node["divisions"].setdefault(division, {"name": division, "cost_centers": {}})
            cost_node = division_node["cost_centers"].setdefault(cost_center, {"name": cost_center, "synthetic_accounts": {}})
            synthetic_node = cost_node["synthetic_accounts"].setdefault(
                synthetic_code,
                {"code": synthetic_code, "name": synthetic_code, "analytical_accounts": {}},
            )
            analytical_node = synthetic_node["analytical_accounts"].setdefault(
                row.account_code,
                {"code": row.account_code, "name": row.account_name or row.account_code, "entries": []},
            )
            analytical_node["entries"].append(
                {
                    "entry_id": row.entry_id,
                    "date": row.accounting_date.isoformat(),
                    "description": row.description,
                    "amount": self._money(row.amount),
                    "entry_type": row.entry_type,
                    "currency": row.currency,
                }
            )

        return {
            "companies": [
                {
                    "name": company["name"],
                    "divisions": [
                        {
                            "name": division["name"],
                            "cost_centers": [
                                {
                                    "name": cost_center["name"],
                                    "synthetic_accounts": [
                                        {
                                            "code": synthetic["code"],
                                            "name": synthetic["name"],
                                            "analytical_accounts": list(synthetic["analytical_accounts"].values()),
                                        }
                                        for synthetic in cost_center["synthetic_accounts"].values()
                                    ],
                                }
                                for cost_center in division["cost_centers"].values()
                            ],
                        }
                        for division in company["divisions"].values()
                    ],
                }
                for company in tree.values()
            ]
        }

    @staticmethod
    def _money(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        return float(value)

    @staticmethod
    def _ratio(numerator: float, denominator: float) -> float | None:
        if denominator == 0:
            return None
        return round(numerator / denominator, 6)

    @staticmethod
    def _first_value(values: dict[str, float], *names: str) -> float:
        for name in names:
            found = values.get(name.casefold())
            if found is not None:
                return found
        return 0.0
