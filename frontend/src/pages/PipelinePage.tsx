import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { DataTable } from "@/components/tables/DataTable";
import { ErrorState, LoadingGrid, EmptyState } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import type { PipelineExecutionSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const columns: ColumnDef<PipelineExecutionSummary>[] = [
  { accessorKey: "id", header: "Execution ID" },
  { accessorKey: "pipeline_name", header: "Pipeline" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <Badge className="bg-secondary text-secondary-foreground">{row.original.status}</Badge>,
  },
  { accessorKey: "duration_seconds", header: "Duration" },
  { accessorKey: "created_at", header: "Created", cell: ({ row }) => formatDate(row.original.created_at) },
];

export function PipelinePage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const history = useQuery({ queryKey: ["pipeline-history"], queryFn: () => enterpriseApi.pipelineHistory(100) });
  const detail = useQuery({
    queryKey: ["pipeline-detail", selectedId],
    queryFn: () => enterpriseApi.pipelineExecution(selectedId as string),
    enabled: Boolean(selectedId),
  });

  if (history.isLoading) return <LoadingGrid />;
  if (history.isError || !history.data) return <ErrorState message="Pipeline history could not be loaded." onRetry={() => history.refetch()} />;

  const executions = history.data.data.executions;

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.6fr)]">
      <section>
        {executions.length === 0 ? (
          <EmptyState title="No pipeline executions" message="No persisted pipeline history is available." />
        ) : (
          <DataTable columns={columns} data={executions} onRowClick={(row) => setSelectedId(row.id)} />
        )}
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Execution Detail</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {!selectedId ? <p className="text-muted-foreground">Select a pipeline execution to inspect persisted counts.</p> : null}
          {detail.isLoading ? <p className="text-muted-foreground">Loading execution...</p> : null}
          {detail.data ? (
            <>
              <p className="font-medium">{detail.data.data.execution.id}</p>
              <p>Accounting entries: {detail.data.data.execution.accounting_entries}</p>
              <p>DRE nodes: {detail.data.data.execution.dre_nodes}</p>
              <p>Reconciliation rows: {detail.data.data.execution.reconciliation_rows}</p>
              <p>Metrics rows: {detail.data.data.execution.metrics_rows}</p>
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
