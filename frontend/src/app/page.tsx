"use client";

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import PromptInput from '@/components/PromptInput';
import SqlEditor from '@/components/SqlEditor';
import ResultsTable from '@/components/ResultsTable';
import Visualizer from '@/components/Visualizer';
import HistorySidebar from '@/components/HistorySidebar';
import ExportModal from '@/components/ExportModal';
import SecurityRestrictionCard from '@/components/SecurityRestrictionCard';
import RagContextCard from '@/components/RagContextCard';
import Link from 'next/link';
import { processTextToSqlQuery, apiClient, QueryResponse, fetchRagStatus, RagStatus } from '@/services/api';
import { AlertTriangle, Sparkles, Database, Terminal, Cpu, Target, Layers } from 'lucide-react';

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [currentQueryResponse, setCurrentQueryResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null);
  const [liveEa, setLiveEa] = useState<{ ea: number; total: number } | null>(null);

  // Initial empty state (user submits prompt on demand). Only cheap status calls - no model quota used.
  useEffect(() => {
    fetchRagStatus().then(setRagStatus).catch(() => setRagStatus(null));
    apiClient
      .get('/benchmarks')
      .then((res) => {
        const m = res.data?.metrics;
        if (m && typeof m.execution_accuracy === 'number') {
          setLiveEa({ ea: m.execution_accuracy, total: res.data.total_cases || 0 });
        }
      })
      .catch(() => setLiveEa(null));
  }, []);

  const handleQuerySubmit = async (promptText: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await processTextToSqlQuery(promptText, { rag: useRag });
      setCurrentQueryResponse(data);
      if (data.execution.error && !data.blocked) {
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
      const isBlocked = !!res.data.blocked;
      
      if (currentQueryResponse) {
        setCurrentQueryResponse({
          ...currentQueryResponse,
          generated_sql: sql,
          rag: undefined, // manually edited/executed SQL is no longer the retrieval-assisted output
          blocked: isBlocked,
          is_safe: !isBlocked,
          blocked_sql: isBlocked ? sql : undefined,
          blocked_operation: isBlocked ? (res.data.error?.match(/'([A-Z]+)'/)?.[1] || 'RESTRICTED_QUERY') : undefined,
          security_message: isBlocked ? res.data.error : undefined,
          execution: res.data
        });
      } else {
        setCurrentQueryResponse({
          prompt: "Custom SQL Execution",
          generated_sql: sql,
          explanation: isBlocked ? "Operation was blocked by security policies." : "Manually executed query.",
          blocked: isBlocked,
          is_safe: !isBlocked,
          blocked_sql: isBlocked ? sql : undefined,
          blocked_operation: isBlocked ? (res.data.error?.match(/'([A-Z]+)'/)?.[1] || 'RESTRICTED_QUERY') : undefined,
          security_message: isBlocked ? res.data.error : undefined,
          execution: res.data
        });
      }

      if (res.data.error && !isBlocked) {
        setError(res.data.error);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error executing SQL query.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#141413] text-[#f3f3ee] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* Main Header Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#2b2b27]">
          <div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#d97757] animate-pulse" />
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#f3f3ee]">
                Natural Language to SQL Workspace
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-[#a1a19a] mt-1">
              Ask database questions in plain English. AI generates optimized PostgreSQL queries, executes live, and renders charts.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <Link
              href="/benchmarks"
              className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono flex items-center space-x-1.5 hover:bg-emerald-500/20 transition-all shadow-sm"
              title="View live Spider benchmark accuracy"
            >
              <Target className="w-3.5 h-3.5 text-emerald-400" />
              <span>{liveEa ? `${(liveEa.ea * 100).toFixed(1)}% EA • ${liveEa.total} tests` : 'Benchmarks'}</span>
            </Link>
            {ragStatus?.available && (
              <span
                className={`text-xs px-3 py-1.5 rounded-lg border font-mono flex items-center space-x-1.5 ${
                  useRag && (ragStatus.examples_enabled || ragStatus.schema_enabled)
                    ? 'bg-[#d97757]/10 border-[#d97757]/30 text-[#f4a284]'
                    : 'bg-[#1c1c1a] border-[#2b2b27] text-[#686861]'
                }`}
                title={`Retrieval index: ${ragStatus.index_total ?? 0} solved questions • ${ragStatus.embedding_model || ''}`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>
                  {useRag && (ragStatus.examples_enabled || ragStatus.schema_enabled)
                    ? `RAG • ${[ragStatus.schema_enabled ? 'tables' : '', ragStatus.examples_enabled ? `${ragStatus.index_project ?? ragStatus.index_total ?? 0} examples` : ''].filter(Boolean).join(' + ')}`
                    : 'RAG off'}
                </span>
              </span>
            )}
            <span className="text-xs px-3 py-1.5 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] text-[#a1a19a] font-mono flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#d97757]" />
              <span>Google Gemini AI</span>
            </span>
            <span className="text-xs px-3 py-1.5 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] text-emerald-400 font-mono flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>PostgreSQL Active</span>
            </span>
          </div>
        </div>

        {/* Prompt Input Box */}
        <PromptInput onSubmit={handleQuerySubmit} isLoading={loading} useRag={useRag} onToggleRag={setUseRag} />

        {/* Error Alert Banner (Only for network/runtime errors, not security blocks) */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center space-x-3">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Layout Grid (Main Workspace 3 cols + History Sidebar 1 col) */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Main Dashboard Column (3 cols) */}
          <div className="lg:col-span-3 space-y-6">
            
            {!currentQueryResponse && !loading && (
              <div className="claude-card p-12 text-center text-[#a1a19a] space-y-3">
                <div className="w-12 h-12 rounded-xl bg-[#242421] border border-[#33332f] flex items-center justify-center mx-auto text-[#d97757]">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-[#f3f3ee] text-base">Ready to Query Database</h3>
                <p className="text-xs text-[#a1a19a] max-w-md mx-auto leading-relaxed">
                  Enter a question in plain English in the search bar above or click one of the popular prompt pills to generate and execute SQL.
                </p>
              </div>
            )}

            {/* SECURITY RESTRICTION CARD: Rendered when a query is blocked/destructive */}
            {currentQueryResponse?.blocked && (
              <SecurityRestrictionCard
                blockedOperation={currentQueryResponse.blocked_operation || 'DESTRUCTIVE_OPERATION'}
                blockedSql={currentQueryResponse.blocked_sql}
                suggestedSafeSql={currentQueryResponse.suggested_safe_sql}
                explanation={currentQueryResponse.explanation}
                securityMessage={currentQueryResponse.security_message}
                onExecuteSafeAlternative={(safeSql) => handleExecuteCustomSql(safeSql)}
                onDismiss={() => setCurrentQueryResponse(null)}
              />
            )}

            {/* SQL Editor (Rendered when response exists and is not blocked, or as fallback) */}
            {currentQueryResponse && !currentQueryResponse.blocked && (
              <SqlEditor
                initialSql={currentQueryResponse.generated_sql}
                explanation={currentQueryResponse.explanation}
                onExecute={handleExecuteCustomSql}
                isLoading={loading}
                isBlocked={currentQueryResponse.blocked}
              />
            )}

            {/* Retrieval Context: what the RAG step added to the prompt for this question */}
            {currentQueryResponse?.rag && !currentQueryResponse.blocked && <RagContextCard rag={currentQueryResponse.rag} />}

            {/* Results Section: Only rendered when safe and successful */}
            {currentQueryResponse && !currentQueryResponse.blocked && currentQueryResponse.execution.success && (
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
      {currentQueryResponse && !currentQueryResponse.blocked && currentQueryResponse.execution.success && (
        <ExportModal
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
          columns={currentQueryResponse.execution.columns}
          rows={currentQueryResponse.execution.rows}
          sqlQuery={currentQueryResponse.generated_sql}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-[#2b2b27] py-5 text-center text-xs text-[#686861] mt-12 bg-[#141413]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-[#d97757]" />
            <span>AI Text-to-SQL System • Executive AI Dashboard</span>
          </span>
          <span className="text-[#a1a19a] font-mono text-[11px]">
            Google Gemini AI Engine • PostgreSQL 16 • Next.js 16
          </span>
        </div>
      </footer>
    </div>
  );
}
