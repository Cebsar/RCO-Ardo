import { useQuery } from "@tanstack/react-query";
import { BarChart3, Database, Download, FileWarning, GitBranch, ShieldCheck } from "lucide-react";
import { notify } from "@/components/layout/ToastViewport";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { downloadTextFile, listOperationalExecutions, listValidationIssues } from "@/lib/operational";

type DownloadItem = {
  title: string;
  description: string;
  icon: typeof Download;
  filename: string;
  content: () => string;
};

function json(data: unknown) {
  return JSON.stringify(data, null, 2);
}

export function DownloadCenterPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: () => enterpriseApi.kpis() });
  const history = useQuery({ queryKey: ["pipeline-history"], queryFn: () => enterpriseApi.pipelineHistory(100) });
  const dre = useQuery({ queryKey: ["dre"], queryFn: () => enterpriseApi.dre() });

  if (kpis.isLoading || history.isLoading || dre.isLoading) return <LoadingGrid />;
  if (kpis.isError || history.isError || dre.isError || !kpis.data || !history.data || !dre.data) {
    return <ErrorState message="Download Center could not load operational artifacts." onRetry={() => { kpis.refetch(); history.refetch(); dre.refetch(); }} />;
  }

  const executions = listOperationalExecutions();
  const validationIssues = listValidationIssues();
  const downloads: DownloadItem[] = [
    {
      title: "Calculated DRE",
      description: "Latest calculated DRE tree returned by the financial API.",
      icon: BarChart3,
      filename: "calculated-dre.json",
      content: () => json(dre.data),
    },
    {
      title: "Warehouse",
      description: "Operational warehouse summary from KPIs and execution history.",
      icon: Database,
      filename: "warehouse-summary.json",
      content: () => json({ kpis: kpis.data, history: history.data }),
    },
    {
      title: "Reconciliation Report",
      description: "Latest reconciliation status and execution counters.",
      icon: ShieldCheck,
      filename: "reconciliation-report.json",
      content: () => json({ reconciliation_rows: kpis.data.data.reconciliation_rows, executions: history.data.data.executions }),
    },
    {
      title: "Validation Report",
      description: "Warnings, errors, normalization issues, and accounting inconsistencies.",
      icon: FileWarning,
      filename: "validation-report.json",
      content: () => json({ api_warnings: kpis.data.data.warnings, validation_issues: validationIssues }),
    },
    {
      title: "Execution Metrics",
      description: "Dashboard execution records with duration, SHA256, rows processed, and ignored rows.",
      icon: GitBranch,
      filename: "execution-metrics.json",
      content: () => json({ api_history: history.data.data.executions, dashboard_runs: executions }),
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Download Center</CardTitle>
        </CardHeader>
        <CardContent>
          {downloads.length === 0 ? (
            <EmptyState title="No downloads available" message="Operational artifacts will appear here after the first successful execution." />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {downloads.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="rounded-lg border p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold">{item.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                      </div>
                    </div>
                    <Button
                      className="mt-4 w-full"
                      variant="outline"
                      onClick={() => {
                        downloadTextFile(item.filename, item.content());
                        notify({ type: "success", title: "Download prepared", message: `${item.title} was generated from current operational data.` });
                      }}
                    >
                      <Download className="h-4 w-4" />
                      Download
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
