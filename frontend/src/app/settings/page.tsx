"use client";

import React, { useEffect, useState, useMemo } from 'react';
import Navbar from '@/components/Navbar';
import { 
  Database, Table, Columns, Key, Loader2, Search, RefreshCw, 
  ExternalLink, Sparkles, Check, Copy, Layers, ShieldCheck, ArrowRight
} from 'lucide-react';
import { fetchDatabaseSchema } from '@/services/api';
import RagStatusCard from '@/components/RagStatusCard';
import Link from 'next/link';

interface TableDetails {
  columns: string[];
  detailed_columns: string[];
  foreign_keys: string[];
}

const DOMAIN_MAP: Record<string, { label: string; badgeClass: string; domain: 'academic' | 'ecommerce' | 'corporate' }> = {
  departments: { label: 'Academic', badgeClass: 'badge-terracotta', domain: 'academic' },
  instructors: { label: 'Academic', badgeClass: 'badge-terracotta', domain: 'academic' },
  students: { label: 'Academic', badgeClass: 'badge-terracotta', domain: 'academic' },
  courses: { label: 'Academic', badgeClass: 'badge-terracotta', domain: 'academic' },
  enrollments: { label: 'Academic', badgeClass: 'badge-terracotta', domain: 'academic' },
  customers: { label: 'E-Commerce', badgeClass: 'badge-blue', domain: 'ecommerce' },
  orders: { label: 'E-Commerce', badgeClass: 'badge-blue', domain: 'ecommerce' },
  products: { label: 'E-Commerce', badgeClass: 'badge-blue', domain: 'ecommerce' },
  order_items: { label: 'E-Commerce', badgeClass: 'badge-blue', domain: 'ecommerce' },
  corp_departments: { label: 'Corporate', badgeClass: 'badge-purple', domain: 'corporate' },
  employees: { label: 'Corporate', badgeClass: 'badge-purple', domain: 'corporate' },
};

function parseColumn(colStr: string) {
  const parts = colStr.trim().split(/\s+/);
  const name = parts[0] || '';
  const type = parts.slice(1).join(' ') || 'VARCHAR';
  return { name, type };
}

function getTypeBadge(type: string) {
  const upper = type.toUpperCase();
  if (upper.includes('INT') || upper.includes('SERIAL')) {
    return { label: type, style: 'badge-green text-[#86efac]' };
  }
  if (upper.includes('CHAR') || upper.includes('TEXT')) {
    return { label: type, style: 'badge-amber text-[#fde047]' };
  }
  if (upper.includes('NUMERIC') || upper.includes('DECIMAL') || upper.includes('FLOAT') || upper.includes('REAL')) {
    return { label: type, style: 'badge-blue text-[#93c5fd]' };
  }
  if (upper.includes('DATE') || upper.includes('TIME')) {
    return { label: type, style: 'badge-purple text-[#d8b4fe]' };
  }
  return { label: type, style: 'badge-neutral text-[#a1a19a]' };
}

