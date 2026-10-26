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
    <div className="w-full claude-card p-5 shadow-xl flex flex-col h-full">
      
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-[#242421] border border-[#33332f] text-[#d97757]">
            <TableIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-[#f3f3ee] text-sm">Execution Output</h3>
            <div className="flex items-center space-x-3 text-xs text-[#a1a19a] mt-0.5">
              <span className="flex items-center space-x-1 font-mono text-[#f3f3ee]">
                <Database className="w-3.5 h-3.5 text-[#d97757]" />
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
            <Search className="w-3.5 h-3.5 text-[#686861] absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter output..."
              className="pl-8 pr-3 py-1.5 bg-[#111110] border border-[#282824] rounded-lg text-xs text-[#f3f3ee] placeholder-[#686861] focus:outline-none focus:border-[#d97757] w-40"
            />
          </div>

          <button
            onClick={onExportClick}
            className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#242421] hover:bg-[#2e2e2a] text-[#f3f3ee] border border-[#33332f] transition-colors font-medium"
          >
            <Download className="w-3.5 h-3.5 text-[#d97757]" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-x-auto rounded-xl border border-[#2b2b27] bg-[#111110] max-h-[400px]">
        {columns.length === 0 || paginatedRows.length === 0 ? (
          <div className="py-16 text-center text-[#686861] flex flex-col items-center justify-center">
            <Database className="w-8 h-8 text-[#383833] mb-2" />
            <p className="text-xs font-medium">No record rows found matching criteria</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#1c1c1a] text-[#a1a19a] font-semibold sticky top-0 border-b border-[#2b2b27]">
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx} className="px-4 py-2.5 uppercase tracking-wider font-mono text-[10px] text-[#f4a284]">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#242421] text-[#f3f3ee]">
              {paginatedRows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-[#1a1a18] transition-colors">
                  {columns.map((col, cIdx) => (
                    <td key={cIdx} className="px-4 py-2.5 whitespace-nowrap font-mono text-xs text-[#a1a19a]">
                      {row[col] === null || row[col] === undefined ? (
                        <span className="text-[#686861] italic">null</span>
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
        <div className="flex items-center justify-between mt-3 pt-2 text-xs text-[#a1a19a]">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-[#242421] disabled:opacity-40 hover:bg-[#2e2e2a]"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-[#242421] disabled:opacity-40 hover:bg-[#2e2e2a]"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

