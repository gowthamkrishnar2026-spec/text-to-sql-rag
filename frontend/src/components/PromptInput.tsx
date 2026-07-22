"use client";

import React, { useState } from 'react';
import { Search, Sparkles, Send, Lightbulb, Loader2 } from 'lucide-react';

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

const SAMPLE_PROMPTS = [
  "Show all students with CGPA between 7 to 9",
  "Show all students with CGPA greater than 8",
  "Top 5 products by revenue",
  "Average salary per department",
  "List low stock products under 50 units"
];

export default function PromptInput({ onSubmit, isLoading }: PromptInputProps) {
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
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-6 shadow-2xl relative overflow-hidden gradient-border-glow">
      {/* Background Glows */}
      <div className="ambient-glow-blue -top-20 -left-20" />
      <div className="ambient-glow-purple -bottom-20 -right-20" />

      <form onSubmit={handleSubmit} className="relative z-10 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
            <span>Ask Natural Language Question</span>
          </label>
          <span className="text-xs text-indigo-400 font-mono font-medium">English → SOTA PostgreSQL</span>
        </div>

        <div className="relative flex items-center">
          <div className="absolute left-4 text-slate-400 pointer-events-none">
            <Search className="w-5 h-5 text-indigo-400" />
          </div>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Show all students with CGPA between 7 to 9."
            disabled={isLoading}
            className="w-full pl-12 pr-36 py-4 bg-slate-950/90 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/60 focus:border-indigo-500 transition-all text-sm sm:text-base shadow-inner font-sans"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="absolute right-2.5 px-4 py-2.5 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-xs sm:text-sm flex items-center space-x-2 shadow-lg shadow-indigo-500/30 transition-all active:scale-95"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <span>Generate & Run</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Suggested Chips */}
      <div className="mt-4 flex items-center flex-wrap gap-2 relative z-10">
        <span className="text-xs text-slate-400 font-medium flex items-center space-x-1 mr-1">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          <span>Suggestions:</span>
        </span>
        {SAMPLE_PROMPTS.map((sample, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(sample)}
            disabled={isLoading}
            className="text-xs px-3.5 py-1.5 rounded-full bg-slate-900/90 hover:bg-indigo-600/20 text-slate-300 hover:text-indigo-300 border border-slate-800 hover:border-indigo-500/40 transition-all font-medium"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
}