function parseForeignKey(fkStr: string) {
  const cleaned = fkStr.replace(/[\['"\]]/g, '');
  const parts = cleaned.split('->').map(s => s.trim());
  const fromCol = parts[0] || '';
  const toParts = (parts[1] || '').split('.');
  const toTable = toParts[0] || '';
  const toCol = toParts[1] || '';
  return { fromCol, toTable, toCol };
}

export default function SchemaPage() {
  const [schema, setSchema] = useState<Record<string, TableDetails>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDomain, setSelectedDomain] = useState<'all' | 'academic' | 'ecommerce' | 'corporate'>('all');
  const [copiedTable, setCopiedTable] = useState<string | null>(null);

  const loadSchema = async () => {
    try {
      setRefreshing(true);
      const res = await fetchDatabaseSchema();
      setSchema(res.tables || {});
    } catch (err) {
      console.error('Failed to load DB schema:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadSchema();
  }, []);

  const handleCopyTableName = (tableName: string) => {
    navigator.clipboard.writeText(tableName);
    setCopiedTable(tableName);
    setTimeout(() => setCopiedTable(null), 1500);
  };

  // Compute schema stats
  const stats = useMemo(() => {
    const tableNames = Object.keys(schema);
    let totalCols = 0;
    let totalFKs = 0;

    tableNames.forEach((t) => {
      totalCols += schema[t].columns?.length || 0;
      totalFKs += schema[t].foreign_keys?.length || 0;
    });

    return {
      tableCount: tableNames.length,
      colCount: totalCols,
      fkCount: totalFKs,
    };
  }, [schema]);

  // Filtered tables
  const filteredTables = useMemo(() => {
    return Object.entries(schema).filter(([tableName, details]) => {
      // Domain filter
      const domainInfo = DOMAIN_MAP[tableName];
      if (selectedDomain !== 'all') {
        if (!domainInfo || domainInfo.domain !== selectedDomain) return false;
      }

      // Search query filter
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      const matchTable = tableName.toLowerCase().includes(q);
      const matchCols = details.columns?.some((c) => c.toLowerCase().includes(q));
      return matchTable || matchCols;
    });
  }, [schema, selectedDomain, searchQuery]);

  return (
    <div className="min-h-screen bg-[#141413] text-[#f3f3ee] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#2b2b27]">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-xl bg-[#242421] border border-[#33332f] text-[#d97757]">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-bold text-[#f3f3ee] tracking-tight">Database Schema Explorer</h1>
                <span className="text-[11px] px-2 py-0.5 rounded-full badge-terracotta font-mono">
                  PostgreSQL 16
                </span>
              </div>
              <p className="text-xs text-[#a1a19a] mt-0.5">
                Live reflection of tables, data types, and relational foreign keys fed into the Gemini AI system prompt.
              </p>
            </div>
          </div>

          {/* Refresh Action */}
          <button
            onClick={loadSchema}
            disabled={refreshing}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-[#242421] hover:bg-[#2e2e2a] border border-[#33332f] text-xs font-medium text-[#f3f3ee] transition-all hover:border-[#d97757]/50 disabled:opacity-50 self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#d97757] ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Synchronizing...' : 'Refresh Schema'}</span>
          </button>
        </div>

        {/* Retrieval (RAG) status */}
        <RagStatusCard />

        {/* Stats Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="claude-card p-4 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-[#a1a19a] font-mono">Total Tables</span>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-[#f3f3ee] font-mono">{stats.tableCount}</span>
              <span className="text-xs text-[#a1a19a]">relational entities</span>
            </div>
          </div>

          <div className="claude-card p-4 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-[#a1a19a] font-mono">Total Columns</span>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-[#f4a284] font-mono">{stats.colCount}</span>
              <span className="text-xs text-[#a1a19a]">schema attributes</span>
            </div>
          </div>

          <div className="claude-card p-4 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-[#a1a19a] font-mono">Foreign Keys</span>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-[#86efac] font-mono">{stats.fkCount}</span>
              <span className="text-xs text-[#a1a19a]">relational joins</span>
            </div>
          </div>

          <div className="claude-card p-4 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-[#a1a19a] font-mono">Engine Status</span>
            <div className="flex items-center space-x-2 pt-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-sm font-semibold text-emerald-400 font-mono">Connected</span>
            </div>
          </div>
        </div>

        {/* Controls Bar: Search & Domain Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#1c1c1a] p-2.5 rounded-xl border border-[#2b2b27]">
          {/* Domain Tabs */}
          <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0">
            {[
              { id: 'all' as const, label: 'All Tables', count: stats.tableCount },
              { id: 'academic' as const, label: 'Academic', count: 5 },
              { id: 'ecommerce' as const, label: 'E-Commerce', count: 4 },
              { id: 'corporate' as const, label: 'Corporate', count: 2 },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedDomain(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedDomain === tab.id
                    ? 'bg-[#282824] text-[#f4a284] border border-[#3d3d37] shadow-sm'
                    : 'text-[#a1a19a] hover:text-[#f3f3ee] hover:bg-[#242421]'
                }`}
              >
                <span>{tab.label}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-[#141413] text-[#a1a19a]">
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-[#686861] absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search table or column..."
              className="w-full pl-8 pr-3 py-1.5 bg-[#111110] border border-[#282824] rounded-lg text-xs text-[#f3f3ee] placeholder-[#686861] focus:outline-none focus:border-[#d97757] transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2 text-[10px] text-[#a1a19a] hover:text-[#f3f3ee]"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center text-[#686861] space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#d97757]" />
            <p className="text-xs font-medium">Inspecting PostgreSQL schema metadata...</p>
          </div>
        ) : filteredTables.length === 0 ? (
          <div className="claude-card p-12 text-center text-[#a1a19a] space-y-3">
            <Database className="w-8 h-8 text-[#686861] mx-auto" />
            <h3 className="text-sm font-semibold text-[#f3f3ee]">No matching tables found</h3>
            <p className="text-xs text-[#a1a19a]">
              No tables or columns match &quot;{searchQuery}&quot; under the selected domain filter.
            </p>
            <button
              onClick={() => { setSearchQuery(''); setSelectedDomain('all'); }}
              className="mt-2 text-xs text-[#d97757] hover:underline"
            >
              Reset filters
            </button>
          </div>
        ) : (
          /* Table Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredTables.map(([tableName, details]) => {
              const domainInfo = DOMAIN_MAP[tableName] || { label: 'General', badgeClass: 'badge-neutral', domain: 'academic' };
              const isCopied = copiedTable === tableName;

              return (
                <div
                  key={tableName}
                  className="claude-card p-5 space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-4">
                    {/* Table Card Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <Table className="w-4 h-4 text-[#d97757]" />
                          <h3 className="font-bold text-base text-[#f3f3ee] font-mono tracking-tight">
                            {tableName}
                          </h3>
                        </div>
                        <div className="flex items-center space-x-2 pt-0.5">
                          <span className={`text-[10px] px-2 py-0.2 rounded-full font-mono font-medium ${domainInfo.badgeClass}`}>
                            {domainInfo.label}
                          </span>
                          <span className="text-[11px] text-[#a1a19a] font-mono">
                            {details.columns?.length || 0} cols
                          </span>
                          {details.foreign_keys && details.foreign_keys.length > 0 && (
                            <span className="text-[11px] text-[#86efac] font-mono">
                              • {details.foreign_keys.length} FKs
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Copy Table Name Button */}
                      <button
                        onClick={() => handleCopyTableName(tableName)}
                        title="Copy table name"
                        className="p-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] border border-[#33332f] text-[#a1a19a] hover:text-[#f3f3ee] transition-colors"
                      >
                        {isCopied ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {/* Columns List */}
                    <div className="space-y-2 pt-3 border-t border-[#2b2b27]">
                      <div className="flex items-center justify-between text-[11px] text-[#a1a19a] font-semibold uppercase tracking-wider font-mono">
                        <span className="flex items-center space-x-1.5">
                          <Columns className="w-3.5 h-3.5 text-[#d97757]" />
                          <span>Attribute Columns</span>
                        </span>
                        <span>Type</span>
                      </div>

                      <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                        {(details.detailed_columns || []).map((colStr: string, idx: number) => {
                          const { name: colName, type: colType } = parseColumn(colStr);
                          const typeBadge = getTypeBadge(colType);
                          const isPk = idx === 0 || colName.endsWith('_id') && colName.startsWith(tableName.slice(0, 3));
                          const isMatch = searchQuery && colName.toLowerCase().includes(searchQuery.toLowerCase().trim());

                          return (
                            <div 
                              key={idx} 
                              className={`p-2 rounded-lg bg-[#111110] border ${
                                isMatch ? 'border-[#d97757]/60 bg-[#d97757]/5' : 'border-[#282824]'
                              } text-xs font-mono flex items-center justify-between transition-colors`}
                            >
                              <div className="flex items-center space-x-2 min-w-0">
                                {isPk && (
                                  <span className="text-[9px] px-1.5 py-0.2 rounded font-bold bg-[#d97757]/20 text-[#f4a284] border border-[#d97757]/30 shrink-0">
                                    PK
                                  </span>
                                )}
                                <span className={`truncate ${isMatch ? 'text-[#f4a284] font-semibold' : 'text-[#f3f3ee]'}`}>
                                  {colName}
                                </span>
                              </div>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-medium shrink-0 ml-2 ${typeBadge.style}`}>
                                {typeBadge.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Foreign Keys Section */}
                    {details.foreign_keys && details.foreign_keys.length > 0 && (
                      <div className="pt-3 border-t border-[#2b2b27] space-y-2">
                        <span className="text-[11px] text-[#a1a19a] font-semibold uppercase tracking-wider font-mono flex items-center space-x-1.5">
                          <Key className="w-3.5 h-3.5 text-[#d97757]" />
                          <span>Relational Foreign Keys</span>
                        </span>
                        <div className="space-y-1.5">
                          {details.foreign_keys.map((fkStr: string, idx: number) => {
                            const { fromCol, toTable, toCol } = parseForeignKey(fkStr);
                            return (
                              <div 
                                key={idx} 
                                className="p-2 rounded-lg bg-[#141413] border border-[#282824] flex items-center justify-between text-xs font-mono"
                              >
                                <span className="text-[#f3f3ee] font-medium">{fromCol}</span>
                                <div className="flex items-center space-x-1.5 text-[11px] text-[#f4a284]">
                                  <ArrowRight className="w-3 h-3 text-[#a1a19a]" />
                                  <span className="text-[#93c5fd] font-semibold">{toTable}</span>
                                  <span className="text-[#a1a19a]">({toCol})</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Card Bottom: Quick Query Action */}
                  <div className="pt-3 mt-3 border-t border-[#2b2b27] flex items-center justify-between text-xs text-[#686861]">
                    <span className="font-mono text-[11px]">{details.columns?.length} indexed fields</span>
                    <Link
                      href="/"
                      className="flex items-center space-x-1 text-[#d97757] hover:text-[#e28363] font-medium transition-colors"
                    >
                      <span>Query in Workbench</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </main>
    </div>
  );
}
