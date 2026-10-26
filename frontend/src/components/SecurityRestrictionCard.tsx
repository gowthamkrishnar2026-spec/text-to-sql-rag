"use client";

import React from 'react';
import { ShieldAlert, AlertTriangle, Play, CheckCircle2, XCircle, ArrowRight, Database, ExternalLink, X } from 'lucide-react';
import Link from 'next/link';

interface SecurityRestrictionCardProps {
  blockedOperation?: string;
  blockedSql?: string;
  suggestedSafeSql?: string;
  explanation?: string;
  securityMessage?: string;
  onExecuteSafeAlternative?: (safeSql: string) => void;
  onDismiss?: () => void;
}

export default function SecurityRestrictionCard({
  blockedOperation = 'DESTRUCTIVE_OPERATION',
  blockedSql,
  suggestedSafeSql,
  explanation,
  securityMessage,
  onExecuteSafeAlternative,
  onDismiss,
}: SecurityRestrictionCardProps) {
  return (
    <div className="w-full rounded-2xl border-2 border-rose-800/80 bg-[#191111] p-6 shadow-2xl relative overflow-hidden animate-in fade-in duration-200">
      
      {/* Background ambient glow */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-rose-900/40">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-800/80 text-rose-400 shadow-md shadow-rose-950/50 shrink-0">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-rose-200 tracking-tight">
                Security Restriction Triggered
              </h2>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-bold uppercase tracking-wider">
                {blockedOperation} BLOCKED
              </span>
            </div>
            <p className="text-xs text-rose-300/80 mt-0.5">
              Destructive database modifications are strictly prohibited by zero-trust PostgreSQL security policies.
            </p>
          </div>
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-rose-400 hover:text-rose-200 p-1.5 rounded-lg hover:bg-rose-950/60 transition-colors"
            title="Dismiss warning"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main explanation & reason */}
      <div className="mt-4 space-y-4">
        <div className="p-4 rounded-xl bg-black/40 border border-rose-900/50 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-rose-300 font-mono uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>Policy Violation Details</span>
          </div>
          <p className="text-xs text-[#d1d1ca] leading-relaxed">
            {securityMessage || "Data modification commands (DELETE, DROP, TRUNCATE, UPDATE, ALTER) are permanently disabled. This database environment only permits read-only SELECT queries to maintain data integrity."}
          </p>
          {explanation && (
            <p className="text-xs text-[#a1a19a] italic pt-1 border-t border-rose-950/60">
              {explanation}
            </p>
          )}
        </div>

        {/* Blocked Statement Representation */}
        {blockedSql && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-mono text-rose-400 font-semibold uppercase tracking-wider flex items-center space-x-1">
              <XCircle className="w-3.5 h-3.5 text-rose-400" />
              <span>Blocked Destructive Command</span>
            </span>
            <div className="p-3 rounded-xl bg-black/60 border border-rose-900/80 font-mono text-xs text-rose-300 overflow-x-auto line-through opacity-85">
              <code>{blockedSql}</code>
            </div>
          </div>
        )}

        {/* Interactive Safe Alternative Suggestion */}
        {suggestedSafeSql && (
          <div className="p-4 rounded-xl bg-[#1c1c1a] border border-[#3d3d37] space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-[#86efac] font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Recommended Non-Destructive Alternative</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full badge-green">
                Safe Read-Only Preview
              </span>
            </div>

            <p className="text-xs text-[#a1a19a]">
              Instead of deleting or modifying records, safely preview the matching rows that would have been targeted:
            </p>

            <div className="p-3 rounded-xl claude-code-box text-xs font-mono text-[#86efac] overflow-x-auto">
              <code>{suggestedSafeSql}</code>
            </div>

            {onExecuteSafeAlternative && (
              <div className="pt-2 flex items-center justify-between">
                <span className="text-[11px] text-[#686861]">Zero data mutation risk</span>
                <button
                  onClick={() => onExecuteSafeAlternative(suggestedSafeSql)}
                  className="flex items-center space-x-2 px-4 py-2 rounded-xl btn-terracotta text-xs font-semibold shadow-md hover:scale-[1.02] active:scale-[0.99] transition-all"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Execute Safe SELECT Alternative</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Security Rule Matrix */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-black/30 border border-rose-950/60 text-xs space-y-1">
            <span className="font-mono text-rose-400 font-bold block text-[11px]">DELETE &amp; DROP</span>
            <span className="text-[#a1a19a] text-[11px] block">Blocked permanently</span>
          </div>
          <div className="p-3 rounded-xl bg-black/30 border border-rose-950/60 text-xs space-y-1">
            <span className="font-mono text-rose-400 font-bold block text-[11px]">UPDATE &amp; ALTER</span>
            <span className="text-[#a1a19a] text-[11px] block">Blocked permanently</span>
          </div>
          <div className="p-3 rounded-xl bg-black/30 border border-emerald-950/60 text-xs space-y-1">
            <span className="font-mono text-emerald-400 font-bold block text-[11px]">SELECT &amp; JOINS</span>
            <span className="text-[#a1a19a] text-[11px] block">Allowed with audit logging</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-3 border-t border-rose-900/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <Link
            href="/settings"
            className="flex items-center space-x-1.5 text-rose-300 hover:text-white transition-colors"
          >
            <Database className="w-3.5 h-3.5 text-rose-400" />
            <span>Inspect Allowed PostgreSQL Schema</span>
            <ExternalLink className="w-3 h-3 ml-1 text-rose-400" />
          </Link>

          {onDismiss && (
            <button
              onClick={onDismiss}
              className="px-3 py-1.5 rounded-lg bg-black/40 hover:bg-black/60 border border-rose-900/60 text-xs text-rose-300 hover:text-white transition-colors"
            >
              Clear Warning
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
