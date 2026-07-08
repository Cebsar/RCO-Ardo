import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Ban, ListChecks, RotateCcw, Sigma } from "lucide-react";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { listValidationIssues, type ValidationIssue } from "@/lib/operational";
import { formatDate, formatNumber } from "@/lib/utils";

const issueConfig = {
  warning: { label: "Warnings", icon: AlertTriangle, className: "border-primary/35 bg-accent/70 text-accent-foreground" },
  error: { label: "Errors", icon: Ban, className: "border-destructive/30 bg-destructive/10 text-destructive" },
  normalization: { label: "Normalization issues", icon: RotateCcw, className: "border-primary/25 bg-secondary text-secondary-foreground" },
  accounting: { label: "Accounting inconsistencies", icon: Sigma, className: "border-primary/25 bg-secondary text-secondary-foreground" },
} satisfies Record<ValidationIssue["type"], { label: string; icon: typeof AlertTriangle; className: string }>;

function issueCount(issues: ValidationIssue[], type: ValidationIssue["type"]) {
  return issues.filter((issue) => issue.type === type).length;
}

export function ValidationCenterPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: () => enterpriseApi.kpis() });

  if (kpis.isLoading) return <LoadingGrid />;
  if (kpis.isError || !kpis.data) return <ErrorState message="Validation signals could not be loaded." onRetry={() => kpis.refetch()} />;

  const apiWarnings: ValidationIssue[] = kpis.data.data.warnings.map((message, index) => ({
    id: `api-warning-${index}`,
    executionId: kpis.data.data.latest_execution_id ?? "latest",
    type: "warning",
    message,
    createdAt: kpis.data.meta.generated_at,
  }));
  const issues = [...apiWarnings, ...listValidationIssues()];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {(Object.keys(issueConfig) as ValidationIssue["type"][]).map((type) => {
          const config = issueConfig[type];
          const Icon = config.icon;
          return (
            <Card key={type}>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">{config.label}</p>
                  <p className="mt-2 text-2xl font-semibold">{formatNumber(issueCount(issues, type))}</p>
                </div>
                <div className="gold-surface flex h-11 w-11 items-center justify-center rounded-md border border-primary/25 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Validation Center</CardTitle>
        </CardHeader>
        <CardContent>
          {issues.length === 0 ? (
            <EmptyState message="Nao ha avisos, erros, normalizacoes ou inconsistencias contabeis reportadas." />
          ) : (
            <div className="grid gap-3">
              {issues.map((issue) => (
                <div key={issue.id} className="rounded-lg border border-border/60 bg-background/25 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Badge className={issueConfig[issue.type].className}>{issueConfig[issue.type].label}</Badge>
                    <span className="text-xs text-muted-foreground">{formatDate(issue.createdAt)}</span>
                  </div>
                  <p className="mt-3 text-sm font-medium">{issue.message}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Execution: {issue.executionId}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
