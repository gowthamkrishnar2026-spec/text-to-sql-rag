"use client";

import React, { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { Database, Table, Columns, Key, ShieldCheck } from 'lucide-react';
import { fetchDatabaseSchema } from '@/services/api';

export default function SchemaPage() {
  const [schema, setSchema] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadSchema = async () => {
      try {
        const res = await fetchDatabaseSchema();
        setSchema(res.tables || {});
      } catch (err) {
        console.error('Failed to load DB schema:', err);
      } finally {
        setLoading(false);
      }
    };
    loadSchema();
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <div className="p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Database Schema Inspector</h1>
            <p className="text-xs text-slate-400">Live reflection of PostgreSQL tables, column types, and relational foreign keys fed into AI context.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 text-sm">Inspecting PostgreSQL database schema...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(schema).map(([tableName, details]: [string, any]) => (
              <div
                key={tableName}
                className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4 hover:border-blue-500/40 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Table className="w-5 h-5 text-indigo-400" />
                    <h3 className="font-bold text-lg text-white font-mono">{tableName}</h3>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                    {details.columns.length} columns
                  </span>
                </div>

                {/* Columns List */}
                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <span className="text-xs text-slate-400 font-semibold flex items-center space-x-1 mb-2">
                    <Columns className="w-3.5 h-3.5 text-blue-400" />
                    <span>Columns & Data Types</span>
                  </span>
                  <div className="space-y-1">
                    {details.detailed_columns.map((colStr: string, idx: number) => (
                      <div key={idx} className="p-2 rounded-lg bg-slate-950/70 text-xs font-mono text-slate-300 flex justify-between">
                        <span>{colStr}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Foreign Keys */}
                {details.foreign_keys && details.foreign_keys.length > 0 && (
                  <div className="pt-2 border-t border-slate-800">
                    <span className="text-xs text-slate-400 font-semibold flex items-center space-x-1 mb-1">
                      <Key className="w-3.5 h-3.5 text-amber-400" />
                      <span>Foreign Keys</span>
                    </span>
                    {details.foreign_keys.map((fkStr: string, idx: number) => (
                      <span key={idx} className="block text-[11px] font-mono text-amber-300">
                        {fkStr}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
