"use client";

import React, { useState } from 'react';
import { Layers, Database, BookOpen, Clock, Hash, ChevronDown, ChevronUp, Info, AlertTriangle } from 'lucide-react';
import { RagMeta } from '@/services/api';

interface RagContextCardProps {
  rag?: RagMeta | null;
}

export default function RagContextCard({ rag }: RagContextCardProps) {
  const [open, setOpen] = useState(true);
  if (!rag) return null;

  const ex = rag.examples;
  const sc = rag.schema;
  const examplesUsed = !!ex?.used;
  const schemaUsed = !!sc?.used;
  const total = sc?.total_tables ?? 0;
  const retrievedTables = sc?.tables ?? [];
  const expanded = new Set(sc?.expanded ?? []);
  const notes = [
    rag.error,
    ex && ex.requested && !ex.used ? ex.reason : null,
    sc && sc.requested && !sc.used ? sc.reason : null,
  ].filter(Boolean) as string[];

  return (
    <div className="w-full claude-card p-5 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-3 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-[#d97757]" />
          <h3 className="font-semibold text-[#f3f3ee] text-sm">Retrieval Context (RAG)</h3>
          {examplesUsed ? (
            <span className="text-[11px] px-2.5 py-0.5 rounded-full badge-green font-medium font-mono">
              {ex?.count} examples retrieved
            </span>
          ) : (
            <span className="text-[11px] px-2.5 py-0.5 rounded-full badge-neutral font-medium font-mono">
              Built-in prompt
            </span>
          )}
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center space-x-1 text-xs px-3 py-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] text-[#a1a19a] hover:text-[#f3f3ee] border border-[#33332f] transition-colors"
        >
          {open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          <span>{open ? 'Hide' : 'Show'}</span>
        </button>
      </div>

      {/* Quick facts */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
          <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
            <BookOpen className="w-3 h-3 text-[#d97757]" /><span>Examples</span>
          </div>
          <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono">{examplesUsed ? ex?.count : 'built-in'}</div>
        </div>
        <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
          <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
            <Database className="w-3 h-3 text-[#d97757]" /><span>Schema sent</span>
          </div>
          <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono">
            {schemaUsed ? `${retrievedTables.length} of ${total} tables` : `full (${total} tables)`}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
          <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
            <Clock className="w-3 h-3 text-[#d97757]" /><span>Retrieval</span>
          </div>
          <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono">
            {rag.retrieval_ms != null ? `${Math.round(rag.retrieval_ms)} ms` : '—'}
          </div>
        </div>
        <div className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
          <div className="flex items-center space-x-1.5 text-[10px] uppercase tracking-wider text-[#686861] font-mono">
            <Hash className="w-3 h-3 text-[#d97757]" /><span>Prompt size</span>
          </div>
          <div className="mt-1 text-sm font-semibold text-[#f3f3ee] font-mono">
            {rag.prompt_tokens ? `${rag.prompt_tokens.toLocaleString()} tokens` : rag.prompt_chars ? `~${Math.round(rag.prompt_chars / 4).toLocaleString()} tokens` : '—'}
          </div>
        </div>
      </div>

      {notes.length > 0 && (
        <div className="mt-3 p-3 rounded-xl bg-amber-950/30 border border-amber-900/50 text-amber-200 text-xs flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span>{notes.join(' • ')} — the original prompt was used instead.</span>
        </div>
      )}

      {open && (
        <div className="mt-4 space-y-4">
          {/* Retrieved tables */}
          {schemaUsed && retrievedTables.length > 0 && (
            <div>
              <p className="text-[11px] uppercase tracking-wider text-[#686861] font-mono mb-2">Tables sent to the model</p>
              <div className="flex flex-wrap gap-2">
                {retrievedTables.map((t) => (
                  <span key={t} className={`text-[11px] px-2.5 py-0.5 rounded-full font-mono ${expanded.has(t) ? 'badge-blue' : 'badge-terracotta'}`}
                    title={expanded.has(t) ? 'Added through a foreign key' : 'Matched the question'}>
                    {t}
                  </span>
                ))}
              </div>
              <p className="text-[11px] text-[#686861] mt-2">Orange = matched the question • Blue = added through a foreign key</p>
            </div>
          )}

          {/* Retrieved examples */}
          {examplesUsed && ex && ex.items.length > 0 && (
            <div>
              <p className="text-[11px] uppercase tracking-wider text-[#686861] font-mono mb-2">Similar solved questions used as examples</p>
              <div className="space-y-2.5">
                {ex.items.map((it, i) => (
                  <div key={i} className="p-3 rounded-xl bg-[#111110] border border-[#282824]">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-xs font-medium text-[#f3f3ee]">{it.question}</p>
                      <span className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full font-mono ${it.source === 'project' ? 'badge-green' : 'badge-neutral'}`}>
                        {it.source === 'project' ? 'this database' : `other: ${it.db_id || 'spider'}`}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 mt-2">
                      <div className="flex-1 bg-[#2b2b27] rounded-full h-1.5 overflow-hidden">
                        <div className="bg-[#d97757] h-1.5 rounded-full" style={{ width: `${Math.max(2, Math.min(100, Math.round(it.score * 100)))}%` }} />
                      </div>
                      <span className="text-[10px] font-mono text-[#a1a19a] w-12 text-right">{(it.score * 100).toFixed(0)}% match</span>
                    </div>
                    <pre className="mt-2 p-2.5 rounded-lg claude-code-box text-[11px] text-[#86efac] font-mono whitespace-pre-wrap break-words">{it.sql.trim()}</pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-[#242421] border border-[#33332f] text-xs text-[#a1a19a]">
            <Info className="w-4 h-4 text-[#d97757] mt-0.5 shrink-0" />
            <span>
              Retrieval-Augmented Generation looks up the most similar solved questions and, for large databases, only the relevant
              tables, then adds them to the prompt. Use the RAG switch above the search box to compare with the original prompt.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
