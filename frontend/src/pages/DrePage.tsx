import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, ChevronRight, Download, FileSearch, FileSpreadsheet, FileText } from "lucide-react";
import { useMemo, useState, type UIEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingGrid } from "@/components/layout/PageState";
import { enterpriseApi } from "@/lib/api";
import { entryMatchesFilters, useFinancialFilters } from "@/lib/financialFilters";
import type { ChartPoint, DreRow, DrilldownEntry, Kpis } from "@/lib/types";

const months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const rowHeight = 44;
const viewportRows = 18;
const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const cleanName = (name: string) => {
  const key = normalize(name);
  const labels: Record<string, string> = {
    "devolucoes/cancelamentos": "(-) Deduções",
    "receita liquida": "Receita Líquida",
    "margem de contribuicao (lucro bruto)": "Lucro Bruto",
    "custos e despesas indiretos - sga": "(-) Despesas Operacionais",
    "depreciacao": "(-) Depreciação / Amortização",
    "lucro operacional (ebit)": "EBIT",
    "receitas e despesas financeiras": "(+/-) Resultado Financeiro",
    "lucro antes do imp.renda e cssl": "Resultado Antes IR",
    "irpj e csll": "(-) IRPJ / CSLL",
    "lucro liquido": "Lucro Líquido",
  };
  return labels[key] ?? name;
};

const formatMoney = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "—";
  const formatted = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Math.abs(value));
  return value < 0 ? `(${formatted})` : formatted;
};
const formatPercent = (value: number | null | undefined) =>
  value === null || value === undefined ? "—" : new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2 }).format(value);
const isNetIncome = (name: string) => normalize(cleanName(name)) === "lucro liquido";
const isResult = (name: string) => ["lucro bruto", "ebitda", "ebit", "resultado antes ir"].includes(normalize(cleanName(name)));
const isExpense = (name: string) => /custo|despesa|dedu|deprecia|amortiza|irpj|csll/i.test(normalize(cleanName(name)));
const isSubtotal = (row: DreRow) => row.level <= 1 || /receita|lucro|resultado|ebit/i.test(normalize(cleanName(row.node_name)));

type LedgerRow = DrilldownEntry & {
  company: string; division: string; costCenter: string; synthetic: string; analytical: string; accountName: string;
};

function ledgerRows(data: Kpis): LedgerRow[] {
  return data.drilldown.companies.flatMap((company) => company.divisions.flatMap((division) =>
    division.cost_centers.flatMap((costCenter) => costCenter.synthetic_accounts.flatMap((synthetic) =>
      synthetic.analytical_accounts.flatMap((analytical) => analytical.entries.map((entry) => ({
        ...entry, company: company.name, division: division.name, costCenter: costCenter.name,
        synthetic: synthetic.code, analytical: analytical.code, accountName: analytical.name,
      })))))));
}

function periodMonth(period?: string) {
  const digits = period?.replace(/\D/g, "") ?? "";
  return digits.length >= 2 ? Number(digits.slice(-2)) - 1 : -1;
}

function monthlySeries(row: DreRow, data: Kpis): ChartPoint[] {
  const name = normalize(cleanName(row.node_name));
  if (name === "receita liquida") return data.charts.receita_mensal;
  if (name === "ebitda") return data.charts.ebitda_mensal;
  return [];
}

