"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { Layers, Play, RefreshCw, History as HistoryIcon, Info, ShieldCheck } from 'lucide-react';
import {
  fetchRagAblation, RagAblation,
  fetchHistoryEval, runHistoryEval, HistoryEvalState,
  fetchBenchmarkStatus, triggerBenchmarkRun,
} from '@/services/api';

const pct = (v?: number | null) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`);

function Bar({ value, tone = 'terracotta' }: { value: number; tone?: 'terracotta' | 'emerald' }) {
  return (
    <div className="w-full bg-[#2b2b27] rounded-full h-1.5 overflow-hidden">
      <div
        className={`h-1.5 rounded-full ${tone === 'emerald' ? 'bg-emerald-400' : 'bg-[#d97757]'}`}
        style={{ width: `${Math.max(1, Math.min(100, Math.round(value * 100)))}%` }}
      />
    </div>
  );
}

export default function RagImpactPanel() {
  const [abl, setAbl] = useState<RagAblation | null>(null);
  const [hist, setHist] = useState<HistoryEvalState | null>(null);
  const [benchRunning, setBenchRunning] = useState<'on' | 'off' | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try { setAbl(await fetchRagAblation()); } catch { /* panel simply stays empty */ }
    try { setHist(await fetchHistoryEval()); } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const histRunning = !!hist?.status.is_running;

  // Poll while the past-queries run or a dashboard benchmark is in progress
  useEffect(() => {
    if (!histRunning && !benchRunning) return;
    const t = setInterval(async () => {
      try {
        if (histRunning) setHist(await fetchHistoryEval());
        if (benchRunning) {
          const st = await fetchBenchmarkStatus();
          if (st && !st.is_running) { setBenchRunning(null); setAbl(await fetchRagAblation()); }
        }
      } catch { /* keep polling */ }
    }, 2500);
    return () => clearInterval(t);
  }, [histRunning, benchRunning]);

  const startHistory = async () => {
    setMsg(null);
    try {
      const r = await runHistoryEval(200, 4);
      if (r.status === 'already_running') setMsg('A past-queries run is already in progress.');
      setHist(await fetchHistoryEval());
    } catch { setMsg('Could not start the past-queries run. Is the backend reachable?'); }
  };

  const startBench = async (rag: boolean) => {
    setMsg(null);
    try {
      const r = await triggerBenchmarkRun(undefined, undefined, rag);
      if (r.status === 'already_running') { setMsg('A benchmark is already running.'); return; }
      setBenchRunning(rag ? 'on' : 'off');
    } catch { setMsg('Could not start the benchmark.'); }
  };

  const rows = abl?.ablation ? Object.entries(abl.ablation.summary) : [];
  const on = abl?.dashboard_runs?.on;
  const off = abl?.dashboard_runs?.off;
  const h = hist?.latest;
  const pctDone = hist && hist.status.total ? Math.round((hist.status.done / hist.status.total) * 100) : 0;

  return (
    <section className="claude-card p-5 sm:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-[#d97757]" />
          <h2 className="text-sm font-semibold text-[#f3f3ee]">Retrieval (RAG) Impact</h2>
        </div>
        <button onClick={load} className="self-start flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] text-[#a1a19a] hover:text-[#f3f3ee] border border-[#33332f] transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /><span>Refresh</span>
        </button>
      </div>

      {msg && <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-900/50 text-amber-200 text-xs">{msg}</div>}

      {/* 1. Dashboard benchmark: RAG on vs off */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#a1a19a] font-mono">30-question suite: RAG on vs off</h3>
          <div className="flex items-center gap-2">
            {(['off', 'on'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => startBench(mode === 'on')}
                disabled={!!benchRunning}
                className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] text-[#f3f3ee] border border-[#33332f] hover:border-[#d97757]/50 transition-all disabled:opacity-50"
              >
                {benchRunning === mode ? <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#d97757]" /> : <Play className="w-3 h-3 fill-current text-[#d97757]" />}
                <span>{benchRunning === mode ? 'Running…' : `Run with RAG ${mode}`}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {([['off', off], ['on', on]] as const).map(([mode, r]) => (
            <div key={mode} className="p-4 rounded-xl bg-[#111110] border border-[#282824]">
              <div className="flex items-center justify-between">
                <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-mono ${mode === 'on' ? 'badge-terracotta' : 'badge-neutral'}`}>RAG {mode}</span>
                <span className="text-[10px] text-[#686861] font-mono">{r ? new Date(r.run_timestamp).toLocaleString() : 'not run yet'}</span>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-[#f3f3ee] tracking-tight">{r ? pct(r.metrics.execution_accuracy) : '—'}</div>
              <div className="text-[11px] text-[#a1a19a] mb-2">execution accuracy{r ? ` • ${r.total_cases} cases • ${Math.round(r.metrics.avg_latency_ms)} ms avg` : ''}</div>
              <Bar value={r?.metrics.execution_accuracy ?? 0} tone={mode === 'on' ? 'terracotta' : 'emerald'} />
            </div>
          ))}
        </div>
        <p className="text-[11px] text-[#686861] flex items-start space-x-1.5">
          <Info className="w-3.5 h-3.5 shrink-0 mt-px" />
          <span>With RAG on, a benchmark question is never retrieved as its own example, so the score is not inflated.</span>
        </p>
      </div>

      {/* 2. Ablation table */}
      {rows.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#a1a19a] font-mono">
            Ablation{abl?.ablation?.run_timestamp ? ` • ${new Date(abl.ablation.run_timestamp).toLocaleDateString()}` : ''}
          </h3>
          <div className="overflow-x-auto rounded-xl border border-[#282824]">
            <table className="w-full text-xs">
              <thead className="bg-[#111110] text-[#a1a19a] font-mono text-[11px]">
                <tr>
                  <th className="text-left px-3 py-2">Configuration</th>
                  <th className="text-left px-3 py-2 w-40">Execution accuracy</th>
                  <th className="text-right px-3 py-2">Tables sent</th>
                  <th className="text-right px-3 py-2">Prompt tokens</th>
                  <th className="text-right px-3 py-2">Avg ms</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(([key, r]) => (
                  <tr key={key} className="border-t border-[#282824]">
                    <td className="px-3 py-2 text-[#f3f3ee]"><span className="font-mono text-[#d97757] mr-2">{key}</span>{r.label}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center space-x-2"><span className="font-mono text-[#f3f3ee] w-12">{pct(r.execution_accuracy)}</span><Bar value={r.execution_accuracy} /></div>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-[#a1a19a]">{r.avg_tables_in_prompt ? r.avg_tables_in_prompt.toFixed(1) : '-'}</td>
                    <td className="px-3 py-2 text-right font-mono text-[#a1a19a]">{Math.round(r.avg_prompt_tokens).toLocaleString()}</td>
                    <td className="px-3 py-2 text-right font-mono text-[#a1a19a]">{Math.round(r.avg_latency_ms)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-[#686861] flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 shrink-0 mt-px" />
            <span>Configuration A contains benchmark questions and answers in its prompt, so it scores higher than a fair test. Compare B (all tables, no examples) with C (retrieved tables only) and D (retrieved examples). One question is 3.3 points when n = 30, so treat 1-2 question gaps as noise.</span>
          </p>
        </div>
      )}

      {/* 3. Past queries */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <HistoryIcon className="w-3.5 h-3.5 text-[#d97757]" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#a1a19a] font-mono">All past queries: RAG on vs off</h3>
          </div>
          <button
            onClick={startHistory}
            disabled={histRunning}
            className="self-start flex items-center space-x-1.5 text-xs px-3.5 py-1.5 rounded-lg bg-[#d97757] hover:bg-[#e28363] text-white font-medium shadow-sm transition-all disabled:opacity-60"
          >
            {histRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{histRunning ? `Running ${hist?.status.done}/${hist?.status.total}…` : 'Re-run all past queries'}</span>
          </button>
        </div>

        {histRunning && (
          <div className="w-full bg-[#1c1c1a] rounded-full h-2 overflow-hidden border border-[#2b2b27]">
            <div className="bg-gradient-to-r from-[#d97757] to-emerald-400 h-2 rounded-full transition-all duration-300" style={{ width: `${pctDone}%` }} />
          </div>
        )}
        {hist?.status.error && !histRunning && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs">{hist.status.error}</div>
        )}

        {h ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {([['off', h.off], ['on', h.on]] as const).map(([mode, side]) => (
                <div key={mode} className="p-4 rounded-xl bg-[#111110] border border-[#282824] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-mono ${mode === 'on' ? 'badge-terracotta' : 'badge-neutral'}`}>RAG {mode}</span>
                    <span className="text-[10px] text-[#686861] font-mono">{side.prompts} prompts</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xl font-extrabold text-[#f3f3ee]">{pct(side.executed_ok_rate)}</div>
                      <div className="text-[11px] text-[#a1a19a]">ran without error</div>
                    </div>
                    <div>
                      <div className="text-xl font-extrabold text-[#f4a284]">{pct(side.match_previous_rate)}</div>
                      <div className="text-[11px] text-[#a1a19a]">same rows as before ({side.with_reference})</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#a1a19a] font-mono pt-1 border-t border-[#242421]">
                    <span className="flex items-center space-x-1"><ShieldCheck className="w-3 h-3 text-emerald-400" /><span>{side.guardrail_held}/{side.guardrail_total} unsafe prompts blocked</span></span>
                    <span>{Math.round(side.avg_latency_ms)} ms</span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-[#a1a19a] font-mono">
              RAG fixed {h.fixed} and changed {h.broke} previously matching answers • {h.prompts} prompts in {h.runtime_seconds}s ({h.workers} in parallel) • {new Date(h.run_timestamp).toLocaleString()}
            </p>
          </>
        ) : (
          !histRunning && <p className="text-xs text-[#a1a19a]">Not run yet. This re-asks every prompt in your history, with and without RAG, in parallel.</p>
        )}
        <p className="text-[11px] text-[#686861] flex items-start space-x-1.5">
          <Info className="w-3.5 h-3.5 shrink-0 mt-px" />
          <span>Past prompts have no hand-written correct answer. “Same rows as before” compares with the most recent successful SQL logged for the same prompt, so it measures consistency, not proven correctness.</span>
        </p>
      </div>
    </section>
  );
}
