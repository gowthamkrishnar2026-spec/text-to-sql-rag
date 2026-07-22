"use client";

import React, { useState } from 'react';
import { Search, Sparkles, Send, Lightbulb, Loader2 } from 'lucide-react';

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

const SAMPLE_PROMPTS = [
  "Show all students with CGPA greater than 8",
  "Top 5 products by revenue",
  "Average salary per department",
  "List low stock products under 50 units",
  "Students enrolled in Computer Science"
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
    <div className="w-full glass-panel rounded-2xl p-4 lg:p-6 shadow-xl relative overflow-hidden">
      {/* Decorative ambient background glow */}
      <div className="absolute -top-24 -left-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <form onSubmit={handleSubmit} className="relative z-10">
        <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center justify-between">
          <span className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span>Ask Natural Language Question</span>
          </span>
          <span className="text-xs text-slate-500 font-normal">English → PostgreSQL</span>
        </label>

        <div className="relative flex items-center">
          <div className="absolute left-4 text-slate-400 pointer-events-none">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Show all students with CGPA greater than 8."
            disabled={isLoading}
            className="w-full pl-12 pr-32 py-3.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all text-sm sm:text-base"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="absolute right-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm flex items-center space-x-2 shadow-md shadow-blue-500/20 transition-all active:scale-95"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Converting...</span>
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
        <span className="text-xs text-slate-400 flex items-center space-x-1 mr-1">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          <span>Suggestions:</span>
        </span>
        {SAMPLE_PROMPTS.map((sample, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(sample)}
            disabled={isLoading}
            className="text-xs px-3 py-1 rounded-full bg-slate-800/80 hover:bg-blue-600/20 text-slate-300 hover:text-blue-300 border border-slate-700/60 hover:border-blue-500/40 transition-all"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
}
