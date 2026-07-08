import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Banknote,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  Database,
  Download,
  GitBranch,
  LineChart as LineChartIcon,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { PipelineRunner } from "@/components/operational/PipelineRunner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { listOperationalExecutions } from "@/lib/operational";
import { useFinancialFilters } from "@/lib/financialFilters";
import type { ChartPoint, DrilldownEntry, ExecutiveDrilldown, Kpis } from "@/lib/types";
import { formatDate, formatDecimal, formatNumber } from "@/lib/utils";

const gold = "#d6a93a";
const green = "#7e8f78";
const copper = "#b98545";
const red = "#e35d5b";

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return "Não disponível";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "Não disponível";
  return new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

function trendFromSeries(series: ChartPoint[]) {
  const current = series.at(-1)?.value ?? null;
  const previous = series.at(-2)?.value ?? null;
  if (current === null || previous === null || previous === 0) return { label: "Sem período anterior", positive: true };
  const delta = (current - previous) / Math.abs(previous);
  return {
    label: `${delta >= 0 ? "▲" : "▼"} ${formatPercent(delta)} vs período anterior`,
    positive: delta >= 0,
  };
}

function topName(series: ChartPoint[]) {
  return series.length > 0 ? series[0].name ?? "Não disponível" : "Não disponível";
}

function compactDreName(name: string) {
  return name
    .replace("Lucro Operacional (EBIT)", "EBIT")
    .replace("Margem de Contribuição (Lucro Bruto)", "Margem de Contribuição")
    .replace("Custos e Despesas Indiretos - SGA", "SG&A")
    .replace("Receitas e Despesas Financeiras", "Resultado Financeiro")
    .replace("Receitas e Despesas Não Operacionais", "Resultado Não Operacional")
    .replace("Lucro Líquido", "Lucro Líquido");
}

function financialWaterfall(data: ChartPoint[]) {
  const wanted = [
    "Receita Bruta",
    "Produção Industrial",
    "Devoluções/Cancelamentos",
    "Impostos sobre Faturamento",
    "Receita Líquida",
    "Margem de Contribuição (Lucro Bruto)",
    "Custos e Despesas Indiretos - SGA",
    "EBITDA",
    "Depreciação",
    "Lucro Operacional (EBIT)",
    "Receitas e Despesas Financeiras",
    "Receitas e Despesas Não Operacionais",
    "IRPJ e CSLL",
    "Lucro Líquido",
  ];
  return wanted
    .map((name) => data.find((item) => item.name === name))
    .filter((item): item is ChartPoint => Boolean(item))
    .map((item) => ({ ...item, name: compactDreName(item.name ?? "") }));
}

