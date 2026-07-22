"use client";

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import PromptInput from '@/components/PromptInput';
import SqlEditor from '@/components/SqlEditor';
import ResultsTable from '@/components/ResultsTable';
import Visualizer from '@/components/Visualizer';
import HistorySidebar from '@/components/HistorySidebar';
import ExportModal from '@/components/ExportModal';
import { processTextToSqlQuery, apiClient, QueryResponse } from '@/services/api';
import { AlertTriangle, Sparkles, Terminal, Database, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [currentQueryResponse, setCurrentQueryResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Auto-run initial query on load for showcase
  useEffect(() => {
    handleQuerySubmit("Show all students with CGPA greater than 8");
  }, []);

  const handleQuerySubmit = async (promptText: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await processTextToSqlQuery(promptText);
      setCurrentQueryResponse(data);
      if (data.execution.error) {
        setError(data.execution.error);
      }
    } catch (err: any) {
      console.error('Error running text-to-sql:', err);
      setError(err.response?.data?.detail || 'Failed to connect to AI Text-to-SQL engine.');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteCustomSql = async (sql: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/execute-query', { sql_query: sql });
      if (currentQueryResponse) {
        setCurrentQueryResponse({
          ...currentQueryResponse,
          generated_sql: sql,
          execution: res.data
        });
      }
      if (res.data.error) {
        setError(res.data.error);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error executing SQL query.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Hero Title Section */}
        <div className="text-center sm:text-left space-y-1">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center justify-center sm:justify-start space-x-3">
            <span>Natural Language to SQL Engine</span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              Spider Benchmark Ready
            </span>
          </h1>
          <p className="text-sm text-slate-400">
            Ask questions in plain English. AI generates safe SQL, executes on PostgreSQL, and renders tables + charts.
          </p>
        </div>

        {/* Prompt Input Box */}
        <PromptInput onSubmit={handleQuerySubmit} isLoading={loading} />

        {/* Error Alert Banner */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-sm flex items-center space-x-3 animate-in fade-in">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Main Dashboard Column (3 cols) */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* SQL Editor */}
            {currentQueryResponse && (
              <SqlEditor
                initialSql={currentQueryResponse.generated_sql}
                explanation={currentQueryResponse.explanation}
                onExecute={handleExecuteCustomSql}
                isLoading={loading}
              />
            )}

            {/* Results Section */}
            {currentQueryResponse && currentQueryResponse.execution.success && (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                
                {/* Table View */}
                <div className="h-full">
                  <ResultsTable
                    columns={currentQueryResponse.execution.columns}
                    rows={currentQueryResponse.execution.rows}
                    rowCount={currentQueryResponse.execution.row_count}
                    executionTimeMs={currentQueryResponse.execution.execution_time_ms}
                    onExportClick={() => setIsExportOpen(true)}
                  />
                </div>

                {/* Visualizer View */}
                <div className="h-full">
                  <Visualizer
                    columns={currentQueryResponse.execution.columns}
                    rows={currentQueryResponse.execution.rows}
                    visualizationConfig={currentQueryResponse.execution.visualization}
                  />
                </div>

              </div>
            )}

          </div>

          {/* Sidebar Column (1 col) */}
          <div className="lg:col-span-1">
            <HistorySidebar
              onSelectQuery={handleQuerySubmit}
              currentPrompt={currentQueryResponse?.prompt}
            />
          </div>

        </div>

      </main>

      {/* Export Modal */}
      {currentQueryResponse && (
        <ExportModal
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
          columns={currentQueryResponse.execution.columns}
          rows={currentQueryResponse.execution.rows}
          sqlQuery={currentQueryResponse.generated_sql}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AI-Powered Text-to-SQL System • M.Tech M.Tech Project</span>
          <span className="text-slate-400 font-mono">Next.js 15 • FastAPI • PostgreSQL • Transformers</span>
        </div>
      </footer>
    </div>
  );
}