function downloadBlob(filename: string, content: BlobPart, mime: string) {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function excelContent(rows: DreRow[], data: Kpis) {
  const header = ["Descrição", ...months, "YTD"];
  const body = rows.map((row) => {
    const series = monthlySeries(row, data);
    const values = months.map((_, index) => series.find((point) => periodMonth(point.period) === index)?.value ?? "");
    return [cleanName(row.node_name), ...values, row.amount ?? ""];
  });
  return `<html><meta charset="utf-8"><body><table>${[header, ...body].map((line) =>
    `<tr>${line.map((cell) => `<td>${String(cell)}</td>`).join("")}</tr>`).join("")}</table></body></html>`;
}

function pdfContent(rows: DreRow[]) {
  const lines = ["ARDO — DRE Gerencial Overview RCO", ...rows.map((row) =>
    `${"  ".repeat(Math.max(0, row.level - 1))}${cleanName(row.node_name)}  ${formatMoney(Number(row.amount ?? 0))}`)];
  const escaped = lines.slice(0, 42).map((line) => line.replace(/[()\\]/g, "\\$&"));
  const text = escaped.map((line, index) => `BT /F1 9 Tf 36 ${806 - index * 18} Td (${line}) Tj ET`).join("\n");
  return `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length ${text.length} >> stream
${text}
endstream endobj
trailer << /Root 1 0 R /Size 6 >>
%%EOF`;
}

export function DrePage() {
  const { filters, controlMode } = useFinancialFilters();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<DreRow | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const dre = useQuery({
    queryKey: ["dre", "overview", filters.company, filters.period],
    queryFn: () => enterpriseApi.dre(filters.company || undefined, filters.period || undefined),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  });
  const kpis = useQuery({ queryKey: ["kpis", "executive"], queryFn: enterpriseApi.kpis, staleTime: 60_000, placeholderData: keepPreviousData });

  const nodes = useMemo(() => {
    const all = dre.data?.data.nodes ?? [];
    const children = new Map<string | null, DreRow[]>();
    all.forEach((row) => children.set(row.parent_node_code, [...(children.get(row.parent_node_code) ?? []), row]));
    children.forEach((items) => items.sort((a, b) => a.ordinal - b.ordinal || a.node_name.localeCompare(b.node_name, "pt-BR")));
    const ordered: DreRow[] = [];
    const walk = (parent: string | null) => (children.get(parent) ?? []).forEach((row) => {
      ordered.push(row);
      walk(row.node_code);
    });
    walk(null);
    return ordered.filter((row) => {
      const searchable = normalize(`${row.node_code} ${row.node_name} ${JSON.stringify(row.payload)}`);
      return (!filters.account || searchable.includes(normalize(filters.account)))
        && (!filters.syntheticAccount || searchable.includes(normalize(filters.syntheticAccount)))
        && (!filters.analyticalAccount || searchable.includes(normalize(filters.analyticalAccount)));
    });
  }, [dre.data, filters.account, filters.syntheticAccount, filters.analyticalAccount]);

  const nodeByCode = useMemo(() => new Map(nodes.map((node) => [node.node_code, node])), [nodes]);
  const childrenByParent = useMemo(() => {
    const map = new Map<string, DreRow[]>();
    nodes.forEach((node) => {
      if (!node.parent_node_code) return;
      map.set(node.parent_node_code, [...(map.get(node.parent_node_code) ?? []), node]);
    });
    return map;
  }, [nodes]);
  const visible = useMemo(() => nodes.filter((row) => {
    let parent = row.parent_node_code;
    while (parent) {
      if (!expanded.has(parent)) return false;
      parent = nodeByCode.get(parent)?.parent_node_code ?? null;
    }
    return true;
  }), [expanded, nodeByCode, nodes]);
  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - 3);
  const end = Math.min(visible.length, start + viewportRows + 6);
  const virtualRows = visible.slice(start, end);

  const entries = useMemo(() => {
    if (!kpis.data || !selected) return [];
    const selectedText = normalize(`${selected.node_code} ${selected.node_name} ${JSON.stringify(selected.payload)}`);
    return ledgerRows(kpis.data.data).filter((entry) =>
      entryMatchesFilters(filters, entry)
      && (selectedText.includes(normalize(entry.analytical))
        || selectedText.includes(normalize(entry.synthetic))
        || normalize(entry.accountName).includes(normalize(selected.node_name))),
    );
  }, [filters, kpis.data, selected]);

  if (dre.isLoading || kpis.isLoading) return <LoadingGrid />;
  if (dre.isError || kpis.isError || !dre.data || !kpis.data) {
    return <ErrorState message="Não foi possível carregar a DRE oficial." onRetry={() => { dre.refetch(); kpis.refetch(); }} />;
  }

  const officialChecks = [
    ["Receita Bruta", kpis.data.data.executive.receita_bruta],
    ["Receita Líquida", kpis.data.data.executive.receita_liquida],
    ["EBITDA", kpis.data.data.executive.ebitda],
    ["EBIT", kpis.data.data.executive.lucro_operacional],
    ["Lucro Líquido", kpis.data.data.charts.waterfall_dre.find((item) => normalize(item.name ?? "") === "lucro liquido")?.value],
  ].map(([name, official]) => {
    const row = nodes.find((item) => normalize(cleanName(item.node_name)) === normalize(String(name)));
    const difference = row && typeof official === "number" ? Number(row.amount ?? 0) - official : null;
    return { name: String(name), difference };
  });
  const onScroll = (event: UIEvent<HTMLDivElement>) => setScrollTop(event.currentTarget.scrollTop);

  return (
    <div className={controlMode ? "space-y-4" : "space-y-6"}>
      <section className="executive-panel rounded-lg p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-primary">Controladoria · Overview RCO oficial</p>
            <h2 className="mt-1 text-2xl font-semibold">DRE Gerencial</h2>
            <p className="mt-1 text-sm text-muted-foreground">Hierarquia, ordem e totalizadores oficiais retornados pela API. Valores em BRL.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => downloadBlob("ARDO_DRE_Overview_RCO.xls", excelContent(visible, kpis.data.data), "application/vnd.ms-excel")}>
              <FileSpreadsheet className="h-4 w-4" />Exportar DRE Excel
            </Button>
            <Button variant="outline" onClick={() => downloadBlob("ARDO_DRE_Overview_RCO.pdf", pdfContent(visible), "application/pdf")}>
              <FileText className="h-4 w-4" />Exportar PDF
            </Button>
          </div>
        </div>
      </section>

      <Card className="border-primary/25">
        <CardContent className="flex flex-wrap gap-2 p-4">
          {officialChecks.map((check) => (
            <Badge key={check.name} className={check.difference === 0 ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100" : ""}>
              <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
              {check.name}: {check.difference === null ? "não disponível" : `diferença ${formatMoney(check.difference)}`}
            </Badge>
          ))}
        </CardContent>
      </Card>

      {nodes.length === 0 ? <EmptyState message="Nenhuma linha da DRE corresponde aos filtros selecionados." /> : (
        <Card>
          <CardContent className="p-0">
            <div className="max-h-[660px] overflow-auto" onScroll={onScroll}>
              <table className="w-full min-w-[1500px] table-fixed text-sm">
                <thead className="sticky top-0 z-[2] bg-muted text-xs uppercase tracking-[0.08em] text-muted-foreground">
                  <tr>
                    <th className="w-[360px] px-4 py-3 text-left">Descrição</th>
                    {months.map((month) => <th key={month} className="w-[82px] px-2 py-3 text-right">{month}</th>)}
                    <th className="w-[112px] px-4 py-3 text-right">YTD</th>
                  </tr>
                </thead>
                <tbody>
                  {start > 0 ? <tr aria-hidden><td colSpan={14} style={{ height: start * rowHeight }} /></tr> : null}
                  {virtualRows.map((row) => {
                    const children = childrenByParent.get(row.node_code) ?? [];
                    const series = monthlySeries(row, kpis.data.data);
                    const classes = isNetIncome(row.node_name) ? "border-y border-emerald-400/40 bg-emerald-400/10 font-bold text-emerald-100"
                      : isResult(row.node_name) ? "border-y border-primary/45 bg-primary/12 font-bold text-primary"
                      : isSubtotal(row) ? "border-t border-border bg-muted/45 font-semibold"
                      : isExpense(row.node_name) ? "border-t border-border/40 text-red-200/90" : "border-t border-border/40";
                    return (
                      <tr key={row.node_code} className={`${classes} h-11 cursor-pointer hover:bg-accent/35`} onClick={() => setSelected(row)}>
                        <td className="truncate px-4 py-2" style={{ paddingLeft: `${16 + Math.max(0, row.level - 1) * 24}px` }}>
                          <button className="flex w-full items-center gap-2 text-left" onClick={(event) => {
                            event.stopPropagation();
                            if (!children.length) { setSelected(row); return; }
                            setExpanded((current) => {
                              const next = new Set(current);
                              next.has(row.node_code) ? next.delete(row.node_code) : next.add(row.node_code);
                              return next;
                            });
                          }}>
                            {children.length ? expanded.has(row.node_code) ? <ChevronDown className="h-4 w-4 shrink-0" /> : <ChevronRight className="h-4 w-4 shrink-0" /> : <span className="w-4 shrink-0" />}
                            <span className="truncate" title={cleanName(row.node_name)}>{cleanName(row.node_name)}</span>
                          </button>
                        </td>
                        {months.map((month, index) => {
                          const point = series.find((item) => periodMonth(item.period) === index);
                          return <td key={month} className="px-2 py-2 text-right tabular-nums">{point ? formatMoney(point.value) : "—"}</td>;
                        })}
                        <td className="px-4 py-2 text-right font-medium tabular-nums">{formatMoney(row.amount === null ? null : Number(row.amount))}</td>
                      </tr>
                    );
                  })}
                  {end < visible.length ? <tr aria-hidden><td colSpan={14} style={{ height: (visible.length - end) * rowHeight }} /></tr> : null}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div><CardTitle>Drilldown Contábil</CardTitle><p className="mt-1 text-sm text-muted-foreground">Conta Sintética → Conta Analítica → Lançamentos → Documento</p></div>
            <Badge>{selected ? cleanName(selected.node_name) : "Selecione uma linha da DRE"}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {!selected ? <EmptyState message="Clique em uma linha para carregar seus lançamentos." /> : entries.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-8 text-center"><FileSearch className="mx-auto h-8 w-8 text-primary" /><p className="mt-3">Nenhum lançamento persistido corresponde à linha e aos filtros atuais.</p></div>
          ) : (
            <div className="max-h-[520px] overflow-auto">
              <table className="w-full min-w-[1200px] text-sm">
                <thead className="sticky top-0 bg-muted text-xs uppercase text-muted-foreground"><tr>
                  {["Data", "Documento", "Histórico", "Conta Sintética", "Conta Analítica", "Débito", "Crédito", "Valor"].map((label) =>
                    <th key={label} className={`px-3 py-3 ${["Débito", "Crédito", "Valor"].includes(label) ? "text-right" : "text-left"}`}>{label}</th>)}
                </tr></thead>
                <tbody>{entries.slice(0, 100).map((entry) => <tr key={entry.entry_id} className="border-t border-border/50">
                  <td className="px-3 py-3">{entry.date}</td><td className="px-3 py-3 font-mono text-xs">{entry.document ?? entry.entry_id}</td>
                  <td className="max-w-sm px-3 py-3">{entry.description ?? "Não informado"}</td><td className="px-3 py-3">{entry.synthetic}</td>
                  <td className="px-3 py-3">{entry.analytical} · {entry.accountName}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{entry.debit ? formatMoney(entry.debit) : "—"}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{entry.credit ? formatMoney(entry.credit) : "—"}</td>
                  <td className="px-3 py-3 text-right font-medium tabular-nums">{formatMoney(entry.amount)}</td>
                </tr>)}</tbody>
              </table>
            </div>
          )}
          {entries.length > 100 ? <p className="mt-3 text-xs text-muted-foreground"><Download className="mr-1 inline h-3.5 w-3.5" />Exibindo 100 lançamentos por vez para preservar performance.</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
