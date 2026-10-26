"use client";

import React, { useEffect, useState } from 'react';
import { History, Clock, Database, ChevronRight, ShieldAlert } from 'lucide-react';
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
    <div className="w-full claude-card p-5 border border-[#2b2b27] flex flex-col h-full">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-[#d97757]" />
          <h3 className="font-semibold text-[#f3f3ee] text-sm">Recent Queries</h3>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#242421] text-[#a1a19a] font-mono">
          {history.length}
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[550px] pr-1">
        {loading ? (
          <div className="py-8 text-center text-[#686861] text-xs">Loading history log...</div>
        ) : history.length === 0 ? (
          <div className="py-8 text-center text-[#686861] text-xs">No previous queries logged.</div>
        ) : (
          history.map((item) => {
            const isBlocked = item.status === 'blocked';

            return (
              <div
                key={item.id}
                onClick={() => onSelectQuery(item.prompt)}
                className={`p-3 rounded-xl ${
                  isBlocked
                    ? 'bg-[#191111] hover:bg-[#201414] border border-rose-950 hover:border-rose-800'
                    : 'bg-[#111110] hover:bg-[#242421] border border-[#282824] hover:border-[#d97757]/40'
                } cursor-pointer transition-all group`}
              >
                <div className="flex items-start justify-between">
                  <p className={`text-xs font-medium ${
                    isBlocked ? 'text-rose-300 group-hover:text-rose-200' : 'text-[#a1a19a] group-hover:text-[#f4a284]'
                  } line-clamp-2`}>
                    {item.prompt}
                  </p>
                  <ChevronRight className={`w-3.5 h-3.5 ${
                    isBlocked ? 'text-rose-500' : 'text-[#686861] group-hover:text-[#d97757]'
                  } shrink-0 ml-2 mt-0.5 transition-transform group-hover:translate-x-0.5`} />
                </div>

                <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#242421] text-[10px] text-[#686861] font-mono">
                  {isBlocked ? (
                    <span className="flex items-center space-x-1 text-rose-400 font-semibold">
                      <ShieldAlert className="w-3 h-3 text-rose-400" />
                      <span>BLOCKED</span>
                    </span>
                  ) : (
                    <span className="flex items-center space-x-1 text-[#a1a19a]">
                      <Database className="w-3 h-3 text-[#d97757]" />
                      <span>{item.row_count} rows</span>
                    </span>
                  )}

                  <span className={`flex items-center space-x-1 ${isBlocked ? 'text-rose-400/80' : 'text-emerald-400'}`}>
                    <Clock className="w-3 h-3" />
                    <span>{isBlocked ? 'Restricted' : `${item.execution_time_ms}ms`}</span>
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
