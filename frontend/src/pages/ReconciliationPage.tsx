import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, GitCompareArrows, Rows3, ShieldCheck } from "lucide-react";
import { ArtifactBarChart } from "@/components/charts/StatusCharts";
import { ErrorState, EmptyState, LoadingGrid } from "@/components/layout/PageState";
import { DataTable } from "@/components/tables/DataTable";
import { Card, CardContent } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import type { PipelineExecutionSummary } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/utils";

type ReconciliationRow = PipelineExecutionSummary & {
  reconciliation_rows?: number;
};

const columns: ColumnDef<ReconciliationRow>[] = [
  { accessorKey: "id", header: "Execution ID" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "duration_seconds", header: "Duration" },
  { accessorKey: "created_at", header: "Created", cell: ({ row }) => formatDate(row.original.created_at) },
];

export function ReconciliationPage() {
  const history = useQuery({ queryKey: ["reconciliation-history"], queryFn: () => enterpriseApi.pipelineHistory(50) });

  if (history.isLoading) return <LoadingGrid />;
  if (history.isError || !history.data) {
    return <ErrorState message="Reconciliation status could not be loaded." onRetry={() => history.refetch()} />;
  }

  const executions = history.data.data.executions;
  const successful = executions.filter((item) => item.success).length;
  const failed = executions.length - successful;
  const reconciled = executions.length === 0 ? 0 : successful / executions.length;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        {[
          ["Conciliação", `${Math.round(reconciled * 100)}%`, ShieldCheck],
          ["Status", failed === 0 ? "Conciliado" : "Diferenças", CheckCircle2],
          ["Diferenças", formatNumber(failed), GitCompareArrows],
          ["Linhas", formatNumber(executions.length), Rows3],
        ].map(([title, value, Icon]) => (
          <Card key={String(title)} className="premium-card">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">{String(title)}</p>
                <p className="mt-2 text-2xl font-semibold">{String(value)}</p>
              </div>
              <Icon className="h-8 w-8 text-primary" />
            </CardContent>
          </Card>
        ))}
      </section>
      <ArtifactBarChart
        values={[
          { name: "Executions", value: executions.length },
          { name: "Successful", value: executions.filter((item) => item.success).length },
          { name: "Failed", value: executions.filter((item) => !item.success).length },
        ]}
      />
      {executions.length === 0 ? (
        <EmptyState message="Nao ha execucoes persistidas disponiveis para revisao de conciliacao." />
      ) : (
        <DataTable columns={columns} data={executions} />
      )}
    </div>
  );
}
