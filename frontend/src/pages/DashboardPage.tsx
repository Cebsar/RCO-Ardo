import { useQuery } from "@tanstack/react-query";
import { Activity, Clock, Database, GitBranch } from "lucide-react";
import { ArtifactBarChart, PipelineStatusChart } from "@/components/charts/StatusCharts";
import { LoadingGrid, ErrorState } from "@/components/layout/PageState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

function MetricCard({ title, value, icon: Icon }: { title: string; value: string; icon: typeof Activity }) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: () => enterpriseApi.kpis() });

  if (kpis.isLoading) return <LoadingGrid />;
  if (kpis.isError || !kpis.data) return <ErrorState message="Enterprise KPIs unavailable." onRetry={() => kpis.refetch()} />;

  const data = kpis.data.data;
  const artifacts = [
    { name: "Accounting", value: data.accounting_entries },
    { name: "DRE", value: data.dre_nodes },
    { name: "Recon", value: data.reconciliation_rows },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Executions" value={formatNumber(data.pipeline_executions)} icon={GitBranch} />
        <MetricCard title="Accounting Entries" value={formatNumber(data.accounting_entries)} icon={Database} />
        <MetricCard title="DRE Nodes" value={formatNumber(data.dre_nodes)} icon={Activity} />
        <MetricCard title="Average Duration" value={`${data.average_duration_seconds.toFixed(2)}s`} icon={Clock} />
      </section>
      <section className="grid gap-4 xl:grid-cols-2">
        <PipelineStatusChart kpis={data} />
        <ArtifactBarChart values={artifacts} />
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Latest Execution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {data.latest_execution_id ?? "No persisted execution has been published yet."}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
