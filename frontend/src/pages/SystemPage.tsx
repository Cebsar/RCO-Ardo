import { useQuery } from "@tanstack/react-query";
import { Activity, Cpu, Database, GitBranch, HardDrive, Server, ShieldCheck, UploadCloud } from "lucide-react";
import { ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/utils";

function StatusCard({ title, value, detail, icon: Icon }: { title: string; value: string; detail?: string; icon: typeof Server }) {
  return (
    <Card className="premium-card">
      <CardContent className="flex items-center justify-between gap-4 p-5">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">{title}</p>
          <div className="mt-2 flex items-center gap-2">
            <Badge>{value}</Badge>
          </div>
          {detail ? <p className="mt-2 text-xs text-muted-foreground">{detail}</p> : null}
        </div>
        <Icon className="h-8 w-8 text-primary" />
      </CardContent>
    </Card>
  );
}

export function SystemPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: () => enterpriseApi.health(), staleTime: 60_000 });
  const version = useQuery({ queryKey: ["version"], queryFn: () => enterpriseApi.version(), staleTime: 60_000 });
  const kpis = useQuery({ queryKey: ["kpis", "executive"], queryFn: () => enterpriseApi.kpis(), staleTime: 60_000 });

  if (health.isLoading || version.isLoading || kpis.isLoading) return <LoadingGrid />;
  if (health.isError || version.isError || kpis.isError || !health.data || !version.data || !kpis.data) {
    return <ErrorState message="System status could not be loaded." onRetry={() => { health.refetch(); version.refetch(); kpis.refetch(); }} />;
  }

  const usedHeap = (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize;
  const memory = usedHeap ? `${Math.round(usedHeap / 1024 / 1024)} MB` : "N/D";
  const cpu = navigator.hardwareConcurrency ? `${navigator.hardwareConcurrency} threads` : "N/D";

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatusCard title="API" value="ONLINE" detail={health.data.data.status} icon={Server} />
        <StatusCard title="Banco" value="ONLINE" detail={health.data.data.database} icon={Database} />
        <StatusCard title="Pipeline" value="ONLINE" detail={`${formatNumber(kpis.data.data.pipeline_executions)} execuções`} icon={GitBranch} />
        <StatusCard title="ETL" value="ONLINE" detail="Sem alteração de core" icon={UploadCloud} />
        <StatusCard title="Memória utilizada" value={memory} icon={HardDrive} />
        <StatusCard title="CPU" value={cpu} icon={Cpu} />
        <StatusCard title="Versão" value={version.data.data.version} detail={version.data.data.name} icon={ShieldCheck} />
        <StatusCard title="Última execução" value={kpis.data.data.latest_execution_id ? "OK" : "N/D"} detail={kpis.data.data.latest_execution_id ?? "Não disponível"} icon={Activity} />
      </section>
      <Card className="premium-card">
        <CardHeader>
          <CardTitle>Painel Técnico</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm md:grid-cols-3">
          <div><p className="text-muted-foreground">Último deploy</p><p className="font-medium">{formatDate(version.data.data.generated_at)}</p></div>
          <div><p className="text-muted-foreground">Último backup</p><p className="font-medium">Sob demanda no Download Center</p></div>
          <div><p className="text-muted-foreground">Última geração API</p><p className="font-medium">{formatDate(kpis.data.meta.generated_at)}</p></div>
        </CardContent>
      </Card>
    </div>
  );
}
