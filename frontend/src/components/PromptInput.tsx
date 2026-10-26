"use client";

import React, { useState } from 'react';
import { Search, Sparkles, Send, Lightbulb, Loader2, Layers } from 'lucide-react';

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
  useRag?: boolean;
  onToggleRag?: (value: boolean) => void;
}

const SAMPLE_PROMPTS = [
  "Show all students with CGPA between 7 to 9",
  "Show all students with CGPA greater than 8",
  "Top 5 products by revenue",
  "Average salary per department",
  "List low stock products under 50 units"
];

export default function PromptInput({ onSubmit, isLoading, useRag = true, onToggleRag }: PromptInputProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim());
    }
  };

  const handleChipClick = (sample: string) => {
    setPrompt(sample);
    if (!isLoading) {
      onSubmit(sample);
    }
  };

  return (
    <div className="w-full claude-card p-5 sm:p-6 shadow-xl relative overflow-hidden">
      <form onSubmit={handleSubmit} className="relative z-10 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs uppercase font-mono tracking-wider font-semibold text-[#a1a19a] flex items-center space-x-2">
            <Sparkles className="w-3.5 h-3.5 text-[#d97757]" />
            <span>Interactive Natural Language Workbench</span>
          </label>
          <div className="flex items-center space-x-3">
            {onToggleRag && (
              <button
                type="button"
                onClick={() => onToggleRag(!useRag)}
                disabled={isLoading}
                title="Retrieval-Augmented Generation: add similar solved questions (and, for large databases, only relevant tables) to the prompt"
                className={`flex items-center space-x-1.5 text-[11px] px-2.5 py-1 rounded-full font-mono font-medium border transition-all ${
                  useRag ? 'badge-terracotta' : 'bg-[#242421] text-[#686861] border-[#33332f] hover:text-[#a1a19a]'
                }`}
              >
                <Layers className="w-3 h-3" />
                <span>RAG {useRag ? 'On' : 'Off'}</span>
              </button>
            )}
            <span className="text-xs text-[#a1a19a] font-mono hidden sm:inline">
              Gemini 3.6 Flash → PostgreSQL
            </span>
          </div>
        </div>

        <div className="relative flex items-center">
          <div className="absolute left-4 text-[#686861] pointer-events-none">
            <Search className="w-5 h-5 text-[#d97757]" />
          </div>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what data you want to query in plain English..."
            disabled={isLoading}
            className="w-full pl-12 pr-36 py-3.5 bg-[#111110] border border-[#282824] rounded-xl text-[#f3f3ee] placeholder-[#686861] focus:outline-none focus:border-[#d97757] transition-all text-sm font-sans"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="absolute right-2 px-4 py-2 bg-[#d97757] hover:bg-[#e28363] disabled:opacity-50 text-white rounded-lg font-medium text-xs sm:text-sm flex items-center space-x-2 transition-all shadow-sm"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <span>Run Query</span>
                <Send className="w-3 h-3" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Suggested Chips */}
      <div className="mt-4 flex items-center flex-wrap gap-2 relative z-10">
        <span className="text-xs text-[#686861] font-medium flex items-center space-x-1 mr-1">
          <Lightbulb className="w-3.5 h-3.5 text-[#d97757]" />
          <span>Popular Prompts:</span>
        </span>
        {SAMPLE_PROMPTS.map((sample, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(sample)}
            disabled={isLoading}
            className="text-xs px-3 py-1 rounded-full bg-[#242421] hover:bg-[#2e2e2a] text-[#a1a19a] hover:text-[#f3f3ee] border border-[#33332f] hover:border-[#d97757]/40 transition-all font-medium"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
}

