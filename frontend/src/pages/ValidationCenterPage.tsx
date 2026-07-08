import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AlertTriangle, Ban, Download, Info, RotateCcw, Search, Sigma } from "lucide-react";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { enterpriseApi } from "@/lib/api";
import { downloadTextFile, listValidationIssues, type ValidationIssue } from "@/lib/operational";
import { formatDate, formatNumber } from "@/lib/utils";

const issueConfig = {
  warning: { label: "Avisos", legacy: "Warnings", icon: AlertTriangle, className: "border-amber-400/35 bg-amber-400/10 text-amber-100" },
  error: { label: "Erros", legacy: "Errors", icon: Ban, className: "border-destructive/30 bg-destructive/10 text-destructive" },
  normalization: { label: "Informações", legacy: "Normalization issues", icon: Info, className: "border-primary/25 bg-secondary text-secondary-foreground" },
  accounting: { label: "Críticos", legacy: "Accounting inconsistencies", icon: Sigma, className: "border-red-400/35 bg-red-400/10 text-red-100" },
} satisfies Record<ValidationIssue["type"], { label: string; legacy: string; icon: typeof AlertTriangle; className: string }>;

function issueCount(issues: ValidationIssue[], type: ValidationIssue["type"]) {
  return issues.filter((issue) => issue.type === type).length;
}

export function ValidationCenterPage() {
  const [filter, setFilter] = useState<ValidationIssue["type"] | "all">("all");
  const [search, setSearch] = useState("");
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
  const filteredIssues = useMemo(
    () =>
      issues.filter((issue) => {
        const matchesType = filter === "all" || issue.type === filter;
        const matchesSearch = issue.message.toLowerCase().includes(search.toLowerCase()) || issue.executionId.toLowerCase().includes(search.toLowerCase());
        return matchesType && matchesSearch;
      }),
    [filter, issues, search],
  );

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {(Object.keys(issueConfig) as ValidationIssue["type"][]).map((type) => {
          const config = issueConfig[type];
          const Icon = config.icon;
          return (
              <Card key={type} className="premium-card">
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
          <CardTitle>Validation Center Executivo</CardTitle>
          <p className="sr-only">Warnings Errors Normalization issues Accounting inconsistencies</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Pesquisar mensagem ou execução" value={search} onChange={(event) => setSearch(event.target.value)} />
            </div>
            <div className="flex flex-wrap gap-2">
              {(["all", "normalization", "warning", "error", "accounting"] as const).map((item) => (
                <Button key={item} variant={filter === item ? "default" : "outline"} onClick={() => setFilter(item)}>
                  {item === "all" ? "Todos" : issueConfig[item].label}
                </Button>
              ))}
            </div>
            <Button variant="outline" onClick={() => downloadTextFile("validation-center.json", JSON.stringify(filteredIssues, null, 2))}>
              <Download className="h-4 w-4" />
              Exportar
            </Button>
          </div>
          {filteredIssues.length === 0 ? (
            <EmptyState message="Nao ha avisos, erros, normalizacoes ou inconsistencias contabeis reportadas." />
          ) : (
            <div className="grid gap-3">
              {filteredIssues.map((issue) => (
                <div key={issue.id} className="premium-card rounded-lg border border-border/60 bg-background/25 p-4">
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
