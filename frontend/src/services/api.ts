import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface RagExampleHit {
  question: string;
  sql: string;
  source: string; // 'project' = this database, anything else = another database
  db_id: string;
  score: number;
}

export interface RagMeta {
  schema?: {
    requested?: boolean | null;
    used: boolean;
    total_tables?: number;
    tables?: string[];
    retrieved?: string[];
    expanded?: string[];
    reason?: string | null;
  };
  examples?: {
    requested?: boolean | null;
    used: boolean;
    count: number;
    items: RagExampleHit[];
    reason?: string | null;
  };
  static_block?: boolean;
  retrieval_ms?: number;
  prompt_chars?: number;
  prompt_tokens?: number | null;
  error?: string;
}

export interface QueryResponse {
  prompt: string;
  is_safe?: boolean;
  blocked?: boolean;
  violation_type?: string;
  blocked_operation?: string;
  blocked_sql?: string;
  generated_sql: string;
  suggested_safe_sql?: string;
  explanation: string;
  security_message?: string;
  rag?: RagMeta | null;
  execution: {
    success: boolean;
    blocked?: boolean;
    sql_query: string;
    columns: string[];
    rows: Record<string, any>[];
    row_count: number;
    execution_time_ms: number;
    visualization?: {
      recommended_chart: 'bar' | 'pie' | 'line' | 'area' | 'table';
      x_axis: string;
      y_axis: string[];
      numeric_columns: string[];
      string_columns: string[];
    };
    error?: string;
  };
}

export interface HistoryItem {
  id: string;
  prompt: string;
  sql_query: string;
  row_count: number;
  execution_time_ms: number;
  timestamp: string;
  status: 'success' | 'error' | 'blocked';
}

export const processTextToSqlQuery = async (
  prompt: string,
  options?: { rag?: boolean }
): Promise<QueryResponse> => {
  // RAG on = server defaults; RAG off = the original fixed prompt (used to compare answers)
  const rag = options?.rag === false
    ? { use_example_rag: false, use_schema_rag: false, static_examples: true }
    : {};
  const response = await apiClient.post<QueryResponse>('/query', { prompt, ...rag });
  return response.data;
};

export const fetchDatabaseSchema = async () => {
  const response = await apiClient.get('/schema');
  return response.data;
};

export const fetchQueryHistory = async (): Promise<{ history: HistoryItem[] }> => {
  const response = await apiClient.get('/history');
  return response.data;
};

export const exportQueryData = async (
  columns: string[],
  rows: Record<string, any>[],
  sql_query: string,
  format: 'csv' | 'excel' | 'pdf'
) => {
  const response = await apiClient.post(
    '/export',
    { columns, rows, sql_query, format },
    { responseType: 'blob' }
  );

  const fileExt = format === 'excel' ? 'xlsx' : format;
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `query_results_${Date.now()}.${fileExt}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export interface BenchmarkMetrics {
  generation_success_rate: number;
  execution_accuracy: number;
  column_match_rate: number;
  exact_match_rate: number;
  avg_latency_ms: number;
  blocked_count: number;
}

export interface BenchmarkCase {
  id: string;
  domain: string;
  difficulty: string;
  prompt: string;
  gold_sql: string;
  generated_sql: string;
  latency_ms: number;
  generation_success: boolean;
  blocked: boolean;
  exec_accuracy: boolean;
  column_match: boolean;
  exact_match: boolean;
  generated_row_count?: number;
  gold_row_count?: number;
  columns?: string[];
  records?: Record<string, any>[];
  error?: string | null;
}

export interface BenchmarkReport {
  run_timestamp: string;
  api_url: string;
  total_cases: number;
  metrics: BenchmarkMetrics;
  cases: BenchmarkCase[];
  is_running?: boolean;
  live_status?: any;
}

export const fetchBenchmarks = async (): Promise<BenchmarkReport> => {
  const response = await apiClient.get<BenchmarkReport>('/benchmarks');
  return response.data;
};

export const fetchBenchmarkStatus = async () => {
  const response = await apiClient.get('/benchmarks/status');
  return response.data;
};

export const triggerBenchmarkRun = async (domain?: string, difficulty?: string, rag?: boolean) => {
  const response = await apiClient.post('/benchmarks/run', { domain, difficulty, rag });
  return response.data;
};

export interface RagStatus {
  available: boolean;
  error?: string;
  examples_enabled?: boolean;
  example_sources?: string[];
  examples_top_k?: number;
  schema_enabled?: boolean;
  schema_min_tables?: number;
  schema_top_k?: number;
  vector_store?: string;
  embedding_model?: string;
  schema_descriptions?: boolean;
  schema_value_hints?: boolean;
  total_tables?: number;
  index_total?: number;
  index_project?: number;
  index_spider?: number;
  index_error?: string;
}

export interface AblationRow {
  label: string;
  n: number;
  execution_accuracy: number;
  column_match: number;
  exact_match: number;
  avg_tables_in_prompt: number;
  avg_prompt_tokens: number;
  avg_latency_ms: number;
  errors: number;
  notes?: string[];
  run_timestamp?: string | null;
}

export interface RagAblation {
  ablation: { run_timestamp?: string; summary: Record<string, AblationRow> } | null;
  dashboard_runs: Partial<Record<'on' | 'off', { run_timestamp: string; total_cases: number; metrics: BenchmarkMetrics; rag_mode: string }>>;
}

export interface HistoryEvalSide {
  prompts: number;
  executed_ok_rate: number;
  match_previous_rate: number;
  with_reference: number;
  avg_latency_ms: number;
  errors: number;
  guardrail_total: number;
  guardrail_held: number;
}

export interface HistoryEvalReport {
  run_timestamp: string;
  prompts: number;
  runtime_seconds: number;
  workers: number;
  off: HistoryEvalSide;
  on: HistoryEvalSide;
  fixed: number;
  broke: number;
}

export interface HistoryEvalState {
  status: { is_running: boolean; done: number; total: number; error?: string | null; started_at?: string | null; completed_at?: string | null };
  latest: HistoryEvalReport | null;
}

export const fetchRagStatus = async (): Promise<RagStatus> => (await apiClient.get<RagStatus>('/rag/status')).data;
export const fetchRagAblation = async (): Promise<RagAblation> => (await apiClient.get<RagAblation>('/rag/ablation')).data;
export const fetchHistoryEval = async (): Promise<HistoryEvalState> => (await apiClient.get<HistoryEvalState>('/rag/history-eval')).data;
export const runHistoryEval = async (limit = 200, workers = 4) =>
  (await apiClient.post('/rag/history-eval/run', { limit, workers })).data;
