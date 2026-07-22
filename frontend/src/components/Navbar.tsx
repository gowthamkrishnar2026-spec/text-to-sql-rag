"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Database, Sparkles, History, Settings, Info, Server, Cpu } from 'lucide-react';
import { apiClient } from '@/services/api';

export default function Navbar() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [modelName, setModelName] = useState<string>('DeepSeek-Coder-33B');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiClient.get('/health');
        setIsOnline(res.data.database_connected ?? true);
        if (res.data.ai_model) {
          const raw = res.data.ai_model.split('/').pop() || 'DeepSeek-Coder-33B';
          setModelName(raw);
        }
      } catch (err) {
        setIsOnline(false);
      }
    };
    checkHealth();
  }, []);

  const navLinks = [
    { name: 'Dashboard', href: '/', icon: Sparkles },
    { name: 'History', href: '/history', icon: History },
    { name: 'DB Schema', href: '/settings', icon: Settings },
    { name: 'About', href: '/about', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Database className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg text-white tracking-wide">Text2SQL</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                Frontier SOTA AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">PostgreSQL • DeepSeek / Qwen SOTA Engine</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1.5 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status Badges */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-purple-300 font-mono font-medium">{modelName}</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400' : 'bg-rose-500'}`} />
            <span className={isOnline ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
              {isOnline ? 'PostgreSQL Active' : 'Offline'}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}
