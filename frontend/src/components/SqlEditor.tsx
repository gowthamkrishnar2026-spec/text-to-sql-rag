"use client";

import React, { useState, useMemo } from 'react';
import { Code2, Check, Copy, Play, ShieldCheck, ShieldAlert, Info, AlertTriangle } from 'lucide-react';

interface SqlEditorProps {
  initialSql: string;
  explanation?: string;
  onExecute: (customSql: string) => void;
  isLoading: boolean;
  isBlocked?: boolean;
}

const FORBIDDEN_WORDS = [
  'DROP', 'DELETE', 'UPDATE', 'ALTER', 'TRUNCATE', 'INSERT', 
  'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'PG_SLEEP'
];

export default function SqlEditor({ initialSql, explanation, onExecute, isLoading, isBlocked }: SqlEditorProps) {
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

  // Real-time safety validation of the SQL in the editor
  const safetyCheck = useMemo(() => {
    if (!sql || !sql.trim()) return { isSafe: true, reason: null };
    const upper = sql.toUpperCase();
    
    for (const kw of FORBIDDEN_WORDS) {
      const regex = new RegExp(`\\b${kw}\\b`, 'i');
      if (regex.test(upper)) {
        return {
          isSafe: false,
          reason: `Contains forbidden statement '${kw}'. Only read-only SELECT queries are allowed.`
        };
      }
    }

    const trimmed = upper.trim();
    if (!trimmed.startsWith('SELECT') && !trimmed.startsWith('WITH')) {
      return {
        isSafe: false,
        reason: "Must begin with SELECT or WITH."
      };
    }

    return { isSafe: true, reason: null };
  }, [sql]);

  const effectiveIsSafe = safetyCheck.isSafe && !isBlocked;

  return (
    <div className="w-full claude-card p-5 shadow-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <Code2 className="w-4 h-4 text-[#d97757]" />
          <h3 className="font-semibold text-[#f3f3ee] text-sm">Generated SQL Query</h3>
          
          {effectiveIsSafe ? (
            <span className="flex items-center space-x-1 text-[11px] px-2.5 py-0.5 rounded-full badge-green font-medium font-mono">
              <ShieldCheck className="w-3 h-3" />
              <span>Validated Safe</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1 text-[11px] px-2.5 py-0.5 rounded-full bg-rose-950/80 border border-rose-800 text-rose-300 font-medium font-mono">
              <ShieldAlert className="w-3 h-3" />
              <span>Restricted / Unsafe SQL</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs px-3 py-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] text-[#a1a19a] hover:text-[#f3f3ee] border border-[#33332f] transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          
          <button
            onClick={() => onExecute(sql)}
            disabled={isLoading || !sql.trim() || !effectiveIsSafe}
            title={effectiveIsSafe ? "Execute SQL query" : "Cannot execute restricted/unsafe SQL"}
            className={`flex items-center space-x-1.5 text-xs px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              effectiveIsSafe 
                ? 'bg-[#d97757] hover:bg-[#e28363] text-white shadow-sm'
                : 'bg-[#242421] text-[#686861] border border-[#33332f] cursor-not-allowed opacity-60'
            }`}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Execute SQL</span>
          </button>
        </div>
      </div>

      {/* Real-time Unsafe Warning Banner */}
      {!safetyCheck.isSafe && (
        <div className="mb-3 p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span><strong>Security Warning:</strong> {safetyCheck.reason}</span>
        </div>
      )}

      {/* SQL Code Box */}
      <div className={`relative rounded-xl overflow-hidden claude-code-box border ${
        effectiveIsSafe ? 'border-[#282824]' : 'border-rose-900/70'
      }`}>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          rows={3}
          className={`w-full p-4 bg-transparent ${
            effectiveIsSafe ? 'text-[#86efac]' : 'text-rose-300'
          } placeholder-[#686861] focus:outline-none focus:ring-1 focus:ring-[#d97757] resize-y leading-relaxed font-mono text-xs sm:text-sm`}
        />
      </div>

      {/* AI Explanation Box */}
      {explanation && (
        <div className="mt-3 flex items-start space-x-2.5 p-3 rounded-xl bg-[#242421] border border-[#33332f] text-xs text-[#a1a19a]">
          <Info className="w-4 h-4 text-[#d97757] mt-0.5 shrink-0" />
          <div>
            <span className="font-semibold text-[#f3f3ee]">AI Logic Breakdown: </span>
            <span>{explanation}</span>
          </div>
        </div>
      )}
    </div>
  );
}
