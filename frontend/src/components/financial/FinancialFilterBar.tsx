import { RotateCcw, SlidersHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useFinancialFilters, type FinancialFilters } from "@/lib/financialFilters";

const fields: Array<[keyof FinancialFilters, string]> = [
  ["company", "Empresa"], ["division", "Divisão"], ["costCenter", "Centro de Custo"],
  ["period", "Período"], ["year", "Ano"], ["account", "Conta Contábil"],
  ["syntheticAccount", "Conta Sintética"], ["analyticalAccount", "Conta Analítica"],
];

export function FinancialFilterBar() {
  const { filters, options, setFilter, clearFilters, controlMode, setControlMode } = useFinancialFilters();
  const active = Object.values(filters).filter(Boolean).length;
  return (
    <Card className="sticky top-20 z-[8] border-primary/25 bg-background/95 shadow-xl backdrop-blur">
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">Filtros Contábeis</span>
            <Badge>{active} ativos</Badge>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant={controlMode ? "default" : "outline"} onClick={() => setControlMode(!controlMode)}>
              Modo Controladoria
            </Button>
            <Button size="sm" variant="ghost" onClick={clearFilters}><RotateCcw className="h-4 w-4" />Limpar</Button>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
          {fields.map(([key, label]) => (
            <label key={key} className="space-y-1 text-xs text-muted-foreground">
              <span>{label}</span>
              <select
                aria-label={label}
                className="h-9 w-full rounded-md border border-input bg-background px-2 text-sm text-foreground"
                value={filters[key]}
                onChange={(event) => setFilter(key, event.target.value)}
              >
                <option value="">Todos</option>
                {options[key].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
          ))}
        </div>
        {Object.values(options).every((items) => items.length === 0) ? (
          <p className="text-xs text-muted-foreground">Carregando valores reais disponíveis na API…</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