function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendPositive = true,
  icon: Icon,
}: {
  title: string;
  value: string;
  subtitle?: string;
  trend?: string;
  trendPositive?: boolean;
  icon: typeof Activity;
}) {
  return (
    <Card className="premium-card group overflow-hidden" title={`${title}: ${value}`}>
      <CardContent className="relative flex items-center justify-between gap-4 p-5">
        <div className="absolute inset-x-0 top-0 h-1 bg-primary/80" />
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">{title}</p>
          <p className="mt-3 truncate text-2xl font-semibold text-foreground">{value}</p>
          {subtitle ? <p className="mt-1 truncate text-xs text-muted-foreground">{subtitle}</p> : null}
          {trend ? (
            <span className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${trendPositive ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200" : "border-red-400/30 bg-red-400/10 text-red-200"}`}>
              {trend}
            </span>
          ) : null}
        </div>
        <div className="gold-surface flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-primary/25 text-primary transition-transform duration-300 group-hover:scale-105">
          <Icon className="h-7 w-7" />
        </div>
      </CardContent>
    </Card>
  );
}

function ChartCard({
  title,
  data,
  kind = "bar",
  nameKey = "period",
}: {
  title: string;
  data: ChartPoint[];
  kind?: "bar" | "line" | "waterfall";
  nameKey?: "period" | "name";
}) {
  const normalized = data.map((item, index) => ({
    ...item,
    label: item[nameKey] ?? item.name ?? item.period ?? String(index + 1),
    fill: item.value < 0 ? red : [gold, green, copper][index % 3],
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          {kind === "line" ? (
            <LineChart data={normalized} margin={{ top: 8, right: 18, left: 0, bottom: 18 }}>
              <CartesianGrid stroke="#3f3a2f" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" />
              <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" tickFormatter={(value) => formatNumber(Number(value))} />
              <Tooltip contentStyle={{ background: "#171a20", border: "1px solid #5f5234", color: "#f0eadc" }} formatter={(value) => formatCurrency(Number(value))} />
              <Line type="monotone" dataKey="value" stroke={gold} strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          ) : kind === "waterfall" ? (
            <ComposedChart data={normalized} margin={{ top: 8, right: 18, left: 0, bottom: 18 }}>
              <CartesianGrid stroke="#3f3a2f" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" interval={0} angle={-20} textAnchor="end" height={64} />
              <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" tickFormatter={(value) => formatNumber(Number(value))} />
              <Tooltip contentStyle={{ background: "#171a20", border: "1px solid #5f5234", color: "#f0eadc" }} formatter={(value) => formatCurrency(Number(value))} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} animationDuration={900}>
                {normalized.map((item, index) => (
                  <Cell key={`${item.label}-${index}`} fill={item.fill} />
                ))}
              </Bar>
            </ComposedChart>
          ) : (
            <BarChart data={normalized} margin={{ top: 8, right: 18, left: 0, bottom: 18 }}>
              <CartesianGrid stroke="#3f3a2f" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" interval={0} angle={-15} textAnchor="end" height={48} />
              <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="#b5aa95" tickFormatter={(value) => formatNumber(Number(value))} />
              <Tooltip contentStyle={{ background: "#171a20", border: "1px solid #5f5234", color: "#f0eadc" }} formatter={(value) => formatCurrency(Number(value))} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} animationDuration={800}>
                {normalized.map((item, index) => (
                  <Cell key={`${item.label}-${index}`} fill={item.fill} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function flattenDrilldown(drilldown: ExecutiveDrilldown): DrilldownEntry[] {
  return drilldown.companies.flatMap((company) =>
    company.divisions.flatMap((division) =>
      division.cost_centers.flatMap((costCenter) =>
        costCenter.synthetic_accounts.flatMap((synthetic) =>
          synthetic.analytical_accounts.flatMap((account) =>
            account.entries.map((entry) => ({
              ...entry,
              description: [company.name, division.name, costCenter.name, synthetic.code, account.code, entry.description]
                .filter(Boolean)
                .join(" → "),
            })),
          ),
        ),
      ),
    ),
  );
}

function DrilldownPanel({ drilldown, entriesLimit }: { drilldown: ExecutiveDrilldown; entriesLimit: number }) {
  const [page, setPage] = useState(0);
  const [companyIndex, setCompanyIndex] = useState(0);
  const [divisionIndex, setDivisionIndex] = useState(0);
  const [costCenterIndex, setCostCenterIndex] = useState(0);
  const [syntheticIndex, setSyntheticIndex] = useState(0);
  const entries = useMemo(() => flattenDrilldown(drilldown), [drilldown]);
  const company = drilldown.companies[companyIndex];
  const division = company?.divisions[divisionIndex];
  const costCenter = division?.cost_centers[costCenterIndex];
  const synthetic = costCenter?.synthetic_accounts[syntheticIndex];
  const pageSize = 12;
  const pages = Math.max(1, Math.ceil(entries.length / pageSize));
  const visible = entries.slice(page * pageSize, page * pageSize + pageSize);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>Drill Down Executivo</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Empresa → Divisão → Centro de Custo → Conta Sintética → Conta Analítica → Lançamentos contábeis.
          </p>
        </div>
        <Badge>{entries.length} de {entriesLimit} lançamentos carregados</Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {[company?.name, division?.name, costCenter?.name, synthetic?.code, "Contas Analíticas", "Lançamentos"].filter(Boolean).map((label, index) => (
            <button key={`${label}-${index}`} className="rounded-full border border-primary/25 bg-accent/30 px-3 py-1 text-primary transition hover:bg-accent">
              {label}
            </button>
          ))}
        </div>
        <div className="grid gap-3 lg:grid-cols-4">
          <div className="rounded-lg border border-border/60 bg-background/25 p-3">
            <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Empresa</p>
            {drilldown.companies.map((item, index) => (
              <button key={item.name} onClick={() => { setCompanyIndex(index); setDivisionIndex(0); setCostCenterIndex(0); setSyntheticIndex(0); }} className={`mt-2 block w-full rounded-md px-3 py-2 text-left text-sm transition ${index === companyIndex ? "bg-primary/20 text-primary" : "hover:bg-accent/30"}`}>
                {item.name} <span className="text-xs text-muted-foreground">({item.divisions.length})</span>
              </button>
            ))}
          </div>
          <div className="rounded-lg border border-border/60 bg-background/25 p-3">
            <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Divisão</p>
            {company?.divisions.map((item, index) => (
              <button key={item.name} onClick={() => { setDivisionIndex(index); setCostCenterIndex(0); setSyntheticIndex(0); }} className={`mt-2 block w-full rounded-md px-3 py-2 text-left text-sm transition ${index === divisionIndex ? "bg-primary/20 text-primary" : "hover:bg-accent/30"}`}>
                {item.name} <span className="text-xs text-muted-foreground">({item.cost_centers.length})</span>
              </button>
            ))}
          </div>
          <div className="rounded-lg border border-border/60 bg-background/25 p-3">
            <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Centro de Custo</p>
            {division?.cost_centers.map((item, index) => (
              <button key={item.name} onClick={() => { setCostCenterIndex(index); setSyntheticIndex(0); }} className={`mt-2 block w-full rounded-md px-3 py-2 text-left text-sm transition ${index === costCenterIndex ? "bg-primary/20 text-primary" : "hover:bg-accent/30"}`}>
                {item.name} <span className="text-xs text-muted-foreground">({item.synthetic_accounts.length})</span>
              </button>
            ))}
          </div>
          <div className="rounded-lg border border-border/60 bg-background/25 p-3">
            <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Conta Sintética</p>
            {costCenter?.synthetic_accounts.map((item, index) => (
              <button key={item.code} onClick={() => setSyntheticIndex(index)} className={`mt-2 block w-full rounded-md px-3 py-2 text-left text-sm transition ${index === syntheticIndex ? "bg-primary/20 text-primary" : "hover:bg-accent/30"}`}>
                {item.code} <span className="text-xs text-muted-foreground">({item.analytical_accounts.length})</span>
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border/60">
          <table className="w-full min-w-[880px] text-sm">
            <thead className="bg-muted/70 text-xs uppercase tracking-[0.12em] text-muted-foreground">
              <tr>
                <th className="px-3 py-3 text-left">Data</th>
                <th className="px-3 py-3 text-left">Lançamento / Caminho</th>
                <th className="px-3 py-3 text-left">Tipo</th>
                <th className="px-3 py-3 text-right">Valor</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((entry) => (
                <tr key={entry.entry_id} className="border-t border-border/45">
                  <td className="px-3 py-3">{entry.date}</td>
                  <td className="px-3 py-3">
                    <p className="font-mono text-xs text-primary">{entry.entry_id}</p>
                    <p className="mt-1 text-muted-foreground">{entry.description}</p>
                  </td>
                  <td className="px-3 py-3">{entry.entry_type}</td>
                  <td className="px-3 py-3 text-right">{formatCurrency(entry.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" disabled={page === 0} onClick={() => setPage((current) => Math.max(0, current - 1))}>
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">Página {page + 1} de {pages}</span>
          <Button variant="outline" disabled={page + 1 >= pages} onClick={() => setPage((current) => Math.min(pages - 1, current + 1))}>
            Próxima
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function downloadExecutiveJson(data: Kpis) {
  const blob = new Blob([JSON.stringify({ generated_at: new Date().toISOString(), data }, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ardo-executive-analytics.json";
  link.click();
  URL.revokeObjectURL(url);
}

export function DashboardPage() {
  const { filters, controlMode } = useFinancialFilters();
  const queryClient = useQueryClient();
  const kpis = useQuery({
    queryKey: ["kpis", "executive"],
    queryFn: () => enterpriseApi.kpis(),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  });
  const history = useQuery({
    queryKey: ["pipeline-history", 10],
    queryFn: () => enterpriseApi.pipelineHistory(10),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  });

  if (kpis.isLoading || history.isLoading) return <LoadingGrid />;
  if (kpis.isError || !kpis.data) return <ErrorState message="Enterprise KPIs indisponíveis." onRetry={() => kpis.refetch()} />;

  const data = kpis.data.data;
  const executive = data.executive;
  const filterPeriod = (series: ChartPoint[]) => series.filter((item) =>
    (!filters.period || item.period === filters.period) && (!filters.year || item.period?.includes(filters.year)));
  const charts = {
    ...data.charts,
    receita_mensal: filterPeriod(data.charts.receita_mensal),
    ebitda_mensal: filterPeriod(data.charts.ebitda_mensal),
    evolucao_caixa: filterPeriod(data.charts.evolucao_caixa),
    receita_por_empresa: data.charts.receita_por_empresa.filter((item) => !filters.company || item.name === filters.company),
    receita_por_divisao: data.charts.receita_por_divisao.filter((item) => !filters.division || item.name === filters.division),
    receita_por_centro_custo: data.charts.receita_por_centro_custo.filter((item) => !filters.costCenter || item.name === filters.costCenter),
  };
  const filteredDrilldown: ExecutiveDrilldown = {
    companies: data.drilldown.companies.filter((company) => !filters.company || company.name === filters.company).map((company) => ({
      ...company,
      divisions: company.divisions.filter((division) => !filters.division || division.name === filters.division).map((division) => ({
        ...division,
        cost_centers: division.cost_centers.filter((center) => !filters.costCenter || center.name === filters.costCenter).map((center) => ({
          ...center,
          synthetic_accounts: center.synthetic_accounts.filter((synthetic) => !filters.syntheticAccount || synthetic.code === filters.syntheticAccount).map((synthetic) => ({
            ...synthetic,
            analytical_accounts: synthetic.analytical_accounts.filter((account) =>
              (!filters.analyticalAccount || account.code === filters.analyticalAccount)
              && (!filters.account || account.code === filters.account || account.name === filters.account)),
          })),
        })),
      })),
    })),
  };
  const revenueTrend = trendFromSeries(charts.receita_mensal);
  const ebitdaTrend = trendFromSeries(charts.ebitda_mensal);
  const waterfall = financialWaterfall(charts.waterfall_dre);
  const latestExecution = history.data?.data.executions[0] ?? null;
  const operationalRuns = listOperationalExecutions();
  const latestOperationalRun = operationalRuns[0] ?? null;
  const processingStatus = data.failed_executions > 0 ? "Requer atenção" : data.pipeline_executions > 0 ? "Operacional" : "Aguardando execução";
  const lastImportDate = latestOperationalRun?.date ?? latestExecution?.created_at ?? null;

  return (
    <div className="space-y-6">
      <section className="executive-panel overflow-hidden rounded-lg p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs uppercase tracking-[0.18em] text-primary">ARDO Financial Analytics Enterprise</p>
            <h2 className="mt-2 text-3xl font-semibold">Sprint Executive Analytics</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Dashboard executivo com dados reais persistidos nas facts autorizadas e no histórico de execução do pipeline.
            </p>
          </div>
          <Button variant="outline" onClick={() => downloadExecutiveJson(data)}>
            <Download className="h-4 w-4" />
            Baixar snapshot executivo
          </Button>
        </div>
      </section>
      {Object.values(filters).some(Boolean) ? (
        <Card className="border-primary/35">
          <CardContent className="p-4 text-sm">
            <strong>Recorte ativo:</strong> gráficos e drilldown exibem somente dados reais compatíveis com os filtros.
            Os totalizadores homologados da DRE não são recalculados no navegador.
          </CardContent>
        </Card>
      ) : null}

      {data.warnings.length > 0 ? (
        <Card className="border-primary/35">
          <CardContent className="space-y-2 p-4 text-sm text-muted-foreground">
            {data.warnings.map((warning) => (
              <p key={warning}>• {warning}</p>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Receita Bruta" value={formatCurrency(executive.receita_bruta)} trend={revenueTrend.label} trendPositive={revenueTrend.positive} icon={TrendingUp} />
        <MetricCard title="Receita Líquida" value={formatCurrency(executive.receita_liquida)} trend={revenueTrend.label} trendPositive={revenueTrend.positive} icon={Banknote} />
        <MetricCard title="EBITDA" value={formatCurrency(executive.ebitda)} trend={ebitdaTrend.label} trendPositive={ebitdaTrend.positive} icon={BarChart3} />
        <MetricCard title="Lucro Operacional" value={formatCurrency(executive.lucro_operacional)} subtitle="EBIT homologado" icon={Activity} />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Margem EBITDA" value={formatPercent(executive.margem_ebitda)} subtitle="Meta atingida quando positiva" icon={LineChartIcon} />
        <MetricCard title="Margem Operacional" value={formatPercent(executive.margem_operacional)} subtitle="Comparável ao EBIT" icon={ShieldCheck} />
        <MetricCard title="Caixa" value={formatCurrency(executive.caixa)} subtitle="Saldo disponível" icon={Database} />
        <MetricCard
          title="Forecast / Plan x Real"
          value={executive.forecast === null ? "Não disponível" : formatCurrency(executive.forecast)}
          subtitle={`Realizado: ${formatCurrency(executive.planejado_x_realizado.realizado)}`}
          icon={CalendarClock}
        />
      </section>

      <Card className="premium-card">
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ["Receita Bruta", formatCurrency(executive.receita_bruta)],
            ["Receita Líquida", formatCurrency(executive.receita_liquida)],
            ["EBITDA", formatCurrency(executive.ebitda)],
            ["EBIT", formatCurrency(executive.lucro_operacional)],
            ["Lucro Líquido", formatCurrency(waterfall.find((item) => item.name === "Lucro Líquido")?.value ?? null)],
            ["Caixa", formatCurrency(executive.caixa)],
            ["Margem EBITDA", formatPercent(executive.margem_ebitda)],
            ["Margem Operacional", formatPercent(executive.margem_operacional)],
            ["Maior empresa", topName(charts.receita_por_empresa)],
            ["Maior divisão", topName(charts.receita_por_divisao)],
            ["Maior centro de custo", topName(charts.receita_por_centro_custo)],
            ["Lançamentos", formatNumber(data.accounting_entries)],
            ["Última execução", data.latest_execution_id ?? "Não disponível"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-border/60 bg-background/25 p-3">
              <p className="text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
              <p className="mt-2 truncate font-semibold">{value}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Status Processamento" value={processingStatus} icon={RefreshCw} />
        <MetricCard title="Reconciliação" value={formatNumber(data.reconciliation_rows)} icon={ShieldCheck} />
        <MetricCard title="Última Importação" value={formatDate(lastImportDate)} icon={CalendarClock} />
        <MetricCard title="Execuções OK" value={formatNumber(data.successful_executions)} icon={CheckCircle2} />
      </section>

      {!controlMode ? <PipelineRunner
        onComplete={async () => {
          await queryClient.invalidateQueries({ queryKey: ["kpis"] });
          await queryClient.invalidateQueries({ queryKey: ["pipeline-history"] });
        }}
      /> : null}

      <section className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Receita mensal" data={charts.receita_mensal} kind="line" />
        <ChartCard title="EBITDA mensal" data={charts.ebitda_mensal} kind="line" />
        {!controlMode ? <><ChartCard title="Receita por empresa" data={charts.receita_por_empresa} nameKey="name" />
          <ChartCard title="Receita por divisão" data={charts.receita_por_divisao} nameKey="name" />
          <ChartCard title="Receita por centro de custo" data={charts.receita_por_centro_custo} nameKey="name" />
          <ChartCard title="Evolução do caixa" data={charts.evolucao_caixa} kind="line" /></> : null}
      </section>

      {!controlMode ? <ChartCard title="Waterfall financeiro" data={waterfall} kind="waterfall" nameKey="name" /> : null}

      <DrilldownPanel drilldown={filteredDrilldown} entriesLimit={data.pagination.entries_limit} />

      <Card>
        <CardHeader>
          <CardTitle>Última Execução</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-3 text-sm md:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">Execution ID</dt>
              <dd className="font-medium">{data.latest_execution_id ?? latestExecution?.id ?? "Nenhum registro encontrado"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium">{latestExecution?.status ?? latestOperationalRun?.status ?? "-"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Reconciliação</dt>
              <dd className="font-medium">{formatDecimal(data.reconciliation_rows)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
