export type ApiEnvelope<T> = {
  data: T;
  meta: {
    api_version: string;
    generated_at: string;
  };
  errors: Array<{
    code: string;
    message: string;
    details: Record<string, unknown>;
  }>;
};

export type Health = {
  status: string;
  database: string;
};

export type Version = {
  name: string;
  version: string;
  generated_at: string;
};

export type Kpis = {
  pipeline_executions: number;
  successful_executions: number;
  failed_executions: number;
  accounting_entries: number;
  dre_nodes: number;
  reconciliation_rows: number;
  average_duration_seconds: number;
  latest_execution_id: string | null;
  warnings: string[];
  executive: ExecutiveAnalytics;
  charts: ExecutiveCharts;
  drilldown: ExecutiveDrilldown;
  pagination: {
    entries_limit: number;
    entries_returned: number;
  };
  filter_options: {
    companies: string[];
    divisions: string[];
    cost_centers: string[];
    periods: string[];
    years: string[];
    accounts: string[];
    synthetic_accounts: string[];
    analytical_accounts: string[];
    dre_groups: string[];
  };
  source_validation: {
    entries: number;
    total: number;
    by_company: ChartPoint[];
    by_division: ChartPoint[];
    by_cost_center: ChartPoint[];
    by_account: ChartPoint[];
  };
};

export type ExecutiveAnalytics = {
  receita_bruta: number;
  receita_liquida: number;
  ebitda: number;
  lucro_operacional: number;
  margem_ebitda: number | null;
  margem_operacional: number | null;
  caixa: number | null;
  forecast: number | null;
  planejado_x_realizado: {
    planejado: number | null;
    realizado: number | null;
    variacao: number | null;
  };
  latest_execution_id: string | null;
};

export type ChartPoint = {
  name?: string;
  period?: string;
  value: number;
  records?: number;
  code?: string;
};

export type ExecutiveCharts = {
  receita_mensal: ChartPoint[];
  ebitda_mensal: ChartPoint[];
  receita_por_empresa: ChartPoint[];
  receita_por_divisao: ChartPoint[];
  receita_por_centro_custo: ChartPoint[];
  evolucao_caixa: ChartPoint[];
  waterfall_dre: ChartPoint[];
};

export type DrilldownEntry = {
  entry_id: string;
  date: string;
  description: string | null;
  amount: number;
  entry_type: string;
  currency: string;
  debit?: number;
  credit?: number;
  document?: string | null;
};

export type ExecutiveDrilldown = {
  companies: Array<{
    name: string;
    divisions: Array<{
      name: string;
      cost_centers: Array<{
        name: string;
        synthetic_accounts: Array<{
          code: string;
          name: string;
          analytical_accounts: Array<{
            code: string;
            name: string;
            entries: DrilldownEntry[];
          }>;
        }>;
      }>;
    }>;
  }>;
};

export type PipelineExecutionSummary = {
  id: string;
  pipeline_name: string;
  source_path: string | null;
  status: string;
  success: boolean;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number;
  created_at: string;
};

export type PipelineExecutionDetail = PipelineExecutionSummary & {
  errors: unknown[];
  metadata: Record<string, unknown>;
  accounting_entries: number;
  dre_nodes: number;
  reconciliation_rows: number;
  metrics_rows: number;
};

export type DreRow = {
  node_code: string;
  node_name: string;
  level: number;
  amount: string | null;
  currency: string;
  percentage: string | null;
  parent_node_code: string | null;
  ordinal: number;
  rule_id: string | null;
  payload: Record<string, unknown>;
};

export type DreResponse = {
  filters: {
    company: string | null;
    period: string | null;
  };
  nodes: DreRow[];
};
