"use client";

import React, { useEffect, useState } from 'react';
import { History, Play, Clock, Database, ChevronRight } from 'lucide-react';
import { fetchQueryHistory, HistoryItem } from '@/services/api';

interface HistorySidebarProps {
  onSelectQuery: (prompt: string) => void;
  currentPrompt?: string;
}

export default function HistorySidebar({ onSelectQuery, currentPrompt }: HistorySidebarProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await fetchQueryHistory();
        setHistory(res.history);
      } catch (err) {
        console.error('Error fetching history:', err);
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, [currentPrompt]);

  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-white text-base">Recent Queries</h3>
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
          {history.length}
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[550px] pr-1">
        {loading ? (
          <div className="py-8 text-center text-slate-500 text-xs">Loading history...</div>
        ) : history.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">No previous queries logged.</div>
        ) : (
          history.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectQuery(item.prompt)}
              className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-blue-500/40 cursor-pointer transition-all group"
            >
              <div className="flex items-start justify-between">
                <p className="text-xs font-medium text-slate-200 group-hover:text-blue-300 line-clamp-2">
                  {item.prompt}
                </p>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 shrink-0 ml-2 mt-0.5 transition-transform group-hover:translate-x-0.5" />
              </div>

              <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400 font-mono">
                <span className="flex items-center space-x-1">
                  <Database className="w-3 h-3 text-indigo-400" />
                  <span>{item.row_count} rows</span>
                </span>
                <span className="flex items-center space-x-1 text-emerald-400">
                  <Clock className="w-3 h-3" />
                  <span>{item.execution_time_ms}ms</span>
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
