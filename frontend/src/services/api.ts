import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface QueryResponse {
  prompt: string;
  generated_sql: string;
  explanation: string;
  execution: {
    success: boolean;
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
  status: 'success' | 'error';
}

export const processTextToSqlQuery = async (prompt: string): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/query', { prompt });
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
