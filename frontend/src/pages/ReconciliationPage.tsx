import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { ArtifactBarChart } from "@/components/charts/StatusCharts";
import { ErrorState, EmptyState, LoadingGrid } from "@/components/layout/PageState";
import { DataTable } from "@/components/tables/DataTable";
import { enterpriseApi } from "@/lib/api";
import type { PipelineExecutionSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

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

  return (
    <div className="space-y-6">
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
