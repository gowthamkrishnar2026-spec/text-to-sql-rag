"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { History, Clock, Database, Code2, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { fetchQueryHistory, HistoryItem } from '@/services/api';
import Link from 'next/link';

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await fetchQueryHistory();
        setHistory(res.history);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, []);

  return (
    <div className="min-h-screen bg-[#141413] text-[#f3f3ee] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-[#2b2b27]">
          <div className="p-2.5 rounded-xl bg-[#242421] border border-[#33332f] text-[#d97757]">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#f3f3ee]">Query Execution History</h1>
            <p className="text-xs text-[#a1a19a]">Audit trail of all natural language prompts, generated SQL, security enforcement, and execution metrics.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[#686861] text-xs">Loading history log...</div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center text-[#686861] text-xs">No query history records found.</div>
        ) : (
          <div className="space-y-4">
            {history.map((item) => {
              const isBlocked = item.status === 'blocked';

              return (
                <div
                  key={item.id}
                  className={`claude-card p-5 space-y-3 ${
                    isBlocked ? 'border-rose-950 bg-[#171111]' : ''
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-[#f3f3ee]">{item.prompt}</span>
                      {isBlocked && (
                        <span className="text-[10px] font-mono px-2 py-0.2 rounded-full bg-rose-950 text-rose-300 border border-rose-800 flex items-center space-x-1 font-semibold">
                          <ShieldAlert className="w-3 h-3" />
                          <span>BLOCKED</span>
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3 text-xs font-mono">
                      {isBlocked ? (
                        <span className="text-rose-400 font-semibold">Security Guardrail Intercepted</span>
                      ) : (
                        <>
                          <span className="flex items-center space-x-1 text-[#a1a19a]">
                            <Database className="w-3.5 h-3.5 text-[#d97757]" />
                            <span>{item.row_count} rows</span>
                          </span>
                          <span className="flex items-center space-x-1 text-emerald-400">
                            <Clock className="w-3.5 h-3.5" />
                            <span>{item.execution_time_ms} ms</span>
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className={`p-3 rounded-xl claude-code-box text-xs overflow-x-auto ${
                    isBlocked ? 'text-rose-300 border-rose-950' : 'text-[#86efac]'
                  }`}>
                    <code>{item.sql_query}</code>
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#686861] pt-1">
                    <span>Logged at: {new Date(item.timestamp).toLocaleString()}</span>
                    <Link
                      href="/"
                      className="flex items-center space-x-1 text-[#d97757] hover:text-[#e28363] font-medium"
                    >
                      <span>Open in Workbench</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
