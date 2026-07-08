import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, CalendarClock, CheckCircle2, Clock, Database, GitBranch, RefreshCw, ShieldCheck } from "lucide-react";
import { ArtifactBarChart, PipelineStatusChart } from "@/components/charts/StatusCharts";
import { ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { PipelineRunner } from "@/components/operational/PipelineRunner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { listOperationalExecutions } from "@/lib/operational";
import { formatDate, formatNumber } from "@/lib/utils";

function MetricCard({ title, value, icon: Icon }: { title: string; value: string; icon: typeof Activity }) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="relative flex items-center justify-between p-5">
        <div className="absolute inset-x-0 top-0 h-1 bg-primary/80" />
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">{title}</p>
          <p className="mt-3 truncate text-3xl font-semibold text-foreground">{value}</p>
        </div>
        <div className="gold-surface flex h-12 w-12 shrink-0 items-center justify-center rounded-md border border-primary/25 text-primary">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const queryClient = useQueryClient();
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: () => enterpriseApi.kpis() });
  const history = useQuery({ queryKey: ["pipeline-history"], queryFn: () => enterpriseApi.pipelineHistory(10) });

  if (kpis.isLoading || history.isLoading) return <LoadingGrid />;
  if (kpis.isError || !kpis.data) return <ErrorState message="Enterprise KPIs unavailable." onRetry={() => kpis.refetch()} />;

  const data = kpis.data.data;
  const latestExecution = history.data?.data.executions[0] ?? null;
  const operationalRuns = listOperationalExecutions();
  const latestOperationalRun = operationalRuns[0] ?? null;
  const artifacts = [
    { name: "Accounting", value: data.accounting_entries },
    { name: "DRE", value: data.dre_nodes },
    { name: "Recon", value: data.reconciliation_rows },
  ];
  const processingStatus = data.failed_executions > 0 ? "Needs attention" : data.pipeline_executions > 0 ? "Operational" : "Waiting for first run";
  const lastImportDate = latestOperationalRun?.date ?? latestExecution?.created_at ?? null;

  return (
    <div className="space-y-6">
      <section className="executive-panel overflow-hidden rounded-lg p-6">
        <div className="max-w-3xl">
          <p className="text-xs uppercase tracking-[0.18em] text-primary">ARDO Enterprise</p>
          <h2 className="mt-2 text-3xl font-semibold">Executive Command Center</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Visao operacional baseada exclusivamente nos dados vivos retornados pela API local.
          </p>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Executions" value={formatNumber(data.pipeline_executions)} icon={GitBranch} />
        <MetricCard title="Accounting Entries" value={formatNumber(data.accounting_entries)} icon={Database} />
        <MetricCard title="DRE Nodes" value={formatNumber(data.dre_nodes)} icon={Activity} />
        <MetricCard title="Average Duration" value={`${data.average_duration_seconds.toFixed(2)}s`} icon={Clock} />
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Processing Status" value={processingStatus} icon={RefreshCw} />
        <MetricCard title="Last Reconciliation" value={formatNumber(data.reconciliation_rows)} icon={ShieldCheck} />
        <MetricCard title="Last Import Date" value={formatDate(lastImportDate)} icon={CalendarClock} />
        <MetricCard title="Successful Runs" value={formatNumber(data.successful_executions)} icon={CheckCircle2} />
      </section>
      <PipelineRunner
        onComplete={async () => {
          await queryClient.invalidateQueries({ queryKey: ["kpis"] });
          await queryClient.invalidateQueries({ queryKey: ["pipeline-history"] });
        }}
      />
      <section className="grid gap-4 xl:grid-cols-2">
        <PipelineStatusChart kpis={data} />
        <ArtifactBarChart values={artifacts} />
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Latest Execution</CardTitle>
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
              <dt className="text-muted-foreground">Workbook SHA256</dt>
              <dd className="truncate font-mono text-xs">{latestOperationalRun?.workbookSha256 ?? "Nenhum registro encontrado"}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
