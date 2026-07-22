"use client";

import React from 'react';
import Navbar from '@/components/Navbar';
import { Info, Sparkles, Database, ShieldCheck, Cpu, Layers } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>M.Tech M.Tech Project Architecture</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">AI-Powered Text-to-SQL Semantic Query System</h1>
          <p className="text-slate-400 text-sm max-w-2xl mx-auto">
            A production-ready full-stack application designed to translate complex natural English prompts into executable, secure SQL queries with automated visualization dashboards.
          </p>
        </div>

        {/* Tech Stack Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-3">
            <div className="flex items-center space-x-3 text-blue-400">
              <Layers className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Frontend Architecture</h3>
            </div>
            <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside font-mono">
              <li>Next.js 15 (React 19 App Router)</li>
              <li>Tailwind CSS + Glassmorphism UX</li>
              <li>Recharts (Dynamic Bar, Line, Pie & Area Charts)</li>
              <li>Axios API Client</li>
            </ul>
          </div>

          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-3">
            <div className="flex items-center space-x-3 text-emerald-400">
              <Cpu className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Backend & AI Engine</h3>
            </div>
            <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside font-mono">
              <li>FastAPI + Uvicorn ASGI Server</li>
              <li>Hugging Face Transformers (SQLCoder / T5)</li>
              <li>SQLAlchemy ORM + Schema Reflection</li>
              <li>Pydantic Input Validation</li>
            </ul>
          </div>
        </div>

        {/* Security & Validation */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-amber-400">
            <ShieldCheck className="w-6 h-6" />
            <h3 className="text-lg font-bold text-white">SQL Security & Safety Enforcement</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The backend incorporates a multi-layer SQL validator using AST tokenization. Destructive DDL/DML statements 
            (<code className="text-rose-400">DROP</code>, <code className="text-rose-400">DELETE</code>, <code className="text-rose-400">UPDATE</code>, <code className="text-rose-400">ALTER</code>, <code className="text-rose-400">TRUNCATE</code>) 
            as well as multiple statement injection attacks are automatically blocked. Only read-only <code className="text-emerald-400">SELECT</code> operations are permitted.
          </p>
        </div>

        {/* Dataset Info */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-3">
          <div className="flex items-center space-x-3 text-purple-400">
            <Database className="w-6 h-6" />
            <h3 className="text-lg font-bold text-white">Spider Dataset Benchmark Integration</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Inspired by the Yale Spider Benchmark (cross-domain Text-to-SQL evaluation dataset), the system pre-populates PostgreSQL with relational databases across University, E-Commerce, and Corporate domains for rich multi-table join and aggregation testing.
          </p>
        </div>

      </main>
    </div>
  );
}
