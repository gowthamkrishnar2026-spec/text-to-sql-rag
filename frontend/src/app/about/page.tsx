"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { 
  Sparkles, Database, ShieldCheck, Cpu, Layers, BookOpen, Code2, 
  CheckCircle2, ArrowRight, Activity, Terminal, Download, ShieldAlert,
  Server, Zap
} from 'lucide-react';
import { apiClient } from '@/services/api';
import Link from 'next/link';

export default function AboutPage() {
  const [liveModel, setLiveModel] = useState<string>('Google Gemini 3.6 Flash');
  const [dbStatus, setDbStatus] = useState<boolean>(true);
  const [pingLatency, setPingLatency] = useState<number | null>(null);

  useEffect(() => {
    const checkSystem = async () => {
      const start = performance.now();
      try {
        const res = await apiClient.get('/health');
        const duration = Math.round(performance.now() - start);
        setPingLatency(duration);
        setDbStatus(res.data.database_connected ?? true);
        if (res.data.ai_model) {
          const modelName = res.data.ai_model.split('/').pop() || 'Google Gemini 3.6 Flash';
          setLiveModel(modelName);
        }
      } catch (err) {
        setDbStatus(false);
      }
    };
    checkSystem();
  }, []);

  const pipelineStages = [
    {
      step: '01',
      title: 'Prompt Contextualization',
      desc: 'User natural language is merged with live PostgreSQL schema definitions, relational keys, table descriptions and allowed column values.',
      icon: Terminal,
      badge: 'Input Prep',
      badgeClass: 'badge-neutral',
    },
    {
      step: '02',
      title: 'Retrieval (RAG)',
      desc: 'Embeds each table as a card and sends only the tables relevant to the question (plus their foreign-key neighbours), and can add similar solved questions to the prompt.',
      icon: Layers,
      badge: 'Retrieval',
      badgeClass: 'badge-blue',
    },
    {
      step: '03',
      title: 'Gemini LLM Inference',
      desc: `Query passed to ${liveModel} targeting PostgreSQL dialect, returning executable SQL and chart specs.`,
      icon: Cpu,
      badge: 'AI Generation',
      badgeClass: 'badge-terracotta',
    },
    {
      step: '04',
      title: 'AST Security Guardrails',
      desc: 'Multi-layer AST validator blocks DDL/DML (DROP, DELETE, UPDATE, ALTER) ensuring 100% read-only safety.',
      icon: ShieldCheck,
      badge: 'Security Engine',
      badgeClass: 'badge-green',
    },
    {
      step: '05',
      title: 'PostgreSQL Execution',
      desc: 'SQL query runs in isolated transaction against multi-domain Spider benchmark tables with millisecond timing.',
      icon: Database,
      badge: 'Database Layer',
      badgeClass: 'badge-blue',
    },
    {
      step: '06',
      title: 'Analytics & Multi-Export',
      desc: 'Results are mapped to dynamic charts (Bar, Line, Pie, Area) and downloadable as CSV, Excel, or PDF.',
      icon: Download,
      badge: 'Visualization',
      badgeClass: 'badge-purple',
    },
  ];

  const techStackCategories = [
    {
      title: 'Frontend & UI Architecture',
      icon: Layers,
      color: 'text-[#d97757]',
      items: [
        { label: 'Framework', val: 'Next.js 16 (React 19 App Router)' },
        { label: 'Styling', val: 'Tailwind CSS + Claude Design System' },
        { label: 'Analytics', val: 'Recharts Responsive Visualizer' },
        { label: 'Icons & UX', val: 'Lucide React + Micro-animations' },
      ],
    },
    {
      title: 'Backend & Inference Engine',
      icon: Cpu,
      color: 'text-emerald-400',
      items: [
        { label: 'API Framework', val: 'FastAPI + Uvicorn ASGI Server' },
        { label: 'AI Model', val: liveModel },
        { label: 'Validation', val: 'Pydantic v2 Strong Typing' },
        { label: 'ORM / Driver', val: 'SQLAlchemy 2.0 + Psycopg2' },
      ],
    },
    {
      title: 'Retrieval (RAG) Layer',
      icon: Layers,
      color: 'text-[#f4a284]',
      items: [
        { label: 'Embeddings', val: 'Gemini Embedding API' },
        { label: 'Vector Store', val: 'ChromaDB (persistent)' },
        { label: 'Examples', val: 'Similar solved questions (top-k)' },
        { label: 'Large Schemas', val: 'Table retrieval + FK expansion' },
      ],
    },
    {
      title: 'Database & Relational Layer',
      icon: Database,
      color: 'text-[#93c5fd]',
      items: [
        { label: 'RDBMS', val: 'PostgreSQL 16 (Dockerized)' },
        { label: 'Dataset', val: 'Yale Spider Benchmark Multi-Domain' },
        { label: 'Domains', val: 'Academic, E-Commerce, Corporate' },
        { label: 'Relations', val: 'Full Foreign Key Integrity & Indexes' },
      ],
    },
    {
      title: 'Export & Document Generation',
      icon: Download,
      color: 'text-[#d8b4fe]',
      items: [
        { label: 'PDF Reports', val: 'ReportLab Tabular Engine' },
        { label: 'Spreadsheets', val: 'OpenPyXL Formatted XLSX' },
        { label: 'Raw Data', val: 'RFC-4180 Streaming CSV' },
        { label: 'Formatting', val: 'Metadata, Timestamps & SQL headers' },
      ],
    },
  ];

  const domains = [
    {
      name: 'Academic Domain',
      badge: 'badge-terracotta',
      tables: ['departments', 'instructors', 'students', 'courses', 'enrollments'],
      description: 'University relational model tracking student CGPA, course registrations, instructor salaries, and departmental budgets.',
    },
    {
      name: 'E-Commerce Domain',
      badge: 'badge-blue',
      tables: ['customers', 'orders', 'products', 'order_items'],
      description: 'Retail lifecycle tracking international customer orders, item quantities, pricing tiers, and real-time inventory.',
    },
    {
      name: 'Corporate Domain',
      badge: 'badge-purple',
      tables: ['corp_departments', 'employees'],
      description: 'Enterprise HR hierarchy managing job titles, corporate divisions, salary compensation, and hiring dates.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#141413] text-[#f3f3ee] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">

        {/* Hero Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full badge-terracotta text-xs font-mono">
            <BookOpen className="w-3.5 h-3.5" />
            <span>M.Tech Advanced AI System</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[#f3f3ee] tracking-tight">
            Text-to-SQL Semantic Query &amp; <br />
            <span className="text-[#d97757]">Automated Analytics Engine</span>
          </h1>
          <p className="text-[#a1a19a] text-sm sm:text-base leading-relaxed">
            A production-grade application combining Google Gemini generative AI with strict AST security guardrails,
            relational PostgreSQL execution, and instant data visualizations.
          </p>
        </div>

        {/* Live System Telemetry Banner */}
        <div className="claude-card p-5 bg-[#1c1c1a] border border-[#2b2b27]">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-[#2b2b27]">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-[#d97757]" />
              <h2 className="text-sm font-bold text-[#f3f3ee] uppercase tracking-wider font-mono">
                Live System Telemetry
              </h2>
            </div>
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 font-semibold">Services Operational</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
            <div className="space-y-1">
              <span className="text-[11px] text-[#a1a19a] font-mono">Active AI Model</span>
              <p className="text-sm font-bold text-[#f4a284] font-mono">{liveModel}</p>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] text-[#a1a19a] font-mono">Database Status</span>
              <p className="text-sm font-bold text-emerald-400 font-mono">
                {dbStatus ? 'PostgreSQL 16 Connected' : 'Disconnected'}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] text-[#a1a19a] font-mono">Round-Trip Ping</span>
              <p className="text-sm font-bold text-[#f3f3ee] font-mono">
                {pingLatency !== null ? `${pingLatency} ms` : 'Measuring...'}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] text-[#a1a19a] font-mono">Security Guard</span>
              <p className="text-sm font-bold text-[#86efac] font-mono">AST Read-Only Active</p>
            </div>
          </div>
        </div>

        {/* 5-Stage Query Execution Flow */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-[#d97757]" />
            <h2 className="text-lg font-bold text-[#f3f3ee]">End-to-End Query Execution Pipeline</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {pipelineStages.map((stage) => {
              const Icon = stage.icon;
              return (
                <div 
                  key={stage.step}
                  className="claude-card p-4 flex flex-col justify-between space-y-3 relative group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-[#d97757]">{stage.step}</span>
                      <span className={`text-[10px] px-2 py-0.2 rounded-full font-mono ${stage.badgeClass}`}>
                        {stage.badge}
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-[#242421] border border-[#33332f] text-[#f4a284] w-fit">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="text-xs font-bold text-[#f3f3ee]">{stage.title}</h3>
                    <p className="text-[11px] text-[#a1a19a] leading-relaxed">{stage.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tech Stack Matrix */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#d97757]" />
            <h2 className="text-lg font-bold text-[#f3f3ee]">System Architecture &amp; Stack</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {techStackCategories.map((cat) => {
              const Icon = cat.icon;
              return (
                <div key={cat.title} className="claude-card p-5 space-y-4">
                  <div className={`flex items-center space-x-2.5 ${cat.color}`}>
                    <div className="p-2 rounded-lg bg-[#242421] border border-[#33332f]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm font-bold text-[#f3f3ee]">{cat.title}</h3>
                  </div>

                  <div className="divide-y divide-[#242421] pt-1">
                    {cat.items.map((item, idx) => (
                      <div key={idx} className="py-2 flex items-center justify-between text-xs">
                        <span className="text-[#a1a19a] font-mono">{item.label}</span>
                        <span className="text-[#f3f3ee] font-mono font-semibold">{item.val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Spider Benchmark Schema Showcase */}
        <div className="claude-card p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#2b2b27]">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-[#242421] border border-[#33332f] text-[#93c5fd]">
                <Code2 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-[#f3f3ee]">Yale Spider Benchmark Dataset</h2>
                <p className="text-xs text-[#a1a19a]">Pre-seeded relational datasets for evaluating cross-domain query complexity</p>
              </div>
            </div>
            <Link
              href="/settings"
              className="flex items-center space-x-1 text-xs text-[#d97757] hover:text-[#e28363] font-medium"
            >
              <span>Explore 11 Tables</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {domains.map((dom) => (
              <div key={dom.name} className="p-4 rounded-xl bg-[#141413] border border-[#282824] space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-[#f3f3ee]">{dom.name}</h3>
                  <span className={`text-[10px] px-2 py-0.2 rounded-full font-mono ${dom.badge}`}>
                    {dom.tables.length} Tables
                  </span>
                </div>
                <p className="text-[11px] text-[#a1a19a] leading-relaxed">{dom.description}</p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {dom.tables.map((tbl) => (
                    <span key={tbl} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1c1c1a] border border-[#2b2b27] text-[#f4a284]">
                      {tbl}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Security & Validation Guardrails */}
        <div className="claude-card p-6 space-y-4">
          <div className="flex items-center space-x-2.5 text-[#86efac]">
            <div className="p-2 rounded-lg bg-[#242421] border border-[#33332f]">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#f3f3ee]">Security &amp; AST Guardrails</h2>
              <p className="text-xs text-[#a1a19a]">Zero-trust validation layer preventing injection and destructive operations</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-[#141413] border border-rose-950/40 space-y-2">
              <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold font-mono">
                <ShieldAlert className="w-4 h-4" />
                <span>Strictly Blocked SQL Patterns</span>
              </div>
              <p className="text-[11px] text-[#a1a19a]">
                AST tokenizer blocks any state modification, injection, or transaction escape keywords:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'GRANT', 'EXEC'].map((kw) => (
                  <span key={kw} className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/50 text-rose-300 border border-rose-900/50">
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#141413] border border-emerald-950/40 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold font-mono">
                <CheckCircle2 className="w-4 h-4" />
                <span>Permitted &amp; Enforced Operations</span>
              </div>
              <p className="text-[11px] text-[#a1a19a]">
                Read-only SELECT queries with relational joins, aggregates, subqueries, and window functions:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {['SELECT', 'INNER JOIN', 'LEFT JOIN', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT'].map((kw) => (
                  <span key={kw} className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-300 border border-emerald-900/50">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CTA to Workbench */}
        <div className="claude-card p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-[#f3f3ee]">Ready to test natural language queries?</h3>
            <p className="text-xs text-[#a1a19a] mt-0.5">
              Launch the Workbench to ask complex questions across academic, retail, and corporate schemas.
            </p>
          </div>
          <Link
            href="/"
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl btn-terracotta text-xs font-semibold whitespace-nowrap shadow-lg"
          >
            <Sparkles className="w-4 h-4" />
            <span>Launch Workbench</span>
          </Link>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-[#2b2b27] py-5 text-center text-xs text-[#686861] mt-12 bg-[#141413]">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-[#d97757]" />
            <span>AI Text-to-SQL System • M.Tech Engineering Architecture</span>
          </span>
          <span className="text-[#a1a19a] font-mono text-[11px]">
            {liveModel} • PostgreSQL 16 • Next.js 16
          </span>
        </div>
      </footer>
    </div>
  );
}
