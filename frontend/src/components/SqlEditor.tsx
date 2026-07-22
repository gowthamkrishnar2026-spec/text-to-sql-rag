"use client";

import React, { useState } from 'react';
import { Code2, Check, Copy, Play, ShieldCheck, Info } from 'lucide-react';

interface SqlEditorProps {
  initialSql: string;
  explanation?: string;
  onExecute: (customSql: string) => void;
  isLoading: boolean;
}

export default function SqlEditor({ initialSql, explanation, onExecute, isLoading }: SqlEditorProps) {
  const [sql, setSql] = useState(initialSql);
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    setSql(initialSql);
  }, [initialSql]);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full glass-panel rounded-2xl p-5 shadow-lg border border-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Code2 className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-white text-base">Generated SQL Query</h3>
          <span className="flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Validated Safe</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={() => onExecute(sql)}
            disabled={isLoading || !sql.trim()}
            className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-sm transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run Query</span>
          </button>
        </div>
      </div>

      {/* SQL Code Box */}
      <div className="relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 font-mono text-sm">
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          rows={3}
          className="w-full p-4 bg-transparent text-emerald-300 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 resize-y leading-relaxed font-mono"
        />
      </div>

      {/* AI Explanation Box */}
      {explanation && (
        <div className="mt-3 flex items-start space-x-2 p-3 rounded-xl bg-blue-950/40 border border-blue-900/50 text-xs text-blue-200">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
          <div>
            <span className="font-semibold text-blue-300">AI Query Logic: </span>
            <span>{explanation}</span>
          </div>
        </div>
      )}
    </div>
  );
}
