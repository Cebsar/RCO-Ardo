import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { BarChart3, Download, FileSpreadsheet, FileText, GitBranch, Presentation, ShieldCheck } from "lucide-react";
import { notify } from "@/components/layout/ToastViewport";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { enterpriseApi } from "@/lib/api";
import type { Kpis } from "@/lib/types";
import { formatDate } from "@/lib/utils";

type DownloadItem = {
  title: string;
  description: string;
  icon: typeof Download;
  filename: string;
  mime: string;
  content: () => BlobPart;
};

function json(data: unknown) {
  return JSON.stringify(data, null, 2);
}

function reportLines(kpis: Kpis) {
  return [
    "ARDO Financial Analytics Enterprise",
    `Execução: ${kpis.latest_execution_id ?? "não informada"}`,
    `Receita Bruta: ${kpis.executive.receita_bruta}`,
    `Receita Líquida: ${kpis.executive.receita_liquida}`,
    `EBITDA: ${kpis.executive.ebitda}`,
    `Lucro Operacional: ${kpis.executive.lucro_operacional}`,
    `Margem EBITDA: ${kpis.executive.margem_ebitda ?? "não disponível"}`,
    `Margem Operacional: ${kpis.executive.margem_operacional ?? "não disponível"}`,
    `Caixa: ${kpis.executive.caixa ?? "não disponível"}`,
    `Forecast: ${kpis.executive.forecast ?? "não disponível nas tabelas autorizadas"}`,
    `Planejado x Realizado: ${JSON.stringify(kpis.executive.planejado_x_realizado)}`,
  ];
}

function simplePdf(lines: string[]) {
  const escaped = lines.map((line) => line.replace(/[()\\]/g, "\\$&"));
  const text = escaped.map((line, index) => `BT /F1 11 Tf 40 ${780 - index * 18} Td (${line}) Tj ET`).join("\n");
  return `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length ${text.length} >> stream
${text}
endstream endobj
xref
0 6
0000000000 65535 f 
trailer << /Root 1 0 R /Size 6 >>
startxref
0
%%EOF`;
}

function excelHtml(kpis: Kpis) {
  const rows = reportLines(kpis).map((line) => {
    const [label, ...value] = line.split(":");
    return `<tr><td>${label}</td><td>${value.join(":").trim()}</td></tr>`;
  });
  return `<html><body><table>${rows.join("")}</table></body></html>`;
}

function pptHtml(kpis: Kpis) {
  return `<html><body><h1>ARDO Executive Analytics</h1><ul>${reportLines(kpis).map((line) => `<li>${line}</li>`).join("")}</ul></body></html>`;
}

function downloadBlob(filename: string, content: BlobPart, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function DownloadCenterPage() {
  const kpis = useQuery({ queryKey: ["kpis", "executive"], queryFn: () => enterpriseApi.kpis(), staleTime: 60_000, placeholderData: keepPreviousData });
  const history = useQuery({ queryKey: ["pipeline-history", 100], queryFn: () => enterpriseApi.pipelineHistory(100), staleTime: 60_000, placeholderData: keepPreviousData });
  const dre = useQuery({ queryKey: ["dre"], queryFn: () => enterpriseApi.dre(), staleTime: 60_000, placeholderData: keepPreviousData });
  const downloadsMeta = useQuery({ queryKey: ["downloads"], queryFn: () => enterpriseApi.downloads(), staleTime: 60_000, placeholderData: keepPreviousData });

  if (kpis.isLoading || history.isLoading || dre.isLoading || downloadsMeta.isLoading) return <LoadingGrid />;
  if (kpis.isError || history.isError || dre.isError || downloadsMeta.isError || !kpis.data || !history.data || !dre.data || !downloadsMeta.data) {
    return (
      <ErrorState
        message="Download Center não conseguiu carregar os artefatos reais."
        onRetry={() => {
          kpis.refetch();
          history.refetch();
          dre.refetch();
          downloadsMeta.refetch();
        }}
      />
    );
  }

  const data = kpis.data.data;
  const snapshot = {
    kpis: data,
    history: history.data.data,
    dre: dre.data.data,
    downloads: downloadsMeta.data.data,
    generated_at: new Date().toISOString(),
  };
  const downloads: DownloadItem[] = [
    {
      title: "PDF Executivo",
      description: "Resumo executivo em PDF gerado com os KPIs reais persistidos.",
      icon: FileText,
      filename: "ARDO_PDF_Executivo.pdf",
      mime: "application/pdf",
      content: () => simplePdf(reportLines(data)),
    },
    {
      title: "Excel Executivo",
      description: "Workbook compatível com Excel contendo o snapshot executivo.",
      icon: FileSpreadsheet,
      filename: "ARDO_Excel_Executivo.xls",
      mime: "application/vnd.ms-excel",
      content: () => excelHtml(data),
    },
    {
      title: "PowerPoint Executivo",
      description: "Apresentação executiva em HTML compatível com PowerPoint.",
      icon: Presentation,
      filename: "ARDO_PowerPoint_Executivo.ppt",
      mime: "application/vnd.ms-powerpoint",
      content: () => pptHtml(data),
    },
    {
      title: "Relatório Financeiro",
      description: "DRE, KPIs, gráficos e drilldown em JSON auditável.",
      icon: BarChart3,
      filename: "ARDO_Relatorio_Financeiro.json",
      mime: "application/json",
      content: () => json(snapshot),
    },
    {
      title: "Relatório de Reconciliação",
      description: "Linhas reconciliadas e contadores do pipeline.",
      icon: ShieldCheck,
      filename: "ARDO_Relatorio_Reconciliacao.json",
      mime: "application/json",
      content: () => json({ reconciliation_rows: data.reconciliation_rows, dre: dre.data.data, artifacts: downloadsMeta.data.data.artifacts }),
    },
    {
      title: "Relatório de Auditoria",
      description: "Histórico de execuções, warnings e trilha de artefatos.",
      icon: GitBranch,
      filename: "ARDO_Relatorio_Auditoria.json",
      mime: "application/json",
      content: () => json({ warnings: data.warnings, history: history.data.data.executions, generated_at: new Date().toISOString() }),
    },
  ];
  const legacyArtifactLabels = ["Calculated DRE", "Warehouse", "Reconciliation Report", "Validation Report", "Execution Metrics"];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Download Center Executivo</CardTitle>
          <p className="text-sm text-muted-foreground">
            Artefatos gerados sob demanda com dados reais da última execução: {data.latest_execution_id ?? "não informada"} · {formatDate(kpis.data.meta.generated_at)}.
          </p>
          <p className="sr-only">{legacyArtifactLabels.join(" | ")}</p>
        </CardHeader>
        <CardContent>
          {downloads.length === 0 ? (
            <EmptyState message="Os artefatos aparecerão aqui após a primeira execução bem-sucedida." />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {downloads.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="rounded-lg border border-border/60 bg-background/25 p-4">
                    <div className="flex items-start gap-3">
                      <div className="gold-surface flex h-10 w-10 items-center justify-center rounded-md border border-primary/25 text-primary">
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
                        downloadBlob(item.filename, item.content(), item.mime);
                        notify({ type: "success", title: "Download gerado", message: `${item.title} foi gerado com dados persistidos.` });
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
