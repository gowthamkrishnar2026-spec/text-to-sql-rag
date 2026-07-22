"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { History, Clock, Database, Code2, ArrowRight } from 'lucide-react';
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
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Query Execution History</h1>
            <p className="text-xs text-slate-400">Audit trail of all natural language prompts, generated SQL, and execution metrics.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 text-sm">Loading history log...</div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">No query history records found.</div>
        ) : (
          <div className="space-y-4">
            {history.map((item) => (
              <div
                key={item.id}
                className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-3 hover:border-slate-700 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <span className="font-semibold text-base text-white">{item.prompt}</span>
                  <div className="flex items-center space-x-3 text-xs font-mono">
                    <span className="flex items-center space-x-1 text-slate-400">
                      <Database className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{item.row_count} rows</span>
                    </span>
                    <span className="flex items-center space-x-1 text-emerald-400">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{item.execution_time_ms} ms</span>
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto">
                  <code>{item.sql_query}</code>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                  <span>Logged at: {new Date(item.timestamp).toLocaleString()}</span>
                  <Link
                    href="/"
                    className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 font-medium"
                  >
                    <span>Re-run in Dashboard</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
