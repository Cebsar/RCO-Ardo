import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { DataTable } from "@/components/tables/DataTable";
import { ErrorState, LoadingGrid, EmptyState } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { listOperationalExecutions } from "@/lib/operational";
import type { PipelineExecutionDetail, PipelineExecutionSummary } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/utils";

type HistoryRow = {
  id: string;
  date: string | null;
  user: string;
  durationSeconds: number;
  workbookSha256: string;
  rowsProcessed: number;
  rowsIgnored: number;
  status: string;
  source: "API" | "Dashboard";
  apiExecution?: PipelineExecutionSummary;
};

const columns: ColumnDef<HistoryRow>[] = [
  { accessorKey: "id", header: "Execution ID" },
  { accessorKey: "date", header: "Date", cell: ({ row }) => formatDate(row.original.date) },
  { accessorKey: "user", header: "User" },
  { accessorKey: "durationSeconds", header: "Duration", cell: ({ row }) => `${row.original.durationSeconds.toFixed(1)}s` },
  {
    accessorKey: "workbookSha256",
    header: "Workbook SHA256",
    cell: ({ row }) => <span className="block max-w-[180px] truncate font-mono text-xs">{row.original.workbookSha256}</span>,
  },
  { accessorKey: "rowsProcessed", header: "Rows processed", cell: ({ row }) => formatNumber(row.original.rowsProcessed) },
  { accessorKey: "rowsIgnored", header: "Rows ignored", cell: ({ row }) => formatNumber(row.original.rowsIgnored) },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <Badge>{row.original.status}</Badge>,
  },
];

function apiRow(execution: PipelineExecutionSummary, detail?: PipelineExecutionDetail): HistoryRow {
  return {
    id: execution.id,
    date: execution.created_at,
    user: "api-service",
    durationSeconds: execution.duration_seconds,
    workbookSha256: typeof detail?.metadata?.workbook_sha256 === "string" ? detail.metadata.workbook_sha256 : "Not available",
    rowsProcessed: (detail?.accounting_entries ?? 0) + (detail?.dre_nodes ?? 0) + (detail?.reconciliation_rows ?? 0),
    rowsIgnored: Array.isArray(detail?.errors) ? detail.errors.length : 0,
    status: execution.status,
    source: "API",
    apiExecution: execution,
  };
}

export function PipelinePage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const history = useQuery({ queryKey: ["pipeline-history"], queryFn: () => enterpriseApi.pipelineHistory(100) });
  const detail = useQuery({
    queryKey: ["pipeline-detail", selectedId],
    queryFn: () => enterpriseApi.pipelineExecution(selectedId as string),
    enabled: Boolean(selectedId) && !selectedId?.startsWith("op-"),
  });

  if (history.isLoading) return <LoadingGrid />;
  if (history.isError || !history.data) return <ErrorState message="Pipeline history could not be loaded." onRetry={() => history.refetch()} />;

  const executions = history.data.data.executions;
  const operationalRows: HistoryRow[] = listOperationalExecutions().map((execution) => ({
    id: execution.id,
    date: execution.date,
    user: execution.user,
    durationSeconds: execution.durationSeconds,
    workbookSha256: execution.workbookSha256,
    rowsProcessed: execution.rowsProcessed,
    rowsIgnored: execution.rowsIgnored,
    status: execution.status,
    source: "Dashboard",
  }));
  const rows = [...operationalRows, ...executions.map((execution) => apiRow(execution))];
  const selectedRow = rows.find((row) => row.id === selectedId);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.6fr)]">
      <section>
        {rows.length === 0 ? (
          <EmptyState message="Execute o pipeline contabil para iniciar o historico operacional." />
        ) : (
          <DataTable columns={columns} data={rows} onRowClick={(row) => setSelectedId(row.id)} />
        )}
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Execution Detail</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {!selectedId ? <p className="text-muted-foreground">Selecione uma execucao para inspecionar os totais operacionais.</p> : null}
          {detail.isLoading ? <p className="text-muted-foreground">Loading execution...</p> : null}
          {selectedRow ? (
            <>
              <p className="font-medium">{selectedRow.id}</p>
              <p>Source: {selectedRow.source}</p>
              <p>Rows processed: {formatNumber(selectedRow.rowsProcessed)}</p>
              <p>Rows ignored: {formatNumber(selectedRow.rowsIgnored)}</p>
            </>
          ) : null}
          {detail.data ? (
            <>
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
