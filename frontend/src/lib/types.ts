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
