import { createContext, useContext, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { enterpriseApi } from "@/lib/api";
import type { ExecutiveDrilldown } from "@/lib/types";

export type FinancialFilters = {
  company: string;
  division: string;
  costCenter: string;
  period: string;
  year: string;
  account: string;
  syntheticAccount: string;
  analyticalAccount: string;
};

const emptyFilters: FinancialFilters = {
  company: "", division: "", costCenter: "", period: "", year: "",
  account: "", syntheticAccount: "", analyticalAccount: "",
};

type FilterOptions = Record<keyof FinancialFilters, string[]>;

type FinancialFiltersState = {
  filters: FinancialFilters;
  setFilter: (key: keyof FinancialFilters, value: string) => void;
  clearFilters: () => void;
  options: FilterOptions;
  controlMode: boolean;
  setControlMode: (value: boolean) => void;
};

const Context = createContext<FinancialFiltersState | null>(null);

const unique = (values: Array<string | undefined>) =>
  [...new Set(values.filter((value): value is string => Boolean(value)))].sort((a, b) => a.localeCompare(b, "pt-BR"));

function optionsFrom(drilldown?: ExecutiveDrilldown, periods: string[] = []): FilterOptions {
  const companies = drilldown?.companies ?? [];
  const divisions = companies.flatMap((company) => company.divisions);
  const centers = divisions.flatMap((division) => division.cost_centers);
  const synthetics = centers.flatMap((center) => center.synthetic_accounts);
  const analytical = synthetics.flatMap((synthetic) => synthetic.analytical_accounts);
  return {
    company: unique(companies.map((item) => item.name)),
    division: unique(divisions.map((item) => item.name)),
    costCenter: unique(centers.map((item) => item.name)),
    period: unique(periods),
    year: unique(periods.map((period) => period.match(/\d{4}/)?.[0])),
    account: unique(analytical.flatMap((item) => [item.code, item.name])),
    syntheticAccount: unique(synthetics.map((item) => item.code)),
    analyticalAccount: unique(analytical.map((item) => item.code)),
  };
}

export function FinancialFiltersProvider({ children }: { children: React.ReactNode }) {
  const [filters, setFilters] = useState(emptyFilters);
  const [controlMode, setControlMode] = useState(false);
  const kpis = useQuery({ queryKey: ["kpis", "filter-options"], queryFn: enterpriseApi.kpis, staleTime: 60_000 });
  const options = useMemo(() => {
    const data = kpis.data?.data;
    if (data?.filter_options) {
      return {
        company: data.filter_options.companies,
        division: data.filter_options.divisions,
        costCenter: data.filter_options.cost_centers,
        period: data.filter_options.periods,
        year: data.filter_options.years,
        account: data.filter_options.accounts,
        syntheticAccount: data.filter_options.synthetic_accounts,
        analyticalAccount: data.filter_options.analytical_accounts,
      };
    }
    const periods = [...(data?.charts.receita_mensal ?? []), ...(data?.charts.evolucao_caixa ?? [])]
      .map((item) => item.period ?? "");
    return optionsFrom(data?.drilldown, periods);
  }, [kpis.data]);

  const setFilter = (key: keyof FinancialFilters, value: string) =>
    setFilters((current) => ({ ...current, [key]: value }));

  return (
    <Context.Provider value={{ filters, setFilter, clearFilters: () => setFilters(emptyFilters), options, controlMode, setControlMode }}>
      {children}
    </Context.Provider>
  );
}

export function useFinancialFilters() {
  const value = useContext(Context);
  if (!value) throw new Error("useFinancialFilters must be used inside FinancialFiltersProvider");
  return value;
}

export function entryMatchesFilters(
  filters: FinancialFilters,
  path: { company: string; division: string; costCenter: string; synthetic: string; analytical: string; date?: string },
) {
  return (!filters.company || path.company === filters.company)
    && (!filters.division || path.division === filters.division)
    && (!filters.costCenter || path.costCenter === filters.costCenter)
    && (!filters.syntheticAccount || path.synthetic === filters.syntheticAccount)
    && (!filters.analyticalAccount || path.analytical === filters.analyticalAccount)
    && (!filters.account || path.analytical === filters.account || path.analytical.toLowerCase().includes(filters.account.toLowerCase()))
    && (!filters.year || path.date?.startsWith(filters.year))
    && (!filters.period || path.date?.replaceAll("-", "").startsWith(filters.period));
}
