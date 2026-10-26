"use client";

import React, { useState, useEffect } from 'react';
import { Download, FileText, FileSpreadsheet, FileCode, X, Loader2, CheckCircle2, Database, Code2 } from 'lucide-react';
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
  const [successFormat, setSuccessFormat] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !downloadingFormat) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, downloadingFormat, onClose]);

  if (!isOpen) return null;

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      setExportError(null);
      setDownloadingFormat(format);
      await exportQueryData(columns, rows, sqlQuery, format);
      setSuccessFormat(format);
      setTimeout(() => {
        setSuccessFormat(null);
        onClose();
      }, 900);
    } catch (err: any) {
      console.error('Export failed:', err);
      setExportError(err?.response?.data?.detail || 'Export failed. Please try again.');
    } finally {
      setDownloadingFormat(null);
    }
  };

  const exportFormats = [
    {
      id: 'csv' as const,
      title: 'CSV Format (.csv)',
      subtitle: 'Universal tabular data, RFC-4180 compliant',
      icon: FileCode,
      iconColor: 'text-[#86efac]',
      badge: 'Fastest',
      badgeClass: 'badge-green',
    },
    {
      id: 'excel' as const,
      title: 'Excel Workbook (.xlsx)',
      subtitle: 'Formatted spreadsheet with styled table headers & auto-fit columns',
      icon: FileSpreadsheet,
      iconColor: 'text-[#93c5fd]',
      badge: 'Rich Format',
      badgeClass: 'badge-blue',
    },
    {
      id: 'pdf' as const,
      title: 'PDF Executive Report (.pdf)',
      subtitle: 'Print-ready report containing SQL query, metadata & data table',
      icon: FileText,
      iconColor: 'text-[#f4a284]',
      badge: 'Doc Report',
      badgeClass: 'badge-terracotta',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg bg-[#1c1c1a] border border-[#2b2b27] rounded-2xl p-6 shadow-2xl relative animate-in zoom-in-95 duration-150 text-[#f3f3ee]"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={!!downloadingFormat}
          className="absolute top-5 right-5 text-[#a1a19a] hover:text-[#f3f3ee] p-1.5 rounded-lg hover:bg-[#242421] transition-colors disabled:opacity-30"
          aria-label="Close export dialog"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-4 pb-4 border-b border-[#2b2b27]">
          <div className="p-2.5 rounded-xl bg-[#242421] border border-[#33332f] text-[#d97757]">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#f3f3ee]">Export Query Dataset</h3>
            <p className="text-xs text-[#a1a19a]">Select your desired export file format</p>
          </div>
        </div>

        {/* Dataset Summary Pill */}
        <div className="mb-5 p-3 rounded-xl bg-[#111110] border border-[#282824] flex items-center justify-between text-xs font-mono">
          <div className="flex items-center space-x-2 text-[#a1a19a]">
            <Database className="w-3.5 h-3.5 text-[#d97757]" />
            <span>Dataset:</span>
            <span className="text-[#f3f3ee] font-semibold">{rows.length} rows</span>
            <span>•</span>
            <span className="text-[#f3f3ee] font-semibold">{columns.length} columns</span>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full badge-neutral">
            Ready to download
          </span>
        </div>

        {/* Error Alert if any */}
        {exportError && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs">
            {exportError}
          </div>
        )}

        {/* Export Options List */}
        <div className="space-y-3">
          {exportFormats.map((fmt) => {
            const Icon = fmt.icon;
            const isCurrentDownloading = downloadingFormat === fmt.id;
            const isCurrentSuccess = successFormat === fmt.id;

            return (
              <button
                key={fmt.id}
                onClick={() => handleExport(fmt.id)}
                disabled={!!downloadingFormat}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#141413] hover:bg-[#242421] border border-[#282824] hover:border-[#3d3d37] text-left transition-all group disabled:opacity-50"
              >
                <div className="flex items-center space-x-3.5">
                  <div className={`p-2 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] ${fmt.iconColor} group-hover:scale-105 transition-transform`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-xs text-[#f3f3ee] group-hover:text-[#f4a284] transition-colors">
                        {fmt.title}
                      </h4>
                      <span className={`text-[10px] px-2 py-0.2 rounded-full font-mono ${fmt.badgeClass}`}>
                        {fmt.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#a1a19a] mt-0.5 max-w-[280px]">
                      {fmt.subtitle}
                    </p>
                  </div>
                </div>

                <div className="shrink-0 pl-2">
                  {isCurrentDownloading ? (
                    <div className="flex items-center space-x-1.5 text-xs text-[#d97757]">
                      <Loader2 className="w-4 h-4 animate-spin" />
                    </div>
                  ) : isCurrentSuccess ? (
                    <div className="flex items-center space-x-1 text-xs text-emerald-400">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="p-1.5 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] text-[#686861] group-hover:text-[#f4a284] group-hover:border-[#3d3d37] transition-colors">
                      <Download className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="mt-5 pt-3 border-t border-[#2b2b27] flex items-center justify-between text-[11px] text-[#686861]">
          <span>Generated directly from PostgreSQL engine</span>
          <button
            onClick={onClose}
            disabled={!!downloadingFormat}
            className="text-[#a1a19a] hover:text-[#f3f3ee] hover:underline"
          >
            Cancel
          </button>
        </div>

      </div>
    </div>
  );
}
