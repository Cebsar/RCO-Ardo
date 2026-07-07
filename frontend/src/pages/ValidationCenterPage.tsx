import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Ban, ListChecks, RotateCcw, Sigma } from "lucide-react";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { listValidationIssues, type ValidationIssue } from "@/lib/operational";
import { formatDate, formatNumber } from "@/lib/utils";

const issueConfig = {
  warning: { label: "Warnings", icon: AlertTriangle, className: "border-amber-200 bg-amber-50 text-amber-800" },
  error: { label: "Errors", icon: Ban, className: "border-destructive/30 bg-destructive/10 text-destructive" },
  normalization: { label: "Normalization issues", icon: RotateCcw, className: "border-sky-200 bg-sky-50 text-sky-800" },
  accounting: { label: "Accounting inconsistencies", icon: Sigma, className: "border-violet-200 bg-violet-50 text-violet-800" },
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
                <div className="flex h-11 w-11 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
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
            <EmptyState title="No validation issues" message="No warnings, errors, normalization issues, or accounting inconsistencies are currently reported." />
          ) : (
            <div className="grid gap-3">
              {issues.map((issue) => (
                <div key={issue.id} className="rounded-lg border p-4">
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
