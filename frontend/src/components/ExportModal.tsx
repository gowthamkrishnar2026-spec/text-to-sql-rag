"use client";

import React, { useState } from 'react';
import { Download, FileText, FileSpreadsheet, FileCode, X, Loader2 } from 'lucide-react';
import { exportQueryData } from '@/services/api';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  columns: string[];
  rows: Record<string, any>[];
  sqlQuery: string;
}

export default function ExportModal({ isOpen, onClose, columns, rows, sqlQuery }: ExportModalProps) {
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      setDownloadingFormat(format);
      await exportQueryData(columns, rows, sqlQuery, format);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setDownloadingFormat(null);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md glass-panel rounded-2xl p-6 border border-slate-700 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Export Dataset</h3>
            <p className="text-xs text-slate-400">Select preferred download format</p>
          </div>
        </div>

        {/* Export Options */}
        <div className="space-y-3 mt-6">
          <button
            onClick={() => handleExport('csv')}
            disabled={!!downloadingFormat}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-left transition-all hover:border-blue-500/50 group"
          >
            <div className="flex items-center space-x-3">
              <FileCode className="w-6 h-6 text-emerald-400 group-hover:scale-110 transition-transform" />
              <div>
                <h4 className="font-semibold text-sm text-white">CSV Format (.csv)</h4>
                <p className="text-xs text-slate-400">Standard comma-separated text file</p>
              </div>
            </div>
            {downloadingFormat === 'csv' ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Download className="w-4 h-4 text-slate-500 group-hover:text-blue-400" />}
          </button>

          <button
            onClick={() => handleExport('excel')}
            disabled={!!downloadingFormat}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-left transition-all hover:border-blue-500/50 group"
          >
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
              <div>
                <h4 className="font-semibold text-sm text-white">Excel Document (.xlsx)</h4>
                <p className="text-xs text-slate-400">Formatted spreadsheet for Excel & Numbers</p>
              </div>
            </div>
            {downloadingFormat === 'excel' ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Download className="w-4 h-4 text-slate-500 group-hover:text-blue-400" />}
          </button>

          <button
            onClick={() => handleExport('pdf')}
            disabled={!!downloadingFormat}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-left transition-all hover:border-blue-500/50 group"
          >
            <div className="flex items-center space-x-3">
              <FileText className="w-6 h-6 text-rose-400 group-hover:scale-110 transition-transform" />
              <div>
                <h4 className="font-semibold text-sm text-white">PDF Report (.pdf)</h4>
                <p className="text-xs text-slate-400">Print-ready document with SQL query metadata</p>
              </div>
            </div>
            {downloadingFormat === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Download className="w-4 h-4 text-slate-500 group-hover:text-blue-400" />}
          </button>
        </div>

      </div>
    </div>
  );
}
