"use client";

import React, { useEffect, useState } from 'react';
import { Layers, BookOpen, Database, Cpu, CheckCircle2, XCircle } from 'lucide-react';
import { fetchRagStatus, RagStatus } from '@/services/api';

function Flag({ on, label }: { on?: boolean; label: string }) {
  return (
    <span className={`inline-flex items-center space-x-1 text-[11px] px-2.5 py-0.5 rounded-full font-mono ${on ? 'badge-green' : 'badge-neutral'}`}>
      {on ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      <span>{label}</span>
    </span>
  );
}

export default function RagStatusCard() {
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRagStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  const tables = status?.total_tables ?? 0;
  const minTables = status?.schema_min_tables ?? 1;
  const schemaWillRetrieve = !!status?.schema_enabled && tables >= minTables;

  return (
    <div className="claude-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-[#d97757]" />
          <h3 className="font-semibold text-[#f3f3ee] text-sm">Retrieval (RAG) Index</h3>
        </div>
        {status?.available && <Flag on={!!status.examples_enabled} label={status.examples_enabled ? 'Active' : 'Disabled'} />}
      </div>

      {loading ? (
        <p className="text-xs text-[#686861]">Loading retrieval status…</p>
      ) : !status?.available ? (
        <p className="text-xs text-[#a1a19a]">
          Retrieval status is unavailable{status?.error ? ` (${status.error})` : ''}. Queries still work using the original prompt.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
              <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
                <BookOpen className="w-3 h-3 text-[#d97757]" /><span>Solved questions</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-[#f3f3ee] font-mono">{status.index_total ?? '—'}</div>
              <div className="text-[11px] text-[#a1a19a]">
                {status.index_project ?? 0} this app • {status.index_spider ?? 0} Spider
              </div>
            </div>
            <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
              <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
                <Layers className="w-3 h-3 text-[#d97757]" /><span>Used for answers</span>
              </div>
              <div className="mt-1 text-sm font-semibold text-[#f4a284] font-mono">{(status.example_sources || []).join(' + ')}</div>
              <div className="text-[11px] text-[#a1a19a]">top {status.examples_top_k} per question</div>
            </div>
            <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
              <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
                <Database className="w-3 h-3 text-[#d97757]" /><span>Table retrieval</span>
              </div>
              <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono">{schemaWillRetrieve ? 'Active' : 'Standby'}</div>
              <div className="text-[11px] text-[#a1a19a]">
                {tables} tables • top {status.schema_top_k} + linked
              </div>
            </div>
            <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
              <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
                <Cpu className="w-3 h-3 text-[#d97757]" /><span>Embeddings</span>
              </div>
              <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono break-all">{status.embedding_model || '—'}</div>
              <div className="text-[11px] text-[#a1a19a]">store: {status.vector_store}</div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Flag on={status.schema_descriptions} label="Table descriptions in prompt" />
            <Flag on={status.schema_value_hints} label="Allowed column values in prompt" />
            {status.index_error && (
              <span className="text-[11px] text-amber-300 font-mono">Index unavailable: {status.index_error}</span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
