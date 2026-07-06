import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Server, ShieldCheck } from "lucide-react";
import { ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export function SystemPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: () => enterpriseApi.health() });
  const version = useQuery({ queryKey: ["version"], queryFn: () => enterpriseApi.version() });

  if (health.isLoading || version.isLoading) return <LoadingGrid />;
  if (health.isError || version.isError || !health.data || !version.data) {
    return <ErrorState message="System status could not be loaded." onRetry={() => { health.refetch(); version.refetch(); }} />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5 text-emerald-700" /> API Health</CardTitle>
        </CardHeader>
        <CardContent>
          <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">{health.data.data.status}</Badge>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5 text-sky-700" /> Database</CardTitle>
        </CardHeader>
        <CardContent>
          <Badge className="border-sky-200 bg-sky-50 text-sky-700">{health.data.data.database}</Badge>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-amber-700" /> API Version</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p className="font-medium">{version.data.data.name}</p>
          <p className="text-muted-foreground">{version.data.data.version}</p>
          <p className="text-muted-foreground">{formatDate(version.data.data.generated_at)}</p>
        </CardContent>
      </Card>
    </div>
  );
}
