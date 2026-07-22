"use client";

import React, { useState } from 'react';
import { Table as TableIcon, Clock, Database, Search, ChevronLeft, ChevronRight, Download } from 'lucide-react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, any>[];
  rowCount: number;
  executionTimeMs: number;
  onExportClick: () => void;
}

export default function ResultsTable({
  columns,
  rows,
  rowCount,
  executionTimeMs,
  onExportClick
}: ResultsTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Filter rows based on search term
  const filteredRows = rows.filter((row) =>
    columns.some((col) => {
      const val = row[col];
      return val !== null && val !== undefined && String(val).toLowerCase().includes(searchTerm.toLowerCase());
    })
  );

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const paginatedRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="w-full glass-panel rounded-2xl p-5 shadow-xl border border-slate-800 flex flex-col h-full">
      
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <TableIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-base">Query Results</h3>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mt-0.5">
              <span className="flex items-center space-x-1 font-mono text-slate-300">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                <span>{rowCount} rows</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1 font-mono text-emerald-400">
                <Clock className="w-3.5 h-3.5" />
                <span>{executionTimeMs} ms</span>
              </span>
            </div>
          </div>
        </div>

        {/* Controls: Search + Export */}
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search in table..."
              className="pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700/80 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-44"
            />
          </div>

          <button
            onClick={onExportClick}
            className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors font-medium"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 max-h-[420px]">
        {columns.length === 0 || paginatedRows.length === 0 ? (
          <div className="py-16 text-center text-slate-500 flex flex-col items-center justify-center">
            <Database className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-sm font-medium">No record rows found matching criteria</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-900/90 text-slate-300 font-semibold sticky top-0 border-b border-slate-800 backdrop-blur-md">
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx} className="px-4 py-3 uppercase tracking-wider font-mono text-[11px] text-indigo-300">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {paginatedRows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                  {columns.map((col, cIdx) => (
                    <td key={cIdx} className="px-4 py-2.5 whitespace-nowrap font-mono text-slate-300">
                      {row[col] === null || row[col] === undefined ? (
                        <span className="text-slate-600 italic">null</span>
                      ) : (
                        String(row[col])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3 pt-2 text-xs text-slate-400">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-slate-800 disabled:opacity-40 hover:bg-slate-700"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-slate-800 disabled:opacity-40 hover:bg-slate-700"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
